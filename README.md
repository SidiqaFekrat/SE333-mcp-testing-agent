# AI Powered Testing Agent:
An intelligent MCP agent that automatically generates tests, measures code coverage with JaCoCo, identifies missing tests using coverage, and iteratively improves test coverage up to 90%+ for the java classes.

## Installation & Setup:
### Prerequisites:
        Python 3.8+
        Java 11+
        Maven 3.6+
        Node.js 18+
        Git

### Installation Steps:
1. Clone and navigate to project:
    cd final_project_se333_sidiqa

2. Create the virtual environment:
    uv venv
    source .venv/bin/activate

3. Install MCP dependencies:
    uv add 'mcp[cli]' httpx fastmcp

4. Start MCP server:
    python3 codebase/server.py

After running, you should see: Uvicorn running on http://127.0.0.1:8000


Configure in VS Code:
    1. Press CTRL+SHIFT+P and search for MCP: Add Server
    2. Enter URL from the output of running codebase/server.py: http://127.0.0.1:8000/sse
    3. Name: testing-agent
    4. Enable Chat: Auto-Approve in VS Code settings
    5. Refresh VS Code Chat view the MCP tools that should be visible 


## MCP Tools Documentation:
### File: codebase/server.py (17 tools)
#### Phase1-2: Test Generation & Coverage.

    1. analyze_java_code(file_path):
        Input: Java file path.
        Output: Methods with signatures
        Purpose: Extract methods for testing
    
    2. generate_test_template(class_name, methods)
        Input: Class name plus methods dict
        Output: JUnit test class code
        Purpose: generate Unit tests
    
    3. run_maven_tests(project_path)
        Input: Project path
        Output: Test results with the coverage info
        Purpose: Get coverage metrics

    4. total_coverage(project_path)
        Input: Project path
        Output:Line/branch/method/instruction %
        Purpose: Get coverage info 


    5. missing_coverage(file_path, project_path)
        Input: File path + project path
        Output: List of uncovered lines
        Purpose: Identify missing coverage if there is any

    6. find_jacoco_path(project_path)
        Input: Project path
        Output: Path to jacoco.xml
        Purpose: Locate coverage report

#### Phase 3: Git Automation

    1. git_status(repo_path)
        Input: Repo path
        Output: Staged / unstaged changes
        Purpose: Check repository status
    
    2. git_add_all(repo_path)
        Input: Repo path
        Output: Stage the changes in the java files and the new added tests by the agent
        Purpose: Stage changes (excludes build artifacts)

    3. git_commit(repo_path, message, coverage)
        Input: Repo path + message + coverage dict
        Output: commit the changes and the coverage result
        Purpose: Commit with coverage stats

    4. git_push(repo_path, remote, branch)
        Input: Repo path + remote + branch
        Output: Push result
        Purpose: Push the commited changes to remote repo
    
    5. git_pull_request(repo_path, base, title, body, coverage)
        Input: Repo path + base + metadata
        Output: PR URL or manual instructions
        Purpose: Create pull request

#### Phase 5: Creative Extensions

    1. generate_specification_tests(java_file_path, class_name)
        Input: Java file path + class name
        Output: Test class with boundary, equivalence, and decision table tests
        Purpose: Advanced specification-based testing

    2. code_review(file_path)
        Input: Java file path
        Output: Issues list with auto-fixes
        Purpose: Detects code smells, security issues, style violations

## Agent Workflow:
### file: tester.prompt.md
### Steps 1-9 (Phase 4-5: Coverage Iteration):
    1. Analyze all the source files.
    2. Generate tests for them.
    3. Run tests with JaCoCo to get the coverage info.
    4. Fix error if needed.
    5. Locate the coverage report.
    6. parse the coverage metrics.
    7. Identify uncovered lines
    8. Generate additional tests if there is missing coverage.
    9. Repeat until 90%+ coverage
    10. Generate specification-based tests
    11. Review code quality
    12. Check git status
    13. Stage files
    14. Commit with coverage stats
    15. Push to origin
    16. Create PR against main


## Usage Example:
 Open VS Code chat and type ( run # tester.prompt.md)

    

## TroubleShooting:
1. Problem: JaCoCo report not found
   Solution: Run mvn clean test jacoco:report in codebase/

2. Problem: MCP server won't start
   solution: Verify: python3 -c "import fastmcp" works

2. Problem: Tools not showing in Chat
   Solution: Restart VS Code and reconnect MCP server




