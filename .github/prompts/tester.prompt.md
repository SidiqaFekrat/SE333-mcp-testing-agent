---
mode: "agent"
tools: ["find_jacoco_path", "analyze_java_code", "generate_test_template","run_maven_tests"," total_coverage", "missing_coverage", "git_status", "git_add_all", "git_commit", "git_push", " git_pull_request"]
description: "a tool that takes a java file, analyze it, generate test for it,run the tests using mvn test, get the total coverage, and finally extracts the missing coverage "
model: 'Gpt-5 mini'
---

## Follow instruction below: ##
1. First find all the source code files to test using "analyze_java_code"
2. For each source file, use "generate_test_template" to create test scaffolds based on extracted methods
3. Run the tests using "run_maven_tests" to execute  "mvn clean test jacoco:report"
4. If the tests have errors, fix the test code and run "run_maven_tests" again
5. Use "find_jacoco_path" to locate the JaCoCo XML report file
6. Use "total_coverage" to parse the JaCoCo report and get line_coverage, branch_coverage, method_coverage, and instruction_coverage percentage.
7. Use "missing_coverage" to identify uncovered lines in each source file.
8. If "missing_coverage" returns uncovered lines (total_uncovered_lines >0), generate additional test cases targeting those specific lines.
9. Repeat steps 3-8 until "total_coverage" shows all metrics at acceptable levels (line_coverage >= 90%) or "missing_coverage" returns total_uncovered_lines=0
10. Check repository status using "git_status" that shows the current changes.
11. Use  "git_add_all" to stage the code and tests
12. Use "git_commit" with coverage stats included in message to commit the changes that were added
13. Use "git_push" to push to origin branch 
14. Use "git_pull_request" to create pull request against main with coverage metadata. 


