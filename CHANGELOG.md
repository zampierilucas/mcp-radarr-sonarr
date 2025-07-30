# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-12-30

### Added
- 22 new tools for comprehensive media library management
- Complete CRUD operations for movies and series
- Episode management tools for Sonarr (list, monitor, files)
- Download queue management and history tracking
- Calendar views for upcoming releases
- Wanted/missing item tracking
- System status and disk space monitoring
- Maintenance command execution
- Movie collections support
- Modular code structure with separate files for extended tools

### Changed
- Reorganized code into modular structure
- Updated README with complete tool listing
- Improved pyproject.toml for PyPI publishing

### Credits
- Based on original work by [hannesrudolph/mcp-server-radarr-sonarr](https://github.com/hannesrudolph/mcp-server-radarr-sonarr)

## [0.1.0] - 2024-12-29

### Initial Release
- Basic Radarr and Sonarr integration
- List movies and series
- Search functionality
- Add movies and series
- MCP protocol support
- STDIO transport for Claude Code integration