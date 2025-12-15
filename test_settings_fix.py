#!/usr/bin/env python3

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

try:
    print("Testing settings import...")
    from config.settings import Settings
    
    print("Creating Settings instance...")
    settings = Settings()
    
    print("✅ SUCCESS: Settings loaded without validation errors!")
    print(f"App name: {settings.app_name}")
    print(f"Debug mode: {settings.debug}")
    
    print("\nTesting API import...")
    from api.main import app
    print("✅ SUCCESS: API app imported successfully!")
    
    print("\nAll tests passed! The Pydantic validation issue is fixed.")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)