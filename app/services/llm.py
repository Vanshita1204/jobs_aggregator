"""Multi-provider LLM dispatch used for job-data extraction and CV tips.

Supported providers: groq, openai, anthropic, gemini. The caller supplies the
provider name and (optionally) an API key; only "groq" falls back to the
server-side GROQ_API_KEY when no key is supplied, since it is the app default.
"""

from app.core.config import settings

_PROVIDERS = {}


def _call_llm(prompt: str, provider: str, api_key: str | None) -> str:
    """Dispatch a prompt to the requested LLM provider and return its raw text reply.

    Input:
        prompt (str): fully-formed prompt text to send to the model.
        provider (str): one of "groq", "openai", "anthropic", "gemini"
            (case-insensitive); treated as "groq" if falsy.
        api_key (str | None): caller-supplied API key. Ignored for "groq"
            when not given (see logic below).

    Output:
        str: the raw text content of the model's response.

    Raises:
        ValueError: if `provider` does not match a key in `_PROVIDERS`.

    Calls: one of `_call_groq()` / `_call_openai()` / `_call_anthropic()` /
        `_call_gemini()`, selected via the `_PROVIDERS` dict.
    Called by: `extract_job_data()`, `get_cv_tips()` (both in this file).

    Variables:
        call (function): the provider-specific implementation looked up
            from `_PROVIDERS` for the normalised `provider` name.

    Logic:
        1. Normalise `provider` to lowercase, defaulting to "groq".
        2. Look up the matching call function in `_PROVIDERS`; raise
           ValueError if the provider name is unrecognised.
        3. Only for "groq" (the app's built-in default), fall back to the
           server-side `settings.GROQ_API_KEY` when the caller supplied no
           key — every other provider requires the caller's own key.
        4. Invoke the provider function with (prompt, api_key) and return
           its result unchanged.
    """
    provider = (provider or "groq").lower()
    call = _PROVIDERS.get(provider)
    if not call:
        raise ValueError(f"Unsupported provider: {provider}")
    if provider == "groq":
        api_key = api_key or settings.GROQ_API_KEY
    return call(prompt, api_key)


def extract_job_data(page_text: str, provider: str = "groq", api_key: str | None = None) -> str:
    """Build a JSON-extraction prompt and ask the LLM to pull job fields out of raw page text.

    Input:
        page_text (str): plain-text content scraped from the job posting
            page, already stripped of script/style/nav tags.
        provider (str): LLM provider name to use for extraction.
        api_key (str | None): caller-supplied API key for the provider.

    Output:
        str: the raw LLM response. Not guaranteed to be bare JSON — the
        caller must locate and `json.loads()` the JSON object within it
        (see `external_ingestion.py::_ingest_via_llm`, which does this via
        a regex search before parsing).

    Calls: `_call_llm()` (this file).
    Called by: `app.services.external_ingestion._ingest_via_llm()` — the
        fallback path used when a job URL does not match one of the
        natively-parsed portals (Indeed/LinkedIn/Hirist).

    Logic:
        Wraps `page_text` in a fixed instruction template that demands a
        single JSON object with exactly the fields title/company/location/
        description, then forwards it to `_call_llm()` unchanged.
    """
    prompt = (
        "Extract job posting details from the following webpage text.\n"
        "Return ONLY a valid JSON object with exactly these fields:\n"
        '{"title": "...", "company": "...", "location": "...", "description": "..."}\n'
        "Use empty string for any field not found. No extra text outside the JSON.\n\n"
        f"Webpage text:\n{page_text}"
    )
    return _call_llm(prompt, provider, api_key)


