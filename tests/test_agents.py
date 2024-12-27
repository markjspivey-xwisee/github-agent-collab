import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from github import Github, Auth, GithubException
from src.agents.specification_agent import SpecificationAgent
from src.agents.developer_agent import DeveloperAgent
from src.agents.review_agent import ReviewAgent
from src.agents.merge_agent import MergeAgent

class MockAuth(Auth.Auth):
    """Mock Auth class that inherits from github.Auth.Auth."""
    def __init__(self, token):
        self._token = token

    @property
    def token(self) -> str:
        return self._token

    @property
    def token_type(self) -> str:
        return "Bearer"

    @property
    def token_value(self) -> str:
        return self._token

@pytest.fixture
def mock_auth():
    """Create a mock GitHub Auth token."""
    with patch('github.Auth.Token') as mock_auth:
        mock_auth.return_value = MockAuth("fake-token")
        return mock_auth

@pytest.fixture
def mock_github(mock_auth):
    """Create a mock GitHub client."""
    mock = Mock(spec=Github)
    mock.get_user.return_value.login = "test-bot"
    # Setup the mock repository
    mock_repo = Mock()
    mock_repo.get_pulls.return_value = []
    mock.get_repo.return_value = mock_repo
    return mock

@pytest.fixture
def mock_repo(mock_github):
    """Get the mock repository from mock_github."""
    return mock_github.get_repo.return_value

class TestSpecificationAgent:
    """Test suite for SpecificationAgent."""

    @pytest.fixture
    def agent(self, mock_github, mock_auth):
        with patch('github.Github', return_value=mock_github):
            with patch('github.Auth.Token', return_value=mock_auth.return_value):
                return SpecificationAgent("fake-token", "owner/repo")

    @pytest.mark.asyncio
    async def test_create_initial_specifications(self, agent):
        """Test creation of initial specifications."""
        # Mock successful branch creation
        agent.create_branch = Mock(return_value=True)
        
        # Mock file creation
        agent.repo.create_file = Mock()
        
        # Mock PR creation
        agent.create_pull_request = Mock()
        
        await agent.create_initial_specifications()
        
        # Verify branch was created
        agent.create_branch.assert_called_once()
        
        # Verify file was created
        agent.repo.create_file.assert_called_once()
        
        # Verify PR was created
        agent.create_pull_request.assert_called_once()
        
        # Check specification content
        spec_content = agent.repo.create_file.call_args[0][2]
        assert "user-auth" in spec_content
        assert "JWT token implementation" in spec_content

class TestDeveloperAgent:
    """Test suite for DeveloperAgent."""

    @pytest.fixture
    def agent(self, mock_github, mock_auth):
        with patch('github.Github', return_value=mock_github):
            with patch('github.Auth.Token', return_value=mock_auth.return_value):
                return DeveloperAgent("fake-token", "owner/repo")

    @pytest.mark.asyncio
    async def test_implement_feature(self, agent):
        """Test feature implementation."""
        feature = {
            "id": "user-auth",
            "title": "User Authentication",
            "status": "pending"
        }
        
        # Mock successful branch creation
        agent.create_branch = Mock(return_value=True)
        
        # Mock file creation
        agent.repo.create_file = Mock()
        
        # Mock PR creation
        agent.create_pull_request = Mock()
        
        await agent.implement_feature(feature)
        
        # Verify branch was created
        agent.create_branch.assert_called_once()
        
        # Verify files were created
        assert agent.repo.create_file.call_count == 4  # user.py, jwt_handler.py, password_handler.py, test_user_auth.py
        
        # Verify PR was created
        agent.create_pull_request.assert_called_once()

class TestReviewAgent:
    """Test suite for ReviewAgent."""

    @pytest.fixture
    def agent(self, mock_github, mock_auth):
        with patch('github.Github', return_value=mock_github):
            with patch('github.Auth.Token', return_value=mock_auth.return_value):
                return ReviewAgent("fake-token", "owner/repo")

    def test_check_commit_messages(self, agent):
        """Test commit message validation."""
        # Mock PR with commits
        pr = Mock()
        commit1 = Mock()
        commit1.commit.message = "feat: add user authentication"
        commit1.sha = "abc123"
        
        commit2 = Mock()
        commit2.commit.message = "invalid commit message"
        commit2.sha = "def456"
        
        pr.get_commits.return_value = [commit1, commit2]
        
        issues = agent.check_commit_messages(pr)
        
        # Should flag the invalid commit message
        assert len(issues) == 1
        assert "def456" in issues[0]
        assert "conventional commit format" in issues[0]

class TestMergeAgent:
    """Test suite for MergeAgent."""

    @pytest.fixture
    def agent(self, mock_github, mock_auth):
        with patch('github.Github', return_value=mock_github):
            with patch('github.Auth.Token', return_value=mock_auth.return_value):
                return MergeAgent("fake-token", "owner/repo")

    @pytest.mark.asyncio
    async def test_evaluate_pr_for_merge(self, agent):
        """Test PR evaluation for merging."""
        pr_dict = {"number": 1}
        
        # Mock PR
        pr = Mock()
        pr.number = 1
        pr.title = "feat: add user auth"
        pr.body = "Implements user authentication"
        pr.head.ref = "feature-branch"
        
        # Mock PR retrieval
        agent.repo.get_pull.return_value = pr
        
        # Mock approval status
        agent.is_pr_approved = Mock(return_value=True)
        
        # Mock merge criteria check
        merge_status = {
            "can_merge": True,
            "checks_passed": True,
            "tests_passed": True,
            "review_requirements_met": True,
            "branch_up_to_date": True,
            "blocking_issues": []
        }
        agent.check_merge_criteria = AsyncMock(return_value=merge_status)
        
        # Mock merge operation
        agent.merge_pr = Mock()
        
        await agent.evaluate_pr_for_merge(pr_dict)
        
        # Verify PR was merged
        agent.merge_pr.assert_called_once()
        
        # Check merge commit message
        commit_msg = agent.merge_pr.call_args[0][1]
        assert "feat: add user auth" in commit_msg
        assert "✅" in commit_msg  # Should show passing checks
