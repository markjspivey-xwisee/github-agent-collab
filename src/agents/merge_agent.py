from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .base_agent import BaseAgent

class MergeAgent(BaseAgent):
    """Agent responsible for making final decisions on merging pull requests."""

    @property
    def role(self) -> str:
        return "MergeAgent"

    async def process(self) -> None:
        """Process pull requests and make merge decisions."""
        open_prs = self.get_open_prs()
        for pr in open_prs:
            await self.evaluate_pr_for_merge(pr)

    async def evaluate_pr_for_merge(self, pr: Dict) -> None:
        """Evaluate a pull request for merging."""
        pr_number = pr["number"]
        github_pr = self.repo.get_pull(pr_number)

        # Skip if PR is not approved or has pending reviews
        if not self.is_pr_approved(github_pr):
            return

        # Check merge criteria
        merge_status = await self.check_merge_criteria(github_pr)
        
        if merge_status["can_merge"]:
            # Merge the PR
            commit_message = self.generate_merge_commit_message(github_pr, merge_status)
            self.merge_pr(pr_number, commit_message)
        else:
            # Comment on why PR cannot be merged
            comment = self.generate_blocking_comment(merge_status)
            self.comment_on_pr(pr_number, comment)

    def is_pr_approved(self, pr) -> bool:
        """Check if PR has necessary approvals."""
        reviews = pr.get_reviews()
        latest_reviews = {}
        
        # Get latest review from each reviewer
        for review in reviews:
            latest_reviews[review.user.login] = review.state

        # Count approvals
        approvals = sum(1 for state in latest_reviews.values() 
                       if state == "APPROVED")
        
        # Require at least one approval and no pending changes
        return (approvals >= 1 and 
                "CHANGES_REQUESTED" not in latest_reviews.values())

    async def check_merge_criteria(self, pr) -> Dict:
        """Check various criteria for merging."""
        status = {
            "can_merge": True,
            "checks_passed": False,
            "tests_passed": False,
            "review_requirements_met": False,
            "branch_up_to_date": False,
            "blocking_issues": []
        }

        # Check if CI checks are passing
        checks = pr.get_commits().reversed[0].get_check_runs()
        status["checks_passed"] = all(check.conclusion == "success" 
                                    for check in checks)
        if not status["checks_passed"]:
            status["blocking_issues"].append("CI checks must pass")
            status["can_merge"] = False

        # Check if tests are passing
        test_check = next((check for check in checks 
                          if check.name.lower().startswith("test")), None)
        status["tests_passed"] = test_check and test_check.conclusion == "success"
        if not status["tests_passed"]:
            status["blocking_issues"].append("All tests must pass")
            status["can_merge"] = False

        # Check review requirements
        reviews = pr.get_reviews()
        review_states = [review.state for review in reviews]
        status["review_requirements_met"] = (
            review_states.count("APPROVED") >= 1 and
            "CHANGES_REQUESTED" not in review_states
        )
        if not status["review_requirements_met"]:
            status["blocking_issues"].append("Required reviews must be approved")
            status["can_merge"] = False

        # Check if branch is up to date
        base = pr.base.repo.get_branch(pr.base.ref)
        status["branch_up_to_date"] = pr.base.sha == base.commit.sha
        if not status["branch_up_to_date"]:
            status["blocking_issues"].append("Branch must be up to date with base")
            status["can_merge"] = False

        return status

    def generate_merge_commit_message(self, pr, merge_status: Dict) -> str:
        """Generate a detailed merge commit message."""
        message_parts = [
            f"Merge pull request #{pr.number} from {pr.head.ref}",
            "",
            pr.title,
            "",
            "# Merge Criteria",
            f"- CI Checks: {'✅' if merge_status['checks_passed'] else '❌'}",
            f"- Tests: {'✅' if merge_status['tests_passed'] else '❌'}",
            f"- Reviews: {'✅' if merge_status['review_requirements_met'] else '❌'}",
            f"- Branch Status: {'✅' if merge_status['branch_up_to_date'] else '❌'}",
            "",
            "# Changes",
            pr.body or "No description provided.",
            "",
            "# Reviews",
        ]

        # Add review information
        reviews = pr.get_reviews()
        for review in reviews:
            message_parts.append(
                f"- {review.user.login}: {review.state}"
            )

        return "\n".join(message_parts)

    def generate_blocking_comment(self, merge_status: Dict) -> str:
        """Generate a comment explaining why PR cannot be merged."""
        comment_parts = [
            "# 🚫 Cannot Merge Pull Request",
            "",
            "The following criteria must be met before merging:",
            ""
        ]

        for issue in merge_status["blocking_issues"]:
            comment_parts.append(f"- ❌ {issue}")

        comment_parts.extend([
            "",
            "Please address these issues and request a new review."
        ])

        return "\n".join(comment_parts)
