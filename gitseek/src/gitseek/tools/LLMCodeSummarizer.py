from crewai.tools import BaseTool
from typing import Type, Dict, Any, List
from typing import ClassVar, Dict
from pydantic import BaseModel, Field
import os
import re


class CodeAnalysisInput(BaseModel):
    """Input schema for LLMCodeSummarizer."""
    file_path: str = Field(..., description="源代码文件路径")
    analysis_depth: str = Field(
        default="medium",
        description="分析深度: shallow/medium/deep"
    )


class LLMCodeSummarizer(BaseTool):
    name: str = "Code Quality Analyzer"
    description: str = """深度分析源代码文件的质量、设计模式和功能。
    评估代码可读性、注释质量、命名规范、复杂度和可维护性。
    支持多种编程语言包括 Python, JavaScript, Java, Go, Rust 等。"""
    args_schema: Type[BaseModel] = CodeAnalysisInput

    # 支持的语言扩展名映射
    LANGUAGE_EXTENSIONS: ClassVar[Dict[str, str]] = {'.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript', '.jsx': 'React', '.tsx': 'React TypeScript', '.java': 'Java', '.cpp': 'C++', '.c': 'C', '.go': 'Go', '.rs': 'Rust', '.rb': 'Ruby', '.php': 'PHP', '.cs': 'C#', '.swift': 'Swift', '.kt': 'Kotlin'}

    def _run(self, file_path: str, analysis_depth: str = "medium") -> Dict[str, Any]:
        """执行代码分析"""
        try:
            if not os.path.exists(file_path):
                return {"error": f"文件不存在: {file_path}"}

            if not os.path.isfile(file_path):
                return {"error": f"路径不是文件: {file_path}"}

            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size > 5 * 1024 * 1024:  # 5MB限制
                return {"error": f"文件过大 ({file_size} bytes)，建议分析较小的文件"}

            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code_content = f.read()

            # 识别编程语言
            language = self._detect_language(file_path)
            
            # 基础统计
            stats = self._calculate_basic_stats(code_content)
            
            # 代码质量分析
            quality = self._analyze_code_quality(code_content, language)
            
            # 设计模式识别
            patterns = self._identify_patterns(code_content, language)
            
            # 复杂度分析
            complexity = self._analyze_complexity(code_content, language)

            # 功能摘要
            functionality = self._extract_functionality(code_content, language)

            return {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "language": language,
                "file_size_bytes": file_size,
                "statistics": stats,
                "functionality_summary": functionality,
                "quality_assessment": quality,
                "design_patterns": patterns,
                "complexity_metrics": complexity,
                "overall_score": self._calculate_overall_score(quality, complexity),
                "recommendations": self._generate_recommendations(quality, complexity, stats)
            }

        except Exception as e:
            return {"error": f"代码分析失败: {str(e)}"}

    def _detect_language(self, file_path: str) -> str:
        """检测编程语言"""
        ext = os.path.splitext(file_path)[1].lower()
        return self.LANGUAGE_EXTENSIONS.get(ext, "Unknown")

    def _calculate_basic_stats(self, code: str) -> Dict[str, Any]:
        """计算基础统计信息"""
        lines = code.split('\n')
        
        total_lines = len(lines)
        
        # 识别注释行（简化版本，支持 #, //, /* */）
        comment_lines = 0
        in_block_comment = False
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//'):
                comment_lines += 1
            elif '/*' in stripped:
                in_block_comment = True
                comment_lines += 1
            elif '*/' in stripped:
                in_block_comment = False
                comment_lines += 1
            elif in_block_comment:
                comment_lines += 1
        
        code_lines = len([l for l in lines if l.strip() and not self._is_comment_line(l)])
        blank_lines = total_lines - code_lines - comment_lines
        
        return {
            "total_lines": total_lines,
            "code_lines": code_lines,
            "comment_lines": comment_lines,
            "blank_lines": blank_lines,
            "comment_ratio": round(comment_lines / max(code_lines, 1) * 100, 2),
            "avg_line_length": round(sum(len(l) for l in lines) / max(total_lines, 1), 2)
        }

    def _is_comment_line(self, line: str) -> bool:
        """判断是否为注释行"""
        stripped = line.strip()
        return (stripped.startswith('#') or 
                stripped.startswith('//') or 
                stripped.startswith('/*') or 
                stripped.startswith('*'))

    def _analyze_code_quality(self, code: str, language: str) -> Dict[str, Any]:
        """分析代码质量"""
        quality_issues = []
        quality_positives = []
        
        lines = code.split('\n')
        
        # 1. 检查注释质量
        comment_ratio = self._calculate_basic_stats(code)['comment_ratio']
        if comment_ratio < 5:
            quality_issues.append("注释较少（<5%），建议增加代码注释以提高可维护性")
        elif comment_ratio > 15:
            quality_positives.append(f"注释充分（{comment_ratio}%），有助于代码理解")
        
        # 2. 检查行长度
        long_lines = [(i, len(line)) for i, line in enumerate(lines, 1) if len(line) > 120]
        if long_lines:
            quality_issues.append(f"发现 {len(long_lines)} 行超过120字符，建议缩短以提高可读性")
        
        # 3. 检查函数/方法长度
        if language == "Python":
            functions = re.findall(r'def\s+\w+.*?(?=\ndef\s|\nclass\s|$)', code, re.DOTALL)
            long_functions = [f for f in functions if len(f.split('\n')) > 50]
            if long_functions:
                quality_issues.append(f"发现 {len(long_functions)} 个超过50行的函数，建议拆分")
        
        # 4. 检查命名规范 (以 Python 为例)
        if language == "Python":
            # 检查类名应该是 CamelCase
            class_pattern = r'class\s+([a-z][a-zA-Z0-9]*)'
            bad_classes = re.findall(class_pattern, code)
            if bad_classes:
                quality_issues.append(f"类名应使用 PascalCase: {', '.join(bad_classes[:3])}")
            
            # 检查常量应该是 UPPER_CASE
            if re.search(r'[a-z_]+\s*=\s*["\']', code):
                potential_constants = re.findall(r'([a-z_]+)\s*=\s*["\'][^"\']+["\']', code)
                if potential_constants:
                    quality_positives.append("发现模块级变量，检查是否应使用 UPPER_CASE 命名")
        
        # 5. 检查代码复用性
        duplicate_patterns = self._find_duplicate_code(code)
        if duplicate_patterns > 3:
            quality_issues.append(f"发现 {duplicate_patterns} 处可能的重复代码，建议重构")
        
        return {
            "issues": quality_issues,
            "positives": quality_positives,
            "issue_count": len(quality_issues),
            "quality_level": self._determine_quality_level(len(quality_issues)),
            "readability_score": self._calculate_readability_score(code, lines)
        }

    def _find_duplicate_code(self, code: str) -> int:
        """简单检测重复代码（3行以上相同）"""
        lines = [l.strip() for l in code.split('\n') if l.strip()]
        duplicates = 0
        
        for i in range(len(lines) - 3):
            pattern = '\n'.join(lines[i:i+3])
            if code.count(pattern) > 1:
                duplicates += 1
        
        return duplicates

    def _calculate_readability_score(self, code: str, lines: List[str]) -> int:
        """计算可读性分数 (0-100)"""
        score = 100
        
        # 行长度扣分
        long_lines = len([l for l in lines if len(l) > 120])
        score -= min(20, long_lines * 2)
        
        # 注释比例加分
        comment_ratio = self._calculate_basic_stats(code)['comment_ratio']
        if comment_ratio > 10:
            score += 10
        elif comment_ratio < 5:
            score -= 10
        
        # 空行使用（适当的空行提高可读性）
        blank_ratio = len([l for l in lines if not l.strip()]) / max(len(lines), 1)
        if 0.1 < blank_ratio < 0.3:
            score += 5
        
        return max(0, min(100, score))

    def _determine_quality_level(self, issue_count: int) -> str:
        """根据问题数量确定质量等级"""
        if issue_count == 0:
            return "Excellent (优秀)"
        elif issue_count <= 2:
            return "Good (良好)"
        elif issue_count <= 5:
            return "Fair (一般)"
        else:
            return "Needs Improvement (需改进)"

    def _identify_patterns(self, code: str, language: str) -> List[str]:
        """识别设计模式"""
        patterns = []
        
        # 1. 单例模式检测
        if re.search(r'(_instance\s*=\s*None|private\s+static.*instance)', code, re.IGNORECASE):
            patterns.append("Singleton Pattern (单例模式)")
        
        # 2. 工厂模式检测
        if re.search(r'(def\s+create_|function\s+create|factory)', code, re.IGNORECASE):
            patterns.append("Factory Pattern (工厂模式)")
        
        # 3. 装饰器模式检测
        if language == "Python" and re.search(r'@\w+', code):
            patterns.append("Decorator Pattern (装饰器模式)")
        
        # 4. 观察者模式检测
        if re.search(r'(subscribe|notify|observer|addEventListener)', code, re.IGNORECASE):
            patterns.append("Observer Pattern (观察者模式)")
        
        # 5. 策略模式检测
        if re.search(r'(strategy|algorithm.*interface)', code, re.IGNORECASE):
            patterns.append("Strategy Pattern (策略模式)")
        
        # 6. 依赖注入检测
        if re.search(r'(inject|dependency.*injection|__init__.*:.*\w+)', code, re.IGNORECASE):
            patterns.append("Dependency Injection (依赖注入)")
        
        # 7. MVC/MVP 模式检测
        if re.search(r'(model|view|controller|presenter)', code, re.IGNORECASE):
            patterns.append("MVC/MVP Pattern (MVC/MVP 模式)")
        
        return patterns if patterns else ["No clear design patterns detected (未检测到明显的设计模式)"]

    def _analyze_complexity(self, code: str, language: str) -> Dict[str, Any]:
        """分析代码复杂度"""
        # 1. 圈复杂度 (Cyclomatic Complexity)
        decision_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 
                            'catch', 'switch', 'case', '&&', '||', '?']
        complexity_score = sum(code.lower().count(keyword) for keyword in decision_keywords)
        
        # 2. 函数/方法分析
        if language == "Python":
            functions = re.findall(r'def\s+(\w+)', code)
            classes = re.findall(r'class\s+(\w+)', code)
        elif language in ["JavaScript", "TypeScript"]:
            functions = re.findall(r'function\s+(\w+)|const\s+(\w+)\s*=.*=>', code)
            classes = re.findall(r'class\s+(\w+)', code)
        else:
            functions = []
            classes = []
        
        function_count = len(functions)
        class_count = len(classes)
        
        # 3. 嵌套深度估算
        max_nesting = self._estimate_nesting_depth(code)
        
        return {
            "cyclomatic_complexity": complexity_score,
            "complexity_level": self._get_complexity_level(complexity_score),
            "function_count": function_count,
            "class_count": class_count,
            "max_nesting_depth": max_nesting,
            "maintainability_index": self._calculate_maintainability_index(
                complexity_score, len(code.split('\n')), function_count
            )
        }

    def _estimate_nesting_depth(self, code: str) -> int:
        """估算最大嵌套深度"""
        max_depth = 0
        current_depth = 0
        
        for line in code.split('\n'):
            stripped = line.strip()
            # 简单的缩进级别计算
            if stripped:
                indent = len(line) - len(line.lstrip())
                depth = indent // 4  # 假设4空格缩进
                max_depth = max(max_depth, depth)
        
        return max_depth

    def _calculate_maintainability_index(self, complexity: int, lines: int, functions: int) -> int:
        """计算可维护性指数 (0-100)"""
        # 简化的 MI 计算
        base_score = 100
        
        # 复杂度影响
        base_score -= min(30, complexity)
        
        # 代码行数影响
        if lines > 500:
            base_score -= 10
        if lines > 1000:
            base_score -= 10
        
        # 函数数量影响（太少或太多都不好）
        if functions < 3:
            base_score -= 5
        elif functions > 50:
            base_score -= 10
        
        return max(0, min(100, base_score))

    def _get_complexity_level(self, score: int) -> str:
        """根据复杂度分数返回等级"""
        if score < 10:
            return "Low (Simple) - 低复杂度"
        elif score < 20:
            return "Medium (Moderate) - 中等复杂度"
        elif score < 30:
            return "High (Complex) - 高复杂度"
        else:
            return "Very High (Highly Complex) - 极高复杂度"

    def _extract_functionality(self, code: str, language: str) -> str:
        """提取代码功能摘要"""
        functionalities = []
        
        # 1. 提取类和函数名
        if language == "Python":
            classes = re.findall(r'class\s+(\w+)', code)
            functions = re.findall(r'def\s+(\w+)', code)
            
            if classes:
                functionalities.append(f"定义了 {len(classes)} 个类: {', '.join(classes[:5])}")
            if functions:
                functionalities.append(f"包含 {len(functions)} 个函数/方法")
        
        # 2. 识别主要功能
        if re.search(r'(database|db|sql|query)', code, re.IGNORECASE):
            functionalities.append("包含数据库操作功能")
        
        if re.search(r'(api|request|response|endpoint)', code, re.IGNORECASE):
            functionalities.append("包含 API/网络请求功能")
        
        if re.search(r'(test|assert|unittest)', code, re.IGNORECASE):
            functionalities.append("包含测试代码")
        
        if re.search(r'(config|settings|environment)', code, re.IGNORECASE):
            functionalities.append("包含配置管理功能")
        
        return "; ".join(functionalities) if functionalities else "功能识别中..."

    def _calculate_overall_score(self, quality: Dict, complexity: Dict) -> int:
        """计算总体质量分数 (0-100)"""
        base_score = 100
        
        # 质量问题扣分
        base_score -= quality["issue_count"] * 8
        
        # 复杂度扣分
        complexity_score = complexity["cyclomatic_complexity"]
        base_score -= min(25, max(0, complexity_score - 10) * 2)
        
        # 可维护性加成
        base_score = (base_score + complexity.get("maintainability_index", 70)) // 2
        
        return max(0, min(100, base_score))

    def _generate_recommendations(self, quality: Dict, complexity: Dict, stats: Dict) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于质量问题
        if quality["issue_count"] > 3:
            recommendations.append("建议重点关注代码质量问题，逐项修复")
        
        # 基于注释
        if stats["comment_ratio"] < 5:
            recommendations.append("增加代码注释，尤其是复杂逻辑和公共 API")
        
        # 基于复杂度
        if complexity["cyclomatic_complexity"] > 20:
            recommendations.append("建议重构高复杂度代码，拆分大函数")
        
        # 基于可维护性
        if complexity.get("maintainability_index", 100) < 50:
            recommendations.append("可维护性较低，建议进行代码重构和模块化")
        
        if not recommendations:
            recommendations.append("代码质量良好，保持当前编码规范")
        
        return recommendations

    def select_key_files(self, directory: str, core_directories: List[str] = None, max_files: int = 5) -> List[str]:
        """从目录中智能选择关键文件进行分析"""
        key_files = []
        
        # 优先级1: 主入口文件
        entry_points = [
            'main.py', '__main__.py', 'app.py', 'server.py', 'index.py',
            'index.js', 'app.js', 'server.js', 'main.js',
            'Main.java', 'Application.java', 'App.java',
            'main.go', 'main.rs', 'main.cpp'
        ]
        
        for entry in entry_points:
            path = os.path.join(directory, entry)
            if os.path.exists(path):
                key_files.append(path)
                if len(key_files) >= max_files:
                    return key_files
        
        # 优先级2: 从核心目录中选择
        if core_directories:
            for core_dir in core_directories:
                core_path = os.path.join(directory, core_dir)
                if os.path.exists(core_path) and os.path.isdir(core_path):
                    for file in os.listdir(core_path):
                        if file.endswith(tuple(self.LANGUAGE_EXTENSIONS.keys())):
                            key_files.append(os.path.join(core_path, file))
                            if len(key_files) >= max_files:
                                return key_files
        
        # 优先级3: 选择最大的源文件
        if len(key_files) < max_files:
            all_files = []
            for root, dirs, files in os.walk(directory):
                # 跳过常见的非核心目录
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'venv', '.venv']]
                
                for file in files:
                    if file.endswith(tuple(self.LANGUAGE_EXTENSIONS.keys())):
                        file_path = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(file_path)
                            all_files.append((file_path, file_size))
                        except:
                            continue
            
            # 按大小排序，选择最大的文件
            all_files.sort(key=lambda x: x[1], reverse=True)
            key_files.extend([f[0] for f in all_files[:max_files - len(key_files)]])
        
        return key_files[:max_files]