def extract_search_filters(query: str, provider: str = "groq", api_key: str | None = None) -> str:
    """Ask the LLM to pull hard exclusion terms out of a natural-language job search query.

    Embedding similarity (`app.services.rag.embeddings`) cannot represent
    negation reliably — "python jobs not remote" embeds *closer* to a
    remote-Python posting than a non-remote one, because small models like
    MiniLM mostly match on the salient keyword ("remote") and largely
    ignore the "not" in front of it (verified empirically: cosine
    similarity to a remote posting came out higher than to an otherwise
    identical on-site one). This function is the fix: an LLM call that
    reads the query and extracts anything the user explicitly wants
    excluded, so `search_jobs()` can hard-filter those terms out of the
    embedding-ranked candidates instead of relying on the vector alone.

    Input:
        query (str): the user's raw natural-language search/question, e.g.
            "python jobs not remote" or "backend roles, no Java".
        provider (str): LLM provider name to use.
        api_key (str | None): caller-supplied API key for the provider.

    Output:
        str: the raw LLM response, expected to contain one JSON object of
        the form `{"exclude_terms": ["..."]}`. Not guaranteed to be bare
        JSON — the caller must locate and `json.loads()` the JSON object
        within it (same convention as `extract_job_data()`; see
        `app.api.v1.job.ask_jobs()`, which does this via a regex search
        before parsing, and falls back to an empty list on any failure so
        a malformed/missing JSON degrades to "no filtering" rather than
        breaking the search).

    Calls: `_call_llm()` (this file).
    Called by: `app.api.v1.job.ask_jobs()` — the `POST /jobs/ask` route,
        before calling `search_jobs()`.

    Logic:
        Wraps `query` in a fixed instruction template that demands a
        single JSON object with one field, `exclude_terms` — short,
        lowercase words/phrases for anything the user explicitly wants
        excluded (e.g. "remote", "java") — and nothing for merely-implied
        or soft preferences, then forwards it to `_call_llm()` unchanged.
    """
    prompt = (
        "A user is searching job postings with this query:\n"
        f'"{query}"\n\n'
        "Identify any terms the user explicitly wants EXCLUDED from results "
        '(e.g. "not remote" -> "remote", "no Java" -> "java", '
        '"excluding Bangalore" -> "bangalore"). Only include terms tied to an '
        "explicit negation in the query — do not infer exclusions from soft "
        "preferences or anything not directly negated.\n"
        "Return ONLY a valid JSON object with exactly this field:\n"
        '{"exclude_terms": ["..."]}\n'
        "Use an empty list if nothing is explicitly excluded. No extra text outside the JSON."
    )
    return _call_llm(prompt, provider, api_key)


def get_cv_tips(
    job_title: str,
    company: str,
    location: str,
    cv_text: str,
    description: str = "",
    provider: str = "groq",
    api_key: str | None = None,
) -> str:
    """Build a CV-tailoring prompt and ask the LLM for 5 line-referenced improvement tips.

    Input:
        job_title (str): title of the job posting.
        company (str): hiring company name.
        location (str): job location, or empty string if unknown.
        cv_text (str): plain text extracted from the candidate's CV file.
        description (str): full job description text; when empty, the
            job-description section is omitted from the prompt entirely
            rather than sent as an empty placeholder (see logic).
        provider (str): LLM provider name to use.
        api_key (str | None): caller-supplied API key for the provider.

    Output:
        str: raw LLM response text containing 5 improvement suggestions.

    Calls: `_call_llm()` (this file).
    Called by: `app.api.v1.cv.cv_tips()` — the `POST /cvs/{cv_id}/tips/{job_id}` route.

    Variables:
        job_section (str): the job-title/company/location block of the
            prompt, built first and conditionally extended.
        prompt (str): the complete instruction sent to `_call_llm()`,
            combining `job_section`, `cv_text`, and the fixed grading
            instructions for the model.

    Logic:
        1. Assemble `job_section` from title/company/location.
        2. Append the job description to `job_section` only if non-empty,
           so the model isn't told "Job description:" with nothing after it.
        3. Concatenate `job_section` with `cv_text` and a fixed instruction
           block demanding exactly 5 tips, each tied to a specific CV
           line/section with a concrete reworded replacement.
        4. Forward the assembled prompt to `_call_llm()` and return its result.
    """
    job_section = (
        f"Job title: {job_title}\n"
        f"Company: {company}\n"
        f"Location: {location or 'Not specified'}\n"
    )
    if description:
        job_section += f"\nJob description:\n{description}\n"

    prompt = (
        f"{job_section}\n"
        f"CV:\n{cv_text}\n\n"
        "You are a senior recruiter reviewing this CV for the job above.\n"
        "Read the ENTIRE CV carefully, then give exactly 5 improvement suggestions.\n"
        "For each suggestion:\n"
        "- Quote or reference the specific CV line/section you are addressing\n"
        "- Explain what is wrong or missing\n"
        "- Give the exact reworded text or concrete addition to make\n\n"
        "Be blunt and specific. No generic advice. Every suggestion must be tied to actual content in the CV and the job description."
    )

    return _call_llm(prompt, provider, api_key)


