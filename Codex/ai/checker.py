"""
Code analysis and execution safety module for CommandCoreCodex.

This module provides tools for static code analysis and safe execution of Python code.
"""

import ast
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

class CodeChecker:
    """
    A class for performing static code analysis and safe execution of Python code.
    
    This class provides methods to:
    1. Lint Python code for common issues and style violations
    2. Execute Python code in a sandboxed environment with resource limits
    """
    
    @staticmethod
    def lint_code(source: str) -> List[str]:
        """
        Perform static analysis on Python source code and return a list of issues.
        
        Args:
            source: Python source code string to analyze
            
        Returns:
            List of strings, where each string describes an issue found in the code.
            Each string is formatted as: "Line X: [TYPE] Description"
            
        Detected issues include:
        - Usage of 'global' keyword
        - Lines longer than 80 characters
        - Trailing whitespace
        - TODO comments
        """
        issues: List[str] = []
        
        # Check for global keyword usage
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Global):
                    line_no = node.lineno
                    issues.append(f"Line {line_no}: [WARNING] Use of 'global' keyword is discouraged")
        except SyntaxError as e:
            issues.append(f"Line {e.lineno or '?'}: [ERROR] {e.msg}")
        
        # Check line length, trailing whitespace, and TODOs
        for i, line in enumerate(source.splitlines(), 1):
            # Check line length
            if len(line) > 80:
                issues.append(f"Line {i}: [STYLE] Line exceeds 80 characters ({len(line)})")
            
            # Check for trailing whitespace
            if line.endswith(' '):
                issues.append(f"Line {i}: [STYLE] Trailing whitespace")
            
            # Check for TODO comments
            if 'TODO' in line.upper():
                issues.append(f"Line {i}: [NOTE] TODO comment found")
        
        return issues
    
    @staticmethod
    def run_sandboxed(source: str, timeout: float = 3.0) -> Tuple[str, str]:
        """
        Execute Python source code in a sandboxed subprocess.
        
        Args:
            source: Python source code to execute
            timeout: Maximum execution time in seconds (default: 3.0)
            
        Returns:
            A tuple of (stdout, stderr) strings from the executed code
            
        Raises:
            subprocess.TimeoutExpired: If the code execution exceeds the timeout
            subprocess.CalledProcessError: If the subprocess returns a non-zero exit code
        """
        # Create a temporary file to store the source code
        with tempfile.NamedTemporaryFile(
            mode='w+',
            suffix='.py',
            encoding='utf-8',
            delete=False
        ) as tmp_file:
            tmp_file.write(source)
            tmp_path = tmp_file.name
        
        try:
            # Prepare environment with minimal safe variables
            env = {
                'PYTHONPATH': '',
                'PATH': os.environ.get('PATH', ''),
                'HOME': os.environ.get('HOME', ''),
                'LANG': 'C.UTF-8',
                'PYTHONIOENCODING': 'utf-8',
            }
            
            # Execute the code in a subprocess
            result = subprocess.run(
                [sys.executable, '-S', '-I', tmp_path],  # -S: don't import site, -I: isolate
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
            
            return result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            # Clean up the process if it's still running
            try:
                result.kill()
            except (UnboundLocalError, AttributeError):
                pass
            raise
            
        finally:
            # Ensure the temporary file is removed
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except (OSError, PermissionError):
                pass


def main() -> None:
    """
    Demonstrate the functionality of the CodeChecker class.
    """
    # Example code with various issues
    example_code = """
# This is an example with a TODO comment
# TODO: Implement this function properly

def example():
    global some_var  # Using global is generally not recommended
    some_var = "This is a very long line that definitely exceeds the 80 character limit and should be reported by the linter."  # noqa: E501
    print(some_var)  
    
    # Line with trailing whitespace    
    return some_var
    
if __name__ == '__main__':
    example()
"""
    
    # Initialize the checker
    checker = CodeChecker()
    
    # Demonstrate linting
    print("=== Linting Results ===")
    issues = checker.lint_code(example_code)
    if issues:
        for issue in issues:
            print(issue)
    else:
        print("No issues found!")
    
    # Demonstrate sandboxed execution
    print("\n=== Execution Results ===")
    try:
        stdout, stderr = checker.run_sandboxed(example_code)
        if stdout:
            print("Output:", stdout.strip())
        if stderr:
            print("Errors:", stderr.strip())
    except subprocess.TimeoutExpired:
        print("Error: Code execution timed out")
    except subprocess.CalledProcessError as e:
        print(f"Error: Process returned non-zero exit code {e.returncode}")
        if e.stderr:
            print("Error output:", e.stderr.strip())


if __name__ == '__main__':
    main()
