from typing import List, Dict
import os
import yaml
from datetime import datetime
from .base_agent import BaseAgent

class SpecificationAgent(BaseAgent):
    """Agent responsible for creating and maintaining project specifications."""

    @property
    def role(self) -> str:
        return "SpecificationAgent"

    async def process(self) -> None:
        """Process specifications and create/update them as needed."""
        # Check existing specifications
        specs = self.get_current_specifications()
        
        # Create or update specifications based on project needs
        if not specs:
            await self.create_initial_specifications()
        else:
            await self.review_and_update_specifications(specs)

    def get_current_specifications(self) -> List[Dict]:
        """Retrieve current specifications from the repository."""
        try:
            specs_file = self.repo.get_contents("specifications/current.yaml")
            return yaml.safe_load(specs_file.decoded_content)
        except:
            return []

    async def create_initial_specifications(self) -> None:
        """Create initial project specifications."""
        initial_specs = {
            "version": "1.0.0",
            "last_updated": datetime.utcnow().isoformat(),
            "features": [
                {
                    "id": "user-auth",
                    "title": "User Authentication",
                    "priority": "high",
                    "status": "pending",
                    "description": "Implement user authentication system",
                    "requirements": [
                        "Email/password authentication",
                        "Password reset functionality",
                        "JWT token implementation",
                        "User session management"
                    ],
                    "acceptance_criteria": [
                        "Users can register with email/password",
                        "Users can login with credentials",
                        "Users can reset passwords",
                        "JWT tokens are properly handled"
                    ],
                    "test_requirements": [
                        "Unit tests for auth functions",
                        "Integration tests for auth flow",
                        "Security testing for password handling"
                    ]
                }
            ]
        }

        # Create a new branch for specifications
        branch_name = f"specs/initial-specifications"
        if self.create_branch(branch_name):
            try:
                # Create specifications directory and file
                specs_yaml = yaml.dump(initial_specs, default_flow_style=False)
                self.repo.create_file(
                    "specifications/current.yaml",
                    "Initial project specifications",
                    specs_yaml,
                    branch=branch_name
                )

                # Create pull request
                pr_body = """
                # Initial Project Specifications
                
                This PR introduces the initial project specifications including:
                - User Authentication feature specification
                - Test requirements
                - Acceptance criteria
                
                Please review the specifications and provide feedback.
                """

                self.create_pull_request(
                    branch=branch_name,
                    title="Initial Project Specifications",
                    body=pr_body
                )

            except Exception as e:
                self.logger.error(f"Failed to create specifications: {str(e)}")

    async def review_and_update_specifications(self, current_specs: List[Dict]) -> None:
        """Review and update existing specifications based on project progress."""
        # Check for completed features
        updated = False
        for feature in current_specs["features"]:
            if feature["status"] == "pending":
                # Check if feature implementation PR exists
                prs = self.repo.get_pulls(state='all')
                for pr in prs:
                    if pr.title.lower().startswith(f"feat: {feature['id']}"):
                        if pr.merged:
                            feature["status"] = "completed"
                            updated = True
                            break
                        elif pr.state == "open":
                            feature["status"] = "in-progress"
                            updated = True
                            break

        if updated:
            branch_name = f"specs/update-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            if self.create_branch(branch_name):
                try:
                    current_specs["last_updated"] = datetime.utcnow().isoformat()
                    specs_yaml = yaml.dump(current_specs, default_flow_style=False)
                    
                    # Update specifications file
                    specs_file = self.repo.get_contents("specifications/current.yaml")
                    self.repo.update_file(
                        specs_file.path,
                        "Update specifications status",
                        specs_yaml,
                        specs_file.sha,
                        branch=branch_name
                    )

                    # Create pull request
                    pr_body = """
                    # Specification Status Update
                    
                    This PR updates the status of features based on implementation progress.
                    """

                    self.create_pull_request(
                        branch=branch_name,
                        title="Update Specification Status",
                        body=pr_body
                    )

                except Exception as e:
                    self.logger.error(f"Failed to update specifications: {str(e)}")
