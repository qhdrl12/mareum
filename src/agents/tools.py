"""
Basic tools for ReAct agents.

This module provides simple example tools that can be used with ReAct agents.
"""

from typing import Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class CalculatorInput(BaseModel):
    """Input for calculator tool."""

    expression: str = Field(
        description="Mathematical expression to evaluate (e.g., '2+3*4')"
    )


class Calculator(BaseTool):
    """A simple calculator tool for basic mathematical operations."""

    name: str = "calculator"
    description: str = (
        "Perform basic mathematical calculations. Input should be a mathematical expression."
    )
    args_schema: type[BaseModel] = CalculatorInput

    def _run(self, expression: str) -> str:
        """Execute the calculator tool."""
        try:
            # Safe evaluation of mathematical expressions
            # Note: In production, you might want to use a more secure method
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                return "Error: Invalid characters in expression. Only numbers and basic operators (+, -, *, /, (), .) are allowed."

            result = eval(expression)
            return f"The result of {expression} is {result}"
        except Exception as e:
            return f"Error calculating expression '{expression}': {str(e)}"


class WebSearchInput(BaseModel):
    """Input for web search tool."""

    query: str = Field(description="Search query to look up information")


class WebSearch(BaseTool):
    """A simple web search tool (mock implementation)."""

    name: str = "web_search"
    description: str = "Search the web for information. Input should be a search query."
    args_schema: type[BaseModel] = WebSearchInput

    def _run(self, query: str) -> str:
        """Execute the web search tool."""
        # This is a mock implementation
        # In a real scenario, you'd integrate with a search API like Google Custom Search, Bing, etc.

        mock_results = {
            "weather": "Today's weather is sunny with a temperature of 22°C (72°F).",
            "python": "Python is a high-level programming language known for its simplicity and readability.",
            "langgraph": "LangGraph is a library for building stateful, multi-actor applications with LLMs.",
            "react": "ReAct (Reasoning and Acting) is a paradigm for building language agents that can reason and take actions.",
        }

        # Simple keyword matching for demo
        for keyword, result in mock_results.items():
            if keyword.lower() in query.lower():
                return f"Search results for '{query}': {result}"

        return f"Search results for '{query}': No specific information found, but here are some general results about your query."


class KnowledgeBaseInput(BaseModel):
    """Input for knowledge base search tool."""

    query: str = Field(description="Query to search in the knowledge base")


class KnowledgeBaseSearch(BaseTool):
    """A tool for searching a knowledge base."""

    name: str = "knowledge_search"
    description: str = (
        "Search the knowledge base for relevant information. Input should be a search query."
    )
    args_schema: type[BaseModel] = KnowledgeBaseInput

    def _run(self, query: str) -> str:
        """Execute the knowledge base search tool."""
        # Mock knowledge base for demonstration
        knowledge_base = {
            "api": "Our API supports REST endpoints for creating, reading, updating, and deleting resources. Authentication is required via API keys.",
            "pricing": "We offer three pricing tiers: Basic ($10/month), Pro ($50/month), and Enterprise (custom pricing).",
            "support": "Technical support is available 24/7 via email, chat, and phone. Response times vary by plan.",
            "features": "Key features include real-time analytics, automated workflows, custom integrations, and advanced security.",
            "deployment": "The platform supports cloud deployment on AWS, Azure, and GCP, as well as on-premises installations.",
        }

        # Simple keyword search
        for key, info in knowledge_base.items():
            if key in query.lower() or any(
                word in query.lower() for word in key.split()
            ):
                return f"Knowledge base result for '{query}': {info}"

        return f"No specific information found in knowledge base for '{query}'. Please try a different search term."


class FileManagerInput(BaseModel):
    """Input for file manager tool."""

    action: str = Field(description="Action to perform: 'read', 'write', 'list'")
    file_path: Optional[str] = Field(
        default=None, description="Path to the file (for read/write operations)"
    )
    content: Optional[str] = Field(
        default=None, description="Content to write (for write operations)"
    )


class FileManager(BaseTool):
    """A simple file management tool."""

    name: str = "file_manager"
    description: str = (
        "Manage files: read file contents, write to files, or list directory contents. Specify action and file path."
    )
    args_schema: type[BaseModel] = FileManagerInput

    def _run(
        self,
        action: str,
        file_path: Optional[str] = None,
        content: Optional[str] = None,
    ) -> str:
        """Execute the file manager tool."""
        try:
            if action == "read":
                if not file_path:
                    return "Error: file_path is required for read operation"
                with open(file_path, "r", encoding="utf-8") as f:
                    file_content = f.read()
                return f"Contents of {file_path}:\n{file_content}"

            elif action == "write":
                if not file_path or content is None:
                    return (
                        "Error: file_path and content are required for write operation"
                    )
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"Successfully wrote content to {file_path}"

            elif action == "list":
                import os

                directory = file_path or "."
                files = os.listdir(directory)
                return f"Files in {directory}: {', '.join(files)}"

            else:
                return f"Error: Unknown action '{action}'. Supported actions: read, write, list"

        except FileNotFoundError:
            return f"Error: File or directory '{file_path}' not found"
        except PermissionError:
            return f"Error: Permission denied accessing '{file_path}'"
        except Exception as e:
            return f"Error performing {action} operation: {str(e)}"


def get_default_tools():
    """Get a list of default tools for ReAct agents."""
    return [
        Calculator(),
        WebSearch(),
        KnowledgeBaseSearch(),
        FileManager(),
    ]
