# Radarr and Sonarr MCP Server

A Python-based Model Context Protocol (MCP) server that provides comprehensive access to your Radarr (movies) and Sonarr (TV series) media libraries.

Based on the original work by [hannesrudolph/mcp-server-radarr-sonarr](https://github.com/hannesrudolph/mcp-server-radarr-sonarr), this fork adds extensive functionality with 28 tools for complete media library management.

## Installation

```bash
# Install latest version directly from GitHub
pip install git+https://github.com/zampierilucas/mcp-radarr-sonarr.git

# Install from source (for development)
git clone https://github.com/zampierilucas/mcp-radarr-sonarr.git
cd mcp-radarr-sonarr
pip install -e .
```

## Quick Start

1. Configure the server:
   ```bash
   radarr-sonarr-mcp configure
   ```

2. Add to Claude Code MCP configuration:
   ```json
   {
     "mcpServers": {
       "radarr-sonarr": {
         "command": "python",
         "args": ["-m", "radarr_sonarr_mcp.server"]
       }
     }
   }
   ```

## Available Tools

### Media Management
- `get_radarr_movies` - List movies with filters (monitored/downloaded)
- `get_sonarr_series` - List TV series with filters
- `search_radarr_movies` - Search movies by title
- `search_sonarr_series` - Search TV series by title
- `add_radarr_movie` - Add movie and request download
- `add_sonarr_series` - Add TV series and request download
- `delete_radarr_movie` - Remove movie from library
- `delete_sonarr_series` - Remove TV series from library
- `update_radarr_movie` - Update movie settings (monitoring, quality)
- `update_sonarr_series` - Update series settings
- `get_radarr_movie_by_id` - Get detailed movie information
- `get_sonarr_series_by_id` - Get detailed series information

### Episode Management (Sonarr)
- `get_sonarr_episodes` - List episodes for a series
- `monitor_sonarr_episodes` - Bulk update episode monitoring
- `get_sonarr_episode_files` - Get downloaded episode files

### Download Management
- `get_download_queue` - View current downloads (both services)
- `remove_from_queue` - Cancel/remove downloads
- `get_history` - View download/import history
- `manual_import` - Manually import downloaded files

### Calendar & Scheduling
- `get_radarr_calendar` - Upcoming movie releases
- `get_sonarr_calendar` - Upcoming episode releases
- `get_wanted_missing` - Missing movies/episodes
- `get_wanted_cutoff` - Items below quality cutoff

### System & Configuration
- `get_system_status` - Health checks and version info
- `get_disk_space` - Storage availability
- `execute_command` - Run maintenance tasks (refresh, RSS sync, backup)

### Collections & Import Lists
- `get_collections` - Movie collections (Radarr)
- `refresh_monitored` - Force refresh of monitored items

### Resources
- `radarr://movies` - Browse all movies
- `sonarr://series` - Browse all TV series

## Configuration

Run `radarr-sonarr-mcp configure` or manually edit `~/.config/radarr-sonarr-mcp/config.json`:

```json
{
  "radarr_config": {
    "api_key": "YOUR_RADARR_API_KEY",
    "url": "http://192.168.1.100:7878",
    "base_path": "/api/v3"
  },
  "sonarr_config": {
    "api_key": "YOUR_SONARR_API_KEY",
    "url": "http://192.168.1.100:8989",
    "base_path": "/api/v3"
  }
}
```

## Finding API Keys

**Radarr**: Settings > General > API Key  
**Sonarr**: Settings > General > API Key

## Example Usage

Ask Claude Code:
- "Show me all undownloaded movies"
- "Add Breaking Bad to my library"
- "What's on the download queue?"
- "Delete all unmonitored series"
- "Show upcoming movie releases this month"
- "Check disk space on my media server"

## Requirements

- Python 3.10+
- MCP SDK
- Radarr/Sonarr instances with API access

## Security

- Uses STDIO transport (no HTTP endpoints)
- API keys stored locally
- All communication happens on your machine