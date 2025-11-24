"""Docker-related helpers: build/scan images."""
import docker
import subprocess
import json
from typing import Dict, Any, Optional
from pathlib import Path

class DockerRunner:
    def __init__(self):
        self.client = docker.from_env()

    def build_image(self, repo_path: Path, image_name: str) -> bool:
        """Build a Docker image from the repository."""
        try:
            # Ensure repo_path is absolute string
            path_str = str(repo_path.resolve())
            print(f"Building image {image_name} from {path_str}...")
            
            # Use low-level API or just subprocess to get better logs if needed
            # But docker-py's build returns a generator of logs
            # Let's try to capture output
            
            # We can use subprocess for better visibility into the build process
            # docker build -t image_name .
            cmd = ["docker", "build", "-t", image_name, "."]
            result = subprocess.run(
                cmd, 
                cwd=path_str, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode != 0:
                print(f"Docker build failed with code {result.returncode}")
                print("--- Build Output ---")
                print(result.stdout)
                print("--- Build Error ---")
                print(result.stderr)
                return False
                
            print(f"Successfully built {image_name}")
            return True
            
        except Exception as e:
            print(f"Error building image: {e}")
            return False

    def scan_image(self, image_name: str) -> Optional[Dict[str, Any]]:
        """Scan the image using Trivy and return the JSON report."""
        print(f"Scanning image {image_name} with Trivy...")
        try:
            # trivy image --format json --quiet image_name
            cmd = [
                "trivy", "image",
                "--format", "json",
                "--quiet",
                image_name
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            report = json.loads(result.stdout)
            return report
        except subprocess.CalledProcessError as e:
            print(f"Trivy scan failed: {e.stderr}")
            return None
        except json.JSONDecodeError:
            print("Failed to parse Trivy output")
            return None
        except FileNotFoundError:
            print("Trivy not found. Please install trivy.")
            return None
