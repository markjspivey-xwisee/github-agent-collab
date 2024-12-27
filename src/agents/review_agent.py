from typing import List, Dict, Set
import re
from .base_agent import BaseAgent

class ReviewAgent(BaseAgent):
    """Agent responsible for reviewing pull requests and providing feedback."""

    @property
    def role(self) -> str:
        return "ReviewAgent"

    async def process(self) -> None:
        """Process open pull requests and provide reviews."""
        open_prs = self.get_open_prs()
        for pr in open_prs:
            await self.review_pull_request(pr)

    async def review_pull_request(self, pr: Dict) -> None:
        """Review a specific pull request and provide feedback."""
        pr_number = pr["number"]
        
        # Get PR details from GitHub
        github_pr = self.repo.get_pull(pr_number)
        
        # Skip if PR has already been reviewed by this agent
        if self.has_reviewed_pr(github_pr):
            return

        # Perform various checks
        review_comments = []
        
        # Check commit messages
        commit_issues = self.check_commit_messages(github_pr)
        if commit_issues:
            review_comments.extend(commit_issues)

        # Check code style and patterns
        code_issues = await self.check_code(github_pr)
        if code_issues:
            review_comments.extend(code_issues)

        # Check tests
        test_issues = await self.check_tests(github_pr)
        if test_issues:
            review_comments.extend(test_issues)

        # Submit review
        if review_comments:
            review_body = "## Code Review Feedback\n\n" + "\n".join(review_comments)
            github_pr.create_review(
                body=review_body,
                event="REQUEST_CHANGES" if any(self.is_blocking_issue(c) for c in review_comments) else "COMMENT"
            )
        else:
            github_pr.create_review(
                body="Code looks good! All checks passed.",
                event="APPROVE"
            )

    def has_reviewed_pr(self, pr) -> bool:
        """Check if this agent has already reviewed the PR."""
        reviews = pr.get_reviews()
        bot_username = self.github.get_user().login
        return any(review.user.login == bot_username for review in reviews)

    def check_commit_messages(self, pr) -> List[str]:
        """Check commit message formatting and content."""
        issues = []
        commits = pr.get_commits()
        
        for commit in commits:
            msg = commit.commit.message
            
            # Check conventional commit format
            if not re.match(r'^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+', msg):
                issues.append(f"❌ Commit `{commit.sha[:7]}` doesn't follow conventional commit format")
            
            # Check message length
            if len(msg.split('\n')[0]) > 72:
                issues.append(f"❌ Commit `{commit.sha[:7]}` has too long subject line (>72 chars)")

        return issues

    async def check_code(self, pr) -> List[str]:
        """Check code style, patterns, and potential issues."""
        issues = []
        files = pr.get_files()
        
        for file in files:
            if file.filename.endswith('.py'):
                # Check Python imports
                if 'import *' in file.patch:
                    issues.append(f"⚠️ Avoid using wildcard imports in `{file.filename}`")
                
                # Check function/class documentation
                if 'def ' in file.patch or 'class ' in file.patch:
                    if '"""' not in file.patch:
                        issues.append(f"⚠️ Missing docstrings in `{file.filename}`")
                
                # Check line length
                long_lines = [line for line in file.patch.split('\n') 
                            if line.startswith('+') and len(line) > 88]
                if long_lines:
                    issues.append(f"⚠️ Lines too long in `{file.filename}` (>88 chars)")

                # Check error handling
                if 'except:' in file.patch:
                    issues.append(f"❌ Bare except clause found in `{file.filename}`. Please specify exception types.")

        return issues

    async def check_tests(self, pr) -> List[str]:
        """Check test coverage and quality."""
        issues = []
        files = pr.get_files()
        
        # Track which source files have corresponding test files
        source_files: Set[str] = set()
        test_files: Set[str] = set()
        
        for file in files:
            if file.filename.startswith('src/') and file.filename.endswith('.py'):
                source_files.add(file.filename)
            elif file.filename.startswith('tests/') and file.filename.endswith('.py'):
                test_files.add(file.filename)

        # Check for missing test files
        for source_file in source_files:
            expected_test = f"tests/{source_file[4:]}"  # Convert src/path/file.py to tests/path/file.py
            if expected_test not in test_files:
                issues.append(f"❌ Missing tests for `{source_file}`")

        # Check test quality
        for test_file in test_files:
            content = self.repo.get_contents(test_file, ref=pr.head.sha).decoded_content.decode()
            
            # Check for assert statements
            if 'assert' not in content:
                issues.append(f"❌ No assertions found in `{test_file}`")
            
            # Check for test function naming
            if not re.search(r'def test_\w+', content):
                issues.append(f"⚠️ Test functions in `{test_file}` should start with 'test_'")
            
            # Check for pytest fixtures usage
            if 'fixture' not in content and 'pytest' in content:
                issues.append(f"💡 Consider using pytest fixtures in `{test_file}` for better test organization")

        return issues

    def is_blocking_issue(self, comment: str) -> bool:
        """Determine if an issue should block PR approval."""
        return comment.startswith('❌')
