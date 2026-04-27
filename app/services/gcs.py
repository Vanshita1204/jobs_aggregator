import datetime

from google.cloud import storage

from app.core.config import settings

_client: storage.Client | None = None


def _get_client() -> storage.Client:
    global _client
    if _client is None:
        _client = storage.Client()
    return _client


def generate_upload_url(gcs_path: str, content_type: str, expires_minutes: int = 15) -> str:
    """Generate a signed URL for uploading a file directly to GCS."""
    bucket = _get_client().bucket(settings.GCS_BUCKET)
    blob = bucket.blob(gcs_path)
    return blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=expires_minutes),
        method="PUT",
        content_type=content_type,
    )


def generate_download_url(gcs_path: str, expires_minutes: int = 15) -> str:
    """Generate a signed URL for downloading a file from GCS."""
    bucket = _get_client().bucket(settings.GCS_BUCKET)
    blob = bucket.blob(gcs_path)
    return blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=expires_minutes),
        method="GET",
    )


def upload_bytes(gcs_path: str, data: bytes, content_type: str) -> None:
    """Upload raw bytes to GCS."""
    bucket = _get_client().bucket(settings.GCS_BUCKET)
    blob = bucket.blob(gcs_path)
    blob.upload_from_string(data, content_type=content_type)


def download_bytes(gcs_path: str) -> bytes:
    """Download a file from GCS and return its raw bytes."""
    bucket = _get_client().bucket(settings.GCS_BUCKET)
    blob = bucket.blob(gcs_path)
    return blob.download_as_bytes()


def delete_file(gcs_path: str) -> None:
    """Delete a file from GCS."""
    bucket = _get_client().bucket(settings.GCS_BUCKET)
    blob = bucket.blob(gcs_path)
    blob.delete()
