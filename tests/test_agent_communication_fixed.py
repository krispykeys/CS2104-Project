"""Test verifying customer agent and property finding capabilities using real APIs."""

import asyncio
import os
import sys
import pytest
from dotenv import load_dotenv
from pathlib import Path

# Add code directory to Python path
test_dir = Path(__file__).parent
project_root = test_dir.parent
code_dir = project_root / "code"
sys.path.insert(0, str(code_dir))

# Load environment variables from project root
load_dotenv(project_root / ".env")

from agents.customer_agent import CustomerAgent
from find_property import ATTOMPropertyFinder


def _have_real_keys() -> bool:
    return bool(os.getenv("GEMINI_API_KEY") and os.getenv("ATTOM_API_KEY"))


@pytest.mark.asyncio
async def test_property_finder():
    """Test that property finder can search for properties"""
    if not _have_real_keys():
        pytest.skip("Skipping: real GEMINI_API_KEY & ATTOM_API_KEY required")

    # Initialize property finder
    finder = ATTOMPropertyFinder()
    
    # Search for properties in Miami, FL
    results = await finder.find_properties(
        city="Miami",
        state="FL",
        max_results=5,
        min_price=200000,
        max_price=500000
    )
    
    # Verify we got results
    assert len(results) > 0, "Should find at least one property"
    
    # Check that results have expected fields
    first_property = results[0]
    assert hasattr(first_property, 'address'), "Property should have address"
    assert hasattr(first_property, 'price'), "Property should have price"
    
    print(f"Found {len(results)} properties in Miami, FL")
    print(f"First property: {first_property.address}")


@pytest.mark.asyncio
async def test_customer_agent_initialization():
    """Test that customer agent can be initialized"""
    if not _have_real_keys():
        pytest.skip("Skipping: real GEMINI_API_KEY & ATTOM_API_KEY required")
    
    # Initialize customer agent
    agent = CustomerAgent(user_id="test-user-123")
    
    # Verify agent was created
    assert agent is not None, "Agent should be created"
    assert agent.user_id == "test-user-123", "Agent should have correct user ID"
    
    print(f"Customer agent initialized successfully for user {agent.user_id}")


if __name__ == "__main__":
    asyncio.run(test_property_finder())