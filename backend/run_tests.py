#!/usr/bin/env python
"""
Test Runner for EcomoveX Backend
Runs all repository and service tests
"""
import sys
import asyncio
import asyncpg
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

async def create_test_databases():
    """Create test databases if they don't exist"""
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="142857",
        database="postgres"
    )
    
    try:
        # Check and create test user database
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'test_ecomovex_users'"
        )
        if not exists:
            await conn.execute('CREATE DATABASE test_ecomovex_users')
            print("✅ Created test user database")
        else:
            print("ℹ️  Test user database already exists")
        
        # Check and create test destination database
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'test_ecomovex_destinations'"
        )
        if not exists:
            await conn.execute('CREATE DATABASE test_ecomovex_destinations')
            print("✅ Created test destination database")
        else:
            print("ℹ️  Test destination database already exists")
            
    finally:
        await conn.close()

def run_tests():
    """Run all tests using pytest"""
    import pytest
    
    print("\n" + "="*70)
    print("  EcomoveX Backend Tests")
    print("="*70 + "\n")
    
    # Run pytest with verbose output
    exit_code = pytest.main([
        "tests/",
        "-v",
        "--tb=short",
        "--color=yes",
        "-s"
    ])
    
    return exit_code

if __name__ == "__main__":
    print("\n🔧 Setting up test databases...")
    asyncio.run(create_test_databases())
    
    print("\n🧪 Running tests...\n")
    exit_code = run_tests()
    
    if exit_code == 0:
        print("\n" + "="*70)
        print("  ✅ ALL TESTS PASSED!")
        print("="*70 + "\n")
    else:
        print("\n" + "="*70)
        print("  ❌ SOME TESTS FAILED")
        print("="*70 + "\n")
    
    sys.exit(exit_code)
