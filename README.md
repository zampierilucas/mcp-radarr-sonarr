# Radarr and Sonarr MCP Server

A Python-based Model Context Protocol (MCP) server that provides Claude Code with access to your Radarr (movies) and Sonarr (TV series) data.

## Overview

This MCP server allows Claude Code to query your movie and TV show collection via Radarr and Sonarr APIs. Built with the standard MCP protocol, it uses STDIO transport for seamless integration with Claude Code.

## Features

- **Standard MCP Implementation**: Built with the official MCP Python SDK
- **Claude Code Compatible**: Uses STDIO transport for direct integration
- **Radarr Integration**: Access your movie collection
- **Sonarr Integration**: Access your TV show and episode data
- **Rich Filtering**: Filter by monitored status, download status, and more
- **Separate URL Configuration**: Support for different servers/ports per service
- **Easy Setup**: Interactive configuration wizard
- **No HTTP Server Required**: Uses STDIO transport for better security and performance

## Installation

### From Source

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/radarr-sonarr-mcp.git
   cd radarr-sonarr-mcp
   ```

2. Install the package:
   ```bash
   pip install -e .
   ```

### Using pip (coming soon)

```bash
pip install radarr-sonarr-mcp
```

## Quick Start

1. Configure the server:
   ```bash
   radarr-sonarr-mcp configure
   ```
   Follow the prompts to enter your Radarr/Sonarr URLs and API keys.

2. Add to Claude Code configuration:
   Create or edit your Claude Code MCP configuration file and add this server.

## Configuration

The configuration wizard will guide you through setting up:

- Radarr URL (complete URL like `http://192.168.1.100:7878`)
- Radarr API key and base path
- Sonarr URL (complete URL like `http://192.168.1.100:8989`) 
- Sonarr API key and base path

### Manual Configuration

You can also manually edit the configuration file at `~/.config/radarr-sonarr-mcp/config.json`:

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

### Environment Variables

You can also configure via environment variables:

```bash
export RADARR_URL="http://192.168.1.100:7878"
export RADARR_API_KEY="your_radarr_api_key"
export SONARR_URL="http://192.168.1.100:8989"
export SONARR_API_KEY="your_sonarr_api_key"
```

## Claude Code Integration

To use this MCP server with Claude Code, add it to your MCP configuration:

### Method 1: Using Configuration File

Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "radarr-sonarr": {
      "command": "python",
      "args": ["-m", "radarr_sonarr_mcp.server"],
      "env": {
        "RADARR_URL": "http://your-radarr-server:7878",
        "RADARR_API_KEY": "your_radarr_api_key_here",
        "SONARR_URL": "http://your-sonarr-server:8989", 
        "SONARR_API_KEY": "your_sonarr_api_key_here"
      }
    }
  }
}
```

### Method 2: Using Installed Configuration

If you've run `radarr-sonarr-mcp configure`, you can use:

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

## Available MCP Tools

This server provides the following tools to Claude Code:

### Movies
- `get_radarr_movies` - Get a list of movies with optional filters (monitored, downloaded)
- `search_radarr_movies` - Search for movies by title
- `add_radarr_movie` - Add a movie to Radarr library and request download

### TV Series  
- `get_sonarr_series` - Get a list of TV series with optional filters (monitored, downloaded)
- `search_sonarr_series` - Search for TV series by title
- `add_sonarr_series` - Add a TV series to Sonarr library and request download

### Resources

The server also provides MCP resources:

- `radarr://movies` - Browse all movies in Radarr
- `sonarr://series` - Browse all TV series in Sonarr

### Filtering Options

Tools support these filtering options:

- `monitored` - Filter by monitored status (true/false)
- `downloaded` - Filter by download status (true/false)

## Example Queries for Claude Code

Once your MCP server is connected to Claude Code, you can ask questions like:

### Browsing and Searching
- "What movies do I have in Radarr?"
- "Show me unmonitored TV shows in Sonarr"
- "Find movies that haven't been downloaded yet"  
- "Search for 'Inception' in my movie collection"
- "How many TV series do I have downloaded?"

### Adding Movies and TV Shows
- "Search for the movie 'Dune' and add it to my library"
- "Find 'The Mandalorian' and add it to Sonarr with automatic download"
- "Add 'Avatar: The Way of Water' to Radarr and start downloading"
- "Search for 'Stranger Things' and add all seasons to my library"

## Finding API Keys

### Radarr API Key
1. Open Radarr in your browser
2. Go to Settings > General
3. Find the "API Key" section
4. Copy the API Key

### Sonarr API Key
1. Open Sonarr in your browser  
2. Go to Settings > General
3. Find the "API Key" section
4. Copy the API Key

## Command-Line Interface

The package provides a command-line interface:

- `radarr-sonarr-mcp configure` - Run configuration wizard
- `radarr-sonarr-mcp start` - Start the MCP server (for testing only)
- `radarr-sonarr-mcp status` - Show the current configuration

**Note:** Claude Code will automatically start the MCP server when needed. The `start` command is mainly for testing purposes.

## Development

### Running Tests

To run the test suite:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=radarr_sonarr_mcp
```

### Testing the MCP Server

You can test the MCP server directly:

```bash
# Test MCP protocol communication
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}' | python -m radarr_sonarr_mcp.server
```

## Requirements

- Python 3.10+
- MCP SDK
- Requests
- Pydantic

## Architecture

This MCP server uses:

- **Transport**: STDIO (Standard Input/Output) for Claude Code integration
- **Protocol**: Standard MCP (Model Context Protocol)
- **No HTTP Server**: Direct communication via STDIO for better security and performance

## Security Notes

- The server communicates with Claude Code via STDIO, eliminating the need for HTTP endpoints
- API keys are stored locally in your configuration file
- All communication happens locally on your machine
- For additional security, ensure your Radarr/Sonarr instances are properly secured