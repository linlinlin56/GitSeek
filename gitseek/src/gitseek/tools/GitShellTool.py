# GitShellTool.py
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import subprocess
import os


class GitCloneInput(BaseModel):
    """Input schema for GitShellTool."""
    repo_url: str = Field(..., description="GitHub repository URL to clone")
    target_dir: str = Field(..., description="Local base directory path to clone into (e.g., './cloned_repos')")


class GitShellTool(BaseTool):
    name: str = "Git Repository Cloner"
    description: str = "Clones GitHub repositories to local directory for analysis"
    args_schema: Type[BaseModel] = GitCloneInput

    def _run(self, repo_url: str, target_dir: str) -> str:
        try:
            # 1. 计算最终克隆路径，以匹配后续分析工具的期望：[target_dir]/[repo_name]
            # 示例：https://github.com/moonlight142790/Smart_Health.git -> Smart_Health
            repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
            final_path = os.path.join(target_dir, repo_name)

            # 2. 检查目标子目录是否已存在且非空
            if os.path.isdir(final_path) and os.listdir(final_path):
                return f"⚠️ Repository already cloned: {repo_url} already exists in {final_path}. Skipping clone."

            # 3. 确保目标基目录存在
            os.makedirs(target_dir, exist_ok=True)

            # 4. 执行 git clone 命令
            result = subprocess.run(
                ['git', 'clone', repo_url, final_path],  # 克隆到正确的目标子目录
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            if result.returncode == 0:
                return f"✅ Successfully cloned {repo_url} to {final_path}"
            else:
                # 克隆失败时，返回完整的错误信息
                return f"❌ Git clone failed: {result.stderr}"

        except subprocess.TimeoutExpired:
            return "❌ Git clone timed out after 5 minutes"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"