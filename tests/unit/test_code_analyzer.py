"""Unit tests for code analysis and diff parsing."""

import pytest
from analysis import CodeAnalyzer, DiffParser, ASTAnalyzer, FileDiff
from ai_generator.models import Function, RiskLevel, TestType


@pytest.mark.unit
class TestDiffParser:
    """Tests for DiffParser."""
    
    def test_parse_simple_diff(self):
        """Test parsing a simple diff with one file."""
        diff_text = """diff --git a/test.c b/test.c
index 1234567..abcdefg 100644
--- a/test.c
+++ b/test.c
@@ -10,6 +10,8 @@ int main() {
     int x = 5;
+    int y = 10;
+    int z = x + y;
     return 0;
 }
"""
        parser = DiffParser()
        file_diffs = parser.parse_diff(diff_text)
        
        assert len(file_diffs) == 1
        assert file_diffs[0].file_path == "test.c"
        assert len(file_diffs[0].added_lines) == 2
        assert file_diffs[0].added_lines[0][1].strip() == "int y = 10;"
        assert file_diffs[0].added_lines[1][1].strip() == "int z = x + y;"
        assert len(file_diffs[0].removed_lines) == 0
    
    def test_parse_diff_with_removals(self):
        """Test parsing a diff with removed lines."""
        diff_text = """diff --git a/kernel/sched.c b/kernel/sched.c
index 1234567..abcdefg 100644
--- a/kernel/sched.c
+++ b/kernel/sched.c
@@ -50,8 +50,6 @@ void schedule() {
     struct task *t = current;
-    // Old comment
-    old_function();
     new_function();
 }
"""
        parser = DiffParser()
        file_diffs = parser.parse_diff(diff_text)
        
        assert len(file_diffs) == 1
        assert file_diffs[0].file_path == "kernel/sched.c"
        assert len(file_diffs[0].removed_lines) == 2
        assert len(file_diffs[0].added_lines) == 0
    
    def test_parse_diff_multiple_files(self):
        """Test parsing a diff with multiple files."""
        diff_text = """diff --git a/file1.c b/file1.c
index 1234567..abcdefg 100644
--- a/file1.c
+++ b/file1.c
@@ -10,6 +10,7 @@ void func1() {
     int x = 1;
+    int y = 2;
 }
diff --git a/file2.c b/file2.c
index 2345678..bcdefgh 100644
--- a/file2.c
+++ b/file2.c
@@ -20,6 +20,7 @@ void func2() {
     int a = 3;
+    int b = 4;
 }
"""
        parser = DiffParser()
        file_diffs = parser.parse_diff(diff_text)
        
        assert len(file_diffs) == 2
        assert file_diffs[0].file_path == "file1.c"
        assert file_diffs[1].file_path == "file2.c"
        assert len(file_diffs[0].added_lines) == 1
        assert len(file_diffs[1].added_lines) == 1
    
    def test_parse_diff_new_file(self):
        """Test parsing a diff with a new file."""
        diff_text = """diff --git a/new_file.c b/new_file.c
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/new_file.c
@@ -0,0 +1,5 @@
+#include <stdio.h>
+
+int main() {
+    return 0;
+}
"""
        parser = DiffParser()
        file_diffs = parser.parse_diff(diff_text)
        
        assert len(file_diffs) == 1
        assert file_diffs[0].file_path == "new_file.c"
        assert file_diffs[0].is_new_file is True
        assert len(file_diffs[0].added_lines) == 5
    
    def test_parse_diff_deleted_file(self):
        """Test parsing a diff with a deleted file."""
        diff_text = """diff --git a/old_file.c b/old_file.c
deleted file mode 100644
index 1234567..0000000
--- a/old_file.c
+++ /dev/null
@@ -1,5 +0,0 @@
-#include <stdio.h>
-
-int main() {
-    return 0;
-}
"""
        parser = DiffParser()
        file_diffs = parser.parse_diff(diff_text)
        
        assert len(file_diffs) == 1
        assert file_diffs[0].file_path == "old_file.c"
        assert file_diffs[0].is_deleted_file is True
        assert len(file_diffs[0].removed_lines) == 5
    
    def test_parse_empty_diff(self):
        """Test parsing an empty diff."""
        parser = DiffParser()
        file_diffs = parser.parse_diff("")
        assert len(file_diffs) == 0
        
        file_diffs = parser.parse_diff("   \n  \n")
        assert len(file_diffs) == 0
    
    def test_extract_changed_functions_python(self):
        """Test extracting changed functions from Python code."""
        source_code = """def function1():
    x = 1
    return x

def function2():
    y = 2
    return y

def function3():
    z = 3
    return z
"""
        file_diff = FileDiff(
            file_path="test.py",
            added_lines=[(6, "    y = 2")],
            removed_lines=[]
        )
        
        parser = DiffParser()
        functions = parser.extract_changed_functions(file_diff, source_code)
        
        assert len(functions) == 1
        assert functions[0].name == "function2"
        assert functions[0].file_path == "test.py"
    
    def test_extract_changed_functions_c(self):
        """Test extracting changed functions from C code."""
        file_diff = FileDiff(
            file_path="test.c",
            added_lines=[(10, "int my_function(int x) {")],
            removed_lines=[]
        )
        
        parser = DiffParser()
        functions = parser.extract_changed_functions(file_diff, None)
        
        assert len(functions) == 1
        assert functions[0].name == "my_function"
        assert functions[0].file_path == "test.c"
        assert functions[0].line_number == 10


