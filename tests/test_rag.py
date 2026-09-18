"""Unit tests for the RAG pipeline: retrieval math, scoping, and the
generation prompt — not through the HTTP API (see `test_unit_services.py`
for the rationale on this style: service-layer functions called directly).

Embeddings are never computed by the real `sentence-transformers` model
here (too slow, and it's third-party behavior, not ours to test) — vectors
are hand-crafted, and `_call_llm` is monkeypatched wherever an LLM call
would otherwise happen.
"""

import json

from sqlmodel import Session, SQLModel, create_engine

from app.models.designation import Designation
from app.models.job import Job
from app.models.jobdesignation import JobDesignation
from app.models.userdesignation import UserDesignation
from app.services.llm import answer_job_query, extract_search_filters
from app.services.rag.retrieval import cosine_similarity, search_jobs


def test_cosine_similarity_identical_vectors_returns_one():
    v = [1.0, 2.0, 3.0]
    assert cosine_similarity(v, v) == 1.0


def test_cosine_similarity_orthogonal_vectors_returns_zero():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_cosine_similarity_opposite_vectors_returns_negative_one():
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == -1.0


def test_cosine_similarity_handles_zero_vector_without_raising():
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def _make_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return engine


def _seed_user_and_designation(session: Session):
    from app.models.user import User

    user = User(email="u@example.com", hashed_password="x", full_name="U")
    session.add(user)
    designation = Designation(title="Backend Engineer")
    session.add(designation)
    session.commit()
    session.refresh(user)
    session.refresh(designation)
    return user.id, designation.id


def _add_job(session: Session, designation_id, **fields) -> Job:
    """Insert a Job plus its JobDesignation link — `search_jobs()` scopes
    visibility through that table, not `Job.designation_id`, directly."""
    job = Job(designation_id=designation_id, **fields)
    session.add(job)
    session.commit()
    session.refresh(job)
    session.add(JobDesignation(job_id=job.id, designation_id=designation_id))
    session.commit()
    return job


def test_search_jobs_ranks_by_similarity_to_query():
    """A job whose embedding points the same direction as the query should
    outrank one whose embedding is orthogonal to it."""
    engine = _make_engine()
    with Session(engine) as session:
        user_id, designation_id = _seed_user_and_designation(session)
        session.add(UserDesignation(user_id=user_id, designation_id=designation_id))

        _add_job(
            session, designation_id,
            title="Close match", company="Acme", location="Remote", description="",
            source="indeed", source_url="https://x/close",
            embedding=json.dumps([1.0, 0.0]),
        )
        _add_job(
            session, designation_id,
            title="Far match", company="Acme", location="Remote", description="",
            source="indeed", source_url="https://x/far",
            embedding=json.dumps([0.0, 1.0]),
        )

        results = search_jobs(session, user_id, query_embedding=[1.0, 0.0], top_k=5)

        assert [job.title for job, _ in results] == ["Close match", "Far match"]
        assert results[0][1] == 1.0
        assert results[1][1] == 0.0


def test_search_jobs_respects_top_k():
    engine = _make_engine()
    with Session(engine) as session:
        user_id, designation_id = _seed_user_and_designation(session)
        session.add(UserDesignation(user_id=user_id, designation_id=designation_id))

        for i in range(3):
            _add_job(
                session, designation_id,
                title=f"Job {i}", company="Acme", location="Remote", description="",
                source="indeed", source_url=f"https://x/{i}",
                embedding=json.dumps([1.0, 0.0]),
            )

        results = search_jobs(session, user_id, query_embedding=[1.0, 0.0], top_k=2)
        assert len(results) == 2


def test_search_jobs_excludes_jobs_without_an_embedding():
    engine = _make_engine()
    with Session(engine) as session:
        user_id, designation_id = _seed_user_and_designation(session)
        session.add(UserDesignation(user_id=user_id, designation_id=designation_id))
        _add_job(
            session, designation_id,
            title="Not yet embedded", company="Acme", location="Remote", description="",
            source="indeed", source_url="https://x/no-embedding",
            embedding=None,
        )

        results = search_jobs(session, user_id, query_embedding=[1.0, 0.0], top_k=5)
        assert results == []


def test_search_jobs_excludes_jobs_outside_users_designations():
    """A job filed under a designation the user isn't subscribed to must
    not be searchable, mirroring the access boundary in fetch_job_records."""
    engine = _make_engine()
    with Session(engine) as session:
        user_id, subscribed_designation_id = _seed_user_and_designation(session)
        other_designation = Designation(title="Data Engineer")
        session.add(other_designation)
        session.commit()
        session.refresh(other_designation)

        session.add(UserDesignation(user_id=user_id, designation_id=subscribed_designation_id))
        session.commit()
        _add_job(
            session, other_designation.id,
            title="Outside my designations", company="Acme", location="Remote", description="",
            source="indeed", source_url="https://x/outside",
            embedding=json.dumps([1.0, 0.0]),
        )

        results = search_jobs(session, user_id, query_embedding=[1.0, 0.0], top_k=5)
        assert results == []


