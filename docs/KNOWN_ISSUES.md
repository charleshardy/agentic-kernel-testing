# Known Issues and Solutions

This document contains known issues encountered in the Agentic AI Testing System for Linux Kernel and BSP, along with their solutions and workarounds.

## Table of Contents

- [Pytest Collection Failures](#pytest-collection-failures)
- [Pydantic v2 Compatibility Issues](#pydantic-v2-compatibility-issues)

---

## Pytest Collection Failures

### Issue: Pydantic v2 Settings Validation Error

**Symptoms:**
- Pytest fails to collect tests with validation errors
- Error message shows: `ValidationError: 47 validation errors for Settings`
- Multiple "Extra inputs are not permitted" errors for environment variables
- Tests cannot run due to collection failure

**Error Example:**
```
pydantic_core._pydantic_core.ValidationError: 47 validation errors for Settings
environment
  Extra inputs are not permitted [type=extra_forbidden, input_value='development', input_type=str]
aws_profile
  Extra inputs are not permitted [type=extra_forbidden, input_value='my-sso-profile', input_type=str]
...
```

**Root Cause:**
The `Settings` class in `config/settings.py` uses Pydantic v2's strict validation mode, which by default forbids extra fields. However, the `.env` file contains many environment variables (like `aws_profile`, `openai__api_key`, etc.) that aren't explicitly defined in the Settings model.

**Solution:**
Add `extra="ignore"` to the `ConfigDict` in the Settings class to allow extra environment variables to be ignored:

```python
# In config/settings.py
class Settings(BaseSettings):
    # ... other fields ...
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"  # ✅ This allows extra environment variables to be ignored
    )
```

**Status:** ✅ **RESOLVED** (Fixed in commit 11de104)

**Prevention:**
- When adding new environment variables to `.env.example`, ensure they are either:
  1. Added to the appropriate config class in `config/settings.py`, or
  2. The `extra="ignore"` setting remains in place to handle undefined variables

---

## Pydantic v2 Compatibility Issues

### Issue: Import and Model Validation Errors

**Symptoms:**
- Import errors related to Pydantic v2 changes
- `BaseSettings` import failures
- Model validation errors with new Pydantic v2 syntax
- API model validation failures

**Common Errors:**
- `ImportError: cannot import name 'BaseSettings' from 'pydantic'`
- `ValidationError` with field validation issues
- `regex` parameter not recognized (should be `pattern`)
- `.dict()` method deprecated warnings

**Solutions Applied:**

1. **BaseSettings Import Fix:**
   ```python
   # OLD (Pydantic v1)
   from pydantic import BaseSettings
   
   # NEW (Pydantic v2)
   from pydantic_settings import BaseSettings
   ```

2. **Field Validation Updates:**
   ```python
   # OLD
   Field(regex=r"pattern")
   
   # NEW  
   Field(pattern=r"pattern")
   ```

3. **Model Method Updates:**
   ```python
   # OLD
   model.dict()
   
   # NEW
   model.model_dump()
   ```

4. **Reserved Field Names:**
   ```python
   # Avoid using 'metadata' as column name in SQLAlchemy models
   # Use 'meta_data' or similar instead
   ```

**Status:** ✅ **RESOLVED** (Fixed in multiple commits)

**Prevention:**
- Follow Pydantic v2 migration guide when adding new models
- Use `model_dump()` instead of `.dict()` for new code
- Test model validation when adding new fields

---

## Contributing to This Document

When you encounter a new issue:

1. **Document the Issue:**
   - Clear description of symptoms
   - Error messages (sanitized of sensitive data)
   - Steps to reproduce

2. **Provide Root Cause Analysis:**
   - What caused the issue
   - Why it occurred

3. **Document the Solution:**
   - Step-by-step fix
   - Code examples where applicable
   - Prevention measures

4. **Update Status:**
   - Mark as resolved when fixed
   - Include commit hash or PR reference

---

## Getting Help

If you encounter an issue not listed here:

1. Check the [GitHub Issues](https://github.com/charleshardy/agentic-kernel-testing/issues)
2. Search existing documentation in the `docs/` directory
3. Create a new issue with detailed reproduction steps
4. Consider adding the solution to this document once resolved

---

*Last Updated: December 12, 2024*