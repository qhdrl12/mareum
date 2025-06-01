#!/usr/bin/env python3
"""
Simple Math MCP Server Example - Streamable HTTP

This is a basic example of an MCP server that provides mathematical tools
via streamable_http transport. Perfect for web UI configuration.

Usage:
    python math_server.py

Server will run on http://localhost:3001 with MCP endpoint at /mcp

This server provides the following tools:
- add: Add two numbers
- subtract: Subtract two numbers  
- multiply: Multiply two numbers
- divide: Divide two numbers
- power: Raise to power
- square_root: Calculate square root
"""

import os
# from mcp.server.fastmcp import FastMCP
from fastmcp import FastMCP


# Create FastMCP server instance
mcp = FastMCP("Math Tools Server")

@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract the second number from the first."""
    return a - b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide the first number by the second."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

@mcp.tool()
def power(base: float, exponent: float) -> float:
    """Raise base to the power of exponent."""
    return base ** exponent

@mcp.tool()
def square_root(x: float) -> float:
    """Calculate the square root of a number."""
    if x < 0:
        raise ValueError("Cannot calculate square root of negative number")
    return x ** 0.5

if __name__ == "__main__":
    # Run the server using streamable-http transport
    print("Starting Math MCP Server on http://0.0.0.0:3001")
    print("MCP protocol endpoints will be automatically configured")
    
    # Run FastMCP server on default port
    mcp.run(transport="streamable-http", host="0.0.0.0", port=3001, path="/mcp")
