from pydantic import BaseModel
from typing import Optional, List

class RepoInfo(BaseModel):
    name: str
    url: str
    test_command: Optional[str] = None

class ScanStartResponse(BaseModel):
    status: str
    repo: str

class ScanStatusResponse(BaseModel):
    status: str
    message: Optional[str] = None
    pr_url: Optional[str] = None
