"""
Data helper utilities for incident management.
"""
import logging
from typing import Any, Dict, List, Tuple

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


def get_next_id(incidents: List[Dict[str, Any]], incident_type: str) -> str:
    """
    Generate next sequential ID for incidents (I0001) or cameras (C0001).
    
    Args:
        incidents: List of existing incident dictionaries
        incident_type: Either "Incident" or "Camera"
        
    Returns:
        Next available ID string (e.g., "I0001" or "C0001")
    """
    prefix = "I" if incident_type == "Incident" else "C"
    max_num = 0
    
    for inc in incidents:
        curr_id = str(inc.get('id', ''))
        if curr_id.startswith(prefix):
            try:
                num = int(curr_id[1:])
                if num > max_num:
                    max_num = num
            except ValueError as e:
                logger.debug(f"Could not parse ID '{curr_id}': {e}")
                continue
    
    return f"{prefix}{max_num + 1:04d}"


def calculate_click_threshold(zoom_level: int) -> float:
    """
    Calculate dynamic click threshold based on map zoom level.
    
    At higher zoom levels (more zoomed in), the threshold should be smaller.
    At lower zoom levels (more zoomed out), the threshold should be larger.
    
    Args:
        zoom_level: Current map zoom level (typically 1-21)
        
    Returns:
        Distance threshold for click detection
    """
    # Base threshold at zoom level 18 is ~5.5 meters (0.00005 degrees)
    # Each zoom level doubles/halves the scale
    base_zoom = 18
    base_threshold = 0.00005
    
    # Adjust threshold based on zoom difference
    zoom_diff = base_zoom - zoom_level
    threshold = base_threshold * (2 ** zoom_diff)
    
    # Clamp to reasonable bounds
    return max(0.00001, min(0.01, threshold))


@st.cache_data
def get_filtered_data(
    incidents_json: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Filter incidents into separate DataFrames for incidents and cameras.
    
    Uses Streamlit caching to avoid redundant filtering on reruns.
    
    Args:
        incidents_json: JSON string of incidents list (for cache key stability)
        
    Returns:
        Tuple of (incidents_df, cameras_df)
    """
    import json
    incidents = json.loads(incidents_json)
    
    if not incidents:
        return pd.DataFrame(), pd.DataFrame()
    
    df = pd.DataFrame(incidents)
    
    if 'type' not in df.columns:
        return pd.DataFrame(), pd.DataFrame()
    
    incidents_df = df[df['type'] == 'Incident'].copy()
    cameras_df = df[df['type'] == 'Camera'].copy()
    
    return incidents_df, cameras_df


def sync_edited_data(
    edited_df: pd.DataFrame,
    incidents: List[Dict[str, Any]],
    columns_to_sync: List[str]
) -> List[Dict[str, Any]]:
    """
    Synchronize edited DataFrame data back to the incidents list.
    
    Args:
        edited_df: DataFrame with edited values
        incidents: Original incidents list
        columns_to_sync: List of column names to sync
        
    Returns:
        Updated incidents list
    """
    if edited_df is None or edited_df.empty:
        return incidents
    
    incident_map = {str(x['id']): i for i, x in enumerate(incidents)}
    
    for _, row in edited_df.iterrows():
        idx = incident_map.get(str(row['id']))
        if idx is not None:
            for col in columns_to_sync:
                if col in row.index:
                    value = row[col]
                    # Type conversion based on column
                    if col == 'compensation':
                        value = float(value) if pd.notna(value) else 0.0
                    elif col in ('claim_filed', 'premium_impact'):
                        value = bool(value)
                    incidents[idx][col] = value
    
    return incidents


def get_selected_ids(edited_df: pd.DataFrame) -> List[str]:
    """
    Get IDs of selected rows from an edited DataFrame.
    
    Args:
        edited_df: DataFrame with 'select' column
        
    Returns:
        List of selected IDs
    """
    if edited_df is None or edited_df.empty:
        return []
    
    if 'select' not in edited_df.columns:
        return []
    
    selected = edited_df[edited_df['select'] == True]
    return selected['id'].tolist() if 'id' in selected.columns else []
