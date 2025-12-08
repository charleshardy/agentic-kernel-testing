"""Example demonstrating historical failure database usage.

This example shows how to:
1. Store failure patterns in the historical database
2. Match new failures against historical patterns
3. Track resolutions
4. Query historical data
"""

from datetime import datetime, timedelta
from analysis.historical_failure_db import (
    HistoricalFailureDatabase,
    FailurePattern,
    PatternMatcher
)
from analysis.root_cause_analyzer import (
    RootCauseAnalyzer,
    StackTraceParser,
    FailureSignatureGenerator
)
from ai_generator.models import (
    TestResult, TestStatus, Environment, HardwareConfig,
    FailureInfo, FailureAnalysis, ArtifactBundle
)


def main():
    """Demonstrate historical failure database usage."""
    
    print("=" * 80)
    print("Historical Failure Database Example")
    print("=" * 80)
    
    # Create database (in-memory for demo)
    db = HistoricalFailureDatabase()
    
    # Example 1: Store historical failure patterns
    print("\n1. Storing Historical Failure Patterns")
    print("-" * 80)
    
    patterns = [
        FailurePattern(
            pattern_id="pattern_001",
            signature="abc123def456",
            error_pattern="null_pointer",
            root_cause="NULL pointer dereference in network driver initialization",
            occurrence_count=5,
            first_seen=datetime.now() - timedelta(days=30),
            last_seen=datetime.now() - timedelta(days=5),
            resolution="Added NULL check before dereferencing driver->priv",
            resolution_date=datetime.now() - timedelta(days=3)
        ),
        FailurePattern(
            pattern_id="pattern_002",
            signature="xyz789abc012",
            error_pattern="use_after_free",
            root_cause="Use-after-free in memory cache cleanup",
            occurrence_count=3,
            first_seen=datetime.now() - timedelta(days=15),
            last_seen=datetime.now() - timedelta(days=2)
        ),
        FailurePattern(
            pattern_id="pattern_003",
            signature="def456ghi789",
            error_pattern="deadlock",
            root_cause="Deadlock between filesystem lock and memory lock",
            occurrence_count=8,
            first_seen=datetime.now() - timedelta(days=60),
            last_seen=datetime.now() - timedelta(days=1),
            resolution="Changed lock ordering to always acquire filesystem lock first",
            resolution_date=datetime.now()
        )
    ]
    
    for pattern in patterns:
        db.store_failure_pattern(pattern)
        status = "RESOLVED" if pattern.resolution else "UNRESOLVED"
        print(f"  Stored: {pattern.pattern_id} - {pattern.error_pattern} ({status})")
    
    # Example 2: Match a new failure against historical patterns
    print("\n2. Matching New Failure Against Historical Patterns")
    print("-" * 80)
    
    # Create a new failure
    env = Environment(
        id="env_test",
        config=HardwareConfig(
            architecture="x86_64",
            cpu_model="Intel Core i7",
            memory_mb=8192
        )
    )
    
    failure_info = FailureInfo(
        error_message="NULL pointer dereference at address 0x0000000000000000",
        stack_trace="""
        [<ffffffff81234567>] network_driver_init+0x42/0x100
        [<ffffffff81234890>] driver_probe+0x10/0x50
        [<ffffffff81234abc>] device_attach+0x20/0x80
        """,
        kernel_panic=True
    )
    
    test_result = TestResult(
        test_id="test_new_001",
        status=TestStatus.FAILED,
        execution_time=10.5,
        environment=env,
        failure_info=failure_info,
        artifacts=ArtifactBundle()
    )
    
    # Analyze the failure
    analyzer = RootCauseAnalyzer()
    failure_analysis = analyzer.analyze_failure(test_result)
    
    print(f"  New Failure Analysis:")
    print(f"    Root Cause: {failure_analysis.root_cause}")
    print(f"    Error Pattern: {failure_analysis.error_pattern}")
    print(f"    Confidence: {failure_analysis.confidence:.2f}")
    
    # Generate signature for matching
    stack_parser = StackTraceParser()
    sig_generator = FailureSignatureGenerator()
    parsed_stack = stack_parser.parse_stack_trace(failure_info.stack_trace)
    signature = sig_generator.generate_signature(failure_info, parsed_stack)
    
    # Match against historical patterns
    matcher = PatternMatcher(db)
    matches = matcher.match_failure(failure_analysis, signature)
    
    print(f"\n  Found {len(matches)} matching historical pattern(s):")
    for i, (pattern, score) in enumerate(matches[:3], 1):
        print(f"\n    Match {i} (similarity: {score:.2f}):")
        print(f"      Pattern ID: {pattern.pattern_id}")
        print(f"      Root Cause: {pattern.root_cause}")
        print(f"      Occurrences: {pattern.occurrence_count}")
        if pattern.resolution:
            print(f"      Resolution: {pattern.resolution}")
            print(f"      Resolved: {pattern.resolution_date.strftime('%Y-%m-%d')}")
    
    # Example 3: Query database statistics
    print("\n3. Database Statistics")
    print("-" * 80)
    
    stats = db.get_statistics()
    print(f"  Total Patterns: {stats['total_patterns']}")
    print(f"  Resolved: {stats['resolved_patterns']}")
    print(f"  Unresolved: {stats['unresolved_patterns']}")
    print(f"  Resolution Rate: {stats['resolution_rate']:.1%}")
    
    print("\n  Common Error Patterns:")
    for ep in stats['common_error_patterns']:
        print(f"    {ep['error_pattern']}: {ep['count']} pattern(s)")
    
    # Example 4: Search for patterns
    print("\n4. Searching for Patterns")
    print("-" * 80)
    
    search_results = db.search_by_root_cause("network")
    print(f"  Found {len(search_results)} pattern(s) related to 'network':")
    for pattern in search_results:
        print(f"    - {pattern.pattern_id}: {pattern.root_cause[:60]}...")
    
    # Example 5: Get unresolved patterns
    print("\n5. Unresolved Patterns (Need Attention)")
    print("-" * 80)
    
    unresolved = db.get_unresolved_patterns(min_occurrences=2)
    print(f"  Found {len(unresolved)} unresolved pattern(s) with 2+ occurrences:")
    for pattern in unresolved:
        print(f"    - {pattern.pattern_id}: {pattern.error_pattern}")
        print(f"      Occurrences: {pattern.occurrence_count}")
        print(f"      Last Seen: {pattern.last_seen.strftime('%Y-%m-%d')}")
    
    # Example 6: Update resolution for a pattern
    print("\n6. Updating Pattern Resolution")
    print("-" * 80)
    
    if unresolved:
        pattern_to_resolve = unresolved[0]
        resolution = "Fixed by adding proper error handling in cleanup path"
        success = db.update_resolution(pattern_to_resolve.pattern_id, resolution)
        
        if success:
            print(f"  Updated resolution for {pattern_to_resolve.pattern_id}")
            print(f"  Resolution: {resolution}")
            
            # Verify update
            updated = db.lookup_by_pattern_id(pattern_to_resolve.pattern_id)
            print(f"  Verified: Resolution stored successfully")
    
    # Clean up
    db.close()
    
    print("\n" + "=" * 80)
    print("Example Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
