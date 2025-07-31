"""Extended handlers for Radarr and Sonarr MCP server."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

logger = logging.getLogger(__name__)


def handle_download_queue(config: Dict[str, Any], service: str, include_unknown: bool = False) -> str:
    """Handle get_download_queue requests."""
    from .server import make_radarr_request, make_sonarr_request
    
    lines = ["Download Queue:"]
    
    if service in ["radarr", "both"]:
        params = {"includeUnknownMovieItems": include_unknown}
        radarr_queue = make_radarr_request(config, "queue", params=params)
        
        items = radarr_queue.get("records", [])
        if items:
            lines.append(f"\nRADAR ({len(items)} items):")
            for item in items[:50]:
                title = item.get("title", "Unknown")
                status = item.get("status", "Unknown")
                size = item.get("size", 0)
                size_left = item.get("sizeleft", 0)
                progress = ""
                if size > 0:
                    progress_pct = ((size - size_left) / size * 100)
                    progress = f" ({progress_pct:.1f}%)"
                lines.append(f"  {title} - {status}{progress}")
        else:
            lines.append("\nRADAR: Empty")
    
    if service in ["sonarr", "both"]:
        params = {"includeUnknownSeriesItems": include_unknown}
        sonarr_queue = make_sonarr_request(config, "queue", params=params)
        
        items = sonarr_queue.get("records", [])
        if items:
            lines.append(f"\nSONARR ({len(items)} items):")
            for item in items[:50]:
                title = item.get("title", "Unknown")
                status = item.get("status", "Unknown")
                size = item.get("size", 0)
                size_left = item.get("sizeleft", 0)
                progress = ""
                if size > 0:
                    progress_pct = ((size - size_left) / size * 100)
                    progress = f" ({progress_pct:.1f}%)"
                lines.append(f"  {title} - {status}{progress}")
        else:
            lines.append("\nSONARR: Empty")
    
    if len(lines) == 1:  # Only header
        return "Download queue is empty."
    
    return "\n".join(lines)


def handle_remove_from_queue(config: Dict[str, Any], service: str, queue_id: int, 
                            remove_from_client: bool = True, blocklist: bool = False) -> Dict[str, Any]:
    """Handle remove_from_queue requests."""
    from .server import make_radarr_request, make_sonarr_request
    
    params = {
        "removeFromClient": remove_from_client,
        "blocklist": blocklist
    }
    
    if service == "radarr":
        # Radarr uses DELETE method with query parameters
        from .server import get_radarr_url
        import requests
        
        base_url = get_radarr_url(config)
        api_key = config["radarrConfig"]["apiKey"]
        headers = {"X-Api-Key": api_key}
        url = f"{base_url}/queue/{queue_id}"
        
        response = requests.delete(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
    else:  # sonarr
        from .server import get_sonarr_url
        import requests
        
        base_url = get_sonarr_url(config)
        api_key = config["sonarrConfig"]["apiKey"]
        headers = {"X-Api-Key": api_key}
        url = f"{base_url}/queue/{queue_id}"
        
        response = requests.delete(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
    
    return {
        "success": True,
        "message": f"Queue item {queue_id} has been removed from {service}",
        "removeFromClient": remove_from_client,
        "blocklist": blocklist
    }


def handle_get_history(config: Dict[str, Any], service: str, page_size: int = 50, 
                      page: int = 1, event_type: str = None) -> Dict[str, Any]:
    """Handle get_history requests."""
    from .server import make_radarr_request, make_sonarr_request
    
    params = {
        "pageSize": page_size,
        "page": page,
        "sortKey": "date",
        "sortDirection": "descending"
    }
    
    if event_type:
        params["eventType"] = event_type
    
    if service == "radarr":
        history = make_radarr_request(config, "history", params=params)
    else:
        history = make_sonarr_request(config, "history", params=params)
    
    return {
        "page": history.get("page", 1),
        "pageSize": history.get("pageSize", page_size),
        "totalRecords": history.get("totalRecords", 0),
        "records": [
            {
                "id": record.get("id"),
                "movieId": record.get("movieId"),
                "seriesId": record.get("seriesId"),
                "episodeId": record.get("episodeId"),
                "sourceTitle": record.get("sourceTitle"),
                "quality": record.get("quality", {}),
                "date": record.get("date"),
                "eventType": record.get("eventType"),
                "data": record.get("data", {})
            }
            for record in history.get("records", [])
        ]
    }


def handle_manual_import(config: Dict[str, Any], service: str, path: str, 
                        movie_id: int = None, series_id: int = None) -> Dict[str, Any]:
    """Handle manual_import requests."""
    from .server import make_radarr_request, make_sonarr_request
    
    params = {"path": path}
    
    if service == "radarr":
        if movie_id:
            params["movieId"] = movie_id
        items = make_radarr_request(config, "manualimport", params=params)
    else:
        if series_id:
            params["seriesId"] = series_id
        items = make_sonarr_request(config, "manualimport", params=params)
    
    return {
        "count": len(items),
        "items": [
            {
                "path": item.get("path"),
                "relativePath": item.get("relativePath"),
                "name": item.get("name"),
                "size": item.get("size", 0),
                "quality": item.get("quality", {}),
                "movie": item.get("movie"),
                "series": item.get("series"),
                "episodes": item.get("episodes", []),
                "rejections": item.get("rejections", [])
            }
            for item in items[:50]
        ]
    }


def handle_calendar(config: Dict[str, Any], service: str, start: str = None, 
                   end: str = None, unmonitored: bool = False) -> Dict[str, Any]:
    """Handle calendar requests."""
    from .server import make_radarr_request, make_sonarr_request
    
    # Default to next 30 days if not specified
    if not start:
        start = datetime.utcnow().isoformat() + "Z"
    if not end:
        end = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
    
    params = {
        "start": start,
        "end": end,
        "unmonitored": unmonitored
    }
    
    if service == "radarr":
        items = make_radarr_request(config, "calendar", params=params)
        return {
            "count": len(items),
            "movies": [
                {
                    "id": movie.get("id"),
                    "title": movie.get("title"),
                    "releaseDate": movie.get("releaseDate"),
                    "inCinemas": movie.get("inCinemas"),
                    "physicalRelease": movie.get("physicalRelease"),
                    "digitalRelease": movie.get("digitalRelease"),
                    "monitored": movie.get("monitored"),
                    "hasFile": movie.get("hasFile", False)
                }
                for movie in items
            ]
        }
    else:
        items = make_sonarr_request(config, "calendar", params=params)
        return {
            "count": len(items),
            "episodes": [
                {
                    "id": ep.get("id"),
                    "seriesId": ep.get("seriesId"),
                    "episodeNumber": ep.get("episodeNumber"),
                    "seasonNumber": ep.get("seasonNumber"),
                    "title": ep.get("title"),
                    "airDate": ep.get("airDate"),
                    "airDateUtc": ep.get("airDateUtc"),
                    "monitored": ep.get("monitored"),
                    "hasFile": ep.get("hasFile", False),
                    "series": {
                        "title": ep.get("series", {}).get("title"),
                        "year": ep.get("series", {}).get("year")
                    }
                }
                for ep in items
            ]
        }


def handle_wanted(config: Dict[str, Any], service: str, missing: bool = True, 
                 page_size: int = 50, page: int = 1, sort_key: str = None, 
                 sort_dir: str = None) -> Dict[str, Any]:
    """Handle wanted missing/cutoff requests."""
    from .server import make_radarr_request, make_sonarr_request
    
    params = {
        "pageSize": page_size,
        "page": page
    }
    
    if sort_key:
        params["sortKey"] = sort_key
    if sort_dir:
        params["sortDirection"] = sort_dir
    
    endpoint = "wanted/missing" if missing else "wanted/cutoff"
    
    if service == "radarr":
        wanted = make_radarr_request(config, endpoint, params=params)
        return {
            "page": wanted.get("page", 1),
            "pageSize": wanted.get("pageSize", page_size),
            "totalRecords": wanted.get("totalRecords", 0),
            "records": [
                {
                    "id": movie.get("id"),
                    "title": movie.get("title"),
                    "year": movie.get("year"),
                    "monitored": movie.get("monitored"),
                    "status": movie.get("status"),
                    "minimumAvailability": movie.get("minimumAvailability")
                }
                for movie in wanted.get("records", [])
            ]
        }
    else:
        wanted = make_sonarr_request(config, endpoint, params=params)
        return {
            "page": wanted.get("page", 1),
            "pageSize": wanted.get("pageSize", page_size),
            "totalRecords": wanted.get("totalRecords", 0),
            "records": [
                {
                    "id": ep.get("id"),
                    "seriesId": ep.get("seriesId"),
                    "episodeNumber": ep.get("episodeNumber"),
                    "seasonNumber": ep.get("seasonNumber"),
                    "title": ep.get("title"),
                    "airDate": ep.get("airDate"),
                    "monitored": ep.get("monitored"),
                    "series": {
                        "title": ep.get("series", {}).get("title"),
                        "year": ep.get("series", {}).get("year")
                    }
                }
                for ep in wanted.get("records", [])
            ]
        }


def handle_system_status(config: Dict[str, Any], service: str) -> Dict[str, Any]:
    """Handle system status requests."""
    from .server import make_radarr_request, make_sonarr_request
    
    result = {"status": {}}
    
    if service in ["radarr", "both"]:
        status = make_radarr_request(config, "system/status")
        health = make_radarr_request(config, "health")
        
        result["status"]["radarr"] = {
            "version": status.get("version"),
            "buildTime": status.get("buildTime"),
            "isDebug": status.get("isDebug"),
            "isProduction": status.get("isProduction"),
            "isAdmin": status.get("isAdmin"),
            "isUserInteractive": status.get("isUserInteractive"),
            "startupPath": status.get("startupPath"),
            "appData": status.get("appData"),
            "osName": status.get("osName"),
            "osVersion": status.get("osVersion"),
            "branch": status.get("branch"),
            "authentication": status.get("authentication"),
            "urlBase": status.get("urlBase"),
            "health": [
                {
                    "source": h.get("source"),
                    "type": h.get("type"),
                    "message": h.get("message"),
                    "wikiUrl": h.get("wikiUrl")
                }
                for h in health
            ]
        }
    
    if service in ["sonarr", "both"]:
        status = make_sonarr_request(config, "system/status")
        health = make_sonarr_request(config, "health")
        
        result["status"]["sonarr"] = {
            "version": status.get("version"),
            "buildTime": status.get("buildTime"),
            "isDebug": status.get("isDebug"),
            "isProduction": status.get("isProduction"),
            "isAdmin": status.get("isAdmin"),
            "isUserInteractive": status.get("isUserInteractive"),
            "startupPath": status.get("startupPath"),
            "appData": status.get("appData"),
            "osName": status.get("osName"),
            "osVersion": status.get("osVersion"),
            "branch": status.get("branch"),
            "authentication": status.get("authentication"),
            "urlBase": status.get("urlBase"),
            "health": [
                {
                    "source": h.get("source"),
                    "type": h.get("type"),
                    "message": h.get("message"),
                    "wikiUrl": h.get("wikiUrl")
                }
                for h in health
            ]
        }
    
    return result


def handle_disk_space(config: Dict[str, Any], service: str) -> Dict[str, Any]:
    """Handle disk space requests."""
    from .server import make_radarr_request, make_sonarr_request
    
    result = {"diskSpace": {}}
    
    if service in ["radarr", "both"]:
        disk_space = make_radarr_request(config, "diskspace")
        result["diskSpace"]["radarr"] = [
            {
                "path": disk.get("path"),
                "label": disk.get("label"),
                "freeSpace": disk.get("freeSpace", 0),
                "totalSpace": disk.get("totalSpace", 0),
                "percentUsed": round((1 - disk.get("freeSpace", 0) / disk.get("totalSpace", 1)) * 100, 2)
            }
            for disk in disk_space
        ]
    
    if service in ["sonarr", "both"]:
        disk_space = make_sonarr_request(config, "diskspace")
        result["diskSpace"]["sonarr"] = [
            {
                "path": disk.get("path"),
                "label": disk.get("label"),
                "freeSpace": disk.get("freeSpace", 0),
                "totalSpace": disk.get("totalSpace", 0),
                "percentUsed": round((1 - disk.get("freeSpace", 0) / disk.get("totalSpace", 1)) * 100, 2)
            }
            for disk in disk_space
        ]
    
    return result


def handle_execute_command(config: Dict[str, Any], service: str, command: str,
                          movie_id: int = None, series_id: int = None) -> Dict[str, Any]:
    """Handle execute command requests."""
    from .server import make_radarr_request, make_sonarr_request
    
    command_data = {"name": command}
    
    # Add specific IDs if provided
    if movie_id and service == "radarr":
        command_data["movieIds"] = [movie_id]
    elif series_id and service == "sonarr":
        command_data["seriesId"] = series_id
    
    if service == "radarr":
        result = make_radarr_request(config, "command", method="POST", json_data=command_data)
    else:
        result = make_sonarr_request(config, "command", method="POST", json_data=command_data)
    
    return {
        "success": True,
        "message": f"Command '{command}' has been queued",
        "command": {
            "id": result.get("id"),
            "name": result.get("name"),
            "status": result.get("status"),
            "queued": result.get("queued"),
            "started": result.get("started"),
            "trigger": result.get("trigger"),
            "stateChangeTime": result.get("stateChangeTime")
        }
    }


def handle_get_collections(config: Dict[str, Any], tmdb_id: int = None) -> Dict[str, Any]:
    """Handle get collections requests."""
    from .server import make_radarr_request
    
    params = {}
    if tmdb_id:
        params["tmdbId"] = tmdb_id
    
    collections = make_radarr_request(config, "collection", params=params)
    
    return {
        "count": len(collections),
        "collections": [
            {
                "id": coll.get("id"),
                "title": coll.get("title"),
                "tmdbId": coll.get("tmdbId"),
                "monitored": coll.get("monitored"),
                "qualityProfileId": coll.get("qualityProfileId"),
                "rootFolderPath": coll.get("rootFolderPath"),
                "minimumAvailability": coll.get("minimumAvailability"),
                "movies": [
                    {
                        "tmdbId": movie.get("tmdbId"),
                        "title": movie.get("title"),
                        "year": movie.get("year"),
                        "runtime": movie.get("runtime"),
                        "overview": movie.get("overview", "")[:200] + "..." if len(movie.get("overview", "")) > 200 else movie.get("overview", "")
                    }
                    for movie in coll.get("movies", [])
                ]
            }
            for coll in collections
        ]
    }


def handle_refresh_monitored(config: Dict[str, Any], service: str) -> Dict[str, Any]:
    """Handle refresh monitored requests."""
    # This uses the execute_command handler with specific commands
    if service == "radarr":
        return handle_execute_command(config, service, "RefreshMovie")
    else:
        return handle_execute_command(config, service, "RefreshSeries")