import hashlib
from pathlib import Path
from typing import BinaryIO, Union

def compute_sha256_bytes(data: bytes) -> str:
    """Compute hex SHA-256 hash of raw bytes."""
    sha256 = hashlib.sha256()
    sha256.update(data)
    return sha256.hexdigest()

def compute_sha256_file(file_path: Union[str, Path]) -> str:
    """Compute hex SHA-256 hash of a file on disk."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def compute_sha256_stream(file_stream: BinaryIO) -> str:
    """Compute hex SHA-256 hash of a readable binary stream and reset position."""
    sha256 = hashlib.sha256()
    for chunk in iter(lambda: file_stream.read(65536), b""):
        sha256.update(chunk)
    file_stream.seek(0)
    return sha256.hexdigest()
