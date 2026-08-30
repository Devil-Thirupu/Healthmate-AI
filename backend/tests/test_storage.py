import pytest
from pathlib import Path
from backend.app.services.storage_service import StorageService
from backend.app.utils.hash_utils import compute_sha256_bytes, compute_sha256_file
from backend.app.utils.file_utils import sanitize_filename, is_allowed_file

def test_hash_utils(tmp_path):
    data = b"Sample Medical Prescription: Metformin 500mg"
    expected_hash = compute_sha256_bytes(data)
    
    test_file = tmp_path / "rx_test.txt"
    test_file.write_bytes(data)
    file_hash = compute_sha256_file(test_file)
    
    assert expected_hash == file_hash
    assert len(expected_hash) == 64

def test_file_utils():
    # Check allowed extensions
    assert is_allowed_file("report.pdf") is True
    assert is_allowed_file("xray.dcm") is True
    assert is_allowed_file("scan.png") is True
    assert is_allowed_file("malicious.exe") is False
    assert is_allowed_file("script.sh") is False
    
    # Path traversal sanitization
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\boot.ini") == "boot.ini"
    assert sanitize_filename("blood test (1).pdf") == "blood_test__1_.pdf"

def test_storage_service_isolation(tmp_path):
    storage = StorageService(base_dir=tmp_path)
    user1_dir = storage.get_user_storage_dir(1)
    user2_dir = storage.get_user_storage_dir(2)
    
    assert user1_dir.exists()
    assert user2_dir.exists()
    assert user1_dir != user2_dir
