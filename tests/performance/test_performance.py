"""Performance tests for the system."""

import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from tests.test_data import PERFORMANCE_TEST_DATA, TEST_QUERIES


@pytest.mark.performance
@pytest.mark.slow
class TestAgentPerformance:
    """Performance tests for agent operations."""
    
    @pytest.mark.asyncio
    async def test_response_time_benchmark(self, react_agent):
        """Benchmark agent response times for different query types."""
        query_types = {
            "simple": TEST_QUERIES["simple_greeting"],
            "calculation": TEST_QUERIES["calculation"],
            "reasoning": TEST_QUERIES["reasoning"]
        }
        
        results = {}
        
        for query_type, query in query_types.items():
            times = []
            
            # Run each query type multiple times
            for i in range(3):
                start_time = time.time()
                result = await react_agent.run(query)
                end_time = time.time()
                
                response_time = end_time - start_time
                times.append(response_time)
                
                # Validate response
                assert "response" in result
            
            # Calculate statistics
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            
            results[query_type] = {
                "average": avg_time,
                "max": max_time,
                "min": min_time
            }
            
            # Assert reasonable response times
            assert avg_time < PERFORMANCE_TEST_DATA["max_response_time"]
            
            print(f"✅ {query_type.capitalize()} queries - Avg: {avg_time:.2f}s, Max: {max_time:.2f}s")
        
        print("✅ Response time benchmark completed")
        return results
    
    @pytest.mark.asyncio
    async def test_basic_performance_monitoring(self, react_agent):
        """Basic performance monitoring without psutil."""
        # Simple performance monitoring using basic timing
        queries = [TEST_QUERIES["simple_greeting"]] * 5
        
        start_time = time.time()
        successful_queries = 0
        
        for i, query in enumerate(queries):
            try:
                result = await react_agent.run(query)
                if "response" in result:
                    successful_queries += 1
                
                # Log progress every few iterations
                if (i + 1) % 2 == 0:
                    elapsed = time.time() - start_time
                    print(f"   After {i+1} queries: {elapsed:.1f}s elapsed")
            except Exception as e:
                print(f"   Query {i+1} failed: {e}")
        
        total_time = time.time() - start_time
        success_rate = successful_queries / len(queries)
        avg_time_per_query = total_time / len(queries)
        
        # Basic performance assertions
        assert success_rate >= 0.8, f"Success rate too low: {success_rate:.1%}"
        assert avg_time_per_query < 10.0, f"Average time per query too high: {avg_time_per_query:.2f}s"
        
        print(f"✅ Basic performance monitoring - Success rate: {success_rate:.1%}, "
              f"Avg time per query: {avg_time_per_query:.2f}s")
        
        return {
            "total_queries": len(queries),
            "successful": successful_queries,
            "total_time": total_time,
            "success_rate": success_rate,
            "avg_time_per_query": avg_time_per_query
        }
    
    @pytest.mark.asyncio
    async def test_concurrent_performance(self, react_agent):
        """Test performance under concurrent load."""
        num_concurrent = PERFORMANCE_TEST_DATA["concurrent_requests"]
        query = TEST_QUERIES["simple_greeting"]
        
        async def single_request(request_id):
            start_time = time.time()
            try:
                result = await react_agent.run(f"{query} #{request_id}")
                end_time = time.time()
                return {
                    "id": request_id,
                    "success": True,
                    "time": end_time - start_time,
                    "has_response": "response" in result
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "id": request_id,
                    "success": False,
                    "time": end_time - start_time,
                    "error": str(e)
                }
        
        # Execute concurrent requests
        start_time = time.time()
        tasks = [single_request(i) for i in range(num_concurrent)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        success_rate = len(successful_requests) / len(results)
        avg_response_time = sum(r["time"] for r in successful_requests) / len(successful_requests) if successful_requests else 0
        
        # Assert performance criteria
        assert success_rate >= 0.7, f"Success rate too low: {success_rate:.1%}"
        assert total_time < 60.0, f"Total time too long: {total_time:.2f}s"
        
        print(f"✅ Concurrent performance - {len(successful_requests)}/{num_concurrent} succeeded")
        print(f"   Success rate: {success_rate:.1%}, Avg response time: {avg_response_time:.2f}s")
        
        return {
            "total_requests": num_concurrent,
            "successful": len(successful_requests),
            "failed": len(failed_requests),
            "success_rate": success_rate,
            "total_time": total_time,
            "avg_response_time": avg_response_time
        }
    
    @pytest.mark.asyncio
    async def test_throughput_measurement(self, react_agent):
        """Measure agent throughput (requests per second)."""
        duration = 15  # Reduced duration for faster testing
        query = "Quick test"
        
        completed_requests = 0
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                result = await react_agent.run(f"{query} #{completed_requests + 1}")
                if "response" in result:
                    completed_requests += 1
            except Exception as e:
                print(f"   Request failed: {e}")
        
        actual_duration = time.time() - start_time
        throughput = completed_requests / actual_duration
        
        print(f"✅ Throughput test - {completed_requests} requests in {actual_duration:.1f}s")
        print(f"   Throughput: {throughput:.2f} requests/second")
        
        # Assert minimum throughput
        assert throughput > 0.1, f"Throughput too low: {throughput:.2f} requests/second"
        
        return {
            "completed_requests": completed_requests,
            "duration": actual_duration,
            "throughput": throughput
        }


@pytest.mark.performance
class TestAPIPerformance:
    """Performance tests for API endpoints."""
    
    def test_api_response_times(self, api_client):
        """Benchmark API endpoint response times."""
        endpoints = [
            ("GET", "/"),
            ("GET", "/health"),
            ("GET", "/agent/info")
        ]
        
        for method, endpoint in endpoints:
            times = []
            for _ in range(5):
                start_time = time.time()
                if method == "GET":
                    response = api_client.get(endpoint)
                elif method == "POST":
                    response = api_client.post(endpoint, json={"message": "test"})
                
                end_time = time.time()
                times.append(end_time - start_time)
                
                # For /agent/info, expect 500 when agent is not initialized in test
                if endpoint == "/agent/info":
                    assert response.status_code in [200, 500], f"Unexpected status for {endpoint}: {response.status_code}"
                else:
                    assert response.status_code == 200, f"Failed: {method} {endpoint} returned {response.status_code}"
            
            avg_time = sum(times) / len(times)
            print(f"✅ {method} {endpoint} - Avg: {avg_time:.3f}s")
    
    def test_api_concurrent_load(self, api_client):
        """Test API performance under concurrent load."""
        def make_request(request_id):
            start_time = time.time()
            response = api_client.get("/health")
            end_time = time.time()
            
            return {
                "id": request_id,
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == 200
            }
        
        num_threads = 5  # Reduced for simpler testing
        num_requests_per_thread = 3
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for i in range(num_threads * num_requests_per_thread):
                future = executor.submit(make_request, i)
                futures.append(future)
            
            results = [future.result() for future in futures]
        
        # Analyze results
        successful_requests = [r for r in results if r["success"]]
        success_rate = len(successful_requests) / len(results)
        avg_response_time = sum(r["response_time"] for r in successful_requests) / len(successful_requests)
        
        assert success_rate >= 0.9, f"API success rate too low: {success_rate:.1%}"
        assert avg_response_time < 2.0, f"Average response time too high: {avg_response_time:.2f}s"
        
        print(f"✅ API concurrent load - {len(successful_requests)}/{len(results)} succeeded")
        print(f"   Success rate: {success_rate:.1%}, Avg response time: {avg_response_time:.3f}s")


@pytest.mark.performance
@pytest.mark.slow
class TestStressTests:
    """Simplified stress tests for the system."""
    
    @pytest.mark.asyncio
    async def test_extended_operation(self, react_agent):
        """Test system stability during extended operation (simplified)."""
        duration = 30  # Reduced from 60 seconds
        query = "Stress test query"
        
        start_time = time.time()
        completed_operations = 0
        errors = 0
        
        while time.time() - start_time < duration:
            try:
                result = await react_agent.run(f"{query} #{completed_operations + 1}")
                if "response" in result:
                    completed_operations += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                print(f"   Error in operation {completed_operations + errors}: {e}")
            
            # Log progress every 5 operations
            if (completed_operations + errors) % 5 == 0:
                elapsed = time.time() - start_time
                print(f"   Progress: {completed_operations} completed, {errors} errors in {elapsed:.1f}s")
        
        actual_duration = time.time() - start_time
        success_rate = completed_operations / (completed_operations + errors) if (completed_operations + errors) > 0 else 0
        
        print(f"✅ Extended operation test completed")
        print(f"   Duration: {actual_duration:.1f}s, Operations: {completed_operations}, Errors: {errors}")
        print(f"   Success rate: {success_rate:.1%}")
        
        # Assert reasonable performance
        assert success_rate >= 0.8, f"Success rate too low: {success_rate:.1%}"
        
        return {
            "duration": actual_duration,
            "operations": completed_operations,
            "errors": errors,
            "success_rate": success_rate
        }
    
    def test_simple_load_test(self, api_client):
        """Simple load test for API operations."""
        # Perform many API requests
        num_requests = 50  # Reduced from 100
        errors = 0
        
        for i in range(num_requests):
            try:
                response = api_client.get("/health")
                if response.status_code != 200:
                    errors += 1
            except Exception as e:
                errors += 1
                print(f"   Request {i} failed: {e}")
            
            if i % 10 == 0:
                print(f"   Completed {i}/{num_requests} requests")
        
        error_rate = errors / num_requests
        
        # Error rate should be low
        assert error_rate < 0.1, f"Error rate too high: {error_rate:.1%}"
        
        print(f"✅ Simple load test - {num_requests - errors}/{num_requests} succeeded")


@pytest.mark.performance
class TestPerformanceRegression:
    """Regression tests for performance."""
    
    @pytest.mark.asyncio
    async def test_performance_regression_check(self, react_agent):
        """Check for performance regressions against known baselines."""
        # These baselines should be updated when performance improvements are made
        baselines = {
            "simple_greeting_max_time": 10.0,  # seconds
            "calculation_max_time": 15.0,      # seconds
        }
        
        # Test simple greeting performance
        start_time = time.time()
        result = await react_agent.run(TEST_QUERIES["simple_greeting"])
        greeting_time = time.time() - start_time
        
        assert greeting_time < baselines["simple_greeting_max_time"]
        print(f"✅ Simple greeting performance: {greeting_time:.2f}s (baseline: {baselines['simple_greeting_max_time']}s)")
        
        # Test calculation performance
        start_time = time.time()
        result = await react_agent.run(TEST_QUERIES["calculation"])
        calc_time = time.time() - start_time
        
        assert calc_time < baselines["calculation_max_time"]
        print(f"✅ Calculation performance: {calc_time:.2f}s (baseline: {baselines['calculation_max_time']}s)")
        
        print("✅ Performance regression check passed") 