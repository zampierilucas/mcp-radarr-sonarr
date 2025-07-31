"""Response formatter to make API responses more concise and Claude-friendly."""

import json
from datetime import datetime
from typing import Any, Dict, List


def format_response(result: Dict[str, Any], tool_name: str) -> str:
    """Format API response into a concise, readable format."""
    
    if tool_name in ["get_radarr_movies", "get_sonarr_series"]:
        return _format_media_list(result, tool_name)
    elif tool_name in ["search_radarr_movies", "search_sonarr_series"]:
        return _format_search_results(result, tool_name)
    elif tool_name in ["get_radarr_movie_by_id", "get_sonarr_series_by_id"]:
        return _format_media_details(result, tool_name)
    elif tool_name == "get_sonarr_episodes":
        return _format_episodes(result)
    elif tool_name == "get_download_queue":
        return _format_download_queue(result)
    elif tool_name == "get_history":
        return _format_history(result)
    elif tool_name in ["get_radarr_calendar", "get_sonarr_calendar"]:
        return _format_calendar(result, tool_name)
    elif tool_name in ["get_wanted_missing", "get_wanted_cutoff"]:
        return _format_wanted(result, tool_name)
    elif tool_name == "get_system_status":
        return _format_system_status(result)
    elif tool_name == "get_disk_space":
        return _format_disk_space(result)
    elif "success" in result:
        return _format_success_message(result)
    else:
        # Default fallback for other responses
        return json.dumps(result, indent=2)


def _format_media_list(result: Dict[str, Any], tool_name: str) -> str:
    """Format movie/series list responses."""
    media_type = "movies" if "radarr" in tool_name else "series"
    items = result.get(media_type, [])
    count = result.get("count", len(items))
    
    if not items:
        return f"No {media_type} found."
    
    lines = [f"{count} {media_type}:"]
    
    for item in items:
        title = item.get("title", "Unknown")
        year = item.get("year", "Unknown")
        item_id = item.get("id", "?")
        
        if media_type == "series":
            ep_count = item.get("episodeFileCount", 0)
            total_eps = item.get("episodeCount", 0)
            lines.append(f"  [{item_id}] {title} ({year}) - {ep_count}/{total_eps}")
        else:
            tmdb_id = item.get("tmdbId", "?")
            lines.append(f"  [{item_id}] {title} ({year}) - TMDB: {tmdb_id}")
    
    if count > len(items):
        lines.append(f"  ... {count - len(items)} more")
    
    return "\n".join(lines)


def _format_search_results(result: Dict[str, Any], tool_name: str) -> str:
    """Format search results."""
    media_type = "movies" if "radarr" in tool_name else "series"
    items = result.get(media_type, [])
    count = result.get("count", len(items))
    
    if not items:
        return f"No {media_type} found in search."
    
    lines = [f"Found {count} {media_type} in search:"]
    
    for item in items:
        title = item.get("title", "Unknown")
        year = item.get("year", "Unknown")
        tmdb_id = item.get("tmdbId") or item.get("tvdbId")
        lines.append(f"  {title} ({year}) - ID: {tmdb_id}")
    
    return "\n".join(lines)


def _format_media_details(result: Dict[str, Any], tool_name: str) -> str:
    """Format detailed movie/series information."""
    media_type = "movie" if "radarr" in tool_name else "series"
    item = result.get(media_type, {})
    
    if not item:
        return f"No {media_type} details found."
    
    title = item.get("title", "Unknown")
    year = item.get("year", "Unknown")
    status = item.get("status", "Unknown")
    monitored = "Yes" if item.get("monitored", False) else "No"
    has_file = "Yes" if item.get("hasFile", False) else "No"
    
    lines = [
        f"**{title} ({year})**",
        f"Status: {status}",
        f"Monitored: {monitored}",
        f"Downloaded: {has_file}"
    ]
    
    if media_type == "series":
        season_count = item.get("seasonCount", 0)
        ep_count = item.get("episodeFileCount", 0)
        total_eps = item.get("totalEpisodeCount", 0)
        lines.extend([
            f"Seasons: {season_count}",
            f"Episodes: {ep_count}/{total_eps}"
        ])
    
    # Add overview if short enough
    overview = item.get("overview", "")
    if overview and len(overview) < 200:
        lines.append(f"Overview: {overview}")
    
    return "\n".join(lines)


def _format_episodes(result: Dict[str, Any]) -> str:
    """Format episode list."""
    episodes = result.get("episodes", [])
    count = result.get("count", len(episodes))
    
    if not episodes:
        return "No episodes found."
    
    lines = [f"Found {count} episodes:"]
    
    for ep in episodes:
        has_file = "Downloaded" if ep.get("hasFile", False) else "Missing"
        monitored = "Monitored" if ep.get("monitored", False) else "Unmonitored"
        
        season = ep.get("seasonNumber", "?")
        episode = ep.get("episodeNumber", "?")
        title = ep.get("title", "Unknown")
        air_date = ep.get("airDate", "")
        
        date_str = f" ({air_date})" if air_date else ""
        lines.append(f"  S{season:02d}E{episode:02d}: {title}{date_str} - {has_file}, {monitored}")
    
    return "\n".join(lines)


