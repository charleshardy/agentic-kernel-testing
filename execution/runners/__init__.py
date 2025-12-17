"""Test runners package for different execution environments."""

from .docker_runner import DockerTestRunner

__all__ = ['DockerTestRunner']