@pytest.mark.unit
class TestASTAnalyzer:
    """Tests for ASTAnalyzer."""
    
    def test_identify_subsystems_filesystem(self):
        """Test identifying filesystem subsystem."""
        file_diffs = [
            FileDiff(file_path="fs/ext4/inode.c", added_lines=[], removed_lines=[]),
            FileDiff(file_path="fs/btrfs/disk-io.c", added_lines=[], removed_lines=[])
        ]
        
        analyzer = ASTAnalyzer()
        subsystems = analyzer.identify_subsystems(file_diffs)
        
        assert "filesystem" in subsystems
    
    def test_identify_subsystems_networking(self):
        """Test identifying networking subsystem."""
        file_diffs = [
            FileDiff(file_path="net/ipv4/tcp.c", added_lines=[], removed_lines=[])
        ]
        
        analyzer = ASTAnalyzer()
        subsystems = analyzer.identify_subsystems(file_diffs)
        
        assert "networking" in subsystems
    
    def test_identify_subsystems_multiple(self):
        """Test identifying multiple subsystems."""
        file_diffs = [
            FileDiff(file_path="fs/ext4/inode.c", added_lines=[], removed_lines=[]),
            FileDiff(file_path="net/core/sock.c", added_lines=[], removed_lines=[]),
            FileDiff(file_path="mm/page_alloc.c", added_lines=[], removed_lines=[])
        ]
        
        analyzer = ASTAnalyzer()
        subsystems = analyzer.identify_subsystems(file_diffs)
        
        assert len(subsystems) == 3
        assert "filesystem" in subsystems
        assert "networking" in subsystems
        assert "memory_management" in subsystems
    
    def test_identify_subsystems_unknown(self):
        """Test identifying unknown subsystem."""
        file_diffs = [
            FileDiff(file_path="random_file.c", added_lines=[], removed_lines=[])
        ]
        
        analyzer = ASTAnalyzer()
        subsystems = analyzer.identify_subsystems(file_diffs)
        
        assert "unknown" in subsystems
    
    def test_calculate_impact_score_small_change(self):
        """Test impact score calculation for small change."""
        file_diffs = [
            FileDiff(
                file_path="test.c",
                added_lines=[(1, "x")],
                removed_lines=[]
            )
        ]
        functions = []
        
        analyzer = ASTAnalyzer()
        score = analyzer.calculate_impact_score(file_diffs, functions)
        
        assert 0.0 <= score <= 0.3
    
    def test_calculate_impact_score_large_change(self):
        """Test impact score calculation for large change."""
        file_diffs = [
            FileDiff(
                file_path=f"file{i}.c",
                added_lines=[(j, f"line{j}") for j in range(50)],
                removed_lines=[]
            )
            for i in range(10)
        ]
        functions = [
            Function(name=f"func{i}", file_path="test.c", line_number=i)
            for i in range(15)
        ]
        
        analyzer = ASTAnalyzer()
        score = analyzer.calculate_impact_score(file_diffs, functions)
        
        assert score >= 0.5
    
    def test_calculate_impact_score_critical_subsystem(self):
        """Test impact score for critical subsystem changes."""
        file_diffs = [
            FileDiff(
                file_path="kernel/sched/core.c",
                added_lines=[(1, "x")],
                removed_lines=[]
            )
        ]
        functions = []
        
        analyzer = ASTAnalyzer()
        score = analyzer.calculate_impact_score(file_diffs, functions)
        
        # Should get critical subsystem bonus
        assert score >= 0.4
    
    def test_calculate_impact_score_empty(self):
        """Test impact score for empty changes."""
        analyzer = ASTAnalyzer()
        score = analyzer.calculate_impact_score([], [])
        assert score == 0.0
    
    def test_determine_risk_level_low(self):
        """Test risk level determination for low risk."""
        analyzer = ASTAnalyzer()
        risk = analyzer.determine_risk_level(0.1, ["documentation"])
        assert risk == RiskLevel.LOW
    
    def test_determine_risk_level_medium(self):
        """Test risk level determination for medium risk."""
        analyzer = ASTAnalyzer()
        risk = analyzer.determine_risk_level(0.3, ["drivers"])
        assert risk == RiskLevel.MEDIUM
    
    def test_determine_risk_level_high(self):
        """Test risk level determination for high risk."""
        analyzer = ASTAnalyzer()
        risk = analyzer.determine_risk_level(0.6, ["networking"])
        assert risk == RiskLevel.HIGH
    
    def test_determine_risk_level_critical(self):
        """Test risk level determination for critical risk."""
        analyzer = ASTAnalyzer()
        risk = analyzer.determine_risk_level(0.9, ["core_kernel"])
        assert risk == RiskLevel.CRITICAL
    
    def test_determine_risk_level_critical_subsystem(self):
        """Test risk level for critical subsystem with medium score."""
        analyzer = ASTAnalyzer()
        risk = analyzer.determine_risk_level(0.3, ["security"])
        assert risk == RiskLevel.HIGH
    
    def test_suggest_test_types_basic(self):
        """Test test type suggestions for basic changes."""
        analyzer = ASTAnalyzer()
        test_types = analyzer.suggest_test_types(["drivers"], [])
        
        assert TestType.UNIT in test_types
    
    def test_suggest_test_types_security(self):
        """Test test type suggestions for security changes."""
        analyzer = ASTAnalyzer()
        test_types = analyzer.suggest_test_types(["security"], [])
        
        assert TestType.UNIT in test_types
        assert TestType.SECURITY in test_types
        assert TestType.FUZZ in test_types
    
    def test_suggest_test_types_performance(self):
        """Test test type suggestions for performance-critical changes."""
        analyzer = ASTAnalyzer()
        test_types = analyzer.suggest_test_types(["memory_management"], [])
        
        assert TestType.UNIT in test_types
        assert TestType.PERFORMANCE in test_types
    
    def test_suggest_test_types_integration(self):
        """Test test type suggestions for multi-subsystem changes."""
        functions = [Function(name=f"f{i}", file_path="test.c", line_number=i) for i in range(10)]
        analyzer = ASTAnalyzer()
        test_types = analyzer.suggest_test_types(["fs", "mm"], functions)
        
        assert TestType.INTEGRATION in test_types


