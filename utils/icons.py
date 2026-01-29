"""
Icon handling utilities for Folium map markers.
"""
import base64
import logging
import os
from functools import lru_cache
from typing import Optional, Tuple

import folium

from config import ICONS

logger = logging.getLogger(__name__)


@lru_cache(maxsize=32)
def _load_icon_base64(icon_path: str) -> Optional[str]:
    """
    Load and cache icon file as base64 string.
    
    Args:
        icon_path: Path to the icon file
        
    Returns:
        Base64 encoded string or None if loading fails
    """
    if not os.path.exists(icon_path):
        return None
    
    try:
        with open(icon_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except OSError as e:
        logger.warning(f"Failed to load icon from {icon_path}: {e}")
        return None


def get_custom_icon(
    incident_type: str,
    level: str,
    size: Tuple[int, int] = (20, 20)
) -> Optional[folium.CustomIcon]:
    """
    Load custom SVG icon as base64 data URI for Folium markers.
    
    Args:
        incident_type: Either "Camera" or "Incident"
        level: Status level (e.g., "Functioning", "Light", "Medium", "Serious")
        size: Tuple of (width, height) for the icon
        
    Returns:
        Folium CustomIcon if successful, None otherwise
    """
    if incident_type == "Camera":
        status = "Functioning" if level == "Functioning" else "Not Functioning"
        icon_path = ICONS["Camera"].get(status)
    else:
        icon_path = ICONS["Incident"].get(level, ICONS["Incident"]["Medium"])
    
    if not icon_path:
        return None
    
    encoded = _load_icon_base64(icon_path)
    if encoded:
        mime = "image/svg+xml" if icon_path.endswith(".svg") else "image/png"
        icon_url = f"data:{mime};base64,{encoded}"
        return folium.CustomIcon(icon_url, icon_size=size)
    return None


def get_standard_icon(incident_type: str, level: str) -> folium.Icon:
    """
    Return a standard Folium icon as fallback when custom icons are unavailable.
    
    Args:
        incident_type: Either "Camera" or "Incident"
        level: Status level for determining icon color
        
    Returns:
        Folium Icon with appropriate color
    """
    color = "blue"
    if incident_type == "Camera":
        color = "green" if level == "Functioning" else "gray"
    elif incident_type == "Incident":
        if level == "Serious":
            color = "red"
        elif level == "Medium":
            color = "orange"
        elif level == "Light":
            color = "green"
    return folium.Icon(color=color, icon="info-sign")


def get_draft_marker_icon(icon_path: str, size: Tuple[int, int] = (25, 25)) -> Optional[folium.CustomIcon]:
    """
    Load a draft/new marker icon.
    
    Args:
        icon_path: Path to the new marker icon
        size: Icon size tuple
        
    Returns:
        Folium CustomIcon if successful, None otherwise
    """
    encoded = _load_icon_base64(icon_path)
    if encoded:
        icon_url = f"data:image/svg+xml;base64,{encoded}"
        return folium.CustomIcon(icon_url, icon_size=size)
    return None
