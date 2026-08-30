import os
import shutil
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException, status
from backend.app.core.config import settings
from backend.app.utils.file_utils import generate_secure_storage_name, is_allowed_file
from backend.app.utils.hash_utils import compute_sha256_bytes, compute_sha256_file
from backend.app.core.logging import logger

class StorageService:
    def __init__(self, base_dir: Path = settings.UPLOADS_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_user_storage_dir(self, user_id: int) -> Path:
        """Get or create user-isolated storage directory."""
        user_dir = self.base_dir / f"user_{user_id}"
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    async def save_uploaded_file(
        self,
        file: UploadFile,
        user_id: int
    ) -> Tuple[str, str, str, int, str]:
        """
        Save an incoming UploadFile to disk securely.
        Returns:
            (stored_filename, clean_original_name, absolute_path_str, file_size_bytes, sha256_hash)
        """
        if not file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename")

        if not is_allowed_file(file.filename):
            allowed_exts = ", ".join(settings.ALLOWED_EXTENSIONS)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format. Permitted types: {allowed_exts}"
            )

        stored_filename, clean_name = generate_secure_storage_name(file.filename)
        user_dir = self.get_user_storage_dir(user_id)
        destination_path = user_dir / stored_filename

        # Read contents and verify file size
        contents = await file.read()
        file_size = len(contents)

        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot upload an empty file"
            )

        # Compute SHA-256 checksum
        sha256_hash = compute_sha256_bytes(contents)

        # Write to disk securely
        with open(destination_path, "wb") as f:
            f.write(contents)

        logger.info(f"File stored securely: {stored_filename} for user {user_id} (SHA-256: {sha256_hash[:12]}...)")
        return stored_filename, clean_name, str(destination_path), file_size, sha256_hash

    def verify_integrity(self, file_path_str: str, expected_hash: str) -> bool:
        """Verify that an existing stored file has not been altered."""
        file_path = Path(file_path_str)
        if not file_path.exists():
            return False
        current_hash = compute_sha256_file(file_path)
        return current_hash == expected_hash

    def resolve_safe_path(self, user_id: int, stored_filename: str) -> Optional[Path]:
        """Resolve path and verify it stays strictly within the user's directory."""
        user_dir = self.get_user_storage_dir(user_id).resolve()
        target_path = (user_dir / stored_filename).resolve()
        
        # Prevent directory traversal attacks
        if not str(target_path).startswith(str(user_dir)):
            logger.warning(f"Directory traversal attempt detected: {stored_filename} for user {user_id}")
            return None

        if not target_path.exists():
            return None

        return target_path

storage_service = StorageService()