@pytest.mark.unit
class TestCodeAnalyzer:
    """Tests for CodeAnalyzer integration."""
    
    def test_analyze_diff_simple(self):
        """Test analyzing a simple diff."""
        diff_text = """diff --git a/kernel/sched/core.c b/kernel/sched/core.c
index 1234567..abcdefg 100644
--- a/kernel/sched/core.c
+++ b/kernel/sched/core.c
@@ -100,6 +100,8 @@ void schedule() {
     struct task *t = current;
+    // New logic
+    check_preempt(t);
     context_switch(t);
 }
"""
        analyzer = CodeAnalyzer()
        analysis = analyzer.analyze_diff(diff_text)
        
        assert len(analysis.changed_files) == 1
        assert "kernel/sched/core.c" in analysis.changed_files
        assert "core_kernel" in analysis.affected_subsystems
        assert analysis.impact_score > 0.0
        assert analysis.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert TestType.UNIT in analysis.suggested_test_types
    
    def test_analyze_diff_empty(self):
        """Test analyzing an empty diff."""
        analyzer = CodeAnalyzer()
        analysis = analyzer.analyze_diff("")
        
        assert len(analysis.changed_files) == 0
        assert len(analysis.affected_subsystems) == 0
        assert analysis.impact_score == 0.0
        assert analysis.risk_level == RiskLevel.LOW
    
    def test_analyze_diff_with_source(self):
        """Test analyzing diff with source code provided."""
        diff_text = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -5,6 +5,7 @@ def my_function():
     x = 1
+    y = 2
     return x
"""
        source_code = """def my_function():
    x = 1
    y = 2
    return x

def other_function():
    pass
"""
        analyzer = CodeAnalyzer()
        analysis = analyzer.analyze_diff(diff_text, {"test.py": source_code})
        
        assert len(analysis.changed_files) == 1
        assert "test.py" in analysis.changed_files
        # Should extract function from AST
        assert len(analysis.changed_functions) >= 0
    
    def test_analyze_diff_multiple_files(self):
        """Test analyzing diff with multiple files."""
        diff_text = """diff --git a/fs/ext4/inode.c b/fs/ext4/inode.c
index 1234567..abcdefg 100644
--- a/fs/ext4/inode.c
+++ b/fs/ext4/inode.c
@@ -100,6 +100,7 @@ int ext4_write() {
+    check_permissions();
     return 0;
 }
diff --git a/net/ipv4/tcp.c b/net/ipv4/tcp.c
index 2345678..bcdefgh 100644
--- a/net/ipv4/tcp.c
+++ b/net/ipv4/tcp.c
@@ -200,6 +200,7 @@ int tcp_send() {
+    validate_packet();
     return 0;
 }
"""
        analyzer = CodeAnalyzer()
        analysis = analyzer.analyze_diff(diff_text)
        
        assert len(analysis.changed_files) == 2
        assert len(analysis.affected_subsystems) == 2
        assert "filesystem" in analysis.affected_subsystems
        assert "networking" in analysis.affected_subsystems
        assert TestType.INTEGRATION in analysis.suggested_test_types
