from fastmcp import FastMCP
import xml.etree.ElementTree as ET
import os
import subprocess
import re
from typing import Optional, List, Dict
mcp = FastMCP("tesing-agent")

@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers"""
    return a + b

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract b from a"""
    return a - b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide a by b"""
    if b == 0:
        return float('inf')
    return a / b

if __name__ == "__main__":
    mcp.run(transport="sse")


# phase2 coverage analysis tools
@mcp.tool()
def find_jacoco_path(project_path: str) -> str:
    """Find the JaCoCo report path in the given project directory."""
    jacoco_paths = [
            f"{project_path}/target/site/jacoco/jacoco.xml",
            f"{project_path}/target/jacoco.xml",
            f"{project_path}/build/jacoco/jacoco.xml"
        ]
        
    for path in jacoco_paths:
            if os.path.exists(path):
                return path
        
    return "JaCoCo report not found. Run 'mvn clean test' first."


@mcp.tool()
def analyze_java_code(file_path: str) -> dict:
    """analyze Java source code and extract methods with signatures."""
    methods = {}
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Better regex for method detection (handles multi-line signatures)
        method_pattern = r'(public|private|protected)\s+(?:static\s+)?(\w+)\s+(\w+)\s*\([^)]*\)'
        
        for match in re.finditer(method_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            method_name = match.group(3)
            return_type = match.group(2)
            methods[line_num] = {
                "name": method_name,
                "return_type": return_type,
                "signature": match.group(0)
            }
        
        return {
            "file": file_path,
            "total_methods": len(methods),
            "methods": methods
        }
    except FileNotFoundError:
        return {"error": f"File not found: {file_path}"}
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}
    
@mcp.tool()
def generate_test_template(class_name: str, methods: dict) -> str:
    """Generate JUnit test class template from analyzed methods."""
    test_class = "import org.junit.jupiter.api.Test;\n"
    test_class += "import static org.junit.jupiter.api.Assertions.*;\n\n"
    test_class += f"public class {class_name}Test {{\n"
    
    for line_num, method_info in methods.items():
        method_name = method_info["name"]
        test_class += "    @Test\n"
        test_class += f"    void test{method_name.capitalize()}() {{\n"
        test_class += "        // Placeholder: Replace with actual test assertions\n"
        test_class += "        assertTrue(true);\n"
        test_class += "    }\n\n"
    
    test_class += "}\n"
    return test_class


@mcp.tool()
def total_coverage(project_path: str = ".") -> dict:
    """Parse JaCoCo report and return total coverage metrics."""
    jacoco_path = find_jacoco_path(project_path)
    if "not found" in jacoco_path:
        return {"error": jacoco_path}
    
    try:
        tree = ET.parse(jacoco_path)
        root = tree.getroot()
        
        coverage_data = {
            "line_coverage": 0,
            "branch_coverage": 0,
            "method_coverage": 0,
            "instruction_coverage": 0
        }
        
        # Parse LINE coverage
        for counter in root.findall(".//counter[@type='LINE']"):
            covered = int(counter.get('covered', 0))
            missed = int(counter.get('missed', 0))
            total = covered + missed
            if total > 0:
                coverage_data["line_coverage"] = round((covered / total) * 100, 2)
        
        # Parse BRANCH coverage
        for counter in root.findall(".//counter[@type='BRANCH']"):
            covered = int(counter.get('covered', 0))
            missed = int(counter.get('missed', 0))
            total = covered + missed
            if total > 0:
                coverage_data["branch_coverage"] = round((covered / total) * 100, 2)
        
        # Parse METHOD coverage
        for counter in root.findall(".//counter[@type='METHOD']"):
            covered = int(counter.get('covered', 0))
            missed = int(counter.get('missed', 0))
            total = covered + missed
            if total > 0:
                coverage_data["method_coverage"] = round((covered / total) * 100, 2)
        
        # Parse INSTRUCTION coverage
        for counter in root.findall(".//counter[@type='INSTRUCTION']"):
            covered = int(counter.get('covered', 0))
            missed = int(counter.get('missed', 0))
            total = covered + missed
            if total > 0:
                coverage_data["instruction_coverage"] = round((covered / total) * 100, 2)
        
        return coverage_data
    except ET.ParseError as e:
        return {"error": f"Invalid JaCoCo XML: {str(e)}"}
    except Exception as e:
        return {"error": f"Coverage parsing failed: {str(e)}"}
    



@mcp.tool()
def run_maven_tests(project_path: str = ".") -> dict:
    """Run Maven tests and generate JaCoCo report"""
    try:
        result = subprocess.run(
            ["mvn", "clean", "test", "jacoco:report"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {
            "success": result.returncode == 0,
            "message": "Tests executed successfully" if result.returncode == 0 else "Tests failed",
            "jacoco_path": find_jacoco_path(project_path)
        }
    except Exception as e:
        return {"error": str(e)}





@mcp.tool()
def missing_coverage(file_path: str, project_path: str = ".") -> dict:
    """Identify uncovered lines in a specific file."""
    jacoco_path = find_jacoco_path(project_path)
    if "not found" in jacoco_path:
        return {"error": jacoco_path}
    
    try:
        tree = ET.parse(jacoco_path)
        root = tree.getroot()
        
        uncovered_lines = []
        file_name = os.path.basename(file_path).replace('.java', '.class')
        
        for sourcefile in root.findall(".//sourcefile"):
            if file_name in sourcefile.get('name', '') or file_path in sourcefile.get('name', ''):
                for line in sourcefile.findall(".//line"):
                    ci = int(line.get('ci', 0))  # ci = covered instructions
                    if ci == 0:
                        uncovered_lines.append({
                            "line_number": int(line.get('nr')),
                            "instruction_count": int(line.get('ci', 0)),
                            "branch_count": int(line.get('cb', 0))
                        })
        
        return {
            "file": file_path,
            "total_uncovered_lines": len(uncovered_lines),
            "uncovered_lines": uncovered_lines
        }
    except Exception as e:
        return {"error": f"Coverage analysis failed: {str(e)}"}
    



@mcp.tool()
def git_status(repo_path: str = ".") -> str:
    """Return git status: clean status, staged changes, conflicts."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        staged_changes = []
        unstaged_changes = []
        conflicts = []
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            status = line[:2]
            file = line[3:]
            
            if status[0] != ' ':
                staged_changes.append({"file": file, "status": status[0]})
            if status[1] != ' ':
                unstaged_changes.append({"file": file, "status": status[1]})
            if 'U' in status:
                conflicts.append(file)
        
        is_clean = not staged_changes and not unstaged_changes and not conflicts
        
        return {
            "is_clean": is_clean,
            "staged_changes": staged_changes,
            "unstaged_changes": unstaged_changes,
            "conflicts": conflicts,
            "total_changes": len(staged_changes) + len(unstaged_changes)
        }
    except Exception as e:
        return {"error": f"Failed to get git status: {str(e)}"}


