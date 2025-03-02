#!/usr/bin/env python
"""Main MCP server implementation for Radarr/Sonarr."""

import os
import json
import sys
import logging
from typing import Optional
import argparse

from fastmcp import FastMCP
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------- 
# Configuration handling 
# -----------------------------------------------------------------------------

def load_config():
    """Load configuration from environment variables or config file."""
    if os.environ.get('RADARR_API_KEY') or os.environ.get('SONARR_API_KEY'):
        logger.info("Loading configuration from environment variables...")
        nas_ip = os.environ.get('NAS_IP', '10.0.0.23')
        return {
            "nasConfig": {
                "ip": nas_ip,
                "port": os.environ.get('RADARR_PORT', '7878')
            },
            "radarrConfig": {
                "apiKey": os.environ.get('RADARR_API_KEY', ''),
                "basePath": os.environ.get('RADARR_BASE_PATH', '/api/v3'),
                "port": os.environ.get('RADARR_PORT', '7878')
            },
            "sonarrConfig": {
                "apiKey": os.environ.get('SONARR_API_KEY', ''),
                "basePath": os.environ.get('SONARR_BASE_PATH', '/api/v3'),
                "port": os.environ.get('SONARR_PORT', '8989')
            },
            # Optionally, include Jellyfin and Plex configuration if set in env
            "jellyfinConfig": {
                "baseUrl": os.environ.get('JELLYFIN_BASE_URL', ''),  # e.g., "http://10.0.0.23:5055"
                "apiKey": os.environ.get('JELLYFIN_API_KEY', ''),
                "userId": os.environ.get('JELLYFIN_USER_ID', '')
            },
            "plexConfig": {
                "baseUrl": os.environ.get('PLEX_BASE_URL', ''),  # e.g., "http://10.0.0.23:32400"
                "token": os.environ.get('PLEX_TOKEN', '')
            },
            "server": {
                "port": int(os.environ.get('MCP_SERVER_PORT', '3000'))
            }
        }
    else:
        config_path = 'config.json'
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            logger.info("Using default configuration")
            return {
                "nasConfig": {"ip": "10.0.0.23", "port": "7878"},
                "radarrConfig": {"apiKey": "", "basePath": "/api/v3", "port": "7878"},
                "sonarrConfig": {"apiKey": "", "basePath": "/api/v3", "port": "8989"},
                "server": {"port": 3000}
            }

# ----------------------------------------------------------------------------- 
# API Service functions 
# -----------------------------------------------------------------------------

def get_radarr_url(config):
    nas_ip = config["nasConfig"]["ip"]
    port = config["radarrConfig"]["port"]
    base_path = config["radarrConfig"]["basePath"]
    return f"http://{nas_ip}:{port}{base_path}"

def get_sonarr_url(config):
    nas_ip = config["nasConfig"]["ip"]
    port = config["sonarrConfig"]["port"]
    base_path = config["sonarrConfig"]["basePath"]
    return f"http://{nas_ip}:{port}{base_path}"

def make_radarr_request(config, endpoint, params=None):
    api_key = config["radarrConfig"]["apiKey"]
    base_url = get_radarr_url(config)
    url = f"{base_url}/{endpoint}"
    if params is None:
        params = {}
    params['apikey'] = api_key
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error making request to {url}: {e}")
        return []

def make_sonarr_request(config, endpoint, params=None):
    api_key = config["sonarrConfig"]["apiKey"]
    base_url = get_sonarr_url(config)
    url = f"{base_url}/{endpoint}"
    if params is None:
        params = {}
    params['apikey'] = api_key
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error making request to {url}: {e}")
        return []

def get_all_series(config):
    from radarr_sonarr_mcp.services.sonarr_service import SonarrService
    service = SonarrService(config["sonarrConfig"])
    return service.get_all_series()

# ----------------------------------------------------------------------------- 
# Helper function to check watched status from multiple sources 
# -----------------------------------------------------------------------------

