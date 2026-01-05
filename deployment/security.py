"""
Security module for the Test Deployment System

Provides encryption, secure credential management, and access control
for sensitive test data and deployment artifacts.
"""

import os
import base64
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import secrets
import json

from .models import TestArtifact, ArtifactType


logger = logging.getLogger(__name__)


class SecurityLevel:
    """Security levels for artifacts and operations"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"


@dataclass
class AccessControlRule:
    """Access control rule for artifacts and operations"""
    resource_id: str
    user_id: str
    permissions: List[str]  # read, write, execute, deploy
    environment_restrictions: List[str] = field(default_factory=list)
    time_restrictions: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    def is_valid(self) -> bool:
        """Check if the access control rule is still valid"""
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True
    
    def has_permission(self, permission: str) -> bool:
        """Check if the rule grants a specific permission"""
        return permission in self.permissions and self.is_valid()


@dataclass
class SecureCredential:
    """Secure credential storage"""
    credential_id: str
    environment_id: str
    credential_type: str  # password, ssh_key, api_token, certificate
    encrypted_data: bytes
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if the credential has expired"""
        return self.expires_at and datetime.now() > self.expires_at


class EncryptionManager:
    """Manages encryption and decryption of sensitive data"""
    
    def __init__(self, master_key: Optional[bytes] = None):
        """
        Initialize encryption manager.
        
        Args:
            master_key: Master encryption key. If None, generates a new key.
        """
        if master_key:
            self._master_key = master_key
        else:
            self._master_key = Fernet.generate_key()
        
        self._fernet = Fernet(self._master_key)
        self._rsa_private_key = None
        self._rsa_public_key = None
        self._generate_rsa_keys()
    
    def _generate_rsa_keys(self):
        """Generate RSA key pair for asymmetric encryption"""
        self._rsa_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self._rsa_public_key = self._rsa_private_key.public_key()
    
    def encrypt_data(self, data: bytes, use_asymmetric: bool = False) -> bytes:
        """
        Encrypt data using symmetric or asymmetric encryption.
        
        Args:
            data: Data to encrypt
            use_asymmetric: Use RSA encryption instead of Fernet
            
        Returns:
            Encrypted data
        """
        try:
            if use_asymmetric and self._rsa_public_key:
                # RSA encryption for small data (like keys)
                encrypted = self._rsa_public_key.encrypt(
                    data,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                return encrypted
            else:
                # Fernet encryption for larger data
                return self._fernet.encrypt(data)
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: bytes, use_asymmetric: bool = False) -> bytes:
        """
        Decrypt data using symmetric or asymmetric decryption.
        
        Args:
            encrypted_data: Encrypted data to decrypt
            use_asymmetric: Use RSA decryption instead of Fernet
            
        Returns:
            Decrypted data
        """
        try:
            if use_asymmetric and self._rsa_private_key:
                # RSA decryption
                decrypted = self._rsa_private_key.decrypt(
                    encrypted_data,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                return decrypted
            else:
                # Fernet decryption
                return self._fernet.decrypt(encrypted_data)
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def derive_key_from_password(self, password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """
        Derive encryption key from password using PBKDF2.
        
        Args:
            password: Password to derive key from
            salt: Salt for key derivation. If None, generates random salt.
            
        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())
        return key, salt
    
    def get_public_key_pem(self) -> bytes:
        """Get RSA public key in PEM format"""
        if not self._rsa_public_key:
            return b""
        
        return self._rsa_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )


class CredentialManager:
    """Manages secure storage and retrieval of credentials"""
    
    def __init__(self, encryption_manager: EncryptionManager):
        """
        Initialize credential manager.
        
        Args:
            encryption_manager: Encryption manager for securing credentials
        """
        self.encryption_manager = encryption_manager
        self._credentials: Dict[str, SecureCredential] = {}
        self._credential_cache: Dict[str, Tuple[Any, datetime]] = {}
        self._cache_ttl = timedelta(minutes=15)  # Cache credentials for 15 minutes
    
    def store_credential(self, 
                        environment_id: str,
                        credential_type: str,
                        credential_data: Dict[str, Any],
                        expires_in_hours: Optional[int] = None) -> str:
        """
        Store a credential securely.
        
        Args:
            environment_id: Environment identifier
            credential_type: Type of credential (password, ssh_key, etc.)
            credential_data: Credential data to encrypt and store
            expires_in_hours: Hours until credential expires
            
        Returns:
            Credential ID for retrieval
        """
        credential_id = f"cred_{secrets.token_hex(8)}"
        
        # Serialize and encrypt credential data
        serialized_data = json.dumps(credential_data).encode()
        encrypted_data = self.encryption_manager.encrypt_data(serialized_data)
        
        # Set expiration if specified
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.now() + timedelta(hours=expires_in_hours)
        
        # Create secure credential
        credential = SecureCredential(
            credential_id=credential_id,
            environment_id=environment_id,
            credential_type=credential_type,
            encrypted_data=encrypted_data,
            expires_at=expires_at
        )
        
        self._credentials[credential_id] = credential
        logger.info(f"Stored {credential_type} credential for environment {environment_id}")
        
        return credential_id
    
    def retrieve_credential(self, credential_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve and decrypt a credential.
        
        Args:
            credential_id: Credential identifier
            
        Returns:
            Decrypted credential data or None if not found/expired
        """
        # Check cache first
        if credential_id in self._credential_cache:
            cached_data, cached_time = self._credential_cache[credential_id]
            if datetime.now() - cached_time < self._cache_ttl:
                return cached_data
            else:
                # Remove expired cache entry
                del self._credential_cache[credential_id]
        
        # Retrieve from storage
        credential = self._credentials.get(credential_id)
        if not credential:
            logger.warning(f"Credential {credential_id} not found")
            return None
        
        if credential.is_expired():
            logger.warning(f"Credential {credential_id} has expired")
            self._credentials.pop(credential_id, None)
            return None
        
        try:
            # Decrypt credential data
            decrypted_data = self.encryption_manager.decrypt_data(credential.encrypted_data)
            credential_data = json.loads(decrypted_data.decode())
            
            # Cache the decrypted data
            self._credential_cache[credential_id] = (credential_data, datetime.now())
            
            return credential_data
        except Exception as e:
            logger.error(f"Failed to decrypt credential {credential_id}: {e}")
            return None
    
    def delete_credential(self, credential_id: str) -> bool:
        """
        Delete a credential.
        
        Args:
            credential_id: Credential identifier
            
        Returns:
            True if deleted, False if not found
        """
        if credential_id in self._credentials:
            del self._credentials[credential_id]
            self._credential_cache.pop(credential_id, None)
            logger.info(f"Deleted credential {credential_id}")
            return True
        return False
    
    def cleanup_expired_credentials(self):
        """Remove expired credentials from storage"""
        expired_ids = [
            cred_id for cred_id, cred in self._credentials.items()
            if cred.is_expired()
        ]
        
        for cred_id in expired_ids:
            del self._credentials[cred_id]
            self._credential_cache.pop(cred_id, None)
        
        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired credentials")


class AccessControlManager:
    """Manages access control rules and permissions"""
    
    def __init__(self):
        """Initialize access control manager"""
        self._access_rules: Dict[str, List[AccessControlRule]] = {}
        self._default_permissions = {
            SecurityLevel.PUBLIC: ["read"],
            SecurityLevel.INTERNAL: ["read"],
            SecurityLevel.CONFIDENTIAL: [],
            SecurityLevel.SECRET: []
        }
    
    def add_access_rule(self, rule: AccessControlRule):
        """
        Add an access control rule.
        
        Args:
            rule: Access control rule to add
        """
        if rule.resource_id not in self._access_rules:
            self._access_rules[rule.resource_id] = []
        
        self._access_rules[rule.resource_id].append(rule)
        logger.info(f"Added access rule for resource {rule.resource_id} and user {rule.user_id}")
    
    def check_permission(self, 
                        resource_id: str, 
                        user_id: str, 
                        permission: str,
                        environment_id: Optional[str] = None) -> bool:
        """
        Check if a user has permission for a resource.
        
        Args:
            resource_id: Resource identifier
            user_id: User identifier
            permission: Permission to check (read, write, execute, deploy)
            environment_id: Environment identifier for environment-specific checks
            
        Returns:
            True if permission is granted, False otherwise
        """
        rules = self._access_rules.get(resource_id, [])
        
        for rule in rules:
            if rule.user_id == user_id and rule.has_permission(permission):
                # Check environment restrictions - if restrictions exist, environment must be in the list
                # Exception: for "read" permission, allow access if no specific environment is requested
                if rule.environment_restrictions:
                    if environment_id and environment_id not in rule.environment_restrictions:
                        continue
                    elif not environment_id and permission != "read":
                        # For non-read permissions, require environment to be specified if restrictions exist
                        continue
                
                # Check time restrictions
                if rule.time_restrictions:
                    if not self._check_time_restrictions(rule.time_restrictions):
                        continue
                
                return True
        
        return False
    
    def _check_time_restrictions(self, time_restrictions: Dict[str, Any]) -> bool:
        """
        Check if current time satisfies time restrictions.
        
        Args:
            time_restrictions: Time restriction configuration
            
        Returns:
            True if time restrictions are satisfied
        """
        now = datetime.now()
        
        # Check allowed hours
        if "allowed_hours" in time_restrictions:
            allowed_hours = time_restrictions["allowed_hours"]
            if now.hour not in allowed_hours:
                return False
        
        # Check allowed days of week
        if "allowed_days" in time_restrictions:
            allowed_days = time_restrictions["allowed_days"]
            if now.weekday() not in allowed_days:
                return False
        
        return True
    
    def get_user_permissions(self, resource_id: str, user_id: str) -> List[str]:
        """
        Get all permissions a user has for a resource.
        
        Args:
            resource_id: Resource identifier
            user_id: User identifier
            
        Returns:
            List of permissions
        """
        permissions = set()
        rules = self._access_rules.get(resource_id, [])
        
        for rule in rules:
            if rule.user_id == user_id and rule.is_valid():
                permissions.update(rule.permissions)
        
        return list(permissions)
    
    def cleanup_expired_rules(self):
        """Remove expired access control rules"""
        for resource_id in list(self._access_rules.keys()):
            valid_rules = [rule for rule in self._access_rules[resource_id] if rule.is_valid()]
            if valid_rules:
                self._access_rules[resource_id] = valid_rules
            else:
                del self._access_rules[resource_id]


class SecureArtifactHandler:
    """Handles secure artifact operations with encryption and access control"""
    
    def __init__(self, 
                 encryption_manager: EncryptionManager,
                 credential_manager: CredentialManager,
                 access_control_manager: AccessControlManager):
        """
        Initialize secure artifact handler.
        
        Args:
            encryption_manager: Encryption manager
            credential_manager: Credential manager
            access_control_manager: Access control manager
        """
        self.encryption_manager = encryption_manager
        self.credential_manager = credential_manager
        self.access_control_manager = access_control_manager
    
    def secure_artifact(self, 
                       artifact: TestArtifact, 
                       security_level: str = SecurityLevel.INTERNAL,
                       user_id: Optional[str] = None) -> TestArtifact:
        """
        Apply security measures to an artifact.
        
        Args:
            artifact: Test artifact to secure
            security_level: Security level to apply
            user_id: User requesting the operation
            
        Returns:
            Secured test artifact
        """
        # Debug logging
        logger.info(f"Securing artifact {artifact.name} with security level {security_level}")
        logger.info(f"Artifact current security level: {artifact.security_level}")
        logger.info(f"Contains sensitive data: {self._contains_sensitive_data(artifact)}")
        
        # Check if artifact contains sensitive data
        if self._contains_sensitive_data(artifact):
            logger.info(f"Encrypting sensitive artifact {artifact.name}")
            
            # Encrypt artifact content
            encrypted_content = self.encryption_manager.encrypt_data(artifact.content)
            
            # Create new artifact with encrypted content
            secured_artifact = TestArtifact(
                artifact_id=artifact.artifact_id,
                name=artifact.name,
                type=artifact.type,
                content=encrypted_content,
                checksum="",  # Will be recalculated
                permissions=artifact.permissions,
                target_path=artifact.target_path,
                dependencies=artifact.dependencies,
                metadata={
                    **artifact.metadata,
                    "encrypted": True,
                    "security_level": security_level,
                    "encryption_timestamp": datetime.now().isoformat()
                },
                is_encrypted=True,
                security_level=security_level,
                access_control_enabled=True
            )
            
            # Add access control if user specified
            if user_id:
                rule = AccessControlRule(
                    resource_id=artifact.artifact_id,
                    user_id=user_id,
                    permissions=["read", "deploy"],
                    environment_restrictions=[]  # No restrictions by default - will be set explicitly
                )
                # Don't add the rule automatically - let the caller add it with proper restrictions
                # self.access_control_manager.add_access_rule(rule)
            
            return secured_artifact
        
        # Return artifact with updated security level even if not encrypted
        artifact.security_level = security_level
        artifact.metadata["security_level"] = security_level
        return artifact
    
    def decrypt_artifact(self, 
                        artifact: TestArtifact, 
                        user_id: str) -> Optional[TestArtifact]:
        """
        Decrypt a secured artifact.
        
        Args:
            artifact: Encrypted test artifact
            user_id: User requesting decryption
            
        Returns:
            Decrypted artifact or None if access denied
        """
        # Debug logging
        logger.info(f"Attempting to decrypt artifact {artifact.artifact_id} for user {user_id}")
        logger.info(f"Artifact is encrypted: {artifact.metadata.get('encrypted', False)}")
        
        # Check if artifact is encrypted
        if not artifact.metadata.get("encrypted", False):
            logger.info(f"Artifact {artifact.artifact_id} is not encrypted, returning as-is")
            return artifact
        
        # Check access permissions
        has_permission = self.access_control_manager.check_permission(
            artifact.artifact_id, user_id, "read"
        )
        
        if not has_permission:
            logger.warning(f"Access denied for user {user_id} to artifact {artifact.artifact_id}")
            return None
        
        try:
            # Decrypt content
            decrypted_content = self.encryption_manager.decrypt_data(artifact.content)
            
            # Create decrypted artifact
            decrypted_artifact = TestArtifact(
                artifact_id=artifact.artifact_id,
                name=artifact.name,
                type=artifact.type,
                content=decrypted_content,
                checksum="",  # Will be recalculated
                permissions=artifact.permissions,
                target_path=artifact.target_path,
                dependencies=artifact.dependencies,
                metadata={
                    k: v for k, v in artifact.metadata.items() 
                    if k not in ["encrypted", "encryption_timestamp"]
                },
                is_encrypted=False,
                security_level=artifact.security_level,
                access_control_enabled=artifact.access_control_enabled
            )
            
            logger.info(f"Successfully decrypted artifact {artifact.name} for user {user_id}")
            return decrypted_artifact
            
        except Exception as e:
            logger.error(f"Failed to decrypt artifact {artifact.name}: {e}")
            return None
    
    def _contains_sensitive_data(self, artifact: TestArtifact) -> bool:
        """
        Check if artifact contains sensitive data that should be encrypted.
        
        Args:
            artifact: Test artifact to check
            
        Returns:
            True if artifact contains sensitive data
        """
        # Check metadata for security level first
        security_level = artifact.metadata.get("security_level", artifact.security_level)
        if security_level in [SecurityLevel.CONFIDENTIAL, SecurityLevel.SECRET]:
            return True
        
        # Check for sensitive keywords in content
        content_str = artifact.content.decode('utf-8', errors='ignore').lower()
        sensitive_keywords = [
            'password', 'secret', 'key', 'token', 'credential',
            'private', 'confidential', 'api_key', 'auth',
            'certificate', 'ssh_key', 'rsa', 'ecdsa'
        ]
        
        for keyword in sensitive_keywords:
            if keyword in content_str:
                return True
        
        # Check artifact type
        if artifact.type in [ArtifactType.CONFIG]:
            return True
        
        return False
    
    def enforce_deployment_permissions(self, 
                                     artifact: TestArtifact, 
                                     user_id: str, 
                                     environment_id: str) -> bool:
        """
        Enforce deployment permissions for an artifact.
        
        Args:
            artifact: Test artifact to deploy
            user_id: User requesting deployment
            environment_id: Target environment
            
        Returns:
            True if deployment is allowed, False otherwise
        """
        return self.access_control_manager.check_permission(
            artifact.artifact_id, user_id, "deploy", environment_id
        )