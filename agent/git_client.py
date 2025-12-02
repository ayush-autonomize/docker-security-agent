"""Git client wrapper using GitPython."""
from pathlib import Path
import git
from typing import Union, Optional
import os

class GitClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token

    def clone_repo(self, repo_url: str, dest: Union[str, Path] = ".") -> Path:
        """Clone a repository to the destination directory and return the path."""
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        dest_path = Path(dest) / repo_name
        
        if dest_path.exists():
            # If it exists, we might want to pull, but for now let's just use it
            # or maybe clean it up. For safety in this agent, let's assume we want fresh.
            # But to be safe against deleting user data, let's just return if it exists
            # and assume it's correct, or maybe pull.
            # Let's try to get the repo object.
            try:
                repo = git.Repo(dest_path)
                try:
                    # Fetch latest changes
                    repo.remotes.origin.fetch()
                    # Reset to main (or detect default branch if needed, assuming main for now)
                    # We force checkout main and reset to origin/main to discard any local drift/feature branches
                    repo.git.checkout('main')
                    repo.git.reset('--hard', 'origin/main')
                    # Pull is technically redundant after reset --hard to origin/main, but ensures we are up to date
                    repo.remotes.origin.pull()
                except git.exc.GitCommandError as e:
                    print(f"Warning: Failed to update {repo_url}: {e}. Using existing version.")
                return dest_path
            except git.exc.InvalidGitRepositoryError:
                # Directory exists but not a git repo? 
                pass
        
        # Insert token into URL if provided
        if self.token and "https://" in repo_url:
            auth_url = repo_url.replace("https://", f"https://{self.token}@")
        else:
            auth_url = repo_url

        git.Repo.clone_from(auth_url, dest_path)
        return dest_path

    def create_branch(self, repo_path: Path, branch_name: str):
        """Create and checkout a new branch."""
        repo = git.Repo(repo_path)
        current = repo.active_branch
        new_branch = repo.create_head(branch_name, force=True)
        new_branch.checkout()
        return new_branch

    def commit_changes(self, repo_path: Path, message: str, files: list[str] = None):
        """Commit changes to the repository."""
        repo = git.Repo(repo_path)
        if files:
            repo.index.add(files)
        else:
            repo.index.add("*") # Add all changes
        repo.index.commit(message)

    def push_changes(self, repo_path: Path, branch_name: str):
        """Push changes to the remote repository."""
        repo = git.Repo(repo_path)
        origin = repo.remotes.origin
        origin.push(branch_name, set_upstream=True)

    def create_pr(self, repo_url: str, branch_name: str, title: str, body: str) -> str:
        """Create a Pull Request on GitHub."""
        if not self.token:
            print("No GitHub token provided. Skipping PR creation.")
            return "skipped"

        import requests
        
        # Convert https://github.com/owner/repo.git to api url
        # API: https://api.github.com/repos/owner/repo/pulls
        
        parts = repo_url.replace(".git", "").split("/")
        owner = parts[-2]
        repo_name = parts[-1]
        
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls"
        
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "title": title,
            "body": body,
            "head": branch_name,
            "base": "main" # Assuming main is the default branch
        }
        
        response = requests.post(api_url, headers=headers, json=data)
        
        if response.status_code == 201:
            print(f"PR created successfully: {response.json().get('html_url')}")
            return response.json().get("html_url")
        elif response.status_code == 422 and "A pull request already exists" in response.text:
            print("PR already exists. Fetching URL...")
            # Try to find the existing PR
            # GET /repos/:owner/:repo/pulls?head=:owner/:branch
            query_url = f"{api_url}?head={owner}:{branch_name}"
            try:
                get_resp = requests.get(query_url, headers=headers)
                if get_resp.status_code == 200 and get_resp.json():
                    pr_url = get_resp.json()[0].get("html_url")
                    print(f"Existing PR found: {pr_url}")
                    return pr_url
            except Exception as e:
                print(f"Failed to fetch existing PR: {e}")
            
            return "exists"
        else:
            print(f"Failed to create PR: {response.status_code} - {response.text}")
            return "failed"
