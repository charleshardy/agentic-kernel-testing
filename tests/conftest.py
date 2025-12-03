"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path
from config import Settings


@pytest.fixture
def test_settings() -> Settings:
    """Provide test settings with safe defaults."""
    return Settings(
        debug=True,
        log_level="DEBUG",
        database={"type": "sqlite", "name": ":memory:"},
        execution={"max_parallel_tests": 2, "test_timeout": 10},
    )


@pytest.fixture
def temp_artifact_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for test artifacts."""
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir(exist_ok=True)
    return artifact_dir


@pytest.fixture
def sample_code_diff() -> str:
    """Provide a sample code diff for testing."""
    return """
diff --git a/kernel/sched/core.c b/kernel/sched/core.c
index 1234567..abcdefg 100644
--- a/kernel/sched/core.c
+++ b/kernel/sched/core.c
@@ -100,6 +100,10 @@ void schedule(void)
     struct task_struct *prev, *next;
     
     prev = current;
+    
+    /* New scheduling logic */
+    if (prev->policy == SCHED_FIFO)
+        return;
     
     next = pick_next_task(rq);
     context_switch(prev, next);
"""


@pytest.fixture
def sample_test_case() -> dict:
    """Provide a sample test case for testing."""
    return {
        "id": "test_001",
        "name": "Test scheduler FIFO policy",
        "description": "Verify FIFO scheduling behavior",
        "test_type": "unit",
        "target_subsystem": "scheduler",
        "code_paths": ["kernel/sched/core.c::schedule"],
        "execution_time_estimate": 5,
        "required_hardware": {
            "architecture": "x86_64",
            "cpu_model": "generic",
            "memory_mb": 512,
            "is_virtual": True,
        },
    }
