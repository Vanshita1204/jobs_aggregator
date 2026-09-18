"""
CV API endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.auth import get_current_user
from app.core.logging import get_logger
from app.db.session import get_session
from app.models.cv import UserCV, UserCVCreate, UserCVRead
from app.models.job import Job
from app.models.user import User
from app.models.userjob import UserJob
from app.services.extractor import extract_text
from app.services.gcs import delete_file, download_bytes, generate_download_url, generate_upload_url
from app.services.llm import get_cv_tips

router = APIRouter(prefix="/cvs", tags=["cvs"])
logger = get_logger(__name__)

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


class UploadUrlResponse(BaseModel):
    upload_url: str
    gcs_path: str


@router.get("/upload-url", response_model=UploadUrlResponse)
def get_upload_url(
    filename: str,
    content_type: str = "application/octet-stream",
    user: User = Depends(get_current_user),
):
    """Return a signed PUT URL for uploading a CV directly to GCS.

    The object path embeds the user's id and a random UUID
    (`cvs/user_{id}/{uuid}.{ext}`) so uploads never collide and are
    trivially scoped per user. Extension is derived from `filename` and
    validated against `ALLOWED_EXTENSIONS` before a URL is issued.

    Input:
        filename (str): original filename, used only to derive the extension.
        content_type (str): MIME type the client will PUT; must match what
            it actually sends or GCS will reject the upload.

    Output: UploadUrlResponse — the signed URL plus the `gcs_path` the
        client must pass back to `POST /cvs` after uploading.
    Raises: HTTPException 400 if the extension is not pdf/docx/txt.

    Calls: `app.services.gcs.generate_upload_url()`.
    Called by: the frontend's CV upload flow in `CVManager.jsx`.

    Variables:
        ext (str): lowercased file extension parsed from `filename`.
        gcs_path (str): the destination object path, built as
            `cvs/user_{id}/{random-uuid}.{ext}` so concurrent uploads by
            different users (or the same user) never collide.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type. Allowed: PDF, DOCX, TXT")

    gcs_path = f"cvs/user_{user.id}/{uuid.uuid4().hex}.{ext}"
    url = generate_upload_url(gcs_path, content_type)
    return UploadUrlResponse(upload_url=url, gcs_path=gcs_path)