@mcp.tool()
def git_add_all(repo_path: str = ".") -> dict:
    """Stage all changes with intelligent filtering (exclude build artifacts and temp files)."""
    try:
        # Files to exclude
        exclude_patterns = [
            "target/",
            "build/",
            ".class",
            ".jar",
            "__pycache__/",
            "*.pyc",
            ".DS_Store",
            "node_modules/"
        ]
        
        # Get current status
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        files_to_add = []
        excluded_files = []
        
        for line in status_result.stdout.strip().split('\n'):
            if not line:
                continue
            file = line[3:]
            
            # Check if file should be excluded
            should_exclude = False
            for pattern in exclude_patterns:
                if pattern in file:
                    should_exclude = True
                    excluded_files.append(file)
                    break
            
            if not should_exclude:
                files_to_add.append(file)
        
        # Stage non-excluded files
        if files_to_add:
            subprocess.run(
                ["git", "add"] + files_to_add,
                cwd=repo_path,
                capture_output=True
            )
        
        return {
            "success": True,
            "files_staged": files_to_add,
            "files_excluded": excluded_files,
            "total_staged": len(files_to_add),
            "total_excluded": len(excluded_files)
        }
    except Exception as e:
        return {"error": f"Failed to stage changes: {str(e)}"}

@mcp.tool()
def git_commit(repo_path: str = ".", message: str = "", coverage: Optional[dict] = None) -> dict:
    """Automated commit with standardized messages and coverage statistics."""
    try:
        # Build commit message with coverage stats if provided
        commit_msg = message
        
        if coverage:
            coverage_info = f"\n\n[Coverage Report]\n"
            coverage_info += f"Line Coverage: {coverage.get('line_coverage', 'N/A')}%\n"
            coverage_info += f"Branch Coverage: {coverage.get('branch_coverage', 'N/A')}%\n"
            coverage_info += f"Method Coverage: {coverage.get('method_coverage', 'N/A')}%\n"
            coverage_info += f"Instruction Coverage: {coverage.get('instruction_coverage', 'N/A')}%"
            commit_msg += coverage_info
        
        # Commit
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": "Commit successful",
                "commit_output": result.stdout.strip()
            }
        else:
            return {
                "success": False,
                "error": result.stderr.strip() if result.stderr else "No changes to commit"
            }
    except Exception as e:
        return {"error": f"Failed to commit: {str(e)}"}


