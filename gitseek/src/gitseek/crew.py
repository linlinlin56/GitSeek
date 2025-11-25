from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from .tools.GitShellTool import GitShellTool  
from .tools.GitHubApiReader import GitHubAPIReader  
from .tools.FileContentReader import FileContentReader
from .tools.FileSystemBrowser import FileSystemBrowser
from .tools.LLMCodeSummarizer import LLMCodeSummarizer
from .tools.ReportGenerator import ReportGenerator
from .tools.SmartQuestionGuide import SmartQuestionGuide
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
import os

@CrewBase
class GitSeek():
    """GitHub Repository Analysis Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # 配置DeepSeek LLM
    llm = LLM(
        model="openai/deepseek-chat",
        api_key=os.environ.get("sk-b5b107797ce14c5e9cb914ba8e7811e2"),  # 建议使用环境变量
        base_url="https://api.deepseek.com/v1",
    )


    @agent
    def scout_agent(self) -> Agent:
        """GitHub仓库侦察员 - 负责克隆仓库和获取元数据"""
        git_tool = GitShellTool()
        api_tool = GitHubAPIReader()
        
        return Agent(
            role="GitHub Repository Scout",
            goal="Clone specified GitHub repositories and gather basic project metadata including stars, forks, main language, and project description",
            backstory="""You are an efficient technical scout specializing in GitHub ecosystem analysis. 
            With expertise in Git operations and GitHub API, you quickly acquire and organize 
            fundamental project intelligence for deeper analysis.""",
            tools=[git_tool, api_tool],
            verbose=True,
            llm=self.llm
        )

    @agent
    def architect_agent(self) -> Agent:
        """软件架构分析师 - 负责分析项目结构和依赖"""
        fs_tool = FileSystemBrowser()
        fc_tool = FileContentReader()

        return Agent(
            role="Software Architecture Analyst",
            goal="Analyze project file structure, identify core directories and configuration files, parse dependencies, and generate comprehensive architectural descriptions",
            backstory="""As a seasoned software architect, you have an exceptional ability to understand 
            and document complex codebase structures. Your keen eye for design patterns and 
            dependency relationships makes you invaluable for project architecture assessment.""",
            tools=[fs_tool, fc_tool], 
            verbose=True,
            llm=self.llm
        )

    @agent
    def code_reviewer_agent(self) -> Agent:
        """代码审查员 - 负责代码质量分析"""
        code_tool = LLMCodeSummarizer()
        file_reader = FileContentReader()
        
        return Agent(
            role="Senior Code Quality Analyst",
            goal="Review key source files from core directories, analyze functionality, identify design patterns, and assess overall code quality",
            backstory="""You are a meticulous code reviewer with years of experience in multiple 
            programming languages. Known for your insightful analysis of code structure, 
            design patterns, and quality metrics that help maintain high coding standards.""",
            tools=[code_tool, file_reader],
            verbose=True,
            llm=self.llm
        )

    @agent
    def community_watcher_agent(self) -> Agent:
        """社区观察员 - 负责社区活跃度分析"""
        api_tool = GitHubAPIReader()
        
        return Agent(
            role="Open Source Community Analyst",
            goal="Extract recent issues and pull requests, summarize community focus areas, development activity levels, and identify key contributors",
            backstory="""You specialize in understanding open source community dynamics. With deep 
            knowledge of GitHub collaboration patterns, you excel at identifying trending 
            issues, contributor engagement, and project health indicators.""",
            tools=[api_tool],
            verbose=True,
            llm=self.llm
        )

    @agent
    def report_writer_agent(self) -> Agent:
        """报告撰写人 - 负责生成最终报告和QA数据集"""
        report_tool = ReportGenerator()
        
        return Agent(
            role="Technical Documentation Specialist",
            goal="Synthesize all analytical findings into a structured Markdown technical report and generate Q&A datasets for model fine-tuning",
            backstory="""You are an expert technical writer who transforms complex technical information 
            into clear, comprehensive documentation. Your unique skill lies in creating 
            both human-readable reports and machine-learning training datasets from the same analysis.""",
            tools=[report_tool],
            verbose=True,
            llm=self.llm
        )
    
    @agent
    def question_guide_agent(self) -> Agent:
        """智能提问引导员 - 负责推荐高频问题和追问方向"""
        guide_tool = SmartQuestionGuide()
        
        return Agent(
            role="智能提问引导专家",
            goal="基于GitHub仓库分析结果，智能推荐用户可能感兴趣的高频问题和追问方向",
            backstory="""你是用户体验专家，擅长根据技术项目的特征预测用户的兴趣点。
            你能快速理解项目特点，并生成有针对性的问题建议，帮助用户深入探索项目。""",
            tools=[guide_tool],
            verbose=True,
            llm=self.llm
    )
    
    '''
    @agent
    def qa_agent(self) -> Agent:
        """GitHub仓库问答专家 - 基于分析结果回答用户自然语言问题"""
        return Agent(
            role="GitHub仓库问答专家",
            goal="""基于已完成的GitHub仓库分析结果（元数据、架构、代码质量、社区动态、完整报告），
            准确回答用户的自然语言问题，支持多轮追问，保持回答的一致性和相关性""",
            backstory="""你是精通技术分析与问答的专家，能自动从CrewAI记忆库中检索与用户问题相关的仓库分析信息，
            无需手动查找报告文件。你会结合历史对话上下文，理解多轮追问的逻辑，用清晰的自然语言给出答案，
            必要时引用分析结果中的具体细节（如“根据架构分析，该项目核心目录为src/core”），
            若记忆中无相关信息，如实告知用户并建议补充提问方向。""",
            verbose=True,
            llm=self.llm
        )
    '''
    
    

    # === 任务定义 ===
    
    @task
    def scout_task(self) -> Task:
        """侦察任务 - 克隆仓库并获取元数据"""
        return Task(
            description="""对指定的GitHub仓库 {repo_url} 进行初步侦察：
            1. 提取仓库所有者和仓库名称
            2. 使用Git工具克隆仓库到工作目录 {work_dir}
            3. 使用GitHub API获取项目基本元数据（stars, forks, language等）
            4. 收集项目描述和README信息
            5. 记录项目的创建时间和最后更新时间
            
            返回结构化数据，包括克隆路径和元数据。
            确保所有收集的数据准确且格式规范。""",
            agent=self.scout_agent(),
            expected_output="""一份包含项目基本信息的侦察报告，必须包括：
            - 仓库克隆状态和本地路径
            - 项目元数据（stars, forks, language等）
            - 项目描述和关键统计信息
            - 数据收集时间戳
            
            输出格式示例:
            {
                "clone_path": "/path/to/repo",
                "metadata": {...},
                "timestamp": "2025-11-16 10:00:00"
            }""",
             output_file='output/scout_data.json'  # 输出到文件
        )

    @task
    def architect_task(self) -> Task:
        """架构分析任务"""
        return Task(
            description="""基于侦察任务的结果，分析项目 {repo_url} 的整体架构：
            1. 使用侦察任务提供的克隆路径
            2. 扫描项目的完整文件目录结构
            3. 识别核心代码目录（如src, lib, app, components等）
            4. 定位并解析关键配置文件（package.json, requirements.txt等）
            5. 分析项目的依赖关系和外部库使用情况
            6. 生成项目的架构层次描述
            
            重点关注项目的组织方式和模块化设计。""",
            agent=self.architect_agent(),
            expected_output="""一份详细的项目架构分析文档，包含：
            - 项目目录结构树状图
            - 核心模块和组件识别
            - 依赖关系清单
            - 架构设计模式分析
            - 配置环境说明
            
            输出格式:
            {
                "structure": {...},
                "core_directories": [...],
                "config_files": [...],
                "dependencies": {...}
            }""",
            #context=[self.scout_task()]
            output_file='output/architect_data.json'  # 输出到文件 
        )

    @task
    def code_review_task(self) -> Task:
        """代码审查任务"""
        return Task(
            description="""基于架构分析结果，对项目 {repo_url} 进行代码质量审查：
            1. 从架构分析识别的核心目录中选择关键文件
            2. 使用 LLMCodeSummarizer 工具随机抽取3-5个重要源代码文件
            3. 深度分析每个文件的功能、代码质量和设计模式
            4. 评估代码的可读性、注释质量和命名规范
            5. 分析代码复杂度、函数长度和模块耦合度
            6. 识别使用的设计模式和架构模式
            
            提供具体的代码示例和改进建议。""",
            agent=self.code_reviewer_agent(),
            expected_output="""一份专业的代码审查报告，包含：
            - 审查的文件列表和选择理由
            - 每个文件的详细分析（质量、复杂度、模式）
            - 代码质量评估（可读性、规范性等）
            - 设计模式识别和分析
            - 具体的改进建议和最佳实践
            - 总体代码质量评分
            
            输出格式:
            {
                "reviewed_files": [...],
                "overall_quality": "Good/Fair/Needs Improvement",
                "average_score": 85,
                "design_patterns": [...],
                "recommendations": [...]
            }""",
            #context=[self.scout_task(),self.architect_task()]
            output_file='output/code_review_data.json'  # 输出到文件
        )

    @task
    def community_analysis_task(self) -> Task:
        """社区分析任务"""
        return Task(
            description="""分析项目 {repo_url} 的社区活跃度和健康度：
            1. 使用侦察任务提供的仓库所有者和名称
            2. 使用 GitHubAPIReader 获取最近10个已打开和已关闭的issue
            3. 获取最近10个pull request记录
            4. 分析issue的类型分布（bug、feature、question等）
            5. 识别社区关注的热点问题和趋势
            6. 统计主要贡献者和他们的活跃度
            7. 评估项目的响应速度和问题解决效率
            8. 计算社区健康度评分
            
            重点关注社区的健康发展状况和活跃度。""",
            agent=self.community_watcher_agent(),
            expected_output="""一份社区动态分析报告，包含：
            - 近期issue和PR的统计摘要
            - 社区关注焦点和趋势分析
            - 核心贡献者识别和活跃度评估
            - 项目维护响应指标
            - 社区健康度评估和评分
            
            输出格式:
            {
                "issues": {...},
                "prs": {...},
                "contributors": {...},
                "health_score": 85,
                "activity_level": "Highly Active"
            }""",
            #context=[self.scout_task()]
            output_file='output/community_data.json'  # 输出到文件
        )

    @task
    def report_generation_task(self) -> Task:
        """报告生成任务"""
        return Task(
            description="""整合所有分析结果，为项目 {repo_url} 生成完整的技术分析报告：
            1. 汇总侦察、架构、代码审查和社区分析的所有数据
            2. 使用 ReportGenerator 工具生成结构化的Markdown技术报告
            3. 报告应包含执行摘要、详细分析和结论建议
            4. 基于报告内容自动生成Q&A训练数据集
            5. 创建针对项目特定问题的问答对
            6. 准备模型微调所需的数据格式

             **重要：请先读取以下数据文件，基于真实数据生成报告：**
        - output/scout_data.json：包含项目stars、forks、语言、描述等元数据
        - output/architect_data.json：包含目录结构、核心模块、依赖关系
        - output/code_review_data.json：包含代码质量评分、设计模式、复杂度分析
        - output/community_data.json：包含issues、PR、贡献者、健康度数据
        
        **报告必须基于这些文件中的具体数据，不要使用占位符：**
        1. 项目概览 - 使用scout_data中的具体stars/forks/语言数据
        2. 架构评估 - 描述architect_data中的实际目录结构和依赖
        3. 代码质量 - 引用code_review_data中的质量评分和审查发现  
        4. 社区分析 - 包含community_data中的真实issues和PR统计
        5. 总体建议 - 基于所有具体分析结果提出改进建议
        
        确保所有数据都是真实分析得到的，不要生成空报告。
            
            确保报告专业、完整、易读。""",
            agent=self.report_writer_agent(),
            expected_output="""完整的项目分析交付物，包括：
            - project_analysis_report.md：结构化技术报告
            - qa_dataset.json：自动生成的问答数据集
            
            报告必须涵盖：
            1. 项目概览（基本信息、描述、技术栈）
            2. 架构评估（目录结构、核心模块、依赖）
            3. 代码质量（质量评分、设计模式、复杂度）
            4. 社区分析（活跃度、贡献者、健康度）
            5. 总体建议（优势、改进、战略规划）""",
            #context=[
            #    self.scout_task(),
            #    self.architect_task(), 
            #    self.code_review_task(),
            #    self.community_analysis_task()
            #],
            output_file='output/project_analysis_report.md'
        )
    
    @task
    def question_guide_task(self) -> Task:
        """智能提问引导任务"""
        return Task(
            description="""基于对仓库 {repo_url} 的完整分析结果，为用户生成智能问题推荐：
            1. 分析项目特征（流行度、活跃度、复杂度、新手友好度等）
            2. 生成个性化问题推荐（15个左右高频问题）
            3. 提供追问引导建议
            4. 按类别组织问题（架构、代码、社区、入门等）
            
            确保问题具有针对性和实用性。""",
            agent=self.question_guide_agent(),
            expected_output="""智能问题推荐报告，包含：
            - 个性化问题列表（按类别分组）
            - 追问引导建议
            - 问题分类统计
            
            输出格式:
            {
                "personalized_questions": [
                    {"question": "问题内容", "category": "问题类别"},
                    ...
                ],
                "follow_up_guides": [
                    {"topic": "主题", "suggestions": ["建议1", "建议2"]},
                    ...
                ],
                "question_categories": ["architecture", "community", ...],
                "total_questions": 15
            }""",
            output_file='output/question_guide.json'
        )
    
    '''
    @task
    def qa_task(self) -> Task:
        """基于仓库分析结果的多轮问答任务"""
        return Task(
            description="""基于已存储的{repo_url}仓库完整分析结果，回答用户的自然语言问题：{user_question}
            1. 从CrewAI记忆库中检索与问题相关的分析信息（包括侦察、架构、代码、社区、报告数据）；
            2. 结合历史对话上下文，判断用户是否为多轮追问，确保回答连贯；
            3. 提取关键信息，用清晰、简洁的自然语言组织答案；
            4. 必要时引用分析结果的具体来源（如“来自代码质量分析”“根据社区活跃度统计”）；
            5. 若无法从记忆中找到相关信息，如实告知用户，不编造内容。""",
            agent=self.qa_agent(),
            expected_output="""针对用户问题的准确、连贯回答，包含：
            - 问题对应的核心分析信息（如架构细节、代码质量、社区数据等）；
            - 必要的引用说明（明确信息来源的分析环节）；
            - 若为多轮追问，需关联历史对话内容；
            - 结尾可询问“是否需要进一步了解该仓库的其他信息？”以引导后续交互。""",
            # 无需显式指定context：记忆库已存储所有前置分析任务结果
        )
    '''
    
    

    @crew
    def crew(self) -> Crew:
        """创建GitHub分析团队"""
        
        return Crew(
            agents=[
                self.scout_agent(),
                self.architect_agent(),
                self.code_reviewer_agent(),
                self.community_watcher_agent(),
                self.report_writer_agent(),
                #self.qa_agent()  # 新增：添加问答智能体
                self.question_guide_agent()  # 新增引导智能体
            ],
            tasks=[
                self.scout_task(),
                self.architect_task(),
                self.code_review_task(),
                self.community_analysis_task(),
                self.report_generation_task(),
                self.question_guide_task()   # 新增引导任务
            ],
            process=Process.sequential,
            verbose=True,
            #memory=True,
            memory=False,
            share_crew=True,
            # 确保任务输出可以在agents间共享
            full_output=True,
            # 3. 传入自定义的 ChromaDB 客户端（强制使用我们的嵌入函数）
            #rag_client=chroma_client
        )
    
