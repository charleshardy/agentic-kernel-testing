#!/bin/bash
python3 -m pytest tests/property/test_baseline_comparison.py::TestBaselineComparison::test_baseline_comparison_execution -v --hypothesis-show-statistics --tb=short
