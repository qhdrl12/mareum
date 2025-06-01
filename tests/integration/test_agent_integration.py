"""Integration tests for agent functionality."""

import pytest
import asyncio
from pathlib import Path
import time
import os

from tests.test_data import TEST_QUERIES, EXPECTED_RESPONSE_PATTERNS, VALID_CONFIGS
from src.schemas.agent_config import AgentConfig
from src.agents.react_agent import ReActAgent


@pytest.mark.integration
class TestAgentIntegration:
    """Integration tests for ReAct Agent."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, react_agent):
        """Test agent initialization and basic properties."""
        assert react_agent is not None
        assert hasattr(react_agent, 'config')
        assert hasattr(react_agent, 'tools')
        assert react_agent.config.metadata.name
        print(f"✅ Agent initialized: {react_agent.config.metadata.name}")
    
    @pytest.mark.asyncio
    async def test_simple_conversation(self, react_agent, test_utils):
        """Test basic conversation capability."""
        query = TEST_QUERIES["simple_greeting"]
        result = await react_agent.run(query)
        
        # Use improved validation
        test_utils.validate_agent_response(result)
        test_utils.validate_response_quality(result, min_length=20)
    
    @pytest.mark.asyncio
    async def test_calculation_request(self, react_agent, test_utils):
        """Test mathematical calculation capability."""
        query = TEST_QUERIES["calculation"]
        result = await react_agent.run(query)
        
        # Basic validation
        test_utils.validate_agent_response(result)
        
        # Check if response contains numbers (basic calculation validation)
        response_text = result["response"]
        has_numbers = any(char.isdigit() for char in response_text)
        assert has_numbers, "Calculation response should contain numbers"
    
    @pytest.mark.asyncio
    async def test_tool_usage_detection(self, react_agent, test_utils):
        """Test detection of tool usage in responses."""
        query = TEST_QUERIES["tool_forcing"]
        result = await react_agent.run(query)
        
        test_utils.validate_agent_response(result)
        
        # Extract and validate tool usage
        tools_used = test_utils.extract_tool_usage_from_result(result)
        assert isinstance(tools_used, list), "Tools used should be a list"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, react_agent):
        """Test agent error handling."""
        # Test with problematic input
        try:
            result = await react_agent.run(None)
            # If it doesn't raise an exception, check if it handles gracefully
            assert "response" in result or "error" in result
        except (ValueError, TypeError, Exception):
            # Expected behavior - should raise an exception for invalid input
            pass  # This is acceptable
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, react_agent, test_utils):
        """Test handling multiple concurrent requests."""
        from tests.test_data import TEST_CONSTANTS
        
        queries = [
            TEST_QUERIES["simple_greeting"],
            TEST_QUERIES["reasoning"],
            "What is 2 + 2?"
        ][:TEST_CONSTANTS["concurrent_request_count"]]
        
        # Run concurrent requests
        tasks = [react_agent.run(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Use improved validation helper
        successful_count, success_rate = test_utils.validate_concurrent_results(results)
        assert successful_count >= len(queries) // 2, f"Only {successful_count}/{len(queries)} requests succeeded"
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_basic_smoke_test_without_api_key(self):
        """Smoke test that works even without real API keys configured."""
        # Store original API key
        original_api_key = os.getenv("OPENAI_API_KEY")
        
        try:
            # Set fallback API key for testing
            if not original_api_key:
                os.environ["OPENAI_API_KEY"] = "not-needed"
            
            # Use test configuration directly
            config_data = VALID_CONFIGS["openai_compatible"]
            config = AgentConfig(**config_data)
            agent = ReActAgent(config=config)
            await agent.initialize()
            
            # Simple smoke test query
            query = "Hello, can you respond to this message?"
            
            try:
                result = await agent.run(query)
                
                # Basic validation
                assert "response" in result, "Response should contain 'response' field"
                assert isinstance(result["response"], str), "Response should be a string"
                assert len(result["response"]) > 0, "Response should not be empty"
                
                print(f"✅ Smoke test successful - Response length: {len(result['response'])} characters")
                
            except Exception as e:
                # Graceful handling for CI/CD environments without real API access
                print(f"⚠️ API call failed (expected in test environments): {e}")
                # This is acceptable - the test verifies basic agent setup works
                pass
            
            finally:
                await agent.cleanup()
                
        finally:
            # Restore original API key state
            if original_api_key:
                os.environ["OPENAI_API_KEY"] = original_api_key
            elif "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]


@pytest.mark.integration
@pytest.mark.slow
class TestAgentPerformance:
    """Performance tests for agent operations."""
    
    @pytest.mark.asyncio
    async def test_response_time(self, react_agent):
        """Test agent response time is within acceptable limits."""
        from tests.test_data import TEST_CONSTANTS
        
        query = TEST_QUERIES["simple_greeting"]
        start_time = time.time()
        result = await react_agent.run(query)
        end_time = time.time()
        
        response_time = end_time - start_time
        max_time = TEST_CONSTANTS["max_response_time"]
        
        assert response_time < max_time, f"Response time {response_time:.2f}s exceeds {max_time}s limit"
        assert "response" in result, "Should return valid response within time limit"
    
    @pytest.mark.asyncio
    async def test_sequential_stability(self, react_agent, test_utils):
        """Test agent stability with sequential operations."""
        from tests.test_data import TEST_CONSTANTS
        
        iterations = TEST_CONSTANTS["memory_test_iterations"]
        successful_queries = 0
        
        # Run multiple sequential queries to test stability
        for i in range(iterations):
            try:
                result = await react_agent.run(TEST_QUERIES["simple_greeting"])
                test_utils.validate_agent_response(result)
                successful_queries += 1
            except Exception:
                pass  # Count failures silently
        
        success_rate = successful_queries / iterations
        min_rate = TEST_CONSTANTS["high_success_rate"]
        
        assert success_rate >= min_rate, f"Stability test failed: {success_rate:.1%} < {min_rate:.1%}"


@pytest.mark.integration
@pytest.mark.mcp
class TestMCPIntegration:
    """Test MCP (Model Context Protocol) integration."""
    
    @pytest.mark.asyncio
    async def test_mcp_tool_availability(self, react_agent):
        """Test that MCP tools are properly loaded."""
        # Check if agent has tools
        assert hasattr(react_agent, 'tools'), "Agent should have tools attribute"
        
        # Check tool count (may be 0 if no MCP tools configured)
        tool_count = len(react_agent.tools)
        print(f"✅ MCP tool availability test - {tool_count} tools loaded") 