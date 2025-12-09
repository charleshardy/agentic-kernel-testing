#!/usr/bin/env python3
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-c", "print('Hello from subprocess')"],
    capture_output=True,
    text=True
)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)
