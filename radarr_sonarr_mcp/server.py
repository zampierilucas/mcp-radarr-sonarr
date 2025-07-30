#!/usr/bin/env python
"""MCP server for Radarr and Sonarr integration with Claude Code."""

import asyncio
import logging
import sys
from typing import Any, Optional

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import requests

from .config import load_config as load_config_module

# Set up logging to stderr (never to stdout as it corrupts MCP JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Global server instance
server = Server("radarr-sonarr-mcp")


def load_config():
    """Load configuration from config module."""
    try:
        config = load_config_module()
        # Convert to internal format
        return {
            "radarrConfig": {
                "apiKey": config.radarr_config.api_key,
                "url": config.radarr_config.url,
                "basePath": config.radarr_config.base_path
            },
            "sonarrConfig": {
                "apiKey": config.sonarr_config.api_key,
                "url": config.sonarr_config.url,
                "basePath": config.sonarr_config.base_path
            }
        }
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {
            "radarrConfig": {"apiKey": "", "url": "http://localhost:7878", "basePath": "/api/v3"},
            "sonarrConfig": {"apiKey": "", "url": "http://localhost:8989", "basePath": "/api/v3"}
        }


def get_radarr_url(config):
    """Get Radarr API URL."""
    url = config["radarrConfig"]["url"].rstrip('/')
    base_path = config["radarrConfig"]["basePath"]
    return f"{url}{base_path}"


def get_sonarr_url(config):
    """Get Sonarr API URL."""
    url = config["sonarrConfig"]["url"].rstrip('/')
    base_path = config["sonarrConfig"]["basePath"]
    return f"{url}{base_path}"


def make_radarr_request(config, endpoint, params=None, method="GET", json_data=None):
    """Make a request to Radarr API."""
    base_url = get_radarr_url(config)
    api_key = config["radarrConfig"]["apiKey"]
    
    if not api_key:
        raise ValueError("Radarr API key not configured")
    
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    url = f"{base_url}/{endpoint.lstrip('/')}"
    
    try:
        if method.upper() == "POST":
            response = requests.post(url, headers=headers, params=params, json=json_data, timeout=30)
        else:
            response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Radarr API request failed: {e}")
        raise


