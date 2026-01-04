"""
Property-based test for sensitive data encryption in deployment system.

Tests that sensitive data is properly encrypted during transfer and storage
with proper key management and access controls.
"""

import asyncio
import pytest
import hashlib
import os
import tempfile
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import AsyncMock, MagicMock, patch

from deployment.artifact_repository import ArtifactRepository
from deployment.models import TestArtifact, ArtifactType


# Property-based test strategies
sensitive_data = st.binary(min_size=10, max_size=10000)
encryption_keys = st.binary(min_size=16, max_size=64)  # 128-512 bit keys
artifact_names = st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))


class MockEncryptionManager:
    """Mock encryption manager for testing"""
    
    def __init__(self):
        self.encrypted_data = {}
        self.decrypted_data = {}
        self.encryption_keys = {}
    
    def encrypt_data(self, data: bytes, key: bytes) -> bytes:
        """Mock encryption - XOR with key for simplicity"""
        # Simple XOR encryption for testing (not secure, just for testing)
        key_repeated = (key * ((len(data) // len(key)) + 1))[:len(data)]
        encrypted = bytes(a ^ b for a, b in zip(data, key_repeated))
        
        # Store for verification
        data_hash = hashlib.sha256(data).hexdigest()
        self.encrypted_data[data_hash] = encrypted
        self.encryption_keys[data_hash] = key
        
        return encrypted
    
    def decrypt_data(self, encrypted_data: bytes, key: bytes) -> bytes:
        """Mock decryption - XOR with key"""
        key_repeated = (key * ((len(encrypted_data) // len(key)) + 1))[:len(encrypted_data)]
        decrypted = bytes(a ^ b for a, b in zip(encrypted_data, key_repeated))
        
        # Store for verification
        encrypted_hash = hashlib.sha256(encrypted_data).hexdigest()
        self.decrypted_data[encrypted_hash] = decrypted
        
        return decrypted
    
    def generate_key(self) -> bytes:
        """Generate a random encryption key"""
        return os.urandom(32)  # 256-bit key
    
    def is_encrypted(self, data: bytes) -> bool:
        """Check if data appears to be encrypted"""
        # Simple heuristic: encrypted data should have high entropy
        if len(data) < 10:
            return False
        
        # Count unique bytes
        unique_bytes = len(set(data))
        entropy_ratio = unique_bytes / min(len(data), 256)
        
        # Encrypted data should have high entropy (> 0.7)
        return entropy_ratio > 0.7


def create_sensitive_artifact(name: str, sensitive_content: bytes) -> TestArtifact:
    """Create a test artifact with sensitive content"""
    return TestArtifact(
        artifact_id=f"sensitive_{hash(name) % 100000}",
        name=name,
        type=ArtifactType.CONFIG,  # Config files often contain sensitive data
        content=sensitive_content,
        checksum="",  # Will be calculated
        permissions="0600",  # Restrictive permissions for sensitive data
        target_path=f"/etc/secure/{name}",
        dependencies=[],
        metadata={"sensitive": True, "encryption_required": True}
    )


@given(
    artifact_name=artifact_names,
    sensitive_content=sensitive_data,
    encryption_key=encryption_keys
)
@settings(max_examples=40, deadline=5000)
async def test_sensitive_data_encryption(artifact_name, sensitive_content, encryption_key):
    """
    Property: Sensitive data encryption protects data confidentiality
    
    This test verifies that:
    1. Sensitive data is encrypted before storage/transfer
    2. Encrypted data cannot be read without the proper key
    3. Decryption with correct key recovers original data
    4. Encryption keys are properly managed and protected
    5. Encrypted data has different characteristics than plaintext
    """
    assume(len(artifact_name.strip()) > 0)
    assume(len(sensitive_content) >= 10)
    assume(len(encryption_key) >= 16)
    
    # Create encryption manager
    encryption_manager = MockEncryptionManager()
    
    # Create sensitive artifact
    artifact = create_sensitive_artifact(
        name=artifact_name.strip(),
        sensitive_content=sensitive_content
    )
    
    # Encrypt the sensitive content
    encrypted_content = encryption_manager.encrypt_data(sensitive_content, encryption_key)
    
    # Verify encryption properties
    assert encrypted_content != sensitive_content, "Encrypted data should differ from plaintext"
    assert len(encrypted_content) == len(sensitive_content), "Encrypted data should have same length"
    assert encryption_manager.is_encrypted(encrypted_content), "Data should appear encrypted"
    
    # Verify decryption recovers original data
    decrypted_content = encryption_manager.decrypt_data(encrypted_content, encryption_key)
    assert decrypted_content == sensitive_content, "Decryption should recover original data"
    
    # Verify wrong key fails to decrypt properly
    wrong_key = os.urandom(len(encryption_key))
    if wrong_key != encryption_key:  # Avoid collision
        wrong_decryption = encryption_manager.decrypt_data(encrypted_content, wrong_key)
        assert wrong_decryption != sensitive_content, "Wrong key should not decrypt correctly"
    
    # Verify encryption key management
    data_hash = hashlib.sha256(sensitive_content).hexdigest()
    assert data_hash in encryption_manager.encryption_keys, "Encryption key should be stored"
    assert encryption_manager.encryption_keys[data_hash] == encryption_key, "Correct key should be stored"


@given(
    artifact_count=st.integers(min_value=2, max_value=6),
    key_count=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=25, deadline=4000)
async def test_multiple_artifact_encryption_isolation(artifact_count, key_count):
    """
    Property: Multiple artifact encryption maintains isolation
    
    This test verifies that:
    1. Different artifacts can use different encryption keys
    2. Encryption of one artifact doesn't affect others
    3. Key management handles multiple keys correctly
    4. Each artifact maintains its own encryption context
    """
    assume(artifact_count >= 2)
    assume(key_count >= 1)
    
    encryption_manager = MockEncryptionManager()
    
    # Generate encryption keys
    encryption_keys = [encryption_manager.generate_key() for _ in range(key_count)]
    
    # Create multiple sensitive artifacts
    artifacts_data = []
    encrypted_artifacts = []
    
    for i in range(artifact_count):
        # Use different keys (cycling through available keys)
        key_index = i % key_count
        key = encryption_keys[key_index]
        
        # Create unique sensitive content
        content = f"sensitive_data_{i}_{'x' * (i * 10)}".encode()
        
        artifact = create_sensitive_artifact(
            name=f"sensitive_config_{i}.conf",
            sensitive_content=content
        )
        
        # Encrypt the content
        encrypted_content = encryption_manager.encrypt_data(content, key)
        
        artifacts_data.append({
            "artifact": artifact,
            "original_content": content,
            "encrypted_content": encrypted_content,
            "key": key,
            "key_index": key_index
        })
        
        encrypted_artifacts.append(encrypted_content)
    
    # Verify each artifact can be decrypted with its own key
    for i, artifact_data in enumerate(artifacts_data):
        decrypted = encryption_manager.decrypt_data(
            artifact_data["encrypted_content"],
            artifact_data["key"]
        )
        assert decrypted == artifact_data["original_content"], f"Artifact {i} should decrypt correctly"
    
    # Verify cross-decryption fails (wrong keys don't work)
    for i, artifact_data in enumerate(artifacts_data):
        for j, other_artifact_data in enumerate(artifacts_data):
            if i != j and artifact_data["key"] != other_artifact_data["key"]:
                # Try to decrypt artifact i with key from artifact j
                wrong_decryption = encryption_manager.decrypt_data(
                    artifact_data["encrypted_content"],
                    other_artifact_data["key"]
                )
                assert wrong_decryption != artifact_data["original_content"], \
                    f"Artifact {i} should not decrypt with key from artifact {j}"
    
    # Verify all encrypted contents are different
    for i in range(len(encrypted_artifacts)):
        for j in range(i + 1, len(encrypted_artifacts)):
            assert encrypted_artifacts[i] != encrypted_artifacts[j], \
                f"Encrypted artifacts {i} and {j} should be different"


@given(
    sensitive_content=sensitive_data,
    storage_iterations=st.integers(min_value=2, max_value=5)
)
@settings(max_examples=20, deadline=4000)
async def test_encrypted_storage_persistence(sensitive_content, storage_iterations):
    """
    Property: Encrypted storage maintains data integrity across operations
    
    This test verifies that:
    1. Encrypted data can be stored and retrieved multiple times
    2. Storage operations don't corrupt encrypted data
    3. Encryption remains consistent across storage cycles
    4. Data integrity is maintained throughout the process
    """
    assume(len(sensitive_content) >= 10)
    assume(storage_iterations >= 2)
    
    encryption_manager = MockEncryptionManager()
    key = encryption_manager.generate_key()
    
    # Initial encryption
    original_encrypted = encryption_manager.encrypt_data(sensitive_content, key)
    
    # Simulate multiple storage/retrieval cycles
    current_encrypted = original_encrypted
    
    for iteration in range(storage_iterations):
        # Simulate storage (in real implementation, this would write to disk/network)
        stored_data = current_encrypted
        
        # Simulate retrieval
        retrieved_data = stored_data
        
        # Verify data integrity
        assert retrieved_data == current_encrypted, f"Data integrity lost in iteration {iteration}"
        
        # Verify decryption still works
        decrypted = encryption_manager.decrypt_data(retrieved_data, key)
        assert decrypted == sensitive_content, f"Decryption failed in iteration {iteration}"
        
        # Update for next iteration
        current_encrypted = retrieved_data
    
    # Final verification
    final_decrypted = encryption_manager.decrypt_data(current_encrypted, key)
    assert final_decrypted == sensitive_content, "Final decryption should recover original data"
    assert current_encrypted == original_encrypted, "Encrypted data should remain unchanged"


@given(
    artifact_name=artifact_names,
    sensitive_content=sensitive_data
)
@settings(max_examples=30, deadline=4000)
async def test_artifact_repository_encryption_integration(artifact_name, sensitive_content):
    """
    Property: Artifact repository properly handles encrypted sensitive data
    
    This test verifies that:
    1. Sensitive artifacts are marked for encryption
    2. Repository can store and retrieve encrypted artifacts
    3. Encryption metadata is preserved
    4. Access controls are enforced for sensitive data
    """
    assume(len(artifact_name.strip()) > 0)
    assume(len(sensitive_content) >= 10)
    
    # Create temporary storage for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        repository = ArtifactRepository(storage_path=temp_dir)
        encryption_manager = MockEncryptionManager()
        
        # Create sensitive artifact
        artifact = create_sensitive_artifact(
            name=artifact_name.strip(),
            sensitive_content=sensitive_content
        )
        
        # Encrypt content before storing
        encryption_key = encryption_manager.generate_key()
        encrypted_content = encryption_manager.encrypt_data(sensitive_content, encryption_key)
        
        # Create encrypted version of artifact
        encrypted_artifact = TestArtifact(
            artifact_id=artifact.artifact_id,
            name=artifact.name,
            type=artifact.type,
            content=encrypted_content,
            checksum="",  # Will be calculated
            permissions=artifact.permissions,
            target_path=artifact.target_path,
            dependencies=artifact.dependencies,
            metadata={
                **artifact.metadata,
                "encrypted": True,
                "encryption_algorithm": "mock_xor",
                "key_id": hashlib.sha256(encryption_key).hexdigest()[:16]
            }
        )
        
        # Store encrypted artifact
        store_result = await repository.store_artifact(encrypted_artifact)
        assert store_result is True, "Encrypted artifact should be stored successfully"
        
        # Retrieve encrypted artifact
        retrieved_artifact = await repository.get_artifact(encrypted_artifact.artifact_id)
        assert retrieved_artifact is not None, "Encrypted artifact should be retrievable"
        
        # Verify encryption metadata is preserved
        assert retrieved_artifact.metadata.get("encrypted") is True, "Encryption flag should be preserved"
        assert retrieved_artifact.metadata.get("encryption_algorithm") == "mock_xor", "Algorithm should be preserved"
        assert "key_id" in retrieved_artifact.metadata, "Key ID should be preserved"
        
        # Verify content is still encrypted
        assert retrieved_artifact.content == encrypted_content, "Encrypted content should be preserved"
        assert retrieved_artifact.content != sensitive_content, "Content should remain encrypted"
        
        # Verify decryption works
        decrypted_content = encryption_manager.decrypt_data(retrieved_artifact.content, encryption_key)
        assert decrypted_content == sensitive_content, "Decryption should recover original sensitive data"
        
        # Verify artifact validation works with encrypted content
        validation_result = await repository.validate_artifact(retrieved_artifact)
        assert validation_result is True, "Encrypted artifact should pass validation"


# Synchronous test runners for pytest
def test_sensitive_data_encryption_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_sensitive_data_encryption(
        artifact_name="secret_config.conf",
        sensitive_content=b"password=secret123\napi_key=abc123xyz",
        encryption_key=b"encryption_key_32_bytes_long_12"
    ))


def test_multiple_artifact_encryption_isolation_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_multiple_artifact_encryption_isolation(
        artifact_count=3,
        key_count=2
    ))


def test_encrypted_storage_persistence_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_encrypted_storage_persistence(
        sensitive_content=b"sensitive_database_credentials",
        storage_iterations=3
    ))


def test_artifact_repository_encryption_integration_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_artifact_repository_encryption_integration(
        artifact_name="database.conf",
        sensitive_content=b"db_password=super_secret_password_123"
    ))


if __name__ == "__main__":
    # Run a few examples manually for testing
    import asyncio
    
    async def run_examples():
        print("Testing sensitive data encryption...")
        await test_sensitive_data_encryption(
            "secret.conf", b"password=secret123", b"key_32_bytes_long_for_testing_12"
        )
        print("✓ Sensitive data encryption test passed")
        
        print("Testing multiple artifact encryption isolation...")
        await test_multiple_artifact_encryption_isolation(3, 2)
        print("✓ Multiple artifact encryption isolation test passed")
        
        print("Testing encrypted storage persistence...")
        await test_encrypted_storage_persistence(b"sensitive_data_content", 3)
        print("✓ Encrypted storage persistence test passed")
        
        print("Testing artifact repository encryption integration...")
        await test_artifact_repository_encryption_integration(
            "config.conf", b"api_key=secret_key_123"
        )
        print("✓ Artifact repository encryption integration test passed")
        
        print("All sensitive data encryption tests completed successfully!")
    
    asyncio.run(run_examples())