def is_watched_series(title: str, fallback: bool, config: dict, sonarr_service) -> bool:
    """
    Check if a series is watched using available media services.
    Returns True if any service reports the series as watched.
    """
    statuses = []
    if config.get("jellyfinConfig", {}).get("baseUrl"):
        from radarr_sonarr_mcp.services.jellyfin_service import JellyfinService
        jellyfin = JellyfinService(config["jellyfinConfig"])
        try:
            statuses.append(jellyfin.is_series_watched(title))
        except Exception as e:
            logger.error(f"Jellyfin check failed for {title}: {e}")
    if config.get("plexConfig", {}).get("baseUrl"):
        from radarr_sonarr_mcp.services.plex_service import PlexService
        plex = PlexService(config["plexConfig"])
        try:
            statuses.append(plex.is_series_watched(title))
        except Exception as e:
            logger.error(f"Plex check failed for {title}: {e}")
    if statuses:
        return any(statuses)
    # Fallback to Sonarr's own logic if no external services are configured.
    return sonarr_service.is_series_watched(title)

def is_watched_movie(title: str, config: dict) -> bool:
    """
    Check if a movie is watched using available media services.
    Returns True if any service reports the movie as watched.
    """
    statuses = []
    if config.get("jellyfinConfig", {}).get("baseUrl"):
        from radarr_sonarr_mcp.services.jellyfin_service import JellyfinService
        jellyfin = JellyfinService(config["jellyfinConfig"])
        try:
            # For movies, you could implement a similar method in JellyfinService.
            statuses.append(jellyfin.is_movie_watched(title))
        except Exception as e:
            logger.error(f"Jellyfin movie check failed for {title}: {e}")
    if config.get("plexConfig", {}).get("baseUrl"):
        from radarr_sonarr_mcp.services.plex_service import PlexService
        plex = PlexService(config["plexConfig"])
        try:
            statuses.append(plex.is_movie_watched(title))
        except Exception as e:
            logger.error(f"Plex movie check failed for {title}: {e}")
    # If no external services configured, default to unwatched.
    return any(statuses)

# ----------------------------------------------------------------------------- 
# MCP Server implementation 
# -----------------------------------------------------------------------------

from radarr_sonarr_mcp.services.sonarr_service import SonarrService

