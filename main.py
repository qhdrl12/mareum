#!/usr/bin/env python3
"""
LangGraph Agent Server

A FastAPI server for running AI agents with LangGraph.
"""

import argparse
import uvicorn
import logging
import sys
from pathlib import Path
from typing import Optional

from src.api.app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the server"""
    parser = argparse.ArgumentParser(
        description="LangGraph Agent Server",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to agent configuration YAML file"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Set the logging level (default: info)"
    )
    
    args = parser.parse_args()
    
    # Set log level
    log_level = getattr(logging, args.log_level.upper())
    logging.getLogger().setLevel(log_level)
    
    # Validate config file if provided
    config_path: Optional[str] = None
    if args.config:
        config_file = Path(args.config)
        if not config_file.exists():
            logger.error(f"Configuration file not found: {args.config}")
            sys.exit(1)
        config_path = str(config_file.absolute())
        logger.info(f"Using configuration file: {config_path}")
    else:
        logger.warning("No configuration file provided. Agent will need to be initialized per request.")
    
    # Create FastAPI app
    app = create_app(config_path=config_path)
    
    # Start server
    logger.info(f"Starting server on {args.host}:{args.port}")
    logger.info(f"Reload mode: {'enabled' if args.reload else 'disabled'}")
    
    try:
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
