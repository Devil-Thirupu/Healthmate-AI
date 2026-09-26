"""
SupabaseStorageService — wraps the Supabase Python SDK Storage client.

Upload flow (unchanged from user perspective):
  User → Frontend → FastAPI → SupabaseStorageService → Supabase Storage
                                  ↓
                               OCR / processing
                                  ↓
                           Supabase PostgreSQL

All buckets are PRIVATE.  Files are accessed only via short-lived signed URLs.
Bucket assignment by document category:
  prescription  → prescriptions
  imaging       → medical-images
  discharge_summary / vaccination / lab_report / other → medical-documents
  appointment-related PDFs → appointment-pdfs  (used by appointment_summary service)
"""

import io
import os
from pathlib import Path
from typing import Optional, Tuple

from backend.app.core.config import settings
from backend.app.core.logging import logger

# ---------------------------------------------------------------------------
# Lazy Supabase client — only initialised when credentials are present
# ---------------------------------------------------------------------------
_supabase_client = None


def _get_supabase():
    """Return a lazily-initialised Supabase client, or None if not configured."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if not settings.supabase_enabled:
        return None

    try:
        from supabase import create_client, Client  # type: ignore
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)
        logger.info("Supabase client initialised successfully.")
        return _supabase_client
    except Exception as exc:
        logger.error(f"Failed to initialise Supabase client: {exc}")
        return None


# ---------------------------------------------------------------------------
# Bucket selection helper
# ---------------------------------------------------------------------------

BUCKET_MAP = {
    "prescription": "prescriptions",
    "lab_report": "medical-documents",
    "imaging": "medical-images",
    "discharge_summary": "medical-documents",
    "vaccination": "medical-documents",
    "insurance": "medical-documents",
    "other": "medical-documents",
    # appointment PDFs are uploaded by appointment_summary_service
    "appointment_pdf": "appointment-pdfs",
}

DEFAULT_BUCKET = "medical-documents"


def _bucket_for_category(category: str) -> str:
    return BUCKET_MAP.get(category.lower(), DEFAULT_BUCKET)


# ---------------------------------------------------------------------------
# SupabaseStorageService
# ---------------------------------------------------------------------------

class SupabaseStorageService:
    """
    Handles all Supabase Storage operations for HealthMate AI.

    The service never exposes public URLs — all access is via signed URLs
    generated on-demand by the backend, valid for `signed_url_expiry` seconds.
    """

    SIGNED_URL_EXPIRY_SECONDS: int = 3600  # 1 hour

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    def upload_file(
        self,
        file_bytes: bytes,
        stored_filename: str,
        user_id: int,
        category: str,
        mime_type: str,
    ) -> Tuple[bool, str]:
        """
        Upload file bytes to the appropriate private Supabase Storage bucket.

        Returns:
            (success: bool, storage_path: str)
            storage_path format: "user_{user_id}/{stored_filename}"
        """
        client = _get_supabase()
        if client is None:
            logger.warning("Supabase not configured — skipping cloud upload.")
            return False, ""

        bucket = _bucket_for_category(category)
        # Store files under a per-user directory for easy RLS-style path isolation
        storage_path = f"user_{user_id}/{stored_filename}"

        try:
            # supabase-py Storage upload
            res = client.storage.from_(bucket).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": mime_type, "upsert": "false"},
            )
            logger.info(
                f"[SupabaseStorage] Uploaded {stored_filename} → bucket={bucket} path={storage_path}"
            )
            return True, storage_path
        except Exception as exc:
            # Check if it's a duplicate — treat as success
            err_str = str(exc)
            if "Duplicate" in err_str or "already exists" in err_str.lower():
                logger.warning(
                    f"[SupabaseStorage] File already exists at {storage_path}, treating as success."
                )
                return True, storage_path
            logger.error(f"[SupabaseStorage] Upload failed for {stored_filename}: {exc}")
            return False, ""

    # ------------------------------------------------------------------
    # Signed URL
    # ------------------------------------------------------------------

    def create_signed_url(
        self,
        storage_path: str,
        category: str,
        expiry_seconds: int = SIGNED_URL_EXPIRY_SECONDS,
    ) -> Optional[str]:
        """
        Generate a short-lived signed URL for a private Supabase Storage object.
        Returns None if Supabase is not configured or the object is not found.
        """
        client = _get_supabase()
        if client is None:
            return None

        bucket = _bucket_for_category(category)
        try:
            res = client.storage.from_(bucket).create_signed_url(
                path=storage_path,
                expires_in=expiry_seconds,
            )
            signed_url = res.get("signedURL") or res.get("signedUrl")
            return signed_url
        except Exception as exc:
            logger.error(
                f"[SupabaseStorage] Failed to create signed URL for {storage_path}: {exc}"
            )
            return None

    # ------------------------------------------------------------------
    # Download (for OCR processing — downloads bytes from Supabase)
    # ------------------------------------------------------------------

    def download_file(
        self,
        storage_path: str,
        category: str,
    ) -> Optional[bytes]:
        """Download file bytes from Supabase Storage (used internally by OCR pipeline)."""
        client = _get_supabase()
        if client is None:
            return None

        bucket = _bucket_for_category(category)
        try:
            data = client.storage.from_(bucket).download(storage_path)
            return data
        except Exception as exc:
            logger.error(
                f"[SupabaseStorage] Download failed for {storage_path}: {exc}"
            )
            return None

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_file(self, storage_path: str, category: str) -> bool:
        """Delete a file from Supabase Storage. Returns True on success."""
        client = _get_supabase()
        if client is None:
            return False

        bucket = _bucket_for_category(category)
        try:
            client.storage.from_(bucket).remove([storage_path])
            logger.info(f"[SupabaseStorage] Deleted {storage_path} from bucket={bucket}")
            return True
        except Exception as exc:
            logger.error(f"[SupabaseStorage] Delete failed for {storage_path}: {exc}")
            return False


# Singleton instance
supabase_storage = SupabaseStorageService()

