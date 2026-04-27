"""
CV API endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.auth import get_current_user
from app.db.session import get_session
from app.models.cv import UserCV, UserCVCreate, UserCVRead
from app.models.job import Job
from app.models.user import User
from app.models.userjob import UserJob
from app.services.extractor import extract_text
from app.services.gcs import delete_file, download_bytes, generate_download_url, generate_upload_url
from app.services.llm import get_cv_tips

router = APIRouter(prefix="/cvs", tags=["cvs"])

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
    """Return a signed PUT URL for uploading a CV directly to GCS."""
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
    """Register a CV after the client has uploaded the file via the signed URL."""
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
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Indeed description fetch failed: {e}")

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
