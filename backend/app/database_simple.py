"""
Simplified database setup for development (no PostgreSQL required)
"""
from typing import AsyncGenerator

# Mock database session for development
class MockSession:
    async def commit(self):
        pass

    async def rollback(self):
        pass

    async def close(self):
        pass

    def add(self, instance):
        pass

async def get_db() -> AsyncGenerator:
    """Get database session (mock for now)"""
    session = MockSession()
    try:
        yield session
    finally:
        await session.close()

async def init_db():
    """Initialize database (mock for now)"""
    print("✓ Mock database initialized")

async def close_db():
    """Close database (mock for now)"""
    print("✓ Mock database closed")
