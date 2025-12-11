#!/usr/bin/env python3
"""
Debug specific test failures.
"""

import sys
import traceback
sys.path.insert(0, '.')

def debug_ai_generator():
    """Debug AI generator issues."""
    print("Debugging AI Generator...")
    
    try:
        from ai_generator.test_generator import AITestGenerator
        from ai_generator.models import CodeAnalysis, Function, RiskLevel
        
        print("✅ Imports successful")
        
        # Create generator
        generator = AITestGenerator()
        print("✅ Generator created")
        
        # Create a simple function
        func = Function(
            name="schedule",
            file_path="kernel/sched/core.c",
            line_number=100
        )
        print("✅ Function created")
        
        # Create code analysis
        analysis = CodeAnalysis(
            changed_functions=[func],
            affected_subsystems=["scheduler"],
            impact_score=0.7,
            risk_level=RiskLevel.MEDIUM
        )
        print("✅ CodeAnalysis created")
        
        # Try to generate test cases
        print("Attempting to generate test cases...")
        test_cases = generator.generate_test_cases(analysis)
        print(f"✅ Generated {len(test_cases)} test cases")
        
        # Check first test case
        if test_cases:
            first_test = test_cases[0]
            print(f"✅ First test case: {first_test.name}")
            print(f"   ID: {first_test.id}")
            print(f"   Type: {first_test.test_type}")
            print(f"   Subsystem: {first_test.target_subsystem}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI Generator debug failed: {e}")
        traceback.print_exc()
        return False

def debug_coverage_analyzer():
    """Debug coverage analyzer issues."""
    print("\nDebugging Coverage Analyzer...")
    
    try:
        from analysis.coverage_analyzer import CoverageAnalyzer
        from ai_generator.models import CoverageData
        
        print("✅ Imports successful")
        
        # Create analyzer
        analyzer = CoverageAnalyzer()
        print("✅ Analyzer created")
        
        # Create simple coverage data
        coverage = CoverageData(
            line_coverage=0.8,
            branch_coverage=0.7,
            function_coverage=0.9
        )
        print("✅ CoverageData created")
        
        # Test identify_gaps method
        print("Testing identify_gaps...")
        gaps = analyzer.identify_gaps(coverage)
        print(f"✅ Identified {len(gaps)} gaps")
        
        # Test merge_coverage method
        print("Testing merge_coverage...")
        coverage2 = CoverageData(
            line_coverage=0.6,
            branch_coverage=0.5,
            function_coverage=0.8
        )
        
        merged = analyzer.merge_coverage([coverage, coverage2])
        print(f"✅ Merged coverage: line={merged.line_coverage:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Coverage Analyzer debug failed: {e}")
        traceback.print_exc()
        return False

def debug_property_test_execution():
    """Debug property test execution."""
    print("\nDebugging Property Test Execution...")
    
    try:
        from hypothesis import given, strategies as st, settings
        
        # Simple property test
        @given(st.integers(min_value=1, max_value=10))
        @settings(max_examples=5)
        def test_simple_property(x):
            assert x > 0
            return x * 2
        
        print("Testing simple property...")
        result = test_simple_property()
        print(f"✅ Simple property test completed")
        
        # Test with AI generator
        @given(st.integers(min_value=1, max_value=5))
        @settings(max_examples=3)
        def test_ai_generator_property(num_functions):
            from ai_generator.test_generator import AITestGenerator
            from ai_generator.models import CodeAnalysis, Function, RiskLevel
            
            # Create functions
            functions = [
                Function(name=f"func_{i}", file_path=f"file_{i}.c", line_number=i*10)
                for i in range(num_functions)
            ]
            
            analysis = CodeAnalysis(
                changed_functions=functions,
                impact_score=0.5,
                risk_level=RiskLevel.MEDIUM
            )
            
            generator = AITestGenerator()
            test_cases = generator.generate_test_cases(analysis)
            
            # Property: Should generate at least one test case
            assert len(test_cases) >= 1, f"Expected at least 1 test, got {len(test_cases)}"
            return len(test_cases)
        
        print("Testing AI generator property...")
        result = test_ai_generator_property()
        print(f"✅ AI generator property test completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Property test debug failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Main debug function."""
    print("Debugging Specific Test Failures")
    print("=" * 50)
    
    results = []
    
    # Debug AI Generator
    results.append(("AI Generator", debug_ai_generator()))
    
    # Debug Coverage Analyzer  
    results.append(("Coverage Analyzer", debug_coverage_analyzer()))
    
    # Debug Property Tests
    results.append(("Property Tests", debug_property_test_execution()))
    
    # Summary
    print("\n" + "=" * 50)
    print("DEBUG SUMMARY")
    print("=" * 50)
    
    passed = 0
    for name, success in results:
        status = "PASSED" if success else "FAILED"
        print(f"{name}: {status}")
        if success:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} debug tests passed")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)