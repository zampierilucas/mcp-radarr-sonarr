"""Tests for the MCP server implementation."""

import unittest
import json
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Add parent directory to path to import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from radarr_sonarr_mcp.config import Config, NasConfig, RadarrConfig, SonarrConfig, ServerConfig
from radarr_sonarr_mcp.server import RadarrSonarrMCPServer, create_server
from radarr_sonarr_mcp.services.radarr_service import Movie
from radarr_sonarr_mcp.services.sonarr_service import Series, Statistics


class TestRadarrSonarrMCPServer(unittest.TestCase):
    """Test suite for the RadarrSonarrMCPServer class."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary config file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        config_data = {
            "nasConfig": {
                "ip": "127.0.0.1",
                "port": "7878"
            },
            "radarrConfig": {
                "apiKey": "test_radarr_api_key",
                "basePath": "/api/v3",
                "port": "7878"
            },
            "sonarrConfig": {
                "apiKey": "test_sonarr_api_key",
                "basePath": "/api/v3",
                "port": "8989"
            },
            "server": {
                "port": 5000
            }
        }
        with open(self.temp_file.name, 'w') as f:
            json.dump(config_data, f)
        
        # Create sample movie and series data
        self.sample_movies = [
            Movie(
                id=1,
                title="Test Movie 1",
                year=2022,
                overview="A test movie",
                has_file=True,
                status="downloaded",
                genres=["Action", "Comedy"],
                tags=[1, 2],
                data={
                    "id": 1,
                    "title": "Test Movie 1",
                    "year": 2022,
                    "overview": "A test movie",
                    "hasFile": True,
                    "status": "downloaded",
                    "genres": ["Action", "Comedy"],
                    "tags": [1, 2],
                    "credits": {
                        "cast": [
                            {"name": "Actor One", "character": "Character One"},
                            {"name": "Actress One", "character": "Character Two"}
                        ]
                    }
                }
            ),
            Movie(
                id=2,
                title="Test Movie 2",
                year=2023,
                overview="Another test movie",
                has_file=False,
                status="wanted",
                genres=["Drama", "Thriller"],
                tags=[2],
                data={
                    "id": 2,
                    "title": "Test Movie 2",
                    "year": 2023,
                    "overview": "Another test movie",
                    "hasFile": False,
                    "status": "wanted",
                    "genres": ["Drama", "Thriller"],
                    "tags": [2],
                    "credits": {
                        "cast": [
                            {"name": "Actor Two", "character": "Character Three"}
                        ]
                    }
                }
            )
        ]

        self.sample_series = [
            Series(
                id=1,
                title="Test Series 1",
                year=2022,
                overview="A test series",
                status="continuing",
                network="Test Network",
                tags=[1],
                genres=["Comedy"],
                statistics=Statistics.from_dict({
                    "episodeFileCount": 10,
                    "episodeCount": 10,
                    "totalEpisodeCount": 20,
                    "sizeOnDisk": 10000
                }),
                data={
                    "id": 1,
                    "title": "Test Series 1",
                    "year": 2022,
                    "overview": "A test series",
                    "status": "continuing",
                    "network": "Test Network",
                    "tags": [1],
                    "genres": ["Comedy"],
                    "statistics": {
                        "episodeFileCount": 10,
                        "episodeCount": 10,
                        "totalEpisodeCount": 20,
                        "sizeOnDisk": 10000
                    },
                    "credits": {
                        "cast": [
                            {"name": "Actor Three", "character": "Character Four"}
                        ]
                    }
                }
            )
        ]

    def tearDown(self):
        """Clean up after tests."""
        self.temp_file.close()
        os.unlink(self.temp_file.name)

    @patch('radarr_sonarr_mcp.server.FastMCP')
    def test_server_initialization(self, mock_fastmcp):
        """Test server initialization with config file."""
        server = create_server(self.temp_file.name)
        self.assertEqual(server.config.radarr_config.api_key, "test_radarr_api_key")
        self.assertEqual(server.config.sonarr_config.api_key, "test_sonarr_api_key")
        self.assertEqual(server.config.server_config.port, 5000)
        
        # Check that FastMCP was initialized correctly
        mock_fastmcp.assert_called_once()
        self.assertEqual(mock_fastmcp.call_args[1]['name'], "radarr-sonarr-mcp-server")

    @patch('radarr_sonarr_mcp.server.RadarrService')
    @patch('radarr_sonarr_mcp.server.SonarrService')
    @patch('radarr_sonarr_mcp.server.FastMCP')
    def test_get_available_movies(self, mock_fastmcp, mock_sonarr_service, mock_radarr_service):
        """Test the get_available_movies tool."""
        # Setup mocks
        mock_radarr_instance = mock_radarr_service.return_value
        mock_radarr_instance.get_all_movies.return_value = self.sample_movies
        mock_radarr_instance.is_movie_watched.return_value = True
        mock_radarr_instance.is_movie_in_watchlist.return_value = False
        
        mock_server = mock_fastmcp.return_value
        
        # Create server and register tools
        server = create_server(self.temp_file.name)
        
        # Extract the registered tool function
        tool_decorator = mock_server.tool.return_value
        get_movies_func = None
        for call in tool_decorator.call_args_list:
            # The decorated function is passed to the decorator
            if call.args and call.args[0].__name__ == 'get_available_movies':
                get_movies_func = call.args[0]
                break
        
        self.assertIsNotNone(get_movies_func, "get_available_movies tool not registered")
        
        # Test the tool function
        result = get_movies_func(year=2022)
        result_data = json.loads(result)
        
        # Check results
        self.assertEqual(result_data['count'], 1)
        self.assertEqual(result_data['movies'][0]['title'], "Test Movie 1")
        self.assertEqual(result_data['movies'][0]['year'], 2022)

    @patch('radarr_sonarr_mcp.server.SonarrService')
    @patch('radarr_sonarr_mcp.server.RadarrService')
    @patch('radarr_sonarr_mcp.server.FastMCP')
    def test_get_available_series(self, mock_fastmcp, mock_radarr_service, mock_sonarr_service):
        """Test the get_available_series tool."""
        # Setup mocks
        mock_sonarr_instance = mock_sonarr_service.return_value
        mock_sonarr_instance.get_all_series.return_value = self.sample_series
        mock_sonarr_instance.is_series_watched.return_value = True
        mock_sonarr_instance.is_series_in_watchlist.return_value = False
        
        mock_server = mock_fastmcp.return_value
        
        # Create server and register tools
        server = create_server(self.temp_file.name)
        
        # Extract the registered tool function
        tool_decorator = mock_server.tool.return_value
        get_series_func = None
        for call in tool_decorator.call_args_list:
            # The decorated function is passed to the decorator
            if call.args and call.args[0].__name__ == 'get_available_series':
                get_series_func = call.args[0]
                break
        
        self.assertIsNotNone(get_series_func, "get_available_series tool not registered")
        
        # Test the tool function
        result = get_series_func()
        result_data = json.loads(result)
        
        # Check results
        self.assertEqual(result_data['count'], 1)
        self.assertEqual(result_data['series'][0]['title'], "Test Series 1")
        self.assertEqual(result_data['series'][0]['year'], 2022)

    @patch('radarr_sonarr_mcp.server.RadarrService')
    @patch('radarr_sonarr_mcp.server.SonarrService')
    @patch('radarr_sonarr_mcp.server.FastMCP')
    def test_server_resources(self, mock_fastmcp, mock_sonarr_service, mock_radarr_service):
        """Test registered resources."""
        # Setup mocks
        mock_radarr_instance = mock_radarr_service.return_value
        mock_radarr_instance.get_all_movies.return_value = self.sample_movies
        
        mock_sonarr_instance = mock_sonarr_service.return_value
        mock_sonarr_instance.get_all_series.return_value = self.sample_series
        
        mock_server = mock_fastmcp.return_value
        
        # Create server and register resources
        server = create_server(self.temp_file.name)

        # Mock get_resource_handler to return MagicMock objects
        mock_server_instance = mock_fastmcp.return_value
        mock_server_instance.get_resource_handler.side_effect = lambda path: MagicMock(return_value={
            '/movies': {"count": 2, "movies": self.sample_movies},
            '/series': {"count": 1, "series": self.sample_series}
        }.get(path))

        # Test movies resource
        movies_resource = server.server.get_resource_handler('/movies')
        self.assertIsNotNone(movies_resource, "Movies resource not registered")
        result_movies = movies_resource()
        self.assertEqual(result_movies['count'], 2)
        self.assertEqual(len(result_movies['movies']), 2)

        # Test series resource
        series_resource = server.server.get_resource_handler('/series')
        self.assertIsNotNone(series_resource, "Series resource not registered")
        result_series = series_resource()
        self.assertEqual(result_series['count'], 1)
        self.assertEqual(len(result_series['series']), 1)


if __name__ == '__main__':
    unittest.main()
