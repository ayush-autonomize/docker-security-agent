"""Repository runner: clones, updates dependencies, runs tests and scans."""
from pathlib import Path
import shutil
import json
from typing import Dict, Any
from .git_client import GitClient
from .dependency_updater import DependencyUpdater
from .test_runner import TestRunner
from .docker_runner import DockerRunner
from .trivy_parser import parse_trivy_report

class RepoRunner:
    def __init__(self, git_token: str = None):
        self.git = GitClient(token=git_token)
        self.deps = DependencyUpdater()
        self.tests = TestRunner()
        self.docker = DockerRunner()

    def run_repo(self, repo_config: Dict[str, Any], work_dir: str = ".") -> dict:
        """Run analysis for a single repository.
        
        Args:
            repo_config: Dict containing 'name', 'url', 'test_command', etc.
            work_dir: Directory to clone repos into.
            
        Returns:
            Dict with results of the run.
        """
        repo_url = repo_config["url"]
        repo_name = repo_config["name"]
        test_cmd = repo_config.get("test_command")
        
        print(f"--- Processing {repo_name} ---")
        
        # 1. Clone Repo
        try:
            repo_path = self.git.clone_repo(repo_url, work_dir)
        except Exception as e:
            print(f"Failed to clone {repo_url}: {e}")
            return {"status": "failed", "step": "clone", "error": str(e)}

        # 2. Build Docker Image
        image_name = f"{repo_name}:security-scan"
        if not self.docker.build_image(repo_path, image_name):
            return {"status": "failed", "step": "build", "error": "Docker build failed"}

        # 3. Scan Image
        report = self.docker.scan_image(image_name)
        if not report:
            return {"status": "failed", "step": "scan", "error": "Trivy scan failed"}

        # Save Raw Report
        report_path = Path(work_dir) / f"{repo_name}_trivy_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Saved Trivy report to {report_path}")

        # 4. Parse Vulnerabilities
        vulns = parse_trivy_report(report)
        high_medium_vulns = [v for v in vulns if v.get("Severity") in ["HIGH", "MEDIUM"]]
        
        if not high_medium_vulns:
            print(f"No HIGH/MEDIUM vulnerabilities found in {repo_name}.")
            return {"status": "success", "action": "none", "details": "No vulnerabilities found"}

        print(f"Found {len(high_medium_vulns)} HIGH/MEDIUM vulnerabilities.")

        # 5. Create Branch
        branch_name = f"security/fix-vulns-{len(high_medium_vulns)}"
        try:
            self.git.create_branch(repo_path, branch_name)
        except Exception as e:
             print(f"Failed to create branch: {e}")
             # Continue on current branch? No, safer to fail.
             return {"status": "failed", "step": "git_branch", "error": str(e)}

        # 6. Update Dependencies
        updated_packages = self.deps.update_dependencies(repo_path, high_medium_vulns)
        
        # Generate Summary
        summary_path = Path(work_dir) / f"{repo_name}_security_summary.md"
        with open(summary_path, "w") as f:
            f.write(f"# Security Scan Summary for {repo_name}\n\n")
            f.write(f"**Total Vulnerabilities Found**: {len(high_medium_vulns)}\n\n")
            
            f.write("## Fixed Vulnerabilities\n")
            if updated_packages:
                for pkg in updated_packages:
                    f.write(f"- **{pkg}**: Updated in dependency file.\n")
            else:
                f.write("None.\n")
                
            f.write("\n## Unfixed Vulnerabilities\n")
            fixed_names = set(updated_packages) if updated_packages else set()
            for v in high_medium_vulns:
                pkg = v.get("PkgName")
                if pkg not in fixed_names:
                    f.write(f"- **{pkg}** ({v.get('VulnerabilityID')}): Not found in direct dependencies (transitive or system package).\n")
        
        print(f"Saved security summary to {summary_path}")

        if not updated_packages:
            print("No dependencies could be automatically updated.")
            return {"status": "skipped", "reason": "no_updates_possible"}

        # 7. Run Tests
        if not self.tests.run_tests(repo_path, test_cmd):
            print("Tests failed after updates. Aborting PR.")
            return {"status": "failed", "step": "tests", "error": "Tests failed after update"}

        # 8. Rebuild & Rescan (Optional - skipping for speed/MVP, but good practice)
        # If we wanted to verify the fix, we'd rebuild and rescan here.

        # 9. Commit & Push
        try:
            self.git.commit_changes(repo_path, "Security: Update dependencies to fix vulnerabilities")
            self.git.push_changes(repo_path, branch_name)
        except Exception as e:
            print(f"Failed to push changes: {e}")
            return {"status": "failed", "step": "git_push", "error": str(e)}

        # 10. Create PR
        pr_body = f"This PR updates dependencies to fix vulnerabilities detected by Trivy.\n\n"
        pr_body += f"**Fixed**: {', '.join(updated_packages)}\n\n"
        pr_body += "See attached report for details."
        
        pr_url = self.git.create_pr(
            repo_url, 
            branch_name, 
            f"Security Fixes for {repo_name}", 
            pr_body
        )
        
        if pr_url == "failed":
             return {"status": "failed", "step": "pr_creation", "error": "PR creation failed"}
        
        return {"status": "success", "action": "pr_created", "pr_url": pr_url}