def make_sonarr_request(config, endpoint, params=None, method="GET", json_data=None):
    """Make a request to Sonarr API."""
    base_url = get_sonarr_url(config)
    api_key = config["sonarrConfig"]["apiKey"]
    
    if not api_key:
        raise ValueError("Sonarr API key not configured")
    
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    url = f"{base_url}/{endpoint.lstrip('/')}"
    
    try:
        if method.upper() == "POST":
            response = requests.post(url, headers=headers, params=params, json=json_data, timeout=30)
        else:
            response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Sonarr API request failed: {e}")
        raise


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="get_radarr_movies",
            description="Get list of movies from Radarr",
            inputSchema={
                "type": "object",
                "properties": {
                    "monitored": {
                        "type": "boolean",
                        "description": "Filter by monitored status"
                    },
                    "downloaded": {
                        "type": "boolean", 
                        "description": "Filter by downloaded status"
                    }
                },
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="get_sonarr_series",
            description="Get list of TV series from Sonarr",
            inputSchema={
                "type": "object",
                "properties": {
                    "monitored": {
                        "type": "boolean",
                        "description": "Filter by monitored status"
                    },
                    "downloaded": {
                        "type": "boolean",
                        "description": "Filter by downloaded status" 
                    }
                },
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="search_radarr_movies",
            description="Search for movies in Radarr",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {
                        "type": "string",
                        "description": "Search term for movie title"
                    }
                },
                "required": ["term"],
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="search_sonarr_series",
            description="Search for TV series in Sonarr",  
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {
                        "type": "string",
                        "description": "Search term for series title"
                    }
                },
                "required": ["term"],
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="add_radarr_movie",
            description="Add a movie to Radarr library and request download",
            inputSchema={
                "type": "object",
                "properties": {
                    "tmdbId": {
                        "type": "integer",
                        "description": "TMDB ID of the movie to add"
                    },
                    "title": {
                        "type": "string",
                        "description": "Movie title"
                    },
                    "year": {
                        "type": "integer",
                        "description": "Release year"
                    },
                    "qualityProfileId": {
                        "type": "integer",
                        "description": "Quality profile ID (optional, uses default if not provided)",
                        "default": 1
                    },
                    "rootFolderPath": {
                        "type": "string",
                        "description": "Root folder path (optional, uses default if not provided)"
                    },
                    "monitored": {
                        "type": "boolean",
                        "description": "Whether to monitor the movie",
                        "default": True
                    },
                    "searchForMovie": {
                        "type": "boolean", 
                        "description": "Whether to search for the movie immediately",
                        "default": True
                    }
                },
                "required": ["tmdbId", "title", "year"],
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="add_sonarr_series",
            description="Add a TV series to Sonarr library and request download",
            inputSchema={
                "type": "object",
                "properties": {
                    "tvdbId": {
                        "type": "integer",
                        "description": "TVDB ID of the series to add"
                    },
                    "title": {
                        "type": "string",
                        "description": "Series title"
                    },
                    "year": {
                        "type": "integer",
                        "description": "First air year"
                    },
                    "qualityProfileId": {
                        "type": "integer",
                        "description": "Quality profile ID (optional, uses default if not provided)",
                        "default": 1
                    },
                    "rootFolderPath": {
                        "type": "string",
                        "description": "Root folder path (optional, uses default if not provided)"
                    },
                    "monitored": {
                        "type": "boolean",
                        "description": "Whether to monitor the series",
                        "default": True
                    },
                    "searchForMissingEpisodes": {
                        "type": "boolean",
                        "description": "Whether to search for missing episodes immediately", 
                        "default": True
                    },
                    "seasonFolder": {
                        "type": "boolean",
                        "description": "Whether to use season folders",
                        "default": True
                    }
                },
                "required": ["tvdbId", "title", "year"],
                "additionalProperties": False
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent]:
    """Handle tool calls."""
    if arguments is None:
        arguments = {}
    
    config = load_config()
    
    try:
        if name == "get_radarr_movies":
            movies = make_radarr_request(config, "movie")
            
            # Apply filters
            if arguments.get("monitored") is not None:
                movies = [m for m in movies if m.get("monitored") == arguments["monitored"]]
            
            if arguments.get("downloaded") is not None:
                downloaded_filter = arguments["downloaded"]
                movies = [m for m in movies if (m.get("hasFile", False)) == downloaded_filter]
            
            result = {
                "count": len(movies),
                "movies": [
                    {
                        "id": m.get("id"),
                        "title": m.get("title"),
                        "year": m.get("year"),
                        "monitored": m.get("monitored"),
                        "hasFile": m.get("hasFile", False),
                        "status": m.get("status"),
                        "overview": m.get("overview", "")[:200] + "..." if len(m.get("overview", "")) > 200 else m.get("overview", "")
                    }
                    for m in movies[:50]  # Limit to 50 results
                ]
            }
            
        elif name == "get_sonarr_series":
            series = make_sonarr_request(config, "series")
            
            # Apply filters  
            if arguments.get("monitored") is not None:
                series = [s for s in series if s.get("monitored") == arguments["monitored"]]
            
            if arguments.get("downloaded") is not None:
                downloaded_filter = arguments["downloaded"]
                series = [s for s in series if (s.get("statistics", {}).get("episodeFileCount", 0) > 0) == downloaded_filter]
            
            result = {
                "count": len(series),
                "series": [
                    {
                        "id": s.get("id"),
                        "title": s.get("title"),
                        "year": s.get("year"),
                        "monitored": s.get("monitored"),
                        "status": s.get("status"),
                        "episodeCount": s.get("statistics", {}).get("episodeCount", 0),
                        "episodeFileCount": s.get("statistics", {}).get("episodeFileCount", 0),
                        "overview": s.get("overview", "")[:200] + "..." if len(s.get("overview", "")) > 200 else s.get("overview", "")
                    }
                    for s in series[:50]  # Limit to 50 results
                ]
            }
            
        elif name == "search_radarr_movies":
            term = arguments["term"]
            movies = make_radarr_request(config, "movie/lookup", {"term": term})
            
            result = {
                "count": len(movies),
                "movies": [
                    {
                        "title": m.get("title"),
                        "year": m.get("year"),
                        "tmdbId": m.get("tmdbId"),
                        "imdbId": m.get("imdbId"),
                        "overview": m.get("overview", "")[:200] + "..." if len(m.get("overview", "")) > 200 else m.get("overview", "")
                    }
                    for m in movies[:20]  # Limit to 20 results
                ]
            }
            
        elif name == "search_sonarr_series":
            term = arguments["term"]
            series = make_sonarr_request(config, "series/lookup", {"term": term})
            
            result = {
                "count": len(series),
                "series": [
                    {
                        "title": s.get("title"),
                        "year": s.get("year"),
                        "tvdbId": s.get("tvdbId"),
                        "imdbId": s.get("imdbId"),
                        "overview": s.get("overview", "")[:200] + "..." if len(s.get("overview", "")) > 200 else s.get("overview", "")
                    }
                    for s in series[:20]  # Limit to 20 results
                ]
            }
            
        elif name == "add_radarr_movie":
            tmdb_id = arguments["tmdbId"]
            title = arguments["title"]
            year = arguments["year"]
            
            # Get default quality profile and root folder if not provided
            quality_profile_id = arguments.get("qualityProfileId")
            root_folder_path = arguments.get("rootFolderPath")
            
            if not quality_profile_id:
                # Get first available quality profile
                profiles = make_radarr_request(config, "qualityprofile")
                quality_profile_id = profiles[0]["id"] if profiles else 1
                
            if not root_folder_path:
                # Get first available root folder
                root_folders = make_radarr_request(config, "rootfolder")
                root_folder_path = root_folders[0]["path"] if root_folders else "/movies"
            
            # Prepare movie data for adding
            movie_data = {
                "title": title,
                "year": year,
                "tmdbId": tmdb_id,
                "qualityProfileId": quality_profile_id,
                "rootFolderPath": root_folder_path,
                "monitored": arguments.get("monitored", True),
                "addOptions": {
                    "searchForMovie": arguments.get("searchForMovie", True),
                    "monitor": "movieOnly"
                }
            }
            
            # Add movie to Radarr
            added_movie = make_radarr_request(config, "movie", method="POST", json_data=movie_data)
            
            result = {
                "success": True,
                "message": f"Movie '{title} ({year})' has been added to Radarr",
                "movie": {
                    "id": added_movie.get("id"),
                    "title": added_movie.get("title"),
                    "year": added_movie.get("year"),
                    "tmdbId": added_movie.get("tmdbId"),
                    "monitored": added_movie.get("monitored"),
                    "hasFile": added_movie.get("hasFile", False),
                    "status": added_movie.get("status")
                }
            }
            
        elif name == "add_sonarr_series":
            tvdb_id = arguments["tvdbId"]
            title = arguments["title"]
            year = arguments["year"]
            
            # Get default quality profile and root folder if not provided
            quality_profile_id = arguments.get("qualityProfileId")
            root_folder_path = arguments.get("rootFolderPath")
            
            if not quality_profile_id:
                # Get first available quality profile
                profiles = make_sonarr_request(config, "qualityprofile")
                quality_profile_id = profiles[0]["id"] if profiles else 1
                
            if not root_folder_path:
                # Get first available root folder
                root_folders = make_sonarr_request(config, "rootfolder")
                root_folder_path = root_folders[0]["path"] if root_folders else "/tv"
            
            # Prepare series data for adding
            series_data = {
                "title": title,
                "year": year,
                "tvdbId": tvdb_id,
                "qualityProfileId": quality_profile_id,
                "rootFolderPath": root_folder_path,
                "monitored": arguments.get("monitored", True),
                "seasonFolder": arguments.get("seasonFolder", True),
                "addOptions": {
                    "searchForMissingEpisodes": arguments.get("searchForMissingEpisodes", True),
                    "monitor": "all"
                }
            }
            
            # Add series to Sonarr
            added_series = make_sonarr_request(config, "series", method="POST", json_data=series_data)
            
            result = {
                "success": True,
                "message": f"Series '{title} ({year})' has been added to Sonarr",
                "series": {
                    "id": added_series.get("id"),
                    "title": added_series.get("title"),
                    "year": added_series.get("year"),
                    "tvdbId": added_series.get("tvdbId"),
                    "monitored": added_series.get("monitored"),
                    "status": added_series.get("status"),
                    "seasonCount": len(added_series.get("seasons", []))
                }
            }
            
        else:
            raise ValueError(f"Unknown tool: {name}")
            
        return [types.TextContent(type="text", text=str(result))]
        
    except Exception as e:
        logger.error(f"Tool call failed: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available resources."""
    return [
        types.Resource(
            uri="radarr://movies",
            name="Radarr Movies",
            description="List of movies in Radarr",
            mimeType="application/json",
        ),
        types.Resource(
            uri="sonarr://series", 
            name="Sonarr Series",
            description="List of TV series in Sonarr",
            mimeType="application/json",
        )
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a resource."""
    config = load_config()
    
    # Convert URI to string if it's not already
    uri_str = str(uri)
    logger.info(f"Reading resource: {uri_str}")
    
    try:
        if uri_str == "radarr://movies":
            logger.info("Handling radarr://movies resource")
            movies = make_radarr_request(config, "movie")
            result = {
                "count": len(movies),
                "movies": [
                    {
                        "id": m.get("id"),
                        "title": m.get("title"),
                        "year": m.get("year"),
                        "monitored": m.get("monitored"),
                        "hasFile": m.get("hasFile", False),
                        "status": m.get("status")
                    }
                    for m in movies
                ]
            }
            import json
            return json.dumps(result, indent=2)
            
        elif uri_str == "sonarr://series":
            logger.info("Handling sonarr://series resource")
            series = make_sonarr_request(config, "series")
            result = {
                "count": len(series),
                "series": [
                    {
                        "id": s.get("id"),
                        "title": s.get("title"),
                        "year": s.get("year"),
                        "monitored": s.get("monitored"),
                        "status": s.get("status"),
                        "episodeCount": s.get("statistics", {}).get("episodeCount", 0),
                        "episodeFileCount": s.get("statistics", {}).get("episodeFileCount", 0)
                    }
                    for s in series
                ]
            }
            import json
            return json.dumps(result, indent=2)
            
        else:
            logger.error(f"Unknown resource requested: {uri_str}")
            raise ValueError(f"Unknown resource: {uri_str}")
            
    except Exception as e:
        logger.error(f"Resource read failed: {e}")
        return f"Error: {str(e)}"


async def main():
    """Main entry point for the MCP server."""
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="radarr-sonarr-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())