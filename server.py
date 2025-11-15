from fastmcp import FastMCP
import xml.etree.ElementTree as ET
import os
import subprocess
import re


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


