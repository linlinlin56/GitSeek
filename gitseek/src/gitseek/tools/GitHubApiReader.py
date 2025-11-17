import requests
from crewai.tools import BaseTool
from typing import Type, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from typing import ClassVar

class GitHubRepoInput(BaseModel):
    """Input schema for basic repository metadata."""
    owner: str = Field(..., description="Repository owner username")
    repo: str = Field(..., description="Repository name")


class GitHubIssuesInput(BaseModel):
    """Input schema for fetching issues."""
    owner: str = Field(..., description="Repository owner username")
    repo: str = Field(..., description="Repository name")
    count: int = Field(default=10, description="Number of issues to fetch")
    state: str = Field(default="all", description="Issue state: open/closed/all")


class GitHubPRsInput(BaseModel):
    """Input schema for fetching pull requests."""
    owner: str = Field(..., description="Repository owner username")
    repo: str = Field(..., description="Repository name")
    count: int = Field(default=10, description="Number of PRs to fetch")
    state: str = Field(default="all", description="PR state: open/closed/all")


class GitHubContributorsInput(BaseModel):
    """Input schema for fetching contributors."""
    owner: str = Field(..., description="Repository owner username")
    repo: str = Field(..., description="Repository name")
    count: int = Field(default=30, description="Number of contributors to fetch")


