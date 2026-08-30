import re
import uuid
from pathlib import Path
from typing import Tuple
from backend.app.core.config import settings

def sanitize_filename(filename: str) -> str:
    """Sanitize original filename to remove path traversal characters."""
    # Keep only alphanumeric, dots, hyphens, and underscores
    name = Path(filename).name
    clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', name)
    return clean_name or "medical_document"

def generate_secure_storage_name(original_filename: str) -> Tuple[str, str]:
    """Generate a collision-resistant UUID-prefixed storage name."""
    clean = sanitize_filename(original_filename)
    extension = Path(clean).suffix.lower()
    if extension not in settings.ALLOWED_EXTENSIONS:
        extension = ".bin"
    unique_id = uuid.uuid4().hex
    stored_filename = f"{unique_id}{extension}"
    return stored_filename, clean

def is_allowed_file(filename: str) -> bool:
    """Check if the file extension is permitted."""
    ext = Path(filename).suffix.lower()
    return ext in settings.ALLOWED_EXTENSIONS
