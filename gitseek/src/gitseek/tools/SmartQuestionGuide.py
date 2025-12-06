from crewai.tools import BaseTool
from typing import Type, List, Dict, Any, ClassVar
from pydantic import BaseModel, Field
import json
import os

class QuestionGuideInput(BaseModel):
    """Input schema for SmartQuestionGuide."""
    repo_data: Dict = Field(..., description="仓库分析数据")
    user_context: str = Field(default="general", description="用户上下文: general/beginner/developer/researcher")

class SmartQuestionGuide(BaseTool):
    name: str = "Smart Question Guide"
    description: str = "基于GitHub仓库分析结果，智能推荐高频问题和追问方向"
    args_schema: Type[BaseModel] = QuestionGuideInput

    # 问题模板库
    QUESTION_TEMPLATES: ClassVar[Dict[str, List[str]]] = {
        "general": [
            "该项目的核心模块是什么？",
            "项目的主要技术栈有哪些？",
            "社区活跃度如何？",
            "代码质量怎么样？",
            "适合初学者参与贡献吗？"
        ],
        "beginner": [
            "这个项目对新手友好吗？",
            "从哪里开始阅读代码比较好？",
            "项目有哪些入门级的issue？",
            "需要哪些前置知识？",
            "如何搭建开发环境？"
        ],
        "developer": [
            "项目的架构设计有什么特点？",
            "使用了哪些设计模式？",
            "依赖管理是怎样的？",
            "测试覆盖率如何？",
            "代码规范遵循什么标准？"
        ],
        "researcher": [
            "项目的创新点在哪里？",
            "技术选型的理由是什么？",
            "性能表现如何？",
            "与其他类似项目相比有什么优势？",
            "未来的发展方向是什么？"
        ],
        "quality": [
            "代码复杂度高吗？",
            "注释和文档是否完善？",
            "有哪些可以改进的代码质量问题？",
            "测试覆盖情况如何？",
            "代码可维护性怎么样？"
        ],
        "community": [
            "近期有哪些重要的更新？",
            "主要贡献者是谁？",
            "issue处理效率如何？",
            "社区讨论的热点问题是什么？",
            "项目的发布频率是怎样的？"
        ]
    }

    def _run(self, repo_data: Dict, user_context: str = "general") -> Dict[str, Any]:
        """生成智能问题推荐"""
        try:
            # 分析仓库特征
            repo_characteristics = self._analyze_repo_characteristics(repo_data)
            
            # 根据特征和上下文生成个性化问题
            recommended_questions = self._generate_personalized_questions(
                repo_characteristics, user_context
            )
            
            # 生成追问引导
            follow_up_guides = self._generate_follow_up_guides(repo_characteristics)
            
            return {
                "success": True,
                "personalized_questions": recommended_questions,
                "follow_up_guides": follow_up_guides,
                "question_categories": list(repo_characteristics.keys()),
                "total_questions": len(recommended_questions)
            }
            
        except Exception as e:
            return {"success": False, "error": f"问题推荐失败: {str(e)}"}

    def _analyze_repo_characteristics(self, repo_data: Dict) -> Dict[str, bool]:
        """分析仓库特征，确定问题方向"""
        characteristics = {
            "has_high_stars": False,
            "has_active_community": False,
            "has_complex_architecture": False,
            "has_quality_issues": False,
            "has_recent_updates": False,
            "is_beginner_friendly": False,
            "has_detailed_docs": False
        }
        
        metadata = repo_data.get('metadata', {})
        community = repo_data.get('community', {})
        architecture = repo_data.get('architecture', {})
        code_review = repo_data.get('code_review', {})
        
        # 分析特征
        characteristics["has_high_stars"] = metadata.get('stars', 0) > 100
        characteristics["has_active_community"] = community.get('health_score', 0) > 70
        characteristics["has_complex_architecture"] = len(architecture.get('core_directories', [])) > 3
        characteristics["has_quality_issues"] = code_review.get('average_score', 100) < 80
        characteristics["has_recent_updates"] = self._is_recently_updated(metadata)
        characteristics["is_beginner_friendly"] = self._is_beginner_friendly(repo_data)
        characteristics["has_detailed_docs"] = self._has_detailed_documentation(repo_data)
        
        return characteristics

    def _is_recently_updated(self, metadata: Dict) -> bool:
        """检查项目是否最近有更新"""
        from datetime import datetime
        try:
            updated_at = metadata.get('updated_at', '')
            if updated_at:
                # 简化判断：3个月内有更新算活跃
                updated_time = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                from datetime import timedelta
                return (datetime.now(updated_time.tzinfo) - updated_time) < timedelta(days=90)
        except:
            pass
        return False

    def _is_beginner_friendly(self, repo_data: Dict) -> bool:
        """判断项目是否对新手友好"""
        metadata = repo_data.get('metadata', {})
        code_review = repo_data.get('code_review', {})
        
        # 简化判断逻辑
        has_good_docs = self._has_detailed_documentation(repo_data)
        code_quality = code_review.get('average_score', 0) > 70
        not_too_complex = len(repo_data.get('architecture', {}).get('core_directories', [])) <= 5
        
        return has_good_docs and code_quality and not_too_complex

    def _has_detailed_documentation(self, repo_data: Dict) -> bool:
        """检查是否有详细文档"""
        metadata = repo_data.get('metadata', {})
        description = metadata.get('description', '')
        has_readme = os.path.exists('cloned_repos/README.md')  # 简化判断
        
        return bool(description and len(description) > 50) or has_readme

    def _generate_personalized_questions(self, characteristics: Dict, user_context: str) -> List[Dict]:
        """生成个性化问题推荐"""
        questions = []
        
        # 基础问题
        questions.extend(self._get_questions_by_category("general"))
        
        # 根据用户上下文
        if user_context in self.QUESTION_TEMPLATES:
            questions.extend(self._get_questions_by_category(user_context))
        
        # 根据仓库特征
        if characteristics["has_high_stars"]:
            questions.extend([
                "为什么这个项目如此受欢迎？",
                "项目解决了什么痛点？"
            ])
        
        if characteristics["has_active_community"]:
            questions.extend(self._get_questions_by_category("community"))
        
        if characteristics["has_complex_architecture"]:
            questions.extend([
                "项目的整体架构是怎样的？",
                "各模块之间如何协作？"
            ])
        
        if characteristics["has_quality_issues"]:
            questions.extend(self._get_questions_by_category("quality"))
        
        if characteristics["is_beginner_friendly"]:
            questions.extend(self._get_questions_by_category("beginner"))
        
        # 去重并限制数量
        unique_questions = list(dict.fromkeys(questions))
        return [{"question": q, "category": self._categorize_question(q)} for q in unique_questions[:15]]

    def _get_questions_by_category(self, category: str) -> List[str]:
        """获取指定类别的问题"""
        return self.QUESTION_TEMPLATES.get(category, [])

    def _categorize_question(self, question: str) -> str:
        """对问题进行分类"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['架构', '模块', '设计', '结构']):
            return "architecture"
        elif any(word in question_lower for word in ['代码', '质量', '复杂度', '注释']):
            return "code_quality"
        elif any(word in question_lower for word in ['社区', '贡献', 'issue', 'pr']):
            return "community"
        elif any(word in question_lower for word in ['新手', '入门', '初学者', '友好']):
            return "beginner"
        elif any(word in question_lower for word in ['技术', '栈', '依赖', '框架']):
            return "tech_stack"
        else:
            return "general"

    def _generate_follow_up_guides(self, characteristics: Dict) -> List[Dict]:
        """生成追问引导"""
        guides = []
        
        if characteristics["has_complex_architecture"]:
            guides.append({
                "topic": "架构深入",
                "suggestions": [
                    "可以追问具体模块的职责划分",
                    "了解数据流和控制流设计",
                    "探讨扩展性和维护性考虑"
                ]
            })
        
        if characteristics["has_active_community"]:
            guides.append({
                "topic": "社区互动",
                "suggestions": [
                    "可以了解最近的讨论热点",
                    "查看核心贡献者的工作重点", 
                    "关注项目的 roadmap 规划"
                ]
            })
        
        if characteristics["has_quality_issues"]:
            guides.append({
                "topic": "代码改进",
                "suggestions": [
                    "可以询问具体的改进建议",
                    "了解技术债务处理计划",
                    "探讨代码重构的可能性"
                ]
            })
        
        return guides