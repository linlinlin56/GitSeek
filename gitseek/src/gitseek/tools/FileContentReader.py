#FileContentReader.py
from crewai.tools import BaseTool
from typing import Type, Dict, Any
from pydantic import BaseModel, Field
import os
import json
import tomllib

class FileContentReadInput(BaseModel):
    """Input schema for FileContentReader."""
    file_path: str = Field(..., description="要读取的文件路径")
    max_lines: int = Field(default=100, description="最大读取行数（防止大文件）")
    parse_content: bool = Field(default=True, description="是否尝试解析结构化内容")

class FileContentReader(BaseTool):
    name: str = "File Content Reader"
    description: str = "读取和解析文件内容，特别支持配置文件和依赖解析"
    args_schema: Type[BaseModel] = FileContentReadInput

    def _run(self, file_path: str, max_lines: int = 100, parse_content: bool = True) -> Dict[str, Any]:
        try:
            if not os.path.exists(file_path):
                return {"error": f"文件不存在: {file_path}"}
            
            if not os.path.isfile(file_path):
                return {"error": f"路径不是文件: {file_path}"}

            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB限制
                return {"error": f"文件过大 ({file_size} bytes)，跳过读取"}

            result = {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size": file_size,
                "content": self._read_file_content(file_path, max_lines)
            }
            
            if parse_content:
                parsed_data = self._parse_file_content(file_path, result["content"])
                if parsed_data:
                    result["parsed"] = parsed_data
            
            return result
            
        except Exception as e:
            return {"error": f"文件读取失败: {str(e)}"}

    def _read_file_content(self, file_path: str, max_lines: int) -> str:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        lines.append(f"... (文件超过{max_lines}行，已截断)")
                        break
                    lines.append(line.rstrip())
                return "\n".join(lines)
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            lines.append(f"... (文件超过{max_lines}行，已截断)")
                            break
                        lines.append(line.rstrip())
                    return "\n".join(lines)
            except Exception:
                return "无法读取文件内容（编码问题）"

    def _parse_file_content(self, file_path: str, content: str) -> Dict[str, Any]:
        """解析文件内容，特别处理配置文件"""
        filename = os.path.basename(file_path).lower()
        
        try:
            if filename == 'package.json':
                return self._parse_package_json(content)
            elif filename == 'requirements.txt':
                return self._parse_requirements_txt(content)
            elif filename == 'pyproject.toml':
                return self._parse_pyproject_toml(content)
            elif filename == 'pom.xml':
                return self._parse_pom_xml(content)
            elif filename in ['dockerfile', 'docker-compose.yml']:
                return self._parse_docker_file(content, filename)
            elif filename == 'go.mod':
                return self._parse_go_mod(content)
            elif filename == 'cargo.toml':
                return self._parse_cargo_toml(content)
                
        except Exception as e:
            return {"parse_error": str(e)}
        
        return None

    def _parse_package_json(self, content: str) -> Dict[str, Any]:
        """解析 package.json"""
        data = json.loads(content)
        return {
            "type": "nodejs_package",
            "name": data.get("name"),
            "version": data.get("version"),
            "description": data.get("description"),
            "dependencies": data.get("dependencies", {}),
            "devDependencies": data.get("devDependencies", {}),
            "scripts": data.get("scripts", {})
        }

    def _parse_requirements_txt(self, content: str) -> Dict[str, Any]:
        """解析 requirements.txt"""
        dependencies = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # 简单的依赖解析
                dep = line.split('==')[0].split('>=')[0].split('<=')[0].strip()
                if dep:
                    dependencies.append(dep)
        
        return {
            "type": "python_requirements",
            "dependencies": dependencies,
            "total_dependencies": len(dependencies)
        }

    def _parse_pyproject_toml(self, content: str) -> Dict[str, Any]:
        """解析 pyproject.toml"""
        try:
            data = tomllib.loads(content)
            result = {"type": "python_pyproject"}
            
            if 'project' in data:
                result.update({
                    "name": data['project'].get('name'),
                    "version": data['project'].get('version'),
                    "dependencies": data['project'].get('dependencies', [])
                })
            
            if 'tool' in data and 'poetry' in data['tool']:
                poetry = data['tool']['poetry']
                result.update({
                    "name": poetry.get('name'),
                    "version": poetry.get('version'),
                    "dependencies": poetry.get('dependencies', {})
                })
                
            return result
        except Exception:
            return {"type": "python_pyproject", "parse_error": "解析失败"}

    def _parse_pom_xml(self, content: str) -> Dict[str, Any]:
        """解析 pom.xml (简化版本)"""
        # 简单的XML解析，实际项目中可能需要更复杂的解析
        import re
        group_id = re.search(r'<groupId>(.*?)</groupId>', content)
        artifact_id = re.search(r'<artifactId>(.*?)</artifactId>', content)
        version = re.search(r'<version>(.*?)</version>', content)
        
        return {
            "type": "java_maven",
            "group_id": group_id.group(1) if group_id else None,
            "artifact_id": artifact_id.group(1) if artifact_id else None,
            "version": version.group(1) if version else None
        }

    def _parse_docker_file(self, content: str, filename: str) -> Dict[str, Any]:
        """解析 Dockerfile"""
        base_images = []
        for line in content.split('\n'):
            if line.strip().upper().startswith('FROM'):
                image = line.strip()[4:].strip().split(' ')[0]
                if image and image != 'scratch':
                    base_images.append(image)
        
        return {
            "type": "docker",
            "file_type": filename,
            "base_images": base_images
        }

    def _parse_go_mod(self, content: str) -> Dict[str, Any]:
        """解析 go.mod"""
        import re
        module_name = re.search(r'module\s+(\S+)', content)
        go_version = re.search(r'go\s+(\S+)', content)
        requires = re.findall(r'require\s+(\S+)\s+(\S+)', content)
        
        return {
            "type": "go_module",
            "module_name": module_name.group(1) if module_name else None,
            "go_version": go_version.group(1) if go_version else None,
            "dependencies": [{"module": req[0], "version": req[1]} for req in requires]
        }

    def _parse_cargo_toml(self, content: str) -> Dict[str, Any]:
        """解析 Cargo.toml"""
        try:
            data = tomllib.loads(content)
            return {
                "type": "rust_cargo",
                "package": data.get('package', {}),
                "dependencies": data.get('dependencies', {})
            }
        except Exception:
            return {"type": "rust_cargo", "parse_error": "解析失败"}