# Gitseek Crew

Welcome to the Gitseek Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```
### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/gitseek/config/agents.yaml` to define your agents
- Modify `src/gitseek/config/tasks.yaml` to define your tasks
- Modify `src/gitseek/crew.py` to add your own logic, tools and specific args
- Modify `src/gitseek/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ crewai run
```

This command initializes the gitseek Crew, assembling the agents and assigning them tasks as defined in your configuration.

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Understanding Your Crew

The gitseek Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the Gitseek Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.


Agent 1: 侦察员 (Scout Agent)
任务: 克隆指定的 GitHub 仓库到本地。使用 GitHub API 获取项目的基本元数据（如 Star 数、Forks、主要语言、项目描述）。
工具: GitShellTool, GitHubAPIReader。

Agent 2: 架构师 (Architect Agent)
任务: 分析项目的文件结构。识别出项目的核心目录（如 src, lib, app），识别出配置文件（如 package.json, requirements.txt）并解析其依赖项。生成一份项目整体架构的文字描述。
工具: FileSystemBrowser, FileContentReader。

Agent 3: 代码审查员 (Code Reviewer Agent)
任务: 在架构师识别的核心目录中，随机抽取或选择几个关键文件进行“阅读”。总结这些核心文件的功能、设计模式和代码质量。
工具: FileContentReader, LLMCodeSummarizer。

Agent 4: 社区观察员 (Community Watcher Agent)
任务: 使用 GitHub API 拉取最近的 10 个 open/closed issues 和 pull requests。总结社区当前关注的焦点问题、开发活跃度以及主要的贡献者。
工具: GitHubAPIReader。

Agent 5: 报告撰写人 (Report Writer Agent)
任务: 整合以上所有智能体的分析结果（项目元数据、架构、代码质量、社区动态），生成一份结构化的 Markdown 技术分析报告。

最终产物:
报告: 一份 project_analysis_report.md。
QA 数据集: 基于报告内容，自动生成一系列 (问题, 答案) 对，例如：“这个项目主要使用了什么框架？”“最近社区在修复什么bug？”
小模型: 使用这个数据集微调一个小型 LLM，得到一个可以回答关于这个特定项目问题的专家模型。