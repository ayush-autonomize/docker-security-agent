"""Entry point for the docker-security-agent."""
import argparse
import os
from agent.config_loader import load_yaml
from agent.repo_runner import RepoRunner
from dotenv import load_dotenv

def main():
    load_dotenv() # Load .env if present
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--repos", default="configs/repos.yaml", help="Path to repos config")
    args = parser.parse_args()
    
    repos_cfg = load_yaml(args.repos)
    if not repos_cfg or "repos" not in repos_cfg:
        print("No repositories configured.")
        return

    # Get GitHub Token from env
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("WARNING: GITHUB_TOKEN not set. PR creation will be skipped.")

    runner = RepoRunner(git_token=github_token)
    
    print(f"Starting security scan for {len(repos_cfg['repos'])} repositories...")
    
    results = []
    for repo in repos_cfg["repos"]:
        res = runner.run_repo(repo, work_dir="temp_repos")
        results.append(res)
        print(f"Result for {repo['name']}: {res['status']}")

    print("\n--- Summary ---")
    for res in results:
        print(res)

if __name__ == "__main__":
    main()
