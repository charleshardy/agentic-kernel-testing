import subprocess
import sys

try:
    # Test the settings import
    result = subprocess.run([
        sys.executable, '-c', 
        'from config.settings import Settings; s = Settings(); print("SUCCESS: Settings loaded")'
    ], capture_output=True, text=True, timeout=10)
    
    print("Settings test result:")
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
    
    if result.returncode == 0:
        print("✅ Settings fix is working!")
    else:
        print("❌ Settings still has issues")
        
    # Test pytest collection
    print("\nTesting pytest collection...")
    result2 = subprocess.run([
        sys.executable, '-m', 'pytest', '--collect-only', '-q'
    ], capture_output=True, text=True, timeout=30)
    
    print("Pytest collection result:")
    print("Return code:", result2.returncode)
    if "ValidationError" in result2.stderr:
        print("❌ Still has validation errors")
    else:
        print("✅ No validation errors in collection!")
        
except Exception as e:
    print(f"Error running test: {e}")