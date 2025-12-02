from fastapi import APIRouter, HTTPException
from agent.config_loader import load_yaml
from .models import RepoInfo
from typing import List
import os

router = APIRouter()

CONFIG_PATH = "configs/repos.yaml"

@router.get("/repos", response_model=List[RepoInfo])
def list_repos():
    if not os.path.exists(CONFIG_PATH):
        raise HTTPException(status_code=500, detail="Repo config not found")
    
    cfg = load_yaml(CONFIG_PATH)
    if not cfg or "repos" not in cfg:
        return []
        
    return [RepoInfo(**r) for r in cfg["repos"]]
