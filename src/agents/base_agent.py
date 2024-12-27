from abc import ABC, abstractmethod
from github import Github, Auth
from typing import Optional, List, Dict
import os
import logging

class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, github_token: str, repo_name: str):
        auth = Auth.Token(github_token)
        self.github = Github(auth=auth)
        self.repo = self.github.get_repo(repo_name)
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def role(self) -> str:
        """Define the agent's role in the system."""
        pass

    @abstractmethod
    async def process(self) -> None:
        """Main processing loop for the agent."""
        pass

    def create_pull_request(self, branch: str, title: str, body: str, base: str = "main") -> Optional[Dict]:
        """Create a new pull request."""
        try:
            pr = self.repo.create_pull(
                title=title,
                body=body,
                head=branch,
                base=base
            )
            self.logger.info(f"Created PR #{pr.number}: {title}")
            return {
                "number": pr.number,
                "url": pr.html_url,
                "id": pr.id
            }
        except Exception as e:
            self.logger.error(f"Failed to create PR: {str(e)}")
            return None

    def comment_on_pr(self, pr_number: int, comment: str) -> bool:
        """Add a comment to a pull request."""
        try:
            pr = self.repo.get_pull(pr_number)
            pr.create_issue_comment(comment)
            self.logger.info(f"Added comment to PR #{pr_number}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to comment on PR #{pr_number}: {str(e)}")
            return False

    def get_open_prs(self) -> List[Dict]:
        """Get all open pull requests."""
        try:
            prs = self.repo.get_pulls(state='open')
            return [{
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "user": pr.user.login,
                "url": pr.html_url,
                "created_at": pr.created_at.isoformat()
            } for pr in prs]
        except Exception as e:
            self.logger.error(f"Failed to fetch PRs: {str(e)}")
            return []

    def merge_pr(self, pr_number: int, commit_message: str) -> bool:
        """Merge a pull request."""
        try:
            pr = self.repo.get_pull(pr_number)
            pr.merge(commit_message=commit_message)
            self.logger.info(f"Merged PR #{pr_number}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to merge PR #{pr_number}: {str(e)}")
            return False

    def create_branch(self, branch_name: str, from_branch: str = "main") -> bool:
        """Create a new branch from the specified base branch."""
        try:
            base = self.repo.get_branch(from_branch)
            self.repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=base.commit.sha
            )
            self.logger.info(f"Created branch: {branch_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create branch {branch_name}: {str(e)}")
            return False