def _format_download_queue(result: Dict[str, Any]) -> str:
    """Format download queue."""
    queues = result.get("queues", {})
    
    if not queues:
        return "Download queue is empty."
    
    lines = ["Download Queue:"]
    
    for service, queue_data in queues.items():
        items = queue_data.get("items", [])
        count = queue_data.get("count", len(items))
        
        if items:
            lines.append(f"\n{service.upper()} ({count} items):")
            for item in items:
                title = item.get("title", "Unknown")
                status = item.get("status", "Unknown")
                progress = ""
                
                size = item.get("size", 0)
                size_left = item.get("sizeleft", 0)
                if size > 0:
                    progress_pct = ((size - size_left) / size * 100)
                    progress = f" ({progress_pct:.1f}%)"
                
                lines.append(f"  {title} - {status}{progress}")
        else:
            lines.append(f"\n{service.upper()}: Empty")
    
    return "\n".join(lines)


def _format_calendar(result: Dict[str, Any], tool_name: str) -> str:
    """Format calendar results."""
    def format_date(date_str):
        """Format ISO date to readable format."""
        if not date_str or date_str == "TBA":
            return "TBA"
        try:
            # Handle ISO format with or without timezone
            if "T" in date_str:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return dt.strftime("%B %d, %Y")
            else:
                # Already a simple date
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                return dt.strftime("%B %d, %Y")
        except:
            return date_str
    
    media_type = "movies" if "radarr" in tool_name else "episodes"
    items = result.get(media_type, [])
    count = result.get("count", len(items))
    
    if not items:
        return f"No upcoming {media_type} found."
    
    lines = [f"Upcoming {media_type} ({count}):"]
    
    for item in items:
        if media_type == "movies":
            title = item.get("title", "Unknown")
            date = item.get("releaseDate") or item.get("inCinemas", "TBA")
            formatted_date = format_date(date)
            lines.append(f"  {title} - {formatted_date}")
        else:
            title = item.get("title", "Unknown")
            series_title = item.get("series", {}).get("title")
            if not series_title or series_title == "None":
                series_title = f"Series ID {item.get('seriesId', '?')}"
            season = item.get("seasonNumber", "?")
            episode = item.get("episodeNumber", "?")
            air_date = item.get("airDate", "TBA")
            formatted_date = format_date(air_date)
            lines.append(f"  {series_title} S{season:02d}E{episode:02d}: {title} - {formatted_date}")
    
    return "\n".join(lines)


def _format_wanted(result: Dict[str, Any], tool_name: str) -> str:
    """Format wanted/missing results."""
    records = result.get("records", [])
    total = result.get("totalRecords", len(records))
    page = result.get("page", 1)
    
    if not records:
        return "No missing/wanted items found."
    
    wanted_type = "missing" if "missing" in tool_name else "cutoff unmet"
    lines = [f"Found {total} {wanted_type} items (page {page}):"]
    
    for item in records:
        if "seriesId" in item:  # Episode
            series_title = item.get("series", {}).get("title", "Unknown")
            season = item.get("seasonNumber", "?")
            episode = item.get("episodeNumber", "?")
            title = item.get("title", "Unknown")
            lines.append(f"  {series_title} S{season:02d}E{episode:02d}: {title}")
        else:  # Movie
            title = item.get("title", "Unknown")
            year = item.get("year", "Unknown")
            lines.append(f"  {title} ({year})")
    
    return "\n".join(lines)


def _format_system_status(result: Dict[str, Any]) -> str:
    """Format system status."""
    status_data = result.get("status", {})
    
    if not status_data:
        return "No system status available."
    
    lines = ["System Status:"]
    
    for service, data in status_data.items():
        version = data.get("version", "Unknown")
        lines.append(f"\n{service.upper()}: v{version}")
        
        health = data.get("health", [])
        if health:
            lines.append("  Health Issues:")
            for issue in health:
                issue_type = "ERROR" if issue.get("type") == "error" else "WARNING"
                lines.append(f"    {issue_type}: {issue.get('message', 'Unknown issue')}")
        else:
            lines.append("  All systems healthy")
    
    return "\n".join(lines)


def _format_disk_space(result: Dict[str, Any]) -> str:
    """Format disk space information."""
    disk_data = result.get("diskSpace", {})
    
    if not disk_data:
        return "No disk space information available."
    
    lines = ["Disk Space:"]
    
    for service, disks in disk_data.items():
        lines.append(f"\n{service.upper()}:")
        for disk in disks:
            path = disk.get("path", "Unknown")
            free_gb = disk.get("freeSpace", 0) / (1024**3)
            total_gb = disk.get("totalSpace", 1) / (1024**3)
            used_pct = disk.get("percentUsed", 0)
            
            lines.append(f"  {path}: {free_gb:.1f}GB free / {total_gb:.1f}GB total ({used_pct:.1f}% used)")
    
    return "\n".join(lines)


def _format_success_message(result: Dict[str, Any]) -> str:
    """Format success messages."""
    message = result.get("message", "Operation completed successfully")
    return message