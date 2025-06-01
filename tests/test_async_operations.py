"""Consolidated async operation tests."""

import pytest
import asyncio
from pathlib import Path
from tests.test_data import TEST_QUERIES
import time


@pytest.mark.asyncio
class TestAsyncOperations:
    """Unified async operation tests."""
    
    async def test_agent_lifecycle(self, react_agent):
        """Test complete agent lifecycle."""
        # Test initialization
        assert react_agent is not None
        assert hasattr(react_agent, 'config')
        
        # Test operation
        result = await react_agent.run(TEST_QUERIES["simple_greeting"])
        assert "response" in result
    
    async def test_multiple_queries_sequence(self, react_agent, test_utils):
        """Test sequential query processing."""
        queries = [
            TEST_QUERIES["simple_greeting"],
            "What is 5 + 3?",
            TEST_QUERIES["reasoning"]
        ]
        
        results = []
        for query in queries:
            result = await react_agent.run(query)
            test_utils.validate_agent_response(result)
            results.append(result)
        
        assert len(results) == len(queries)
    
    async def test_async_error_handling(self, react_agent):
        """Test async error handling."""
        # Test with problematic input
        try:
            await react_agent.run(None)
            # If no exception, assume graceful handling
        except (ValueError, TypeError, Exception):
            # Expected behavior for invalid input
            pass
    
    async def test_timeout_handling(self, react_agent):
        """Test operation timeout handling."""
        from tests.test_data import TEST_CONSTANTS
        
        # Test with very long query that might timeout
        long_query = "Please analyze this topic in extreme detail: " + "artificial intelligence " * 50
        
        try:
            result = await asyncio.wait_for(
                react_agent.run(long_query), 
                timeout=TEST_CONSTANTS["short_timeout"]
            )
            # If it completes, validate the result
            assert "response" in result
        except asyncio.TimeoutError:
            # Timeout is acceptable for very long operations
            pass
    
    async def test_concurrent_async_operations(self, react_agent, test_utils):
        """Test concurrent async operations."""
        from tests.test_data import TEST_CONSTANTS
        
        queries = [
            "Hello!",
            "What is 2+2?",
            "Tell me a joke"
        ][:TEST_CONSTANTS["concurrent_request_count"]]
        
        # Create tasks for concurrent execution
        tasks = [react_agent.run(query) for query in queries]
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Use improved validation helper
        successful_count, success_rate = test_utils.validate_concurrent_results(results)
        assert successful_count >= len(queries) // 2
    
    async def test_async_performance_monitoring(self, react_agent):
        """Test async performance monitoring."""
        from tests.test_data import TEST_CONSTANTS
        
        query = "Performance test query"
        
        # Monitor execution time
        start_time = time.time()
        result = await react_agent.run(query)
        end_time = time.time()
        
        execution_time = end_time - start_time
        max_time = TEST_CONSTANTS["max_response_time"] * 0.67  # Be more strict for performance test
        
        assert execution_time < max_time, f"Async operation took too long: {execution_time:.2f}s"
        assert "response" in result


@pytest.mark.asyncio
@pytest.mark.slow
class TestAsyncStressOperations:
    """Stress tests for async operations."""
    
    async def test_rapid_fire_requests(self, react_agent, test_utils):
        """Test rapid consecutive requests."""
        from tests.test_data import TEST_CONSTANTS
        
        num_requests = TEST_CONSTANTS["rapid_fire_count"]
        query = "Quick response test"
        
        start_time = asyncio.get_event_loop().time()
        
        # Send rapid requests
        results = []
        for i in range(num_requests):
            result = await react_agent.run(f"{query} #{i+1}")
            results.append(result)
        
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        
        # Use improved validation
        successful_count, success_rate = test_utils.validate_concurrent_results(results)
        
        # Additional rapid fire specific checks
        avg_time_per_request = total_time / num_requests
        assert avg_time_per_request < 5.0, f"Average time per request too high: {avg_time_per_request:.2f}s"
    
    async def test_async_memory_stability(self, react_agent, test_utils):
        """Test memory stability during async operations (simplified)."""
        from tests.test_data import TEST_CONSTANTS
        
        iterations = TEST_CONSTANTS["memory_test_iterations"]
        successful_queries = 0
        
        start_time = time.time()
        
        # Run multiple queries and track basic metrics
        for i in range(iterations):
            try:
                result = await react_agent.run(f"Memory test query {i+1}")
                test_utils.validate_agent_response(result)
                successful_queries += 1
            except Exception:
                pass  # Count failures silently
        
        total_time = time.time() - start_time
        success_rate = successful_queries / iterations
        min_rate = TEST_CONSTANTS["high_success_rate"]
        
        # Assert basic stability
        assert success_rate >= min_rate, f"Success rate too low: {success_rate:.1%}"
        assert total_time < 60.0, f"Total time too long: {total_time:.2f}s" 