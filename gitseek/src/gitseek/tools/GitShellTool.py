#GitShellTool.py
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import subprocess
import os

class GitCloneInput(BaseModel):
    """Input schema for GitShellTool."""
    repo_url: str = Field(..., description="GitHub repository URL to clone")
    target_dir: str = Field(..., description="Local directory path to clone into")

class GitShellTool(BaseTool):
    name: str = "Git Repository Cloner"
    description: str = "Clones GitHub repositories to local directory for analysis"
    args_schema: Type[BaseModel] = GitCloneInput

    def _run(self, repo_url: str, target_dir: str) -> str:
        try:
            # 确保目标目录存在
            os.makedirs(target_dir, exist_ok=True)
            
            # 执行 git clone 命令
            result = subprocess.run(
                ['git', 'clone', repo_url, target_dir],
                capture_output=True, 
                text=True, 
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                return f"✅ Successfully cloned {repo_url} to {target_dir}"
            else:
                return f"❌ Git clone failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "❌ Git clone timed out after 5 minutes"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"