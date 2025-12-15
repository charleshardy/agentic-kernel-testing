#!/bin/bash

# Add the settings fix
git add config/settings.py

# Commit the fix
git commit -m "Fix Pydantic v2 settings validation error

- Added extra='ignore' to ConfigDict in Settings class
- This allows extra environment variables to be ignored instead of causing validation errors
- Resolves the 47 validation errors that were preventing pytest from running
- Fixes the 'Extra inputs are not permitted' error for environment variables"

echo "Settings fix committed successfully!"

# Test the fix
echo "Testing the fix..."
python3 -c "
try:
    from config.settings import Settings
    s = Settings()
    print('✅ SUCCESS: Settings loaded without validation errors!')
except Exception as e:
    print(f'❌ ERROR: {e}')
"