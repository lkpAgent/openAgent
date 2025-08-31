#!/usr/bin/env python3
"""Test password verification."""

from backend.chat_agent.db.database import get_db
from backend.chat_agent.models.user import User
from backend.chat_agent.services.auth import AuthService

def test_password():
    """Test password verification."""
    db = next(get_db())
    try:
        user = db.query(User).filter(User.email == 'demo@example.com').first()
        if user:
            print(f'User found: {user.username}')
            print(f'Hashed password: {user.hashed_password[:50]}...')
            result = AuthService.verify_password('123456', user.hashed_password)
            print(f'Password verification result: {result}')
        else:
            print('User not found')
    finally:
        db.close()

if __name__ == '__main__':
    test_password()