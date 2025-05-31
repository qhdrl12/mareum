"""
Comprehensive API tests for ReAct Agent API.
"""

import os
import json
import time
from fastapi.testclient import TestClient

# Add src to Python path
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.api.app import app, _agent_manager
from src.core.agent_manager import AgentManager
import src.api.app as app_module


class TestAPIComprehensive:
    """Comprehensive API tests."""

    @classmethod
    def setup_class(cls):
        """Setup test environment."""
        cls.client = TestClient(app)
        cls.agent_manager = None

        # Initialize agent for testing
        config_path = "examples/configs/openai_compatible.yaml"  # Fixed filename
        if os.path.exists(config_path):
            try:
                # Set the global agent manager for the API
                cls.agent_manager = AgentManager()
                cls.agent_manager.initialize_agent(config_path)
                app_module._agent_manager = cls.agent_manager
                print(f"✅ Test agent initialized with config: {config_path}")
            except Exception as e:
                print(f"⚠️ Failed to initialize agent for tests: {e}")
        else:
            print(f"⚠️ Config file not found: {config_path}")

    @classmethod 
    def teardown_class(cls):
        """Cleanup after tests."""
        if cls.agent_manager is not None:
            cls.agent_manager.shutdown()
        app_module._agent_manager = None

    def test_01_health_endpoints(self):
        """Test health check endpoints."""
        print("\n🔍 Testing health endpoints...")

        # Test root endpoint
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
        print("✅ Root endpoint working")

        # Test health endpoint
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
        print("✅ Health endpoint working")

    def test_02_agent_info(self):
        """Test agent info endpoint."""
        print("\n🔍 Testing agent info endpoint...")

        response = self.client.get("/agent/info")

        # Agent should now be properly initialized
        assert response.status_code == 200
        data = response.json()
        
        # Check the new response structure from AgentManager.get_agent_info()
        assert "initialized" in data
        assert data["initialized"] == True
        assert "config_path" in data
        assert "agent_name" in data
        assert "agent_version" in data
        assert "model_provider" in data
        assert "model_name" in data
        assert "tools_count" in data
        assert "memory_enabled" in data

        # Check tool count
        assert data["tools_count"] == 4  # Calculator, WebSearch, KnowledgeBaseSearch, FileManager

        print(f"✅ Agent info endpoint working - Agent: {data['agent_name']}")
        print(f"   Model: {data['model_provider']}/{data['model_name']}")
        print(f"   Tools: {data['tools_count']}")
        print(f"   Memory: {data['memory_enabled']}")

    def test_03_simple_chat(self):
        """Test simple chat functionality."""
        print("\n🔍 Testing simple chat...")

        if self.agent_manager is None or not self.agent_manager.is_initialized:
            print("⚠️ Skipping chat test - agent not initialized")
            return

        # Simple greeting
        request_data = {"message": "Hello! Can you introduce yourself?"}

        response = self.client.post("/chat", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "response" in data
        assert "tools_used" in data
        assert "metadata" in data
        assert isinstance(data["response"], str)
        assert len(data["response"]) > 0

        print(f"✅ Simple chat working - Response length: {len(data['response'])}")
        print(f"📝 Response preview: {data['response'][:100]}...")

    def test_04_chat_with_calculation(self):
        """Test chat with calculator tool usage."""
        print("\n🔍 Testing chat with calculation...")

        if self.agent_manager is None or not self.agent_manager.is_initialized:
            print("⚠️ Skipping calculation test - agent not initialized")
            return

        request_data = {
            "message": "Calculate 45 * 67 + 123. Show me the step-by-step calculation."
        }

        response = self.client.post("/chat", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "response" in data
        assert "tools_used" in data

        # Check if calculator was used
        tool_names = data["tools_used"]
        if "calculator" in tool_names:
            print("✅ Calculator tool was used")
        else:
            print("⚠️ Calculator tool was not used (might be due to model behavior)")

        print(f"✅ Calculation test completed - Tools used: {tool_names}")
        print(f"📝 Response preview: {data['response'][:150]}...")

    def test_05_chat_with_history(self):
        """Test chat with conversation history."""
        print("\n🔍 Testing chat with history...")

        if self.agent_manager is None or not self.agent_manager.is_initialized:
            print("⚠️ Skipping history test - agent not initialized")
            return

        # Create chat history
        chat_history = [
            {"role": "human", "content": "My name is John"},
            {"role": "assistant", "content": "Hello John! Nice to meet you."},
            {"role": "human", "content": "I'm working on a math project"},
        ]

        request_data = {
            "message": "What was my name again?",
            "chat_history": chat_history,
        }

        response = self.client.post("/chat", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "response" in data

        # Check if the agent remembers the name
        response_text = data["response"].lower()
        if "john" in response_text:
            print("✅ Agent correctly remembered the name from history")
        else:
            print(
                "⚠️ Agent didn't explicitly mention the name (might still understand context)"
            )

        print(f"✅ Chat with history working")
        print(f"📝 Response preview: {data['response'][:150]}...")

    def test_06_streaming_chat(self):
        """Test streaming chat functionality."""
        print("\n🔍 Testing streaming chat...")

        if self.agent_manager is None or not self.agent_manager.is_initialized:
            print("⚠️ Skipping streaming test - agent not initialized")
            return

        request_data = {
            "message": "Tell me a short story about a robot learning to cook."
        }

        # Test streaming response
        with self.client as client:
            with client.stream("POST", "/chat/stream", json=request_data) as response:
                assert response.status_code == 200
                assert (
                    response.headers["content-type"]
                    == "text/event-stream; charset=utf-8"
                )

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

                assert chunks_received > 0
                print(f"✅ Streaming working - Received {chunks_received} chunks")
                print(f"📝 Total content length: {len(total_content)}")

    def test_07_error_handling(self):
        """Test error handling."""
        print("\n🔍 Testing error handling...")

        # Test invalid request format
        response = self.client.post("/chat", json={"invalid": "request"})
        assert response.status_code == 422  # Validation error
        print("✅ Invalid request format properly rejected")

        # Test empty message
        response = self.client.post("/chat", json={"message": ""})
        # This might succeed depending on validation rules
        print(f"✅ Empty message handling - Status: {response.status_code}")

        # Test non-existent endpoint
        response = self.client.get("/non-existent")
        assert response.status_code == 404
        print("✅ Non-existent endpoint properly returns 404")

    def test_08_concurrent_requests(self):
        """Test concurrent request handling."""
        print("\n🔍 Testing concurrent requests...")

        if self.agent_manager is None or not self.agent_manager.is_initialized:
            print("⚠️ Skipping concurrent test - agent not initialized")
            return

        def make_request(request_id):
            """Make a single request."""
            request_data = {
                "message": f"Hello from request {request_id}. Please respond with the request number."
            }

            start_time = time.time()
            response = self.client.post("/chat", json=request_data)
            end_time = time.time()

            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == 200,
            }

        # Make 3 concurrent requests
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, i) for i in range(3)]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # Check results
        successful_requests = sum(1 for r in results if r["success"])
        average_response_time = sum(r["response_time"] for r in results) / len(results)

        print(f"✅ Concurrent requests test - {successful_requests}/3 successful")
        print(f"📊 Average response time: {average_response_time:.2f}s")

        assert successful_requests >= 2  # At least 2 should succeed

    def test_09_performance_check(self):
        """Basic performance check."""
        print("\n🔍 Testing performance...")

        if self.agent_manager is None or not self.agent_manager.is_initialized:
            print("⚠️ Skipping performance test - agent not initialized")
            return

        # Measure response times for different request types
        test_cases = [
            {"name": "Simple greeting", "message": "Hello!"},
            {"name": "Health check", "endpoint": "/health"},
            {"name": "Agent info", "endpoint": "/agent/info"},
        ]

        results = {}

        for case in test_cases:
            start_time = time.time()

            if "endpoint" in case:
                response = self.client.get(case["endpoint"])
            else:
                response = self.client.post("/chat", json={"message": case["message"]})

            end_time = time.time()
            response_time = end_time - start_time

            results[case["name"]] = {
                "response_time": response_time,
                "status_code": response.status_code,
                "success": response.status_code == 200,
            }

        # Print results
        for name, result in results.items():
            status = "✅" if result["success"] else "❌"
            print(f"{status} {name}: {result['response_time']:.3f}s")

        # Check if any endpoint is too slow (>10 seconds)
        slow_endpoints = [
            name for name, result in results.items() if result["response_time"] > 10
        ]
        if slow_endpoints:
            print(f"⚠️ Slow endpoints detected: {slow_endpoints}")
        else:
            print("✅ All endpoints responding within acceptable time")


def run_comprehensive_tests():
    """Run all comprehensive tests."""
    print("🚀 Starting comprehensive API tests...\n")

    # Create test instance
    test_instance = TestAPIComprehensive()
    test_instance.setup_class()

    # Run all tests
    test_methods = [
        test_instance.test_01_health_endpoints,
        test_instance.test_02_agent_info,
        test_instance.test_03_simple_chat,
        test_instance.test_04_chat_with_calculation,
        test_instance.test_05_chat_with_history,
        test_instance.test_06_streaming_chat,
        test_instance.test_07_error_handling,
        test_instance.test_08_concurrent_requests,
        test_instance.test_09_performance_check,
    ]

    passed = 0
    failed = 0

    for test_method in test_methods:
        try:
            test_method()
            passed += 1
        except Exception as e:
            print(f"❌ {test_method.__name__} failed: {str(e)}")
            failed += 1

    # Summary
    print(f"\n📊 Test Summary:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")

    return passed, failed


if __name__ == "__main__":
    run_comprehensive_tests()
