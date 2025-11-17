#main.py
import sys
import warnings
import time
from datetime import datetime
from gitseek.crew import GitSeek

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    CrewAI 标准入口函数 - 由 crewai run 命令调用
    """
    print("=" * 60)
    print("🎯 你好，我是GitSeek GitHub分析师！")
    print("📝 当前版本：执行侦察 + 架构分析功能（Agent 1 + Agent 2）")
    print("=" * 60)
    
    # 获取用户输入的GitHub URL
    while True:
        repo_url = input("\n🔗 请输入要分析的GitHub仓库URL: ").strip()
        
        if not repo_url:
            print("❌ URL不能为空，请重新输入。")
            continue
            
        # 简单的URL格式验证
        if not (repo_url.startswith('https://github.com/') or repo_url.startswith('http://github.com/')):
            print("❌ 请输入有效的GitHub仓库URL（以 https://github.com/ 开头）")
            continue
            
        # 确认URL
        confirm = input(f"✅ 确认分析仓库: {repo_url} ? (y/N): ").strip().lower()
        if confirm in ['y', 'yes', '是']:
            break
        else:
            print("🔄 请重新输入URL...")
    
    print(f"\n🚀 开始分析: {repo_url}")
    print("⏳ 分析流程:")
    print("  1️⃣ Agent 1 - 侦察员: 克隆仓库 + 获取元数据")
    print("  2️⃣ Agent 2 - 架构师: 分析文件结构 + 解析依赖")
    print("-" * 60)
    
    # 准备输入参数
    inputs = {
        'repo_url': repo_url,
        'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'work_dir': './cloned_repos'  # ✅ 添加 work_dir
    }
    
    try:
        # 运行分析团队（Agent 1 + Agent 2）
        print("\n🔄 启动GitSeek分析团队...")
        crew = GitSeek().crew()
        
        print("🎯 开始执行任务序列...")
        result = crew.kickoff(inputs=inputs)
        
        print("\n" + "=" * 60)
        print("✅ 分析任务完成！")
        print("=" * 60)
        print("📊 完成的分析任务:")
        print("  ✅ Agent 1 - 侦察员:")
        print("     - 仓库克隆状态")
        print("     - 项目元数据（stars, forks, language等）")
        print("     - 项目描述和基础信息")
        print("  ✅ Agent 2 - 架构师:")
        print("     - 项目文件结构分析")
        print("     - 核心目录识别")
        print("     - 配置文件解析")
        print("     - 依赖关系分析")
        print(f"\n📝 任务摘要: {result}")
        print("\n💡 提示：当前执行侦察+架构分析，完整分析需等待其他Agent开发完成")
        print("感谢使用GitSeek！")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 分析过程中出现错误: {e}")
        print("请检查：")
        print("1. GitHub URL是否正确且可访问")
        print("2. 网络连接是否正常")
        print("3. Git和GitHub API工具配置是否正确")
        print("4. 是否有足够的磁盘空间克隆仓库")
        print("5. 文件系统权限是否正常")
        raise e

def test():
    """
    测试函数 - 可用于 crewai test 命令
    """
    print("🧪 测试GitSeek分析团队功能（Agent 1 + Agent 2）...")
    
    # 使用测试仓库
    test_repo = "https://github.com/octocat/Hello-World"
    
    print(f"🔍 测试仓库: {test_repo}")
    print("=" * 50)
    
    inputs = {
        'repo_url': test_repo,
        'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    try:
        print("🔄 初始化分析团队...")
        crew = GitSeek().crew()
        
        print("🎯 开始执行分析流程...")
        start_time = time.time()
        
        result = crew.kickoff(inputs=inputs)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"✅ 测试完成！执行时间: {execution_time:.2f}秒")
        print(f"📝 结果摘要: {result}")
        
        return result
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        raise e

# CrewAI CLI 需要的标准入口点
if __name__ == "__main__":
    run()