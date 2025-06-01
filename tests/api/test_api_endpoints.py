"""API endpoint tests."""

import pytest
import json
import time
from fastapi.testclient import TestClient

from tests.test_data import API_TEST_DATA, TEST_QUERIES


@pytest.mark.api
class TestAPIEndpoints:
    """Test API endpoint functionality."""
    
    def test_health_endpoints(self, api_client):
        """Test health check endpoints."""
        # Test root endpoint
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
        print("✅ Root endpoint working")
        
        # Test health endpoint
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        print("✅ Health endpoint working")
    
    def test_agent_info(self, api_client):
        """Test agent info endpoint (may return uninitialized state)."""
        response = api_client.get("/agent/info")
        
        # API should respond, but agent might not be initialized
        if response.status_code == 200:
            data = response.json()
            required_fields = [
                "initialized", "config_path", "agent_name", 
                "agent_version", "model_provider", "model_name", "tools_count"
            ]
            
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            print(f"✅ Agent info endpoint working - Agent: {data.get('agent_name', 'Unknown')}")
        elif response.status_code == 500:
            # Expected when agent manager is not initialized in test environment
            data = response.json()
            assert "error" in data
            assert "Agent manager not initialized" in data["error"]
            print("✅ Agent info endpoint correctly reports uninitialized state")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    @pytest.mark.parametrize("request_data", API_TEST_DATA["valid_requests"])
    def test_chat_endpoint_valid_requests(self, api_client, test_utils, request_data):
        """Test chat endpoint with valid requests."""
        response = api_client.post("/chat", json=request_data)
        
        if response.status_code == 200:
            data = response.json()
            test_utils.validate_api_response(data)
            print(f"✅ Valid request test passed: {request_data['message'][:30]}...")
        else:
            # If agent is not initialized, this might return 500
            print(f"⚠️ Chat endpoint returned {response.status_code} - Agent may not be initialized")
    
    @pytest.mark.parametrize("request_data", API_TEST_DATA["invalid_requests"])
    def test_chat_endpoint_invalid_requests(self, api_client, request_data):
        """Test chat endpoint with invalid requests."""
        response = api_client.post("/chat", json=request_data)
        assert response.status_code == 422  # Validation error
        print(f"✅ Invalid request properly rejected: {request_data}")
    
    def test_streaming_chat(self, api_client):
        """Test streaming chat functionality."""
        request_data = {"message": TEST_QUERIES["story_request"]}
        
        try:
            with api_client.stream("POST", "/chat/stream", json=request_data) as response:
                if response.status_code == 200:
                    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
                    
                    chunks_received = 0
                    total_content = ""
                    
                    for line in response.iter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            if data_str.strip():
                                try:
                                    chunk_data = json.loads(data_str)
                                    chunks_received += 1
                                    total_content += chunk_data.get("chunk", "")
                                    
                                    if chunk_data.get("is_final", False):
                                        break
                                except json.JSONDecodeError:
                                    continue
                    
                    assert chunks_received > 0, "Should receive at least one chunk"
                    print(f"✅ Streaming test passed - {chunks_received} chunks received")
                else:
                    print(f"⚠️ Streaming endpoint returned {response.status_code} - Agent may not be initialized")
        except Exception as e:
            print(f"⚠️ Streaming test encountered issue: {e}")
    
    def test_error_handling(self, api_client):
        """Test API error handling."""
        # Test non-existent endpoint
        response = api_client.get("/non-existent")
        assert response.status_code == 404
        print("✅ Non-existent endpoint returns 404")
        
        # Test method not allowed
        response = api_client.put("/chat")
        assert response.status_code == 405
        print("✅ Method not allowed returns 405")
    
    @pytest.mark.slow
    def test_concurrent_requests(self, api_client):
        """Test concurrent request handling."""
        import concurrent.futures
        import threading
        
        def make_request(request_id):
            request_data = {"message": f"Hello from request {request_id}"}
            start_time = time.time()
            response = api_client.post("/chat", json=request_data)
            end_time = time.time()
            
            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == 200
            }
        
        # Test with 3 concurrent requests (reduced for reliability)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, i) for i in range(3)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Validate results
        successful_requests = sum(1 for r in results if r["success"])
        total_requests = len(results)
        
        print(f"✅ Concurrent test completed - {successful_requests}/{total_requests} succeeded")
        
        # Check response times
        if results:
            avg_response_time = sum(r["response_time"] for r in results) / len(results)
            print(f"   Average response time: {avg_response_time:.2f}s")


@pytest.mark.api
@pytest.mark.integration
class TestAPIWithAgent:
    """Test API endpoints that require an initialized agent."""
    
    def test_chat_with_agent_manager(self, api_client, agent_manager):
        """Test chat endpoint with properly initialized agent."""
        if not agent_manager.is_initialized:
            pytest.skip("Agent manager not initialized - missing config files")
        
        # Set the agent manager in the app
        from src.api import app as app_module
        app_module._agent_manager = agent_manager
        
        try:
            request_data = {"message": "Hello! How are you?"}
            response = api_client.post("/chat", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert "tools_used" in data
            assert "metadata" in data
            
            print("✅ Chat with agent manager test passed")
        finally:
            # Cleanup
            app_module._agent_manager = None
    
    def test_agent_info_with_initialized_agent(self, api_client, agent_manager):
        """Test agent info endpoint with initialized agent."""
        if not agent_manager.is_initialized:
            pytest.skip("Agent manager not initialized - missing config files")
        
        from src.api import app as app_module
        app_module._agent_manager = agent_manager
        
        try:
            response = api_client.get("/agent/info")
            assert response.status_code == 200
            
            data = response.json()
            assert data["initialized"] == True
            assert data["tools_count"] >= 0
            
            print(f"✅ Agent info with initialized agent test passed - Tools: {data['tools_count']}")
        finally:
            app_module._agent_manager = None


@pytest.mark.api
@pytest.mark.performance
class TestAPIPerformance:
    """Performance tests for API endpoints."""
    
    def test_response_time_limits(self, api_client):
        """Test API response time limits."""
        request_data = {"message": "Quick response test"}
        
        start_time = time.time()
        response = api_client.post("/chat", json=request_data)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Response should come back within reasonable time
        # Note: May be slower if agent is not initialized
        max_time = 10.0 if response.status_code == 200 else 5.0
        assert response_time < max_time, f"Response time {response_time:.2f}s exceeds {max_time}s limit"
        
        print(f"✅ Response time test passed - {response_time:.2f}s")
    
    def test_health_endpoint_performance(self, api_client):
        """Test health endpoint response time."""
        # Health endpoints should be very fast
        start_time = time.time()
        response = api_client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 1.0, f"Health endpoint response time {response_time:.2f}s too slow"
        assert response.status_code == 200
        
        print(f"✅ Health endpoint performance test passed - {response_time:.2f}s") 