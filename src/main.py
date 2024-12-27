import asyncio
import os
import logging
from dotenv import load_dotenv
from typing import List
from agents.base_agent import BaseAgent
from agents.specification_agent import SpecificationAgent
from agents.developer_agent import DeveloperAgent
from agents.review_agent import ReviewAgent
from agents.merge_agent import MergeAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """Coordinates the execution of all agents in the system."""

    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Get GitHub configuration
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_name = os.getenv('GITHUB_REPO')
        
        if not self.github_token or not self.repo_name:
            raise ValueError("GitHub token and repository name must be configured")

        # Initialize agents
        self.agents: List[BaseAgent] = [
            SpecificationAgent(self.github_token, self.repo_name),
            DeveloperAgent(self.github_token, self.repo_name),
            ReviewAgent(self.github_token, self.repo_name),
            MergeAgent(self.github_token, self.repo_name)
        ]

    async def run_agent_cycle(self) -> None:
        """Run one cycle of all agents."""
        for agent in self.agents:
            try:
                logger.info(f"Starting {agent.role} processing cycle")
                await agent.process()
                logger.info(f"Completed {agent.role} processing cycle")
            except Exception as e:
                logger.error(f"Error in {agent.role}: {str(e)}")

    async def run(self, interval_seconds: int = 300) -> None:
        """Run the orchestrator continuously."""
        logger.info("Starting Agent Orchestrator")
        
        while True:
            try:
                await self.run_agent_cycle()
                logger.info(f"Waiting {interval_seconds} seconds before next cycle")
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in orchestrator cycle: {str(e)}")
                await asyncio.sleep(10)  # Short delay on error before retrying

async def main():
    """Main entry point."""
    try:
        orchestrator = AgentOrchestrator()
        await orchestrator.run()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    # Create example .env file if it doesn't exist
    if not os.path.exists(".env"):
        with open(".env.example", "w") as f:
            f.write("""# GitHub Configuration
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=owner/repository_name
""")
        logger.info("Created .env.example file. Please configure with your GitHub credentials.")
    
    # Run the application
    asyncio.run(main())
