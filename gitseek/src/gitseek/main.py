import sys
import warnings
import time
import os
import json
from datetime import datetime
from gitseek.crew import GitSeek

# 忽略无关警告
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
warnings.filterwarnings("ignore", category=UserWarning)

def run():
    """
    CrewAI 标准入口函数 - 仓库分析功能
    """
    print("=" * 60)
    print("🎯 GitSeek GitHub 分析专家（V2.0）")
    print("📝 功能：完整仓库分析 + 智能提问引导")
    print("🤖 已激活智能体：侦察员 + 架构师 + 代码审查员 + 社区观察员 + 报告撰写人 + 提问引导员")
    print("=" * 60)
    
    # 1. 获取并验证GitHub URL
    while True:
        repo_url = input("\n🔗 请输入要分析的GitHub仓库URL: ").strip()
        
        if not repo_url:
            print("❌ URL不能为空，请重新输入。")
            continue
            
        if not (repo_url.startswith('https://github.com/') or repo_url.startswith('http://github.com/')):
            print("❌ 请输入有效的GitHub仓库URL（以 https://github.com/ 开头）")
            continue
            
        # 确认URL
        confirm = input(f"✅ 确认分析仓库: {repo_url} ? (y/N): ").strip().lower()
        if confirm in ['y', 'yes', '是']:
            break
        else:
            print("🔄 请重新输入URL...")
    
    # 2. 显示分析流程并执行完整分析
    print(f"\n🚀 开始分析: {repo_url}")
    print("⏳ 分析流程（预计5-10分钟，取决于仓库大小）:")
    print("  1️⃣ 侦察员: 克隆仓库 + 获取元数据")
    print("  2️⃣ 架构师: 分析文件结构 + 解析依赖")
    print("  3️⃣ 代码审查员: 核心代码质量评估")
    print("  4️⃣ 社区观察员: 社区活跃度 + 健康度分析")
    print("  5️⃣ 报告撰写人: 生成结构化报告")
    print("  6️⃣ 提问引导员: 生成智能问题推荐")
    print("-" * 60)
    
    # 准备输入参数
    inputs = {
        'repo_url': repo_url,
        'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'work_dir': './cloned_repos'  # 仓库克隆目录
    }
    
    try:
        # 初始化并运行完整分析团队
        print("\n🔄 启动GitSeek分析团队...")
        crew_instance = GitSeek()
        full_crew = crew_instance.crew()
        
        print("🎯 开始执行分析任务序列...")
        start_time = time.time()
        analysis_result = full_crew.kickoff(inputs=inputs)
        end_time = time.time()
        
        # 计算分析耗时
        analysis_duration = (end_time - start_time) / 60  # 转换为分钟
        
        # 3. 分析完成提示
        print("\n" + "=" * 60)
        print("✅ 完整分析任务完成！")
        print("=" * 60)
        print(f"⏱️  分析耗时: {analysis_duration:.1f} 分钟")
        print("📊 已完成的分析内容:")
        print("  ✅ 项目基础信息（stars/forks/技术栈）")
        print("  ✅ 代码仓库结构与核心模块")
        print("  ✅ 核心代码质量评估（设计模式/复杂度）")
        print("  ✅ 社区活跃度与健康度评分")
        print("  ✅ 结构化技术报告（output/project_analysis_report.md）")
        print("  ✅ 智能问题推荐（output/question_guide.json）")
        print("-" * 60)
        
        # 4. 智能提问引导功能（新增部分）
        try:
            print("\n" + "=" * 60)
            print("🤔 智能提问引导")
            print("=" * 60)
            
            # 加载分析结果数据
            project_data = {}
            try:
                with open('output/scout_data.json', 'r', encoding='utf-8') as f:
                    scout_data = json.load(f)
                    project_data['metadata'] = scout_data.get('metadata', {})
                
                with open('output/architect_data.json', 'r', encoding='utf-8') as f:
                    project_data['architecture'] = json.load(f)
                    
                with open('output/code_review_data.json', 'r', encoding='utf-8') as f:
                    project_data['code_review'] = json.load(f)
                    
                with open('output/community_data.json', 'r', encoding='utf-8') as f:
                    project_data['community'] = json.load(f)
                    
            except Exception as e:
                print(f"⚠️ 读取分析数据失败: {e}")
                project_data = {'metadata': {}}
            
            # 用户上下文选择
            print("\n🎯 请选择您的身份背景（这将帮助生成更相关的问题）:")
            print("1. 普通用户")
            print("2. 初学者/学生") 
            print("3. 开发者")
            print("4. 研究人员")
            
            context_choice = input("请选择 (1-4, 默认1): ").strip()
            context_map = {
                "1": "general",
                "2": "beginner", 
                "3": "developer",
                "4": "researcher"
            }
            user_context = context_map.get(context_choice, "general")
            
            # 生成问题推荐
            from gitseek.tools.SmartQuestionGuide import SmartQuestionGuide  # 确保导入
            guide_tool = SmartQuestionGuide()
            question_result = guide_tool._run(
                repo_data=project_data,
                user_context=user_context
            )
            
            if question_result.get('success'):
                questions = question_result.get('personalized_questions', [])
                guides = question_result.get('follow_up_guides', [])
                
                print(f"\n💡 为您推荐以下 {len(questions)} 个问题:")
                print("-" * 60)
                
                # 按类别分组显示问题
                categories = {}
                for q in questions:
                    cat = q.get('category', 'general')
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(q['question'])
                
                for category, q_list in categories.items():
                    print(f"\n📂 {_get_category_name(category)}:")
                    for i, question in enumerate(q_list, 1):
                        print(f"   {i}. {question}")
                
                # 显示追问引导
                if guides:
                    print(f"\n🔍 追问引导:")
                    for guide in guides:
                        print(f"\n   📌 {guide['topic']}:")
                        for suggestion in guide['suggestions']:
                            print(f"      • {suggestion}")
                
                print(f"\n💡 提示: 您可以复制以上问题继续追问，深入了解项目细节")
                
                # 保存问题推荐
                with open('output/question_guide.json', 'w', encoding='utf-8') as f:
                    json.dump(question_result, f, ensure_ascii=False, indent=2)
                    
            else:
                print("❌ 问题推荐生成失败")
                
        except Exception as e:
            print(f"⚠️ 智能引导功能异常: {e}")
        
        print("🤖 分析结束，感谢使用GitSeek！")
        return analysis_result
        
    except Exception as e:
        print(f"\n❌ 分析过程中出现错误: {e}")
        print("请检查：")
        print("1. GitHub URL是否正确且可访问")
        print("2. 网络连接是否正常（需支持Git克隆和API访问）")
        print("3. API密钥是否有效")
        print("4. 磁盘空间是否充足（至少预留仓库大小2倍空间）")
        print("5. 文件系统权限是否允许创建目录和写入文件")
        import traceback
        traceback.print_exc()
        raise e

# 辅助函数（放在 run() 函数外面）
def _get_category_name(category_key: str) -> str:
    """获取分类名称"""
    name_map = {
        'architecture': '🏗️  架构设计',
        'code_quality': '📊 代码质量', 
        'community': '👥 社区动态',
        'beginner': '🎓 新手入门',
        'tech_stack': '🛠️  技术栈',
        'general': '📝 一般问题'
    }
    return name_map.get(category_key, '📝 其他问题')

# CrewAI CLI 标准入口点
if __name__ == "__main__":
    run()