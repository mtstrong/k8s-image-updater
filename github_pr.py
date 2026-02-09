"""
GitHub Pull Request Creator Module

Creates GitHub branches and pull requests with updated manifests.
"""

import logging
import os
from datetime import datetime
from github import Github, GithubException
from typing import List, Dict

logger = logging.getLogger(__name__)


class GitHubPRCreator:
    """Create GitHub pull requests for image updates"""
    
    def __init__(self, config):
        """Initialize GitHub PR creator"""
        self.config = config
        self.github_token = config['github']['token']
        self.owner = config['github']['owner']
        self.repo_name = config['github']['repo']
        self.base_branch = config['github']['base_branch']
        self.branch_prefix = config['github'].get('branch_prefix', 'image-updates')
        
        # Initialize GitHub client
        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(f"{self.owner}/{self.repo_name}")
    
    def create_pr(
        self,
        updated_files: List[str],
        updates: List[Dict],
        summary: str
    ) -> str:
        """Create a pull request with updated manifest files"""
        
        # Generate branch name
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        branch_name = f"{self.branch_prefix}/{timestamp}"
        
        logger.info(f"Creating branch: {branch_name}")
        
        try:
            # Get base branch reference
            base_ref = self.repo.get_git_ref(f"heads/{self.base_branch}")
            base_sha = base_ref.object.sha
            
            # Create new branch
            self.repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=base_sha
            )
            logger.info(f"✓ Branch created: {branch_name}")
            
            # Update files in the new branch
            self._commit_changes(branch_name, updated_files, updates)
            
            # Create pull request
            pr_title = self._generate_pr_title(updates)
            pr_body = self._generate_pr_body(updates, summary)
            
            pr = self.repo.create_pull(
                title=pr_title,
                body=pr_body,
                head=branch_name,
                base=self.base_branch
            )
            
            logger.info(f"✓ Pull request created: {pr.html_url}")
            
            # Add labels if configured
            self._add_labels(pr)
            
            return pr.html_url
            
        except GithubException as e:
            logger.error(f"GitHub API error: {e}")
            raise
    
    def _commit_changes(
        self,
        branch_name: str,
        updated_files: List[str],
        updates: List[Dict]
    ):
        """Commit updated files to the branch"""
        
        for file_path in updated_files:
            try:
                # Read the updated file content
                with open(file_path, 'r') as f:
                    new_content = f.read()
                
                # Get the file's path relative to repo root
                # This assumes files are in the repo
                repo_file_path = self._get_repo_relative_path(file_path)
                
                # Get current file to update
                try:
                    file_contents = self.repo.get_contents(
                        repo_file_path,
                        ref=branch_name
                    )
                    
                    # Update existing file
                    commit_message = self._generate_commit_message(
                        repo_file_path,
                        updates
                    )
                    
                    self.repo.update_file(
                        path=repo_file_path,
                        message=commit_message,
                        content=new_content,
                        sha=file_contents.sha,
                        branch=branch_name
                    )
                    
                    logger.info(f"  ✓ Updated: {repo_file_path}")
                    
                except GithubException as e:
                    if e.status == 404:
                        # File doesn't exist, create it
                        commit_message = f"Add new manifest: {repo_file_path}"
                        self.repo.create_file(
                            path=repo_file_path,
                            message=commit_message,
                            content=new_content,
                            branch=branch_name
                        )
                        logger.info(f"  ✓ Created: {repo_file_path}")
                    else:
                        raise
                
            except Exception as e:
                logger.error(f"Error committing file {file_path}: {e}")
                continue
    
    def _get_repo_relative_path(self, file_path: str) -> str:
        """Convert absolute file path to repository-relative path"""
        # Try to find the repo root
        # This is a simplified approach - adjust based on your structure
        
        file_path = str(file_path)
        
        # Common patterns
        if '/code/homelab/' in file_path:
            return file_path.split('/code/homelab/')[1]
        elif '/Manifest/' in file_path:
            # If Manifest is at root level
            return file_path.split('/Manifest/')[1]
        else:
            # Try to extract relative path from current directory
            from pathlib import Path
            return Path(file_path).name
    
    def _generate_commit_message(
        self,
        file_path: str,
        updates: List[Dict]
    ) -> str:
        """Generate commit message for file update"""
        # Find updates related to this file
        file_updates = []
        for update_item in updates:
            dep = update_item['deployment']
            upd = update_item['update']
            file_updates.append(
                f"{dep['deployment']}: {dep['current_tag']} → {upd['latest_tag']}"
            )
        
        if file_updates:
            return f"Update images in {file_path}\n\n" + "\n".join(file_updates)
        else:
            return f"Update container images in {file_path}"
    
    def _generate_pr_title(self, updates: List[Dict]) -> str:
        """Generate pull request title"""
        count = len(updates)
        date = datetime.now().strftime('%Y-%m-%d')
        return f"🤖 Weekly Container Image Updates - {date} ({count} updates)"
    
    def _generate_pr_body(self, updates: List[Dict], summary: str) -> str:
        """Generate detailed pull request description"""
        lines = [
            "## 🤖 Automated Container Image Updates",
            "",
            "This PR contains automated updates to container images in Kubernetes manifests.",
            "",
            "### Summary",
            "",
            "```",
            summary,
            "```",
            ""
        ]
        
        # Add AI insights if available
        include_ai = self.config.get('reporting', {}).get('include_ai_analysis', True)
        analyses = [u.get('analysis') for u in updates if u.get('analysis')]
        
        if include_ai and analyses:
            from ai_analyzer import AIAnalyzer
            ai_analyzer = AIAnalyzer(self.config)
            ai_insights = ai_analyzer.generate_pr_insights(analyses)
            if ai_insights:
                lines.append(ai_insights)
        
        lines.append("### Detailed Changes")
        lines.append("")
        
        # Group by namespace
        by_namespace = {}
        for update_item in updates:
            dep = update_item['deployment']
            namespace = dep['namespace']
            if namespace not in by_namespace:
                by_namespace[namespace] = []
            by_namespace[namespace].append(update_item)
        
        for namespace, items in sorted(by_namespace.items()):
            lines.append(f"#### Namespace: `{namespace}`")
            lines.append("")
            
            for item in items:
                dep = item['deployment']
                upd = item['update']
                analysis = item.get('analysis')
                changelog = item.get('changelog')
                
                update_icon = {
                    'major': '🔴',
                    'minor': '🟡',
                    'patch': '🟢'
                }.get(upd['update_type'], '⚪')
                
                # Build update line with risk indicator
                risk_badge = ""
                if analysis:
                    risk_level = analysis.get('risk_level', '')
                    risk_score = analysis.get('risk_score', 0)
                    if risk_level:
                        risk_badge = f" `Risk: {risk_level.upper()} ({risk_score}/10)`"
                
                lines.append(
                    f"- {update_icon} **{dep['deployment']}** "
                    f"`{dep['image']}:{dep['current_tag']}` → "
                    f"`:{upd['latest_tag']}` "
                    f"*({upd['update_type']})*{risk_badge}"
                )
                
                # Add AI analysis details
                if analysis:
                    if analysis.get('breaking_changes'):
                        lines.append("  - ⚠️  **Breaking Changes:**")
                        for change in analysis['breaking_changes'][:3]:  # Limit to 3
                            lines.append(f"    - {change}")
                    
                    if analysis.get('security_updates'):
                        lines.append("  - 🔒 **Security Updates:**")
                        for security in analysis['security_updates'][:3]:
                            lines.append(f"    - {security}")
                    
                    if analysis.get('summary'):
                        lines.append(f"  - 📝 {analysis['summary']}")
                
                # Add changelog link
                if changelog and changelog.get('url'):
                    lines.append(f"  - 📖 [View Changelog]({changelog['url']})")
                
                lines.append("")
            
            lines.append("")
        
        lines.extend([
            "### 🔍 Review Checklist",
            "",
            "- [ ] Review the version changes above",
            "- [ ] Check for any breaking changes in changelogs",
            "- [ ] Verify tests pass",
            "- [ ] Deploy to staging first if available",
            "",
            "---",
            "",
            f"🤖 *Generated by K8s Image Updater Agent on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*"
        ])
        
        return "\n".join(lines)
    
    def _add_labels(self, pr):
        """Add labels to the pull request"""
        try:
            # Try to add common labels
            labels = ['automated', 'dependencies', 'kubernetes']
            
            # Check which labels exist
            existing_labels = {label.name for label in self.repo.get_labels()}
            labels_to_add = [l for l in labels if l in existing_labels]
            
            if labels_to_add:
                pr.add_to_labels(*labels_to_add)
                logger.info(f"Added labels: {', '.join(labels_to_add)}")
        
        except Exception as e:
            logger.warning(f"Could not add labels: {e}")
