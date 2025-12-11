#!/bin/bash
python3 -m pytest tests/property/test_security_report_completeness.py --hypothesis-seed=0 -v > test_output_security_report.txt 2>&1
echo "Exit code: $?" >> test_output_security_report.txt
cat test_output_security_report.txt
