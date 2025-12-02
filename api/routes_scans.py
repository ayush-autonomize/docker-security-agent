from fastapi import APIRouter, BackgroundTasks, HTTPException
from agent.repo_runner import RepoRunner
from agent.config_loader import load_yaml
from .models import ScanStartResponse, ScanStatusResponse
import os
from typing import Dict

router = APIRouter()

# In-memory status store
SCAN_STATUS: Dict[str, Dict] = {}

CONFIG_PATH = "configs/repos.yaml"

def run_repo_scan(repo_name: str):
    """Background task to run the full agent scan logic."""
    try:
        SCAN_STATUS[repo_name] = {"status": "running", "message": "Initializing scan..."}
        
        # Load config to find the specific repo
        cfg = load_yaml(CONFIG_PATH)
        repo_config = next((r for r in cfg.get("repos", []) if r["name"] == repo_name), None)
        
        if not repo_config:
            SCAN_STATUS[repo_name] = {"status": "failed", "message": "Repo config not found during execution"}
            return

        # Initialize Runner (ensure env vars like GITHUB_TOKEN are set)
        github_token = os.getenv("GITHUB_TOKEN")
        runner = RepoRunner(git_token=github_token)
        
        SCAN_STATUS[repo_name]["message"] = "Running scan logic..."
        
        # Run the scan
        result = runner.run_repo(repo_config, work_dir="temp_repos")
        
        # Update status based on result
        if result["status"] == "success":
             SCAN_STATUS[repo_name] = {
                 "status": "success", 
                 "message": "Scan completed successfully",
                 "pr_url": result.get("pr_url")
             }
        elif result["status"] == "skipped":
             SCAN_STATUS[repo_name] = {
                 "status": "success", 
                 "message": f"Scan skipped: {result.get('reason')}"
             }
        else:
             SCAN_STATUS[repo_name] = {
                 "status": "failed", 
                 "message": f"Scan failed at step {result.get('step')}: {result.get('error')}"
             }
             
    except Exception as e:
        SCAN_STATUS[repo_name] = {"status": "failed", "message": f"Unexpected error: {str(e)}"}


@router.post("/scan/{repo_name}", response_model=ScanStartResponse)
def trigger_scan(repo_name: str, background_tasks: BackgroundTasks):
    # Verify repo exists
    if not os.path.exists(CONFIG_PATH):
         raise HTTPException(status_code=500, detail="Config file missing")
         
    cfg = load_yaml(CONFIG_PATH)
    repo_exists = any(r["name"] == repo_name for r in cfg.get("repos", []))
    
    if not repo_exists:
        raise HTTPException(status_code=404, detail=f"Repository '{repo_name}' not found in config")

    # Add to background tasks
    background_tasks.add_task(run_repo_scan, repo_name)
    
    # Set initial status
    SCAN_STATUS[repo_name] = {"status": "queued", "message": "Scan queued"}
    
    return ScanStartResponse(status="started", repo=repo_name)

@router.get("/scan-status/{repo_name}", response_model=ScanStatusResponse)
def get_scan_status(repo_name: str):
    status = SCAN_STATUS.get(repo_name)
    if not status:
        return ScanStatusResponse(status="idle", message="No scan history found")
    
    return ScanStatusResponse(**status)