class GitHubAPIReader(BaseTool):
    name: str = "GitHub Repository Metadata & Community Analyzer"
    description: str = """完整的 GitHub API 工具，用于获取仓库元数据、Issues、Pull Requests 和贡献者信息。
    支持社区活跃度分析、贡献者统计和趋势识别。"""
    args_schema: Type[BaseModel] = GitHubRepoInput
    
    # GitHub API 基础 URL
    BASE_URL: ClassVar[str] = "https://api.github.com"

    def _run(self, owner: str, repo: str) -> Dict[str, Any]:
        """获取基础仓库元数据"""
        try:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}"

            response = requests.get(url, headers=self._get_headers())

            if response.status_code == 200:
                data = response.json()

                # --- 修复后的 License 逻辑 ---
                # 检查 data["license"] 是否为 None。如果是，使用空字典 {}，否则使用 data["license"] 的值。
                # 这样可以保证后续的 .get("name", ...) 调用在一个字典上执行。
                license_info = data.get("license") or {}
                license_name = license_info.get("name", "No license")
                # -----------------------------

                return {
                    "success": True,
                    "name": data["name"],
                    "full_name": data["full_name"],
                    "description": data.get("description", "No description"),
                    "stars": data["stargazers_count"],
                    "forks": data["forks_count"],
                    "watchers": data["watchers_count"],
                    "language": data.get("language", "Not specified"),
                    "open_issues": data["open_issues_count"],
                    "created_at": data["created_at"],
                    "updated_at": data["updated_at"],
                    "pushed_at": data.get("pushed_at"),
                    "size": data["size"],  # KB
                    "default_branch": data["default_branch"],

                    # 使用修复后的 license_name
                    "license": license_name,

                    "topics": data.get("topics", []),
                    "html_url": data["html_url"],
                    "homepage": data.get("homepage"),
                    "has_wiki": data.get("has_wiki", False),
                    "has_pages": data.get("has_pages", False),
                    "has_downloads": data.get("has_downloads", False),
                }
            elif response.status_code == 404:
                return {"success": False, "error": f"Repository {owner}/{repo} not found"}
            elif response.status_code == 403:
                return {"success": False, "error": "API rate limit exceeded. Please wait or use authentication."}
            else:
                return {"success": False, "error": f"API request failed with status {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": f"GitHub API error: {str(e)}"}
    
    def _get_headers(self) -> Dict[str, str]:
        """获取 API 请求头（可选择性添加认证）"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitSeek-Analyzer"
        }
        # 如果有 GitHub Token，可以添加认证
        # headers["Authorization"] = f"token {GITHUB_TOKEN}"
        return headers
    
    def get_recent_issues(self, owner: str, repo: str, count: int = 10, state: str = "all") -> Dict[str, Any]:
        """获取最近的 Issues 并进行分析"""
        try:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues"
            params = {
                "state": state,
                "per_page": min(count, 100),  # GitHub API 限制
                "sort": "updated",
                "direction": "desc"
            }
            
            response = requests.get(url, params=params, headers=self._get_headers())
            
            if response.status_code == 200:
                issues = response.json()
                
                # 过滤掉 Pull Requests (GitHub API 将 PR 也算作 issue)
                pure_issues = [i for i in issues if 'pull_request' not in i]
                
                # 统计分析
                open_count = len([i for i in pure_issues if i['state'] == 'open'])
                closed_count = len([i for i in pure_issues if i['state'] == 'closed'])
                
                # 标签统计
                label_stats = {}
                for issue in pure_issues:
                    for label in issue.get('labels', []):
                        label_name = label['name']
                        label_stats[label_name] = label_stats.get(label_name, 0) + 1
                
                # 识别热点问题
                hot_issues = self._identify_hot_issues(pure_issues)
                
                # 响应时间分析
                response_time_stats = self._analyze_response_time(pure_issues)
                
                return {
                    "success": True,
                    "total_fetched": len(pure_issues),
                    "open_issues": open_count,
                    "closed_issues": closed_count,
                    "closure_rate": round(closed_count / max(len(pure_issues), 1) * 100, 2),
                    "label_distribution": dict(sorted(label_stats.items(), key=lambda x: x[1], reverse=True)[:10]),
                    "top_labels": list(sorted(label_stats.items(), key=lambda x: x[1], reverse=True)[:5]),
                    "hot_issues": hot_issues,
                    "response_time_analysis": response_time_stats,
                    "recent_issues": [
                        {
                            "number": i['number'],
                            "title": i['title'],
                            "state": i['state'],
                            "created_at": i['created_at'],
                            "updated_at": i['updated_at'],
                            "closed_at": i.get('closed_at'),
                            "user": i['user']['login'],
                            "labels": [l['name'] for l in i.get('labels', [])],
                            "comments": i['comments'],
                            "html_url": i['html_url']
                        }
                        for i in pure_issues[:count]
                    ]
                }
            elif response.status_code == 404:
                return {"success": False, "error": f"Repository {owner}/{repo} not found"}
            elif response.status_code == 403:
                return {"success": False, "error": "API rate limit exceeded"}
            else:
                return {"success": False, "error": f"Failed with status {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Failed to fetch issues: {str(e)}"}
    
    def get_recent_prs(self, owner: str, repo: str, count: int = 10, state: str = "all") -> Dict[str, Any]:
        """获取最近的 Pull Requests 并进行分析"""
        try:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls"
            params = {
                "state": state,
                "per_page": min(count, 100),
                "sort": "updated",
                "direction": "desc"
            }
            
            response = requests.get(url, params=params, headers=self._get_headers())
            
            if response.status_code == 200:
                prs = response.json()
                
                # 统计分析
                merged_count = len([pr for pr in prs if pr.get('merged_at')])
                open_count = len([pr for pr in prs if pr['state'] == 'open'])
                closed_count = len([pr for pr in prs if pr['state'] == 'closed' and not pr.get('merged_at')])
                
                # 代码变更统计
                total_additions = sum(pr.get('additions', 0) for pr in prs)
                total_deletions = sum(pr.get('deletions', 0) for pr in prs)
                
                # 合并时间分析
                merge_time_stats = self._analyze_merge_time(prs)
                
                # 活跃贡献者
                contributors = {}
                for pr in prs:
                    author = pr['user']['login']
                    contributors[author] = contributors.get(author, 0) + 1
                
                return {
                    "success": True,
                    "total_fetched": len(prs),
                    "merged_prs": merged_count,
                    "open_prs": open_count,
                    "closed_prs": closed_count,
                    "merge_rate": round(merged_count / max(len(prs), 1) * 100, 2),
                    "total_code_changes": {
                        "additions": total_additions,
                        "deletions": total_deletions,
                        "net_change": total_additions - total_deletions
                    },
                    "merge_time_analysis": merge_time_stats,
                    "active_contributors": dict(sorted(contributors.items(), key=lambda x: x[1], reverse=True)[:10]),
                    "recent_prs": [
                        {
                            "number": pr['number'],
                            "title": pr['title'],
                            "state": pr['state'],
                            "merged": pr.get('merged_at') is not None,
                            "created_at": pr['created_at'],
                            "updated_at": pr['updated_at'],
                            "merged_at": pr.get('merged_at'),
                            "closed_at": pr.get('closed_at'),
                            "user": pr['user']['login'],
                            "additions": pr.get('additions', 0),
                            "deletions": pr.get('deletions', 0),
                            "changed_files": pr.get('changed_files', 0),
                            "comments": pr.get('comments', 0),
                            "review_comments": pr.get('review_comments', 0),
                            "html_url": pr['html_url']
                        }
                        for pr in prs[:count]
                    ]
                }
            elif response.status_code == 404:
                return {"success": False, "error": f"Repository {owner}/{repo} not found"}
            elif response.status_code == 403:
                return {"success": False, "error": "API rate limit exceeded"}
            else:
                return {"success": False, "error": f"Failed with status {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Failed to fetch PRs: {str(e)}"}
    
    def get_contributors(self, owner: str, repo: str, count: int = 30) -> Dict[str, Any]:
        """获取主要贡献者信息"""
        try:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}/contributors"
            params = {"per_page": min(count, 100)}
            
            response = requests.get(url, params=params, headers=self._get_headers())
            
            if response.status_code == 200:
                contributors = response.json()
                
                # 贡献度分析
                total_contributions = sum(c['contributions'] for c in contributors)
                
                # 识别核心贡献者（前20%贡献者）
                core_contributor_threshold = int(len(contributors) * 0.2)
                core_contributors = contributors[:max(core_contributor_threshold, 5)]
                
                return {
                    "success": True,
                    "total_contributors": len(contributors),
                    "total_contributions": total_contributions,
                    "contributor_diversity": self._calculate_contributor_diversity(contributors),
                    "core_contributors": [
                        {
                            "login": c['login'],
                            "contributions": c['contributions'],
                            "contribution_percentage": round(c['contributions'] / total_contributions * 100, 2),
                            "profile_url": c['html_url'],
                            "avatar_url": c['avatar_url']
                        }
                        for c in core_contributors
                    ],
                    "top_10_contributors": [
                        {
                            "rank": idx + 1,
                            "login": c['login'],
                            "contributions": c['contributions'],
                            "profile_url": c['html_url']
                        }
                        for idx, c in enumerate(contributors[:10])
                    ]
                }
            elif response.status_code == 404:
                return {"success": False, "error": f"Repository {owner}/{repo} not found"}
            elif response.status_code == 403:
                return {"success": False, "error": "API rate limit exceeded"}
            else:
                return {"success": False, "error": f"Failed with status {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Failed to fetch contributors: {str(e)}"}
    
    def get_community_health(self, owner: str, repo: str) -> Dict[str, Any]:
        """综合社区健康度评估"""
        try:
            # 获取基础元数据
            metadata = self._run(owner, repo)
            if not metadata.get("success"):
                return metadata
            
            # 获取 Issues 分析
            issues = self.get_recent_issues(owner, repo, count=20)
            
            # 获取 PRs 分析
            prs = self.get_recent_prs(owner, repo, count=20)
            
            # 获取贡献者分析
            contributors = self.get_contributors(owner, repo, count=50)
            
            # 计算健康度指标
            health_score = self._calculate_health_score(metadata, issues, prs, contributors)
            
            return {
                "success": True,
                "repository": f"{owner}/{repo}",
                "health_score": health_score,
                "metrics": {
                    "star_count": metadata.get("stars", 0),
                    "fork_count": metadata.get("forks", 0),
                    "open_issues": metadata.get("open_issues", 0),
                    "total_contributors": contributors.get("total_contributors", 0),
                    "issue_closure_rate": issues.get("closure_rate", 0),
                    "pr_merge_rate": prs.get("merge_rate", 0),
                },
                "activity_level": self._determine_activity_level(metadata, issues, prs),
                "community_engagement": self._assess_community_engagement(issues, prs, contributors),
                "recommendations": self._generate_health_recommendations(health_score, metadata, issues, prs)
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to assess community health: {str(e)}"}
    
    # === 辅助分析方法 ===
    
    def _identify_hot_issues(self, issues: List[Dict]) -> List[Dict]:
        """识别热点问题（高评论、新创建、高关注）"""
        hot_issues = []
        
        for issue in issues[:10]:
            if issue['comments'] > 5 or issue['state'] == 'open':
                hot_issues.append({
                    "number": issue['number'],
                    "title": issue['title'],
                    "comments": issue['comments'],
                    "created_at": issue['created_at'],
                    "reason": "高互动" if issue['comments'] > 5 else "待解决"
                })
        
        return hot_issues[:5]
    
    def _analyze_response_time(self, issues: List[Dict]) -> Dict[str, Any]:
        """分析问题响应时间"""
        closed_issues = [i for i in issues if i['state'] == 'closed' and i.get('closed_at')]
        
        if not closed_issues:
            return {"average_days": None, "status": "暂无数据"}
        
        total_time = 0
        for issue in closed_issues:
            created = datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00'))
            closed = datetime.fromisoformat(issue['closed_at'].replace('Z', '+00:00'))
            total_time += (closed - created).days
        
        avg_days = total_time / len(closed_issues)
        
        return {
            "average_days": round(avg_days, 2),
            "sample_size": len(closed_issues),
            "status": "快速响应" if avg_days < 7 else "正常响应" if avg_days < 30 else "响应较慢"
        }
    
    def _analyze_merge_time(self, prs: List[Dict]) -> Dict[str, Any]:
        """分析 PR 合并时间"""
        merged_prs = [pr for pr in prs if pr.get('merged_at')]
        
        if not merged_prs:
            return {"average_days": None, "status": "暂无数据"}
        
        total_time = 0
        for pr in merged_prs:
            created = datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00'))
            merged = datetime.fromisoformat(pr['merged_at'].replace('Z', '+00:00'))
            total_time += (merged - created).days
        
        avg_days = total_time / len(merged_prs)
        
        return {
            "average_days": round(avg_days, 2),
            "sample_size": len(merged_prs),
            "status": "快速合并" if avg_days < 3 else "正常合并" if avg_days < 14 else "合并较慢"
        }
    
    def _calculate_contributor_diversity(self, contributors: List[Dict]) -> str:
        """计算贡献者多样性"""
        if not contributors:
            return "无数据"
        
        # 计算基尼系数（简化版）
        total = sum(c['contributions'] for c in contributors)
        top_10_percent = int(len(contributors) * 0.1) or 1
        top_contributions = sum(c['contributions'] for c in contributors[:top_10_percent])
        
        concentration = top_contributions / total if total > 0 else 0
        
        if concentration > 0.8:
            return "高度集中（少数核心贡献者）"
        elif concentration > 0.5:
            return "中等集中"
        else:
            return "分散（贡献者多样）"
    
    def _calculate_health_score(self, metadata: Dict, issues: Dict, prs: Dict, contributors: Dict) -> int:
        """计算社区健康度分数 (0-100)"""
        score = 0
        
        # Stars 权重 (20分)
        stars = metadata.get("stars", 0)
        score += min(20, stars // 50)
        
        # Issue 处理效率 (20分)
        closure_rate = issues.get("closure_rate", 0)
        score += closure_rate * 0.2
        
        # PR 合并率 (20分)
        merge_rate = prs.get("merge_rate", 0)
        score += merge_rate * 0.2
        
        # 贡献者活跃度 (20分)
        contributor_count = contributors.get("total_contributors", 0)
        score += min(20, contributor_count // 5)
        
        # 代码活跃度 (20分)
        # 基于最近更新时间
        try:
            updated_at = datetime.fromisoformat(metadata.get("updated_at", "").replace('Z', '+00:00'))
            days_since_update = (datetime.now(updated_at.tzinfo) - updated_at).days
            if days_since_update < 7:
                score += 20
            elif days_since_update < 30:
                score += 15
            elif days_since_update < 90:
                score += 10
        except:
            pass
        
        return min(100, int(score))
    
    def _determine_activity_level(self, metadata: Dict, issues: Dict, prs: Dict) -> str:
        """确定活跃度等级"""
        try:
            updated_at = datetime.fromisoformat(metadata.get("updated_at", "").replace('Z', '+00:00'))
            days_since_update = (datetime.now(updated_at.tzinfo) - updated_at).days
            
            open_issues = issues.get("open_issues", 0)
            recent_prs = len(prs.get("recent_prs", []))
            
            if days_since_update < 7 and (open_issues > 0 or recent_prs > 0):
                return "非常活跃 (Highly Active)"
            elif days_since_update < 30:
                return "活跃 (Active)"
            elif days_since_update < 90:
                return "中等活跃 (Moderately Active)"
            else:
                return "不活跃 (Inactive)"
        except:
            return "未知 (Unknown)"
    
    def _assess_community_engagement(self, issues: Dict, prs: Dict, contributors: Dict) -> str:
        """评估社区参与度"""
        total_contributors = contributors.get("total_contributors", 0)
        recent_issue_count = issues.get("total_fetched", 0)
        recent_pr_count = prs.get("total_fetched", 0)
        
        engagement_score = total_contributors + (recent_issue_count + recent_pr_count) * 2
        
        if engagement_score > 100:
            return "高度参与 (High Engagement)"
        elif engagement_score > 50:
            return "中等参与 (Moderate Engagement)"
        elif engagement_score > 20:
            return "低度参与 (Low Engagement)"
        else:
            return "极少参与 (Minimal Engagement)"
    
    def _generate_health_recommendations(self, score: int, metadata: Dict, issues: Dict, prs: Dict) -> List[str]:
        """生成健康度改进建议"""
        recommendations = []
        
        if score < 50:
            recommendations.append("社区健康度较低，建议增加项目宣传和贡献者招募")
        
        if issues.get("closure_rate", 0) < 50:
            recommendations.append("Issue 关闭率较低，建议加强问题处理和响应速度")
        
        if prs.get("merge_rate", 0) < 50:
            recommendations.append("PR 合并率较低，建议优化代码审查流程")
        
        if metadata.get("stars", 0) < 100:
            recommendations.append("Star 数量较少，建议提升项目质量和知名度")
        
        if not recommendations:
            recommendations.append("项目健康状况良好，继续保持！")
        
        return recommendations
