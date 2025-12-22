#!/usr/bin/env python3
"""
Script to organize test, verification, and debug files from root directory
"""
import os
import shutil
import glob

def organize_files():
    """Organize files into appropriate directories"""
    
    # Define file patterns and their target directories
    file_mappings = {
        'dev-scripts/test-scripts/': [
            'test_*.py',
            'simple_test*.py', 
            'comprehensive_test*.py',
            'final_test*.py',
            'quick_test*.py'
        ],
        'dev-scripts/verification-scripts/': [
            'verify_*.py',
            '*_verification.py',
            'final_verification.py'
        ],
        'dev-scripts/debug-scripts/': [
            'debug_*.py'
        ],
        'dev-scripts/runners/': [
            'run_*.py',
            '*_runner.py'
        ],
        'dev-scripts/validation/': [
            'comprehensive_system_check.py',
            'comprehensive_property_test.py'
        ]
    }
    
    moved_files = []
    
    for target_dir, patterns in file_mappings.items():
        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)
        
        for pattern in patterns:
            files = glob.glob(pattern)
            for file_path in files:
                if os.path.isfile(file_path):
                    target_path = os.path.join(target_dir, os.path.basename(file_path))
                    try:
                        shutil.move(file_path, target_path)
                        moved_files.append(f"{file_path} -> {target_path}")
                        print(f"Moved: {file_path} -> {target_path}")
                    except Exception as e:
                        print(f"Error moving {file_path}: {e}")
    
    return moved_files

if __name__ == "__main__":
    print("Organizing root directory files...")
    moved = organize_files()
    print(f"\nTotal files moved: {len(moved)}")
    
    if moved:
        print("\nMoved files:")
        for item in moved:
            print(f"  {item}")
    else:
        print("No files were moved.")