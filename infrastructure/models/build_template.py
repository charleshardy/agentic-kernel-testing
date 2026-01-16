"""
Build Template Models

Defines data models for saving and loading build configuration templates.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class BuildTemplate(BaseModel):
    """
    Build configuration template that can be saved and reused.
    
    Allows users to save common build configurations (custom commands,
    environment variables, etc.) and load them when submitting new builds.
    """
    id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    
    # Build configuration
    build_mode: str = Field("kernel", description="Build mode: kernel or custom")
    
    # Build paths
    workspace_root: Optional[str] = None
    output_directory: Optional[str] = None
    keep_workspace: bool = False
    
    # Git options
    git_depth: Optional[int] = None
    git_submodules: bool = False
    
    # Kernel build config
    kernel_config: Optional[str] = None
    extra_make_args: Optional[List[str]] = None
    artifact_patterns: Optional[List[str]] = None
    
    # Custom build commands
    pre_build_commands: Optional[List[str]] = None
    build_commands: Optional[List[str]] = None
    post_build_commands: Optional[List[str]] = None
    
    # Environment variables
    custom_env: Optional[Dict[str, str]] = None
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: Optional[str] = Field(None, description="User who created the template")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "uboot-qemu-arm64",
                "name": "U-Boot QEMU ARM64",
                "description": "Build U-Boot for QEMU ARM64 target",
                "build_mode": "custom",
                "pre_build_commands": [
                    "export CROSS_COMPILE=aarch64-linux-gnu-",
                    "export ARCH=arm64"
                ],
                "build_commands": [
                    "make clean",
                    "make qemu_arm64_defconfig",
                    "make -j$(nproc)"
                ],
                "post_build_commands": [
                    "ls -lh u-boot.bin"
                ],
                "custom_env": {
                    "CC": "gcc-12",
                    "CFLAGS": "-O2"
                }
            }
        }


class BuildTemplateCreate(BaseModel):
    """Request model for creating a new build template"""
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    build_mode: str = Field("kernel", description="Build mode: kernel or custom")
    workspace_root: Optional[str] = None
    output_directory: Optional[str] = None
    keep_workspace: bool = False
    git_depth: Optional[int] = None
    git_submodules: bool = False
    kernel_config: Optional[str] = None
    extra_make_args: Optional[List[str]] = None
    artifact_patterns: Optional[List[str]] = None
    pre_build_commands: Optional[List[str]] = None
    build_commands: Optional[List[str]] = None
    post_build_commands: Optional[List[str]] = None
    custom_env: Optional[Dict[str, str]] = None


class BuildTemplateUpdate(BaseModel):
    """Request model for updating an existing build template"""
    name: Optional[str] = None
    description: Optional[str] = None
    build_mode: Optional[str] = None
    workspace_root: Optional[str] = None
    output_directory: Optional[str] = None
    keep_workspace: Optional[bool] = None
    git_depth: Optional[int] = None
    git_submodules: Optional[bool] = None
    kernel_config: Optional[str] = None
    extra_make_args: Optional[List[str]] = None
    artifact_patterns: Optional[List[str]] = None
    pre_build_commands: Optional[List[str]] = None
    build_commands: Optional[List[str]] = None
    post_build_commands: Optional[List[str]] = None
    custom_env: Optional[Dict[str, str]] = None
