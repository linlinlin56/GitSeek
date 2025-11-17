#FileSystemBrowser.py
from crewai.tools import BaseTool
from typing import Type, List, Dict, Any
from pydantic import BaseModel, Field
import os
import glob

class FileSystemBrowseInput(BaseModel):
    """Input schema for FileSystemBrowser."""
    directory_path: str = Field(..., description="要浏览的目录路径")
    max_depth: int = Field(default=3, description="最大递归深度")
    file_patterns: List[str] = Field(default=[], description="要匹配的文件模式，如 ['*.py', '*.json']")

class FileSystemBrowser(BaseTool):
    name: str = "File System Browser"
    description: str = "浏览和分析文件系统目录结构，识别核心目录和文件"
    args_schema: Type[BaseModel] = FileSystemBrowseInput

    def _run(self, directory_path: str, max_depth: int = 3, file_patterns: List[str] = None) -> Dict[str, Any]:
        try:
            if not os.path.exists(directory_path):
                return {"error": f"目录不存在: {directory_path}"}
            
            if not os.path.isdir(directory_path):
                return {"error": f"路径不是目录: {directory_path}"}

            result = {
                "directory": directory_path,
                "structure": self._scan_directory(directory_path, max_depth, file_patterns or []),
                "core_directories": self._identify_core_directories(directory_path),
                "config_files": self._find_config_files(directory_path)
            }
            
            return result
            
        except Exception as e:
            return {"error": f"文件系统浏览失败: {str(e)}"}

    def _scan_directory(self, path: str, max_depth: int, file_patterns: List[str], current_depth: int = 0) -> Dict[str, Any]:
        """递归扫描目录结构"""
        if current_depth > max_depth:
            return {"name": os.path.basename(path), "type": "directory", "truncated": True}
        
        structure = {
            "name": os.path.basename(path),
            "type": "directory",
            "path": path,
            "items": []
        }
        
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                
                if os.path.isdir(item_path):
                    # 递归扫描子目录
                    sub_structure = self._scan_directory(item_path, max_depth, file_patterns, current_depth + 1)
                    structure["items"].append(sub_structure)
                else:
                    # 检查文件是否匹配模式
                    if self._matches_patterns(item, file_patterns):
                        structure["items"].append({
                            "name": item,
                            "type": "file",
                            "path": item_path,
                            "size": os.path.getsize(item_path) if os.path.exists(item_path) else 0
                        })
                        
        except PermissionError:
            structure["items"].append({"name": "权限不足", "type": "error"})
        except Exception as e:
            structure["items"].append({"name": f"扫描错误: {str(e)}", "type": "error"})
            
        return structure

    def _matches_patterns(self, filename: str, patterns: List[str]) -> bool:
        """检查文件名是否匹配模式"""
        if not patterns:
            return True
            
        for pattern in patterns:
            if glob.fnmatch.fnmatch(filename, pattern):
                return True
        return False

    def _identify_core_directories(self, base_path: str) -> List[str]:
        """识别核心目录"""
        core_patterns = ['src', 'lib', 'app', 'components', 'core', 'main', 'bin', 'scripts']
        core_directories = []
        
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                if any(pattern in item.lower() for pattern in core_patterns):
                    core_directories.append(item)
                    
        return core_directories

    def _find_config_files(self, base_path: str) -> List[str]:
        """查找配置文件"""
        config_patterns = [
            'package.json', 'requirements.txt', 'pyproject.toml', 'setup.py',
            'pom.xml', 'build.gradle', 'CMakeLists.txt', 'Dockerfile',
            'docker-compose.yml', '.env', 'config.json', 'settings.py',
            'webpack.config.js', 'tsconfig.json', 'go.mod', 'Cargo.toml',
            'composer.json', 'Gemfile', 'Makefile'
        ]
        
        found_configs = []
        
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file in config_patterns:
                    found_configs.append(os.path.join(root, file))
                    
        return found_configs