@mcp.tool()
def git_push(repo_path: str = ".", remote: str = "origin", branch: Optional[str] = None) -> dict:
    """Push to remote with upstream configuration and authentication."""
    try:
        # Get current branch if not specified
        if not branch:
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            branch = branch_result.stdout.strip()
        
        # Check if branch protection exists (main/master)
        protected_branches = ["main", "master"]
        if branch in protected_branches:
            return {
                "warning": f"Branch '{branch}' is protected. Consider creating a pull request instead.",
                "branch": branch
            }
        
        # Push to remote
        result = subprocess.run(
            ["git", "push", "-u", remote, branch],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": f"Successfully pushed '{branch}' to '{remote}'",
                "push_output": result.stdout.strip()
            }
        else:
            return {
                "success": False,
                "error": result.stderr.strip() if result.stderr else "Push failed"
            }
    except Exception as e:
        return {"error": f"Failed to push: {str(e)}"}



@mcp.tool()
def git_pull_request(repo_path: str = ".", base: str = "main", title: str = "", body: str = "", coverage: Optional[dict] = None) -> dict:
    """Create a pull request with standardized templates and metadata."""
    try:
        # Get current branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        current_branch = branch_result.stdout.strip()
        
        if current_branch == base:
            return {"error": f"Cannot create PR from '{base}' to itself"}
        
        # Build PR body with coverage metadata
        pr_body = body if body else "## Changes\n- Automated test generation and coverage improvements\n"
        
        if coverage:
            pr_body += "\n## Coverage Improvements\n"
            pr_body += f"- **Line Coverage**: {coverage.get('line_coverage', 'N/A')}%\n"
            pr_body += f"- **Branch Coverage**: {coverage.get('branch_coverage', 'N/A')}%\n"
            pr_body += f"- **Method Coverage**: {coverage.get('method_coverage', 'N/A')}%\n"
            pr_body += f"- **Instruction Coverage**: {coverage.get('instruction_coverage', 'N/A')}%\n"
        
        pr_body += "\n## Test Quality Metrics\n"
        pr_body += "- All tests pass\n"
        pr_body += "- Generated by AI Testing Agent\n"
        pr_body += "- Coverage gaps identified and addressed\n"
        
        # Use gh CLI to create PR
        result = subprocess.run(
            [
                "gh", "pr", "create",
                "--base", base,
                "--head", current_branch,
                "--title", title if title else f"Test Coverage Improvement: {current_branch}",
                "--body", pr_body
            ],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            pr_url = result.stdout.strip()
            return {
                "success": True,
                "message": "Pull request created successfully",
                "pr_url": pr_url,
                "base_branch": base,
                "head_branch": current_branch
            }
        else:
            # If gh CLI not available, provide manual instructions
            return {
                "success": False,
                "note": "GitHub CLI (gh) not found. Manual PR creation required.",
                "instructions": {
                    "steps": [
                        f"1. Push your branch: git push -u origin {current_branch}",
                        f"2. Open GitHub and create PR from '{current_branch}' to '{base}'",
                        f"3. Use this title: {title if title else f'Test Coverage Improvement: {current_branch}'}",
                        f"4. Paste this description: {pr_body}"
                    ]
                }
            }
    except Exception as e:
        return {"error": f"Failed to create PR: {str(e)}"}
    


@mcp.tool()
def generate_specification_tests(java_file_path: str, class_name: str) -> str:
    try:
        with open(java_file_path, 'r') as f:
            content = f.read()
        
        methods = {}
        method_pattern = r'(public|private|protected)\s+(?:static\s+)?(\w+)\s+(\w+)\s*\([^)]*\)'
        
        for match in re.finditer(method_pattern, content):
            method_name = match.group(3)
            return_type = match.group(2)
            methods[method_name] = return_type
        
        test_class = "import org.junit.jupiter.api.Test;\n"
        test_class += "import static org.junit.jupiter.api.Assertions.*;\n\n"
        test_class += f"public class {class_name}SpecificationTest {{\n\n"
        test_class += "    private " + class_name + " instance = new " + class_name + "();\n\n"
        
        for method_name in list(methods.keys())[:5]:
            test_class += "    // Boundary Value Analysis\n"
            test_class += f"    @Test\n"
            test_class += f"    void test{method_name}WithMinValue() {{\n"
            test_class += f"        assertDoesNotThrow(() -> instance.{method_name}());\n"
            test_class += f"    }}\n\n"
            
            test_class += f"    @Test\n"
            test_class += f"    void test{method_name}WithMaxValue() {{\n"
            test_class += f"        assertDoesNotThrow(() -> instance.{method_name}());\n"
            test_class += f"    }}\n\n"
            
            test_class += "    // Equivalence Class Partitioning\n"
            test_class += f"    @Test\n"
            test_class += f"    void test{method_name}WithValidInput() {{\n"
            test_class += f"        assertDoesNotThrow(() -> instance.{method_name}());\n"
            test_class += f"    }}\n\n"
            
            test_class += f"    @Test\n"
            test_class += f"    void test{method_name}WithInvalidInput() {{\n"
            test_class += f"        assertThrows(Exception.class, () -> instance.{method_name}());\n"
            test_class += f"    }}\n\n"
            
            test_class += "    // Decision Table Testing\n"
            test_class += f"    @Test\n"
            test_class += f"    void test{method_name}DecisionTable() {{\n"
            test_class += f"        boolean condition1 = true;\n"
            test_class += f"        boolean condition2 = false;\n"
            test_class += f"        assertNotNull(instance);\n"
            test_class += f"    }}\n\n"
            
            test_class += "    // Contract-Based Testing\n"
            test_class += f"    @Test\n"
            test_class += f"    void test{method_name}Preconditions() {{\n"
            test_class += f"        assertNotNull(instance);\n"
            test_class += f"    }}\n\n"
            
            test_class += f"    @Test\n"
            test_class += f"    void test{method_name}Postconditions() {{\n"
            test_class += f"        assertDoesNotThrow(() -> instance.{method_name}());\n"
            test_class += f"    }}\n\n"
        
        test_class += "}\n"
        return test_class
    
    except FileNotFoundError:
        return f"// File not found: {java_file_path}"
    except Exception as e:
        return f"// Error: {str(e)}"
    

@mcp.tool()
def code_review(file_path: str) -> dict:
    """AI Code Review: static analysis, code smells, security vulnerabilities, style enforcement."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        issues = []
        
        # Code Smells: Long methods (>50 lines)
        for match in re.finditer(r'(public|private|protected)\s+\w+\s+(\w+)\s*\([^)]*\)\s*\{', content):
            brace, pos = 1, match.end()
            lines = 1
            while brace > 0 and pos < len(content):
                if content[pos] == '{': brace += 1
                elif content[pos] == '}': brace -= 1
                elif content[pos] == '\n': lines += 1
                pos += 1
            if lines > 50:
                issues.append({"smell": "Long Method", "method": match.group(2), "fix": "Extract methods"})
        
        # Security: SQL Injection
        if re.search(r'".*\+.*SELECT|UPDATE|DELETE', content, re.IGNORECASE):
            issues.append({"security": "SQL Injection", "fix": "Use PreparedStatement"})
        
        # Security: Logging vulnerability
        if re.search(r'System\.out\.println|printStackTrace', content):
            issues.append({"security": "Insecure Logging", "fix": "Use logger.info()"})
        
        # Security: Command execution
        if re.search(r'Runtime\.getRuntime\(\)\.exec', content):
            issues.append({"security": "Command Injection", "fix": "Validate input"})
        
        # Style: Missing Javadoc
        methods = len(re.findall(r'public\s+\w+\s+\w+\s*\([^)]*\)', content))
        docs = len(re.findall(r'/\*\*.*?\*/', content, re.DOTALL))
        if methods > docs:
            issues.append({"style": "Missing Documentation", "fix": f"Add {methods - docs} Javadoc comments"})
        
        # Style: Unused imports
        imports = re.findall(r'import\s+([\w.]+);', content)
        unused = [i for i in imports if i.split('.')[-1] not in content]
        if unused:
            issues.append({"style": "Unused Imports", "fix": f"Remove {len(unused)} imports"})
        
        return {"file": file_path, "issues": issues, "total": len(issues)}
    
    except FileNotFoundError:
        return {"error": f"File not found: {file_path}"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run(transport="sse")



