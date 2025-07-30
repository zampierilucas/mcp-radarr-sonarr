"""Extended tools for Radarr and Sonarr MCP server."""

import mcp.types as types


def get_extended_tools():
    """Get list of extended tools for download management, calendar, and system."""
    return [
        # Download Management
        types.Tool(
            name="get_download_queue",
            description="Get current download queue for Radarr and Sonarr",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Which service to query",
                        "enum": ["radarr", "sonarr", "both"]
                    },
                    "includeUnknownItems": {
                        "type": "boolean",
                        "description": "Include items with unknown series/movie",
                        "default": False
                    }
                },
                "required": ["service"],
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="remove_from_queue",
            description="Remove an item from the download queue",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Which service to use",
                        "enum": ["radarr", "sonarr"]
                    },
                    "id": {
                        "type": "integer",
                        "description": "Queue item ID to remove"
                    },
                    "removeFromClient": {
                        "type": "boolean",
                        "description": "Remove from download client",
                        "default": True
                    },
                    "blocklist": {
                        "type": "boolean",
                        "description": "Add to blocklist to prevent re-download",
                        "default": False
                    }
                },
                "required": ["service", "id"],
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="get_history",
            description="Get download/import history",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Which service to query",
                        "enum": ["radarr", "sonarr"]
                    },
                    "pageSize": {
                        "type": "integer",
                        "description": "Number of items per page",
                        "default": 50
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number",
                        "default": 1
                    },
                    "eventType": {
                        "type": "string",
                        "description": "Filter by event type",
                        "enum": ["grabbed", "downloadFolderImported", "downloadFailed", "deleted", "renamed"]
                    }
                },
                "required": ["service"],
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="manual_import",
            description="Manually import downloaded files",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Which service to use",
                        "enum": ["radarr", "sonarr"]
                    },
                    "path": {
                        "type": "string",
                        "description": "Path to scan for importable files"
                    },
                    "movieId": {
                        "type": "integer",
                        "description": "Movie ID (for Radarr)"
                    },
                    "seriesId": {
                        "type": "integer",
                        "description": "Series ID (for Sonarr)"
                    }
                },
                "required": ["service", "path"],
                "additionalProperties": False
            }
        ),
        # Calendar & Scheduling
        types.Tool(
            name="get_radarr_calendar",
            description="Get upcoming movie releases",
            inputSchema={
                "type": "object",
                "properties": {
                    "start": {
                        "type": "string",
                        "description": "Start date (ISO format)"
                    },
                    "end": {
                        "type": "string",
                        "description": "End date (ISO format)"
                    },
                    "unmonitored": {
                        "type": "boolean",
                        "description": "Include unmonitored movies",
                        "default": False
                    }
                },
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="get_sonarr_calendar",
            description="Get upcoming episode releases",
            inputSchema={
                "type": "object",
                "properties": {
                    "start": {
                        "type": "string",
                        "description": "Start date (ISO format)"
                    },
                    "end": {
                        "type": "string",
                        "description": "End date (ISO format)"
                    },
                    "unmonitored": {
                        "type": "boolean",
                        "description": "Include unmonitored episodes",
                        "default": False
                    }
                },
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="get_wanted_missing",
            description="Get missing movies or episodes",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Which service to query",
                        "enum": ["radarr", "sonarr"]
                    },
                    "pageSize": {
                        "type": "integer",
                        "description": "Number of items per page",
                        "default": 50
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number",
                        "default": 1
                    },
                    "sortKey": {
                        "type": "string",
                        "description": "Sort by field",
                        "enum": ["title", "airDateUtc", "releaseDate", "year"]
                    },
                    "sortDir": {
                        "type": "string",
                        "description": "Sort direction",
                        "enum": ["asc", "desc"]
                    }
                },
                "required": ["service"],
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="get_wanted_cutoff",
            description="Get items not meeting quality cutoff",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Which service to query",
                        "enum": ["radarr", "sonarr"]
                    },
                    "pageSize": {
                        "type": "integer",
                        "description": "Number of items per page",
                        "default": 50
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number",
                        "default": 1
                    }
                },
                "required": ["service"],
                "additionalProperties": False
            }
        ),
        # System & Configuration
        types.Tool(
            name="get_system_status",
            description="Get system status and health checks",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Which service to query",
                        "enum": ["radarr", "sonarr", "both"]
                    }
                },
                "required": ["service"],
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="get_disk_space",
            description="Get disk space information",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Which service to query",
                        "enum": ["radarr", "sonarr", "both"]
                    }
                },
                "required": ["service"],
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="execute_command",
            description="Execute maintenance commands",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Which service to use",
                        "enum": ["radarr", "sonarr"]
                    },
                    "command": {
                        "type": "string",
                        "description": "Command to execute",
                        "enum": ["RefreshMovie", "RefreshSeries", "RescanMovie", "RescanSeries", "RssSync", "Backup", "MissingMoviesSearch", "MissingEpisodeSearch"]
                    },
                    "movieId": {
                        "type": "integer",
                        "description": "Movie ID (for movie-specific commands)"
                    },
                    "seriesId": {
                        "type": "integer",
                        "description": "Series ID (for series-specific commands)"
                    }
                },
                "required": ["service", "command"],
                "additionalProperties": False
            }
        ),
        # Import Lists & Collections
        types.Tool(
            name="get_collections",
            description="Get movie collections from Radarr",
            inputSchema={
                "type": "object",
                "properties": {
                    "tmdbId": {
                        "type": "integer",
                        "description": "Filter by collection TMDB ID"
                    }
                },
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="refresh_monitored",
            description="Force refresh of monitored items",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Which service to use",
                        "enum": ["radarr", "sonarr"]
                    }
                },
                "required": ["service"],
                "additionalProperties": False
            }
        )
    ]