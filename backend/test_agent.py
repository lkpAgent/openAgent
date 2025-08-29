#!/usr/bin/env python3
"""Simple test script to verify search tool functionality."""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_search_tool_directly():
    """Test search tool directly without full agent setup."""
    print("=== Testing Search Tool Directly ===")
    
    try:
        # Import search tool
        from chat_agent.services.agent.tools.search import SearchTool
        
        # Create search tool instance
        search_tool = SearchTool()
        print(f"✓ Search tool created: {search_tool.get_name()}")
        print(f"✓ Description: {search_tool.get_description()}")
        
        # Test search functionality
        query = "今天的A股股市指数"
        print(f"\n=== Testing search with query: '{query}' ===")
        
        result = await search_tool.execute(query=query)
        print(f"✓ Search result: {result}")
        
        if result and result.success:  # Check if search was successful
            print("✓ Search tool is working correctly!")
            print(f"✓ Search summary: {result.result.get('summary', 'No summary available')}")
            return True
        else:
            print(f"⚠ Search tool failed: {result.error if result else 'Unknown error'}")
            return False
            
    except Exception as e:
        print(f"✗ Error during search tool test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tool_registration():
    """Test if tools are properly registered."""
    print("\n=== Testing Tool Registration ===")
    
    try:
        # Import all tools
        from chat_agent.services.agent.tools import (
            CalculatorTool, WeatherTool, SearchTool, DateTimeTool, FileTool
        )
        
        tools = [
            CalculatorTool(),
            WeatherTool(),
            SearchTool(),
            DateTimeTool(),
            FileTool()
        ]
        
        print("✓ Available tools:")
        for tool in tools:
            print(f"  - {tool.get_name()}: {tool.get_description()}")
        
        # Check if search tool is in the list
        search_tools = [tool for tool in tools if tool.get_name() == 'search']
        if search_tools:
            print("✓ Search tool is properly registered!")
            return True
        else:
            print("✗ Search tool is not found in registered tools")
            return False
            
    except Exception as e:
        print(f"✗ Error during tool registration test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("Starting search tool functionality test...")
    
    # Test 1: Tool registration test
    registration_success = test_tool_registration()
    
    # Test 2: Direct search tool test
    tool_success = await test_search_tool_directly()
    
    if registration_success and tool_success:
        print("\n🎉 All tests passed! Search tool is working correctly.")
        print("\n📝 Summary:")
        print("- Search tool is properly registered")
        print("- Search tool can be imported and executed directly")
        print("- When you ask '今天的A股股市是多少' with use_agent=True, the search tool should be called")
        print("\n💡 To test the full integration:")
        print("1. Make sure the backend server is running (port 8001)")
        print("2. Send a POST request to /api/chat with use_agent=True")
        print("3. Include a message like '今天的A股股市是多少？'")
        return True
    elif registration_success:
        print("\n⚠ Search tool is registered but execution may have issues.")
        return False
    else:
        print("\n❌ Search tool test failed!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1)