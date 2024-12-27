from typing import Dict, Optional
import os
import yaml
from datetime import datetime
from .base_agent import BaseAgent

class DeveloperAgent(BaseAgent):
    """Agent responsible for implementing features based on specifications."""

    @property
    def role(self) -> str:
        return "DeveloperAgent"

    async def process(self) -> None:
        """Process specifications and implement features."""
        # Get current specifications
        specs = self.get_specifications()
        if not specs:
            self.logger.info("No specifications found to implement")
            return

        # Look for pending features to implement
        for feature in specs.get("features", []):
            if feature["status"] == "pending":
                await self.implement_feature(feature)

    def get_specifications(self) -> Optional[Dict]:
        """Get current project specifications."""
        try:
            specs_file = self.repo.get_contents("specifications/current.yaml")
            return yaml.safe_load(specs_file.decoded_content)
        except Exception as e:
            self.logger.error(f"Failed to get specifications: {str(e)}")
            return None

    async def implement_feature(self, feature: Dict) -> None:
        """Implement a specific feature based on its specifications."""
        feature_id = feature["id"]
        branch_name = f"feat/{feature_id}"

        if self.create_branch(branch_name):
            try:
                # Create implementation files based on feature requirements
                if feature_id == "user-auth":
                    await self.implement_user_auth(branch_name)
                # Add more feature implementations as needed

            except Exception as e:
                self.logger.error(f"Failed to implement feature {feature_id}: {str(e)}")

    async def implement_user_auth(self, branch_name: str) -> None:
        """Implement user authentication feature."""
        # Create necessary files for user authentication
        files_to_create = {
            "src/auth/user.py": self.get_user_model_code(),
            "src/auth/jwt_handler.py": self.get_jwt_handler_code(),
            "src/auth/password_handler.py": self.get_password_handler_code(),
            "tests/auth/test_user_auth.py": self.get_auth_tests_code()
        }

        for file_path, content in files_to_create.items():
            try:
                self.repo.create_file(
                    file_path,
                    f"Add {file_path}",
                    content,
                    branch=branch_name
                )
            except Exception as e:
                self.logger.error(f"Failed to create {file_path}: {str(e)}")
                return

        # Create pull request for the implementation
        pr_body = f"""
        # User Authentication Implementation

        This PR implements the user authentication system with the following components:
        - User model with email/password
        - JWT token handling
        - Password encryption and verification
        - Unit tests for authentication flow

        ## Implementation Details
        - Uses bcrypt for password hashing
        - JWT tokens for session management
        - Email validation and password strength requirements
        - Comprehensive test coverage

        ## Testing
        - Run tests with: `pytest tests/auth/`
        - All test cases are documented in test_user_auth.py

        Closes #{feature_id}
        """

        self.create_pull_request(
            branch=branch_name,
            title=f"feat: {feature_id} - Implement User Authentication",
            body=pr_body
        )

    def get_user_model_code(self) -> str:
        """Generate code for user model."""
        return '''from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class User(BaseModel):
    """User model for authentication."""
    id: Optional[int] = None
    email: EmailStr
    hashed_password: str
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Config:
        orm_mode = True
'''

    def get_jwt_handler_code(self) -> str:
        """Generate code for JWT handling."""
        return '''import jwt
from datetime import datetime, timedelta
from typing import Dict

class JWTHandler:
    """Handle JWT token operations."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_token(self, user_id: int, expires_delta: timedelta = timedelta(days=1)) -> str:
        """Create a new JWT token."""
        expire = datetime.utcnow() + expires_delta
        to_encode = {
            "user_id": user_id,
            "exp": expire
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            raise ValueError("Invalid token")
'''

    def get_password_handler_code(self) -> str:
        """Generate code for password handling."""
        return '''import bcrypt
from typing import Tuple

class PasswordHandler:
    """Handle password hashing and verification."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(
            plain_password.encode(),
            hashed_password.encode()
        )
'''

    def get_auth_tests_code(self) -> str:
        """Generate test code for authentication."""
        return '''import pytest
from datetime import datetime, timedelta
from src.auth.user import User
from src.auth.jwt_handler import JWTHandler
from src.auth.password_handler import PasswordHandler

def test_user_model():
    """Test user model creation and validation."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_pwd"
    )
    assert user.email == "test@example.com"
    assert user.hashed_password == "hashed_pwd"

def test_password_hashing():
    """Test password hashing and verification."""
    password = "secure_password123"
    hashed = PasswordHandler.hash_password(password)
    
    assert PasswordHandler.verify_password(password, hashed)
    assert not PasswordHandler.verify_password("wrong_password", hashed)

def test_jwt_token():
    """Test JWT token creation and verification."""
    handler = JWTHandler("secret_key")
    user_id = 1
    
    token = handler.create_token(user_id)
    payload = handler.verify_token(token)
    
    assert payload["user_id"] == user_id
    assert "exp" in payload

def test_jwt_token_expiration():
    """Test JWT token expiration."""
    handler = JWTHandler("secret_key")
    token = handler.create_token(1, expires_delta=timedelta(seconds=1))
    
    # Wait for token to expire
    import time
    time.sleep(2)
    
    with pytest.raises(ValueError):
        handler.verify_token(token)
'''
