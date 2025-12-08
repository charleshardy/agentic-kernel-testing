# Historical Failure Database

The Historical Failure Database provides persistent storage and pattern matching for test failures, enabling the system to learn from past issues and provide better root cause analysis.

## Features

- **Failure Pattern Storage**: Store failure patterns with signatures, error types, and root causes
- **Pattern Matching**: Match new failures against historical patterns using signature and error pattern matching
- **Resolution Tracking**: Track when and how failures were resolved
- **Statistical Analysis**: Get insights into failure patterns, resolution rates, and common issues
- **Search Capabilities**: Search patterns by root cause, error type, or other criteria

## Architecture

### Components

1. **FailurePattern**: Data model representing a pattern of failures
   - Unique signature for matching
   - Error pattern classification
   - Root cause description
   - Occurrence count and timestamps
   - Resolution information

2. **HistoricalFailureDatabase**: SQLite-based storage for patterns and instances
   - Pattern storage and retrieval
   - Instance tracking
   - Resolution management
   - Statistical queries

3. **PatternMatcher**: Matches new failures against historical patterns
   - Exact signature matching (score 1.0)
   - Error pattern matching with similarity scoring
   - Ranked results by relevance

## Usage

### Basic Usage

```python
from analysis.historical_failure_db import (
    HistoricalFailureDatabase,
    FailurePattern,
    PatternMatcher
)

# Create database
db = HistoricalFailureDatabase("failures.db")

# Store a failure pattern
pattern = FailurePattern(
    pattern_id="pattern_001",
    signature="abc123def456",
    error_pattern="null_pointer",
    root_cause="NULL pointer dereference in driver",
    occurrence_count=5
)
db.store_failure_pattern(pattern)

# Match a new failure
matcher = PatternMatcher(db)
matches = matcher.match_failure(failure_analysis, signature)

for pattern, score in matches:
    print(f"Match: {pattern.root_cause} (score: {score})")
    if pattern.resolution:
        print(f"Resolution: {pattern.resolution}")
```

### Integration with Root Cause Analyzer

```python
from analysis.root_cause_analyzer import RootCauseAnalyzer
from analysis.historical_failure_db import HistoricalFailureDatabase, PatternMatcher

# Analyze a failure
analyzer = RootCauseAnalyzer()
failure_analysis = analyzer.analyze_failure(test_result)

# Check against historical patterns
db = HistoricalFailureDatabase("failures.db")
matcher = PatternMatcher(db)

# Generate signature
from analysis.root_cause_analyzer import FailureSignatureGenerator, StackTraceParser
parser = StackTraceParser()
sig_gen = FailureSignatureGenerator()

parsed_stack = parser.parse_stack_trace(test_result.failure_info.stack_trace)
signature = sig_gen.generate_signature(test_result.failure_info, parsed_stack)

# Find matches
matches = matcher.match_failure(failure_analysis, signature)

if matches:
    best_match, score = matches[0]
    print(f"Similar issue found: {best_match.root_cause}")
    if best_match.resolution:
        print(f"Previous resolution: {best_match.resolution}")
```

### Querying Historical Data

```python
# Get statistics
stats = db.get_statistics()
print(f"Total patterns: {stats['total_patterns']}")
print(f"Resolution rate: {stats['resolution_rate']:.1%}")

# Search by root cause
results = db.search_by_root_cause("network driver")

# Get unresolved patterns
unresolved = db.get_unresolved_patterns(min_occurrences=3)

# Get resolved patterns
resolved = db.get_resolved_patterns(error_pattern="null_pointer")
```

### Updating Resolutions

```python
# Mark a pattern as resolved
db.update_resolution(
    pattern_id="pattern_001",
    resolution="Added NULL check before dereferencing pointer"
)

# Verify update
pattern = db.lookup_by_pattern_id("pattern_001")
print(f"Resolution: {pattern.resolution}")
print(f"Resolved on: {pattern.resolution_date}")
```

## Database Schema

### failure_patterns Table

| Column | Type | Description |
|--------|------|-------------|
| pattern_id | TEXT | Unique pattern identifier (PRIMARY KEY) |
| signature | TEXT | Failure signature hash for matching |
| error_pattern | TEXT | Error pattern type (null_pointer, deadlock, etc.) |
| root_cause | TEXT | Root cause description |
| occurrence_count | INTEGER | Number of times this pattern occurred |
| first_seen | TEXT | ISO timestamp of first occurrence |
| last_seen | TEXT | ISO timestamp of last occurrence |
| resolution | TEXT | Resolution description (NULL if unresolved) |
| resolution_date | TEXT | ISO timestamp when resolved |
| metadata | TEXT | JSON metadata |

### failure_instances Table

| Column | Type | Description |
|--------|------|-------------|
| instance_id | TEXT | Unique instance identifier (PRIMARY KEY) |
| pattern_id | TEXT | Foreign key to failure_patterns |
| test_id | TEXT | Test that produced this failure |
| failure_message | TEXT | Error message |
| stack_trace | TEXT | Stack trace |
| timestamp | TEXT | ISO timestamp |
| environment_info | TEXT | JSON environment information |

## Pattern Matching Algorithm

The pattern matcher uses a two-stage approach:

1. **Exact Signature Match**: If the failure signature exactly matches a stored pattern, return it with score 1.0

2. **Error Pattern Match**: If no exact match, find patterns with the same error pattern type and calculate similarity based on root cause text overlap

Similarity scoring uses word overlap:
```
similarity = |words_in_common| / |total_unique_words|
```

Results are filtered by a minimum similarity threshold (0.3) and sorted by score.

## Best Practices

1. **Store Patterns Early**: Store failure patterns as soon as they're analyzed to build historical knowledge

2. **Update Resolutions**: Always update patterns with resolution information when issues are fixed

3. **Regular Cleanup**: Periodically review and clean up old or obsolete patterns

4. **Use Metadata**: Store additional context in the metadata field for richer analysis

5. **Monitor Statistics**: Track resolution rates and common patterns to identify systemic issues

## Performance Considerations

- Database uses SQLite with indices on signature and error_pattern for fast lookups
- In-memory database option available for testing (`:memory:`)
- Pattern matching is optimized with early exit on exact matches
- Limit query results to prevent memory issues with large datasets

## Testing

The implementation includes comprehensive tests:

- **Unit Tests**: `tests/unit/test_historical_failure_db.py`
  - Database operations
  - Pattern storage and retrieval
  - Resolution tracking
  - Search functionality

- **Property-Based Tests**: `tests/property/test_historical_pattern_matching.py`
  - Pattern matching correctness
  - Statistical accuracy
  - Query consistency
  - 100+ test iterations per property

Run tests:
```bash
pytest tests/unit/test_historical_failure_db.py -v
pytest tests/property/test_historical_pattern_matching.py -v
```

## Example

See `examples/historical_failure_example.py` for a complete working example demonstrating all features.

Run example:
```bash
PYTHONPATH=. python3 examples/historical_failure_example.py
```

## Future Enhancements

Potential improvements for future versions:

1. **Advanced Similarity Metrics**: Use embeddings or TF-IDF for better text similarity
2. **Pattern Clustering**: Automatically group related patterns
3. **Trend Analysis**: Track pattern evolution over time
4. **Export/Import**: Support for sharing pattern databases between teams
5. **Web Interface**: Dashboard for browsing and managing patterns
6. **Integration with Issue Trackers**: Link patterns to bug tracking systems
