"""Run repository tests."""
from pathlib import Path
from typing import Union, Optional
import subprocess
import shlex

class TestRunner:
    def run_tests(self, repo_path: Union[str, Path], test_command: Optional[str] = None) -> bool:
        """Run tests in the repository.
        
        Args:
            repo_path: Path to the repository.
            test_command: Optional custom test command. Defaults to "pytest".
            
        Returns:
            True if tests pass, False otherwise.
        """
        repo_path = Path(repo_path)
        
        if not test_command:
            # Default to pytest if no command provided
            test_command = "pytest"
            
        print(f"Running tests in {repo_path} with command: {test_command}")
        
        try:
            # Run tests using shell=True to support && and other operators
            print(f"Executing: {test_command}")
            result = subprocess.run(
                test_command,
                cwd=repo_path,
                capture_output=True,
                text=True,
                shell=True
            )
            
            if result.returncode == 0:
                print("Tests passed!")
                return True
            else:
                print("Tests failed!")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except FileNotFoundError:
            print(f"Test command not found: {test_command}")
            return False
        except Exception as e:
            print(f"Error running tests: {e}")
            return False
