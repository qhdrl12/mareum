#!/usr/bin/env python3
"""
Debug script for MCP tool usage testing.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.agents.react_agent import ReActAgent

load_dotenv('.env', override=True)

async def debug_mcp_tool_usage():
    """Debug MCP tool usage with detailed logging."""
    
    print("🔍 Debug MCP Tool Usage")
    print("=" * 50)
    
    # Load MCP agent configuration
    config_path = str(
        Path(__file__).parent.parent.parent
        / "examples"
        / "configs"
        / "mcp_agent.yaml"
    )
    
    print(f"📝 Loading MCP agent: {config_path}")
    
    agent = ReActAgent(config_path=config_path)
    await agent.initialize()
    
    print(f"🤖 Agent: {agent.config.metadata.name}")
    print(f"🧠 Model: {agent.config.model.provider.value}/{agent.config.model.name}")
    print(f"🛠️ Tools: {len(agent.tools)} tools loaded")
    
    # Print tool details
    for tool in agent.tools:
        print(f"   - {tool.name}: {tool.description}")
        print(f"     Type: {type(tool)}")
        print(f"     Has _mcp_tool: {hasattr(tool, '_mcp_tool')}")
    
    # Simple test query
    query = "Calculate 12 * 8"
    print(f"\n🧪 Test Query: {query}")
    print("-" * 40)
    
    try:
        result = await agent.run(query)
        
        print(f"✅ Response: {result.get('response', 'No response')}")
        print(f"\n📊 Full Result Structure:")
        for key, value in result.items():
            if key == 'messages':
                print(f"   {key}: {len(value)} messages")
                for i, msg in enumerate(value):
                    print(f"      Message {i+1}: {type(msg)} - {str(msg)[:100]}...")
            else:
                print(f"   {key}: {value}")
        
        # Check for tool calls in messages
        if "messages" in result:
            print(f"\n🔍 Detailed Message Analysis:")
            for i, message in enumerate(result["messages"]):
                print(f"\nMessage {i+1}:")
                print(f"  Type: {type(message)}")
                print(f"  String representation: {str(message)}")
                
                # Check all attributes
                attrs = [attr for attr in dir(message) if not attr.startswith('_')]
                print(f"  Attributes: {attrs}")
                
                # Check for tool calls
                if hasattr(message, 'tool_calls'):
                    print(f"  tool_calls: {message.tool_calls}")
                    if message.tool_calls:
                        for j, tool_call in enumerate(message.tool_calls):
                            print(f"    Tool Call {j+1}:")
                            print(f"      Function: {tool_call.get('function', {}).get('name', 'Unknown')}")
                            print(f"      Arguments: {tool_call.get('function', {}).get('arguments', 'Unknown')}")
                    
                # Check for additional_kwargs
                if hasattr(message, 'additional_kwargs'):
                    print(f"  additional_kwargs: {message.additional_kwargs}")
                    
                # Check content
                if hasattr(message, 'content'):
                    print(f"  content: {message.content}")
        
        # Additional analysis: Check which tools were actually called
        print(f"\n🛠️ Tool Usage Analysis:")
        actual_tools_used = []
        if "messages" in result:
            for message in result["messages"]:
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    for tool_call in message.tool_calls:
                        if 'function' in tool_call:
                            tool_name = tool_call['function'].get('name', 'Unknown')
                            actual_tools_used.append(tool_name)
        
        if actual_tools_used:
            print(f"  Actually called tools: {actual_tools_used}")
            # Check if the called tools are MCP or builtin
            for tool_name in actual_tools_used:
                matching_tool = None
                for tool in agent.tools:
                    if tool.name == tool_name:
                        matching_tool = tool
                        break
                if matching_tool:
                    print(f"  Tool '{tool_name}' type: {type(matching_tool)}")
                    print(f"  Tool '{tool_name}' is MCP: {hasattr(matching_tool, '_mcp_tool')}")
                else:
                    print(f"  Tool '{tool_name}' not found in agent.tools!")
        else:
            print(f"  No tools were actually called (AI may have calculated directly)")
            print(f"  This means tool_calls: {result.get('tool_calls', 0)} might be counting AI reasoning steps, not actual tool usage")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(debug_mcp_tool_usage()) 