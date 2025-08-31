#!/usr/bin/env python3
"""Test authentication."""

from backend.chat_agent.db.database import get_db
from backend.chat_agent.services.auth import AuthService

def test_auth():
    """Test authentication."""
    db = next(get_db())
    try:
        # Test authenticate_user_by_email
        user = AuthService.authenticate_user_by_email(db, 'demo@example.com', '123456')
        if user:
            print(f'Authentication successful: {user.username} ({user.email})')
        else:
            print('Authentication failed')
    finally:
        db.close()

if __name__ == '__main__':
    test_auth()