class RadarrSonarrMCP:
    """MCP Server for Radarr and Sonarr."""
    
    def __init__(self):
        self.config = load_config()
        self.server = FastMCP(
            name="radarr-sonarr-mcp-server",
            description="MCP Server for Radarr and Sonarr media management"
        )
        self.sonarr_service = SonarrService(self.config["sonarrConfig"])
        self._register_tools()
        self._register_resources()
        # Optionally, register prompts.
    
    def _register_tools(self):
        @self.server.tool()
        def get_available_series(year: Optional[int] = None,
                                 downloaded: Optional[bool] = None,
                                 watched: Optional[bool] = None,
                                 actors: Optional[str] = None) -> dict:
            """
            Get a list of available TV series with optional filters.
            Watched status is determined using Plex and/or Jellyfin; if either reports watched, the series is considered watched.
            """
            all_series = get_all_series(self.config)  # List of Series objects
            filtered_series = all_series
            
            if year is not None:
                filtered_series = [s for s in filtered_series if s.year == year]
            
            if downloaded is not None:
                filtered_series = [
                    s for s in filtered_series 
                    if (s.statistics and s.statistics.episode_file_count > 0) == downloaded
                ]
            
            if watched is not None:
                if watched:
                    filtered_series = [
                        s for s in filtered_series 
                        if is_watched_series(s.title, False, self.config, self.sonarr_service)
                    ]
                else:
                    filtered_series = [
                        s for s in filtered_series 
                        if not is_watched_series(s.title, False, self.config, self.sonarr_service)
                    ]
            
            if actors:
                filtered_series = [
                    s for s in filtered_series 
                    if s.data.get("credits") and any(
                        actors.lower() in cast.get("name", "").lower()
                        for cast in s.data.get("credits", {}).get("cast", [])
                    )
                ]
            
            return {
                "count": len(filtered_series),
                "series": [
                    {
                        "id": s.id,
                        "title": s.title,
                        "year": s.year,
                        "overview": s.overview,
                        "status": s.status,
                        "network": s.network,
                        "genres": s.genres,
                        "watched": is_watched_series(s.title, False, self.config, self.sonarr_service)
                    }
                    for s in filtered_series
                ]
            }
        
        @self.server.tool()
        def lookup_series(term: str) -> dict:
            service = SonarrService(self.config["sonarrConfig"])
            results = service.lookup_series(term)
            return {
                "count": len(results),
                "series": [
                    {
                        "id": s.id,
                        "title": s.title,
                        "year": s.year,
                        "overview": s.overview
                    }
                    for s in results
                ]
            }
        
        # Similarly, for movies you can define a tool:
        @self.server.tool()
        def get_available_movies(year: Optional[int] = None,
                                 downloaded: Optional[bool] = None,
                                 watched: Optional[bool] = None,
                                 actors: Optional[str] = None) -> dict:
            """
            Get a list of all available movies with optional filters.
            Watched status is determined using Plex and/or Jellyfin.
            """
            # For movies, assume you have a function get_all_movies similar to get_all_series.
            from radarr_sonarr_mcp.services.radarr_service import RadarrService
            # You would need to instantiate a RadarrService and fetch movies.
            radarr_service = RadarrService(self.config["radarrConfig"])
            all_movies = radarr_service.get_all_movies()  # Assuming this returns a list of dicts
            filtered_movies = all_movies
            
            if year is not None:
                filtered_movies = [m for m in filtered_movies if m.get("year") == year]
            
            if downloaded is not None:
                filtered_movies = [m for m in filtered_movies if m.get("hasFile") == downloaded]
            
            if watched is not None:
                if watched:
                    filtered_movies = [
                        m for m in filtered_movies
                        if is_watched_movie(m.get("title", ""), self.config)
                    ]
                else:
                    filtered_movies = [
                        m for m in filtered_movies
                        if not is_watched_movie(m.get("title", ""), self.config)
                    ]
            
            if actors:
                filtered_movies = [
                    m for m in filtered_movies
                    if m.get("credits") and any(
                        actors.lower() in cast.get("name", "").lower()
                        for cast in m.get("credits", {}).get("cast", [])
                    )
                ]
            
            return {
                "count": len(filtered_movies),
                "movies": [
                    {
                        "id": m.get("id"),
                        "title": m.get("title"),
                        "year": m.get("year"),
                        "overview": m.get("overview"),
                        "hasFile": m.get("hasFile"),
                        "status": m.get("status"),
                        "genres": m.get("genres", []),
                        "watched": is_watched_movie(m.get("title", ""), self.config)
                    }
                    for m in filtered_movies
                ]
            }
    
    def _register_resources(self):
        @self.server.resource("http://example.com/series", description="TV series collection from Sonarr")
        def series() -> dict:
            series_list = get_all_series(self.config)
            return {
                "count": len(series_list),
                "series": [
                    {
                        "id": s.id,
                        "title": s.title,
                        "year": s.year
                    }
                    for s in series_list
                ]
            }
        @self.server.resource("http://example.com/movies", description="Movie collection from Radarr")
        def movies() -> dict:
            from radarr_sonarr_mcp.services.radarr_service import RadarrService
            radarr_service = RadarrService(self.config["radarrConfig"])
            movies_list = radarr_service.get_all_movies()  # Assuming list of dicts
            return {
                "count": len(movies_list),
                "movies": [
                    {
                        "id": m.get("id"),
                        "title": m.get("title"),
                        "year": m.get("year")
                    }
                    for m in movies_list
                ]
            }
    
    def run(self):
        port = self.config["server"]["port"]
        logger.info(f"Starting Radarr-Sonarr MCP Server on port {port}")
        logger.info(f"Connect Claude Desktop to: http://localhost:{port}")
        self.server.run()

if __name__ == "__main__":
    server = RadarrSonarrMCP()
    server.run()