def test_search_jobs_excludes_jobs_matching_exclude_terms():
    """A job whose location mentions an excluded term must not be returned,
    even if it's the closest semantic match — the fix for embedding
    similarity not honoring negation (e.g. "python jobs not remote")."""
    engine = _make_engine()
    with Session(engine) as session:
        user_id, designation_id = _seed_user_and_designation(session)
        session.add(UserDesignation(user_id=user_id, designation_id=designation_id))

        _add_job(
            session, designation_id,
            title="Python Developer", company="Acme", location="Bangalore, Remote", description="",
            source="indeed", source_url="https://x/remote",
            embedding=json.dumps([1.0, 0.0]),
        )
        _add_job(
            session, designation_id,
            title="Python Developer", company="Beta", location="Bangalore", description="On-site only.",
            source="indeed", source_url="https://x/onsite",
            embedding=json.dumps([0.9, 0.1]),
        )

        results = search_jobs(
            session, user_id, query_embedding=[1.0, 0.0], top_k=5, exclude_terms=["remote"]
        )

        assert [job.source_url for job, _ in results] == ["https://x/onsite"]


def test_search_jobs_exclude_terms_is_whole_word_only():
    """"remote" must not false-match a job whose location is merely
    "Remotely" or similar — the filter is a whole-word check."""
    engine = _make_engine()
    with Session(engine) as session:
        user_id, designation_id = _seed_user_and_designation(session)
        session.add(UserDesignation(user_id=user_id, designation_id=designation_id))
        _add_job(
            session, designation_id,
            title="Python Developer", company="Acme", location="Remotington", description="",
            source="indeed", source_url="https://x/1",
            embedding=json.dumps([1.0, 0.0]),
        )

        results = search_jobs(
            session, user_id, query_embedding=[1.0, 0.0], top_k=5, exclude_terms=["remote"]
        )
        assert len(results) == 1


def test_extract_search_filters_prompt_asks_for_exclude_terms(monkeypatch):
    captured = {}

    def fake_call_llm(prompt, provider, api_key):
        captured["prompt"] = prompt
        return '{"exclude_terms": ["remote"]}'

    monkeypatch.setattr("app.services.llm._call_llm", fake_call_llm)

    result = extract_search_filters("python jobs not remote", provider="groq", api_key=None)

    assert result == '{"exclude_terms": ["remote"]}'
    assert "python jobs not remote" in captured["prompt"]
    assert "exclude_terms" in captured["prompt"]


def test_answer_job_query_grounds_prompt_in_matched_jobs(monkeypatch):
    captured = {}

    def fake_call_llm(prompt, provider, api_key):
        captured["prompt"] = prompt
        return "Job A at Acme is the best fit."

    monkeypatch.setattr("app.services.llm._call_llm", fake_call_llm)

    matched_jobs = [
        {"title": "Job A", "company": "Acme", "location": "Remote", "description": "Python backend role."},
    ]
    result = answer_job_query("which job is remote?", matched_jobs, provider="groq", api_key=None)

    assert result == "Job A at Acme is the best fit."
    assert "Job A" in captured["prompt"]
    assert "Acme" in captured["prompt"]
    assert "which job is remote?" in captured["prompt"]


def test_answer_job_query_returns_llm_reply_unchanged_with_no_matches(monkeypatch):
    monkeypatch.setattr("app.services.llm._call_llm", lambda prompt, provider, api_key: "No matching jobs.")

    result = answer_job_query("anything remote?", [], provider="groq", api_key=None)
    assert result == "No matching jobs."


def test_ask_jobs_route_applies_extracted_exclude_terms(client, engine, auth_headers, designation, monkeypatch):
    """End-to-end wiring test for POST /jobs/ask: a "not remote" query must
    exclude the remote job even though it's the closer embedding match —
    this is the actual user-visible fix for negation in search queries."""
    from app.api.v1 import job as job_module

    client.post("/api/v1/user-designation", json={"designation_id": designation["id"]}, headers=auth_headers)

    monkeypatch.setattr(job_module, "embed_text", lambda text: [1.0, 0.0])
    monkeypatch.setattr(
        job_module, "extract_search_filters",
        lambda query, provider, api_key: '{"exclude_terms": ["remote"]}',
    )
    monkeypatch.setattr(
        job_module, "answer_job_query",
        lambda query, matched_jobs, provider, api_key: f"{len(matched_jobs)} job(s) matched.",
    )

    with Session(engine) as session:
        _add_job(
            session, designation["id"],
            title="Python Developer", company="Acme", location="Bangalore, Remote", description="",
            source="indeed", source_url="https://x/remote-ask",
            embedding=json.dumps([1.0, 0.0]),
        )
        _add_job(
            session, designation["id"],
            title="Python Developer", company="Beta", location="Bangalore", description="On-site only.",
            source="indeed", source_url="https://x/onsite-ask",
            embedding=json.dumps([0.9, 0.1]),
        )

    resp = client.post(
        "/api/v1/jobs/ask", json={"query": "python jobs not remote", "top_k": 5}, headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert [m["source_url"] for m in body["matches"]] == ["https://x/onsite-ask"]
    assert body["answer"] == "1 job(s) matched."
