# Known Issues and Solutions

This document contains known issues encountered in the Agentic AI Testing System for Linux Kernel and BSP, along with their solutions and workarounds.

## Table of Contents

- [Pytest Collection Failures](#pytest-collection-failures)
- [Pydantic v2 Compatibility Issues](#pydantic-v2-compatibility-issues)
- [Dashboard Empty Contents Issue](#dashboard-empty-contents-issue)
- [Dashboard Auto-Redirect to Login](#dashboard-auto-redirect-to-login)

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

**Prevention:**q
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

## Dashboard Empty Contents Issue

### Issue: Dashboard Shows Flash of Content Then Goes Empty

**Symptoms:**
- Dashboard loads briefly showing content, then becomes empty/blank
- Page appears to be connected but no content is displayed
- Browser console may show TypeScript compilation errors
- Vite development server may show compilation failures

**Error Examples:**
```
TypeScript compilation errors:
src/pages/Dashboard.tsx(349,15): error TS2322: Type 'ExecutionPlanStatus[]' is not assignable...
Type '{ plan_id: string; overall_status: "running"; ... }' is missing properties: submission_id, failed_tests, test_statuses
```

**Root Cause:**
The Dashboard component contains mock data objects that don't match the TypeScript interfaces defined in the API service. When TypeScript compilation fails, the component fails to render properly, causing the empty content issue.

**Solution:**
1. **Fix Mock Data Types**: Ensure all mock data objects match their TypeScript interfaces:

```typescript
// ❌ Incorrect - missing required properties
const mockExecutions = [
  {
    plan_id: 'exec-plan-001',
    overall_status: 'running',
    progress: 0.65,
    completed_tests: 13,
    total_tests: 20,
  }
]

// ✅ Correct - includes all required properties
const mockExecutions: ExecutionPlanStatus[] = [
  {
    plan_id: 'exec-plan-001',
    submission_id: 'sub-001',
    overall_status: 'running',
    progress: 0.65,
    completed_tests: 13,
    total_tests: 20,
    failed_tests: 1,
    test_statuses: [],
    started_at: new Date().toISOString(),
  }
]
```

2. **Fix Connection State**: Update the store to start with `isConnected: true` and handle API errors gracefully:

```typescript
// In store/index.ts
const initialState = {
  isConnected: true, // Start as connected, let queries handle errors
  // ... other state
}
```

3. **Remove Blocking Connection Check**: Remove the early return that blocks rendering when not connected:

```typescript
// ❌ Remove this blocking check
if (!isConnected) {
  return <Alert message="Connection Lost" ... />
}

// ✅ Always render dashboard content
```

**Status:** ✅ **RESOLVED** (Fixed in current commit)

**Verification:**
1. Run TypeScript compilation: `cd dashboard && npx tsc --noEmit`
2. Should complete without errors
3. Start dashboard: `npm run dev`
4. Dashboard should show rich content with system metrics, charts, and data

**Prevention:**
- Always run TypeScript compilation before committing dashboard changes
- Use proper TypeScript interfaces for all mock data
- Test dashboard in both connected and disconnected states
- Use the diagnose script: `cd dashboard && node diagnose.js`

---

## Dashboard Auto-Redirect to Login

### Issue: Browser Automatically Redirects from / to /login

**Symptoms:**
- Visiting `http://localhost:3000/` automatically redirects to `http://localhost:3000/login`
- Login page shows but no authentication is implemented
- User cannot access the main dashboard

**Root Cause:**
The API service has an authentication interceptor that automatically redirects to `/login` when any API call returns a 401 (Unauthorized) status. In demo mode, many API endpoints return 401, triggering this redirect.

**Solution:**
1. **Disable Auto-Redirect in Demo Mode**: Update the API service interceptor to not redirect automatically:

```typescript
// In dashboard/src/services/api.ts
this.client.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log authentication errors but don't auto-redirect in demo mode
    if (error.response?.status === 401) {
      console.log('Authentication required for:', error.config?.url)
      localStorage.removeItem('auth_token')
      // Don't auto-redirect - let the dashboard handle this gracefully with mock data
    }
    return Promise.reject(error)
  }
)
```

2. **Add Login Route Handler**: Create a placeholder login page that redirects back to dashboard:

```typescript
// In dashboard/src/App.tsx
const LoginPlaceholder = () => (
  <Alert
    message="Demo Mode - No Authentication Required"
    description="Click below to return to the dashboard."
    action={<a href="/">Return to Dashboard</a>}
  />
)

// Add route: <Route path="/login" element={<LoginPlaceholder />} />
```

3. **Update Logout Handler**: Prevent logout from redirecting to login in demo mode:

```typescript
// In dashboard/src/components/Layout/DashboardLayout.tsx
const handleUserMenuClick = ({ key }: { key: string }) => {
  if (key === 'logout') {
    localStorage.removeItem('auth_token')
    // In demo mode, just stay on the dashboard
    console.log('Logout clicked - staying in demo mode')
  }
}
```

**Status:** ✅ **RESOLVED** (Fixed in current commit)

**Verification:**
1. Visit `http://localhost:3000/`
2. Should stay on the dashboard, not redirect to login
3. If redirected to login, click "Return to Dashboard" link
4. Dashboard should show with demo data

**Prevention:**
- Use conditional authentication redirects based on endpoint type
- Implement proper authentication flow when moving from demo to production
- Test both authenticated and unauthenticated scenarios

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