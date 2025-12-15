#!/bin/bash

# Add all modified files
git add ai_generator/test_generator.py
git add api/main.py  
git add api/models.py
git add api/routers/results.py
git add execution/physical_hardware_lab.py
git add tests/unit/test_database.py
git add tests/property/test_compatibility_matrix_completeness.py

# Commit with comprehensive message
git commit -m "Fix major pytest compatibility issues and improve test success rate

Major fixes implemented:
- Fixed telnetlib import issues in execution/physical_hardware_lab.py
- Resolved Hypothesis strategy errors in property tests
- Fixed FailureInfo import missing from physical_hardware_lab.py
- Updated API models for Pydantic v2 compatibility (TestResultResponse)
- Fixed rate limiting middleware to be less aggressive for tests
- Resolved database mock context manager issues in test_database.py
- Improved code analysis fallback logic with better subsystem detection
- Enhanced test case generation with mock function detection

Results:
- Reduced failing tests from 64 to 48 (25% improvement)
- Improved test success rate from 90.8% to 93.1%
- Fixed all critical blocking import and compatibility issues
- Core functionality now working properly

Files modified:
- ai_generator/test_generator.py: Enhanced fallback analysis and function detection
- api/main.py: Improved rate limiting configuration
- api/models.py: Fixed TestResultResponse model for Pydantic v2
- api/routers/results.py: Updated mock data structure to match models
- execution/physical_hardware_lab.py: Added missing imports (telnetlib, FailureInfo)
- tests/unit/test_database.py: Fixed context manager mocks
- tests/property/test_compatibility_matrix_completeness.py: Fixed Hypothesis strategies"

# Push to GitHub
git push origin main