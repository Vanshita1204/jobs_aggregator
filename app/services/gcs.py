"""Google Cloud Storage helpers for CV file upload/download/delete.

All access is via V4 signed URLs so the browser can PUT/GET the file bytes
directly against GCS without routing them through the FastAPI backend; the
backend only ever handles metadata and (for text extraction) a server-side
download of the object.
"""

import datetime

from google.cloud import storage

from app.core.config import settings

_client: storage.Client | None = None


def _get_client() -> storage.Client:
    """Return a process-wide cached `storage.Client`, creating it on first use.

    Input: none. Output: storage.Client.
    Variables: `_client` (module-level cache, avoids re-authenticating per call).
    Called by: every other function in this file.
    """
    global _client
    if _client is None:
        _client = storage.Client()
    return _client


def generate_upload_url(gcs_path: str, content_type: str, expires_minutes: int = 15) -> str:
    """Generate a V4 signed PUT URL for uploading a file directly to GCS.

    Input:
        gcs_path (str): destination object path within GCS_BUCKET.
        content_type (str): MIME type the client must send; must match
            exactly or the signed URL request will be rejected by GCS.
        expires_minutes (int): URL validity window in minutes.

    Output: str — a signed HTTPS URL the client can PUT the file bytes to.

    Calls: `_get_client()`, `google.cloud.storage.Blob.generate_signed_url()`.
    Called by: `app.api.v1.cv.get_upload_url()` — `GET /cvs/upload-url`.

    Logic: fetch the bucket named `settings.GCS_BUCKET`, address the blob at
        `gcs_path` (need not exist yet), and ask GCS to sign a PUT URL valid
        for `expires_minutes` and bound to `content_type`.
    """
    bucket = _get_client().bucket(settings.GCS_BUCKET)
    blob = bucket.blob(gcs_path)
    return blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=expires_minutes),
        method="PUT",
        content_type=content_type,
    )


def generate_download_url(gcs_path: str, expires_minutes: int = 15) -> str:
    """Generate a V4 signed GET URL for downloading a file from GCS.

    Input:
        gcs_path (str): object path within GCS_BUCKET.
        expires_minutes (int): URL validity window in minutes.

    Output: str — a signed HTTPS URL the client can GET the file bytes from.

    Calls: `_get_client()`, `google.cloud.storage.Blob.generate_signed_url()`.
    Called by: `app.api.v1.cv.download_cv()` — `GET /cvs/{cv_id}/download`.
    """
    bucket = _get_client().bucket(settings.GCS_BUCKET)
    blob = bucket.blob(gcs_path)
    return blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=expires_minutes),
        method="GET",
    )


def upload_bytes(gcs_path: str, data: bytes, content_type: str) -> None:
    """Upload raw bytes to GCS directly from the backend (server-side upload path).

    Input:
        gcs_path (str): destination object path within GCS_BUCKET.
        data (bytes): raw file content to upload.
        content_type (str): MIME type to set on the stored object.

    Output: None.

    Calls: `_get_client()`, `google.cloud.storage.Blob.upload_from_string()`.
    Called by: nobody currently — every upload in this codebase goes
        client-to-GCS via `generate_upload_url()` instead. Kept for any
        future server-initiated upload path (e.g. a batch-import feature).
    """
    bucket = _get_client().bucket(settings.GCS_BUCKET)
    blob = bucket.blob(gcs_path)
    blob.upload_from_string(data, content_type=content_type)


def download_bytes(gcs_path: str) -> bytes:
    """Download a file from GCS and return its raw bytes.

    Input: gcs_path (str) — object path within GCS_BUCKET.
    Output: bytes — raw file content.

    Calls: `_get_client()`, `google.cloud.storage.Blob.download_as_bytes()`.
    Called by: `app.api.v1.cv.create_cv()` — `POST /cvs`, immediately after
        the client's signed-URL upload completes, so the backend can run
        text extraction on the file server-side.
    """
    bucket = _get_client().bucket(settings.GCS_BUCKET)
    blob = bucket.blob(gcs_path)
    return blob.download_as_bytes()


def delete_file(gcs_path: str) -> None:
    """Delete a file from GCS.

    Input: gcs_path (str) — object path within GCS_BUCKET to remove.
    Output: None.

    Calls: `_get_client()`, `google.cloud.storage.Blob.delete()`.
    Called by: `app.api.v1.cv.delete_cv()` — `DELETE /cvs/{cv_id}` — inside
        a try/except there, so a GCS failure never blocks the DB row from
        being removed.
    """
    bucket = _get_client().bucket(settings.GCS_BUCKET)
    blob = bucket.blob(gcs_path)
    blob.delete()