def answer_job_query(
    query: str,
    matched_jobs: list[dict],
    provider: str = "groq",
    api_key: str | None = None,
) -> str:
    """Build a RAG prompt from retrieved jobs and ask the LLM to answer a user's question.

    This is the "augmented generation" half of the job-search RAG pipeline:
    `app.services.rag.retrieval.search_jobs()` has already picked the
    jobs most semantically similar to `query`; this function is only
    responsible for turning that shortlist plus the original question into
    one grounded answer.

    Input:
        query (str): the user's natural-language question, e.g. "remote
            React jobs that don't require weekend on-call".
        matched_jobs (list[dict]): the jobs retrieved for `query`, each
            with at least title/company/location/description keys — the
            only jobs the model is allowed to answer from.
        provider (str): LLM provider name to use.
        api_key (str | None): caller-supplied API key for the provider.

    Output: str — the raw LLM response text, expected to reference the
        matched jobs by title/company rather than inventing new ones.

    Calls: `_call_llm()` (this file).
    Called by: `app.api.v1.job.ask_jobs()` — the `POST /jobs/ask` route.

    Variables:
        jobs_block (str): `matched_jobs` rendered as a numbered list of
            title/company/location/description, forming the retrieved
            context the model must ground its answer in.
        prompt (str): `jobs_block` combined with `query` and a fixed
            instruction forbidding the model from answering outside the
            given job list.

    Logic:
        1. Render each job in `matched_jobs` as a numbered block of its
           title/company/location/description fields.
        2. Wrap that block with the user's `query` and an instruction that
           the model must answer only from the listed jobs and must name
           the specific job(s) (by title and company) it bases its answer
           on, saying so explicitly if none of them fit.
        3. Forward the assembled prompt to `_call_llm()` and return its result.
    """
    jobs_block = "\n\n".join(
        f"{i}. {job.get('title', '')} at {job.get('company', '')} "
        f"({job.get('location') or 'location not specified'})\n"
        f"{job.get('description', '')}"
        for i, job in enumerate(matched_jobs, start=1)
    )

    prompt = (
        f"Here are job postings retrieved as relevant to the question below:\n\n"
        f"{jobs_block}\n\n"
        f"Question: {query}\n\n"
        "Answer the question using ONLY the job postings listed above. "
        "Explicitly name the job(s) (title and company) your answer is based on. "
        "If none of the listed jobs answer the question, say so plainly instead of guessing."
    )

    return _call_llm(prompt, provider, api_key)


def _call_groq(prompt: str, api_key: str) -> str:
    """Send `prompt` to Groq's chat-completions API (model: openai/gpt-oss-120b).

    Input: prompt (str), api_key (str). Output: str (model reply text).
    Calls: `groq.Groq.chat.completions.create()` (external SDK).
    Called by: `_call_llm()`.
    """
    from groq import Groq

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048,
        temperature=0.7,
    )
    return response.choices[0].message.content


def _call_openai(prompt: str, api_key: str) -> str:
    """Send `prompt` to OpenAI's chat-completions API (model: gpt-4o-mini).

    Input: prompt (str), api_key (str). Output: str (model reply text).
    Calls: `openai.OpenAI.chat.completions.create()` (external SDK).
    Called by: `_call_llm()`.
    """
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
        temperature=0.7,
    )
    return response.choices[0].message.content


def _call_anthropic(prompt: str, api_key: str) -> str:
    """Send `prompt` to Anthropic's Messages API (model: claude-opus-5).

    Input: prompt (str), api_key (str). Output: str (model reply text).
    Calls: `anthropic.Anthropic.messages.create()` (external SDK).
    Called by: `_call_llm()`.
    """
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _call_gemini(prompt: str, api_key: str) -> str:
    """Send `prompt` to Google's Gemini API (model: gemini-1.5-flash).

    Input: prompt (str), api_key (str). Output: str (model reply text).
    Calls: `google.generativeai.GenerativeModel.generate_content()` (external SDK).
    Called by: `_call_llm()`.
    """
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text


_PROVIDERS.update(
    {
        "groq": _call_groq,
        "openai": _call_openai,
        "anthropic": _call_anthropic,
        "gemini": _call_gemini,
    }
)