@router.post("", response_model=UserCVRead)
def create_cv(
    body: UserCVCreate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Register a CV row after the client uploads the file via the signed URL.

    Downloads the just-uploaded object back from GCS server-side to run text
    extraction (`extract_text`), so `extracted_text` is populated for later
    LLM tip generation without the client having to send the file twice.

    Input: body (UserCVCreate) — name, gcs_path (from `GET /cvs/upload-url`),
        and optional user_job_id to link this CV to a specific application.
    Output: UserCVRead — the created CV record.
    Raises: HTTPException 400 for a disallowed extension, 502 if the object
        can't be downloaded from GCS, 422 if text extraction fails.

    Calls: `app.services.gcs.download_bytes()`, `app.services.extractor.extract_text()`.
    Called by: the frontend's CV upload flow in `CVManager.jsx`, immediately
        after the browser's direct PUT to the signed URL succeeds.

    Variables:
        ext (str): extension parsed from `body.gcs_path`, re-validated here
            since `POST /cvs` can in principle be called independently of
            `GET /cvs/upload-url`.
        file_bytes (bytes): the uploaded file, downloaded back from GCS.
        text (str): plain text extracted from `file_bytes`, stored as
            `UserCV.extracted_text` for later LLM tip generation.

    Logic:
        1. Re-validate the extension against `ALLOWED_EXTENSIONS`.
        2. Download the object back from GCS (proves the upload actually
           landed, and gives the backend the bytes to run extraction on).
        3. Extract text via `extract_text()`, dispatching on extension.
        4. Insert the `UserCV` row and return it.
    """
    ext = body.gcs_path.rsplit(".", 1)[-1].lower() if "." in body.gcs_path else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    try:
        file_bytes = download_bytes(body.gcs_path)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not fetch file from storage: {e}")

    try:
        text = extract_text(file_bytes, f"file.{ext}")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not extract text: {e}")

    cv = UserCV(
        user_id=user.id,
        name=body.name,
        gcs_path=body.gcs_path,
        extracted_text=text,
        user_job_id=body.user_job_id,
    )
    session.add(cv)
    session.commit()
    session.refresh(cv)
    return cv


@router.get("", response_model=list[UserCVRead])
def list_cvs(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """List the current user's CVs, with linked job title/company if any.

    Output: list[UserCVRead] — `job_title`/`job_company` are populated via
        a left join through `UserJob` when `user_job_id` is set, else None.
    Calls: none beyond the SQLModel query itself.
    Called by: the frontend's `CVManager.jsx` page.
    Variables: rows (list[tuple[UserCV, str | None, str | None]]) — each
        query result row, unpacked into a `UserCVRead` in the list comprehension.
    Logic: `UserCV` OUTER JOIN `UserJob` (via `user_job_id`) OUTER JOIN
        `Job` (via `UserJob.job_id`) — both outer so a CV with no linked
        job still appears, with `job_title`/`job_company` as None.
    """
    rows = session.exec(
        select(UserCV, Job.title, Job.company)
        .outerjoin(UserJob, UserCV.user_job_id == UserJob.id)
        .outerjoin(Job, UserJob.job_id == Job.id)
        .where(UserCV.user_id == user.id)
    ).all()
    return [
        UserCVRead(
            id=cv.id,
            name=cv.name,
            gcs_path=cv.gcs_path,
            user_job_id=cv.user_job_id,
            job_title=job_title,
            job_company=job_company,
            created_at=cv.created_at,
        )
        for cv, job_title, job_company in rows
    ]


@router.get("/{cv_id}/download")
def download_cv(
    cv_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Return a short-lived signed URL for downloading one of the user's CVs.

    Input: cv_id (int) — id of the CV to download.
    Output: {"download_url": str}
    Raises: HTTPException 404 if no CV with `cv_id` belongs to the current user.
    Calls: `app.services.gcs.generate_download_url()`.
    Called by: the frontend's CV list "Download" button in `CVManager.jsx`.
    """
    cv = session.exec(select(UserCV).where(UserCV.id == cv_id, UserCV.user_id == user.id)).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    url = generate_download_url(cv.gcs_path)
    return {"download_url": url}


@router.delete("/{cv_id}")
def delete_cv(
    cv_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Delete one of the user's CVs, from both GCS and the database.

    Input: cv_id (int) — id of the CV to delete.
    Output: {"detail": "CV deleted"}
    Raises: HTTPException 404 if no CV with `cv_id` belongs to the current user.
    Calls: `app.services.gcs.delete_file()`.
    Called by: the frontend's CV list "Delete" button in `CVManager.jsx`.
    Logic: delete the GCS object first (best-effort — failure is caught
        and ignored, so an already-gone or unreachable object never blocks
        removing the DB row), then delete the `UserCV` row and commit.
    """
    cv = session.exec(select(UserCV).where(UserCV.id == cv_id, UserCV.user_id == user.id)).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    try:
        delete_file(cv.gcs_path)
    except Exception:
        pass
    session.delete(cv)
    session.commit()
    return {"detail": "CV deleted"}


@router.post("/{cv_id}/tips/{job_id}")
def cv_tips(
    cv_id: int,
    job_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
    x_llm_provider: str = Header(default="groq"),
    x_llm_key: str = Header(default=""),
):
    """Generate AI-tailored CV improvement tips for a specific job.

    If the job has no cached description yet and is an Indeed listing, this
    also opportunistically fetches and caches the description before
    calling the LLM (mirrors the on-demand fetch in
    `GET /jobs/{job_id}/description`, duplicated here for Indeed only).

    Input:
        cv_id (int): id of the CV to tailor (must belong to the current user).
        job_id (int): id of the job to tailor the CV against.
        x_llm_provider (str): LLM provider name, from the `X-Llm-Provider`
            header (set in the frontend via the user's Settings page).
        x_llm_key (str): LLM API key, from the `X-Llm-Key` header. Never
            persisted server-side.

    Output: {"tips": str} — raw LLM response text with 5 suggestions.
    Raises: HTTPException 404 if the CV or job is not found, 422 if the CV
        has no extracted text, 502 if the LLM call fails.

    Calls: `app.services.fetchers.page_fetcher.fetch_page_cffi()` (Indeed
        description fetch only), `app.services.llm.get_cv_tips()`.
    Called by: the frontend's "Get CV Tips" button in `Jobs.jsx`.

    Variables:
        cv (UserCV | None): the caller's CV row, or None -> 404.
        job (Job | None): the target job row, or None -> 404.
        jk (str | None): Indeed's `jk` query parameter extracted from
            `job.source_url`, used to build the canonical detail-page URL
            for the opportunistic description fetch.

    Logic:
        1. Load `cv` and `job`, scoped to the current user for `cv`; 404 if
           either is missing.
        2. 422 if `cv.extracted_text` is empty (nothing to send the LLM).
        3. If `job.description` is empty and the job is from Indeed,
           opportunistically fetch and cache the full description before
           calling the LLM (best-effort — any failure here is logged and
           swallowed, not raised, so a fetch failure never blocks tip
           generation). LinkedIn/Hirist jobs skip this step entirely.
        4. Call `get_cv_tips()` with the CV text and job details; 502 on failure.
    """
    cv = session.exec(select(UserCV).where(UserCV.id == cv_id, UserCV.user_id == user.id)).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not cv.extracted_text:
        raise HTTPException(status_code=422, detail="CV has no extracted text")

    if not job.description and job.source == "Indeed" and job.source_url:
        try:
            from urllib.parse import urlparse, parse_qs
            from bs4 import BeautifulSoup
            from app.services.fetchers.page_fetcher import fetch_page_cffi
            parsed = urlparse(job.source_url)
            jk = parse_qs(parsed.query).get("jk", [None])[0]
            if jk:
                detail_url = f"https://in.indeed.com/viewjob?jk={jk}"
                html = fetch_page_cffi(detail_url)
                soup = BeautifulSoup(html, "html.parser")
                el = soup.select_one("#jobDescriptionText")
                if el:
                    job.description = el.get_text(separator=" ", strip=True)
                    session.add(job)
                    session.commit()
        except Exception:
            logger.exception("Indeed description fetch failed for job %s", job.id)

    try:
        tips = get_cv_tips(
            job_title=job.title,
            company=job.company,
            location=job.location or "",
            description=job.description,
            cv_text=cv.extracted_text,
            provider=x_llm_provider,
            api_key=x_llm_key or None,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    return {"tips": tips}
