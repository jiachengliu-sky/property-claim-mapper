"""
Map View component for the Property Claim Mapper.
"""
import streamlit as st
import folium
from folium.plugins import LocateControl
from streamlit_folium import st_folium

from config import NEW_MARKER_ICON, TILE_SERVERS
from utils.icons import get_custom_icon, get_standard_icon, get_draft_marker_icon
from utils.data_helpers import calculate_click_threshold


def render_map_view(map_locked: bool) -> None:
    """
    Render the map view tab content.
    
    Args:
        map_locked: Whether the map is locked for marker placement
    """
    st.caption(
        "Navigate the map below. Toggle the **Lock Switch** in the sidebar to create new markers."
    )
    
    interaction_opt = not map_locked
    
    # Sync state from actual map interaction (if any)
    # We skip this if a jump is requested to avoid overwriting the jump target
    # Sync state from actual map interaction (if any)
    # We skip this if a jump is requested to avoid overwriting the jump target
    
    map_key = f"main_map_{st.session_state.get('map_reset_counter', 0)}"
    
    if not st.session_state.get('_map_jump_requested') and map_key in st.session_state and st.session_state[map_key]:
        _update_map_state(st.session_state[map_key])
    
    # Use live map state if available (persists user's pan/zoom)
    # Otherwise fall back to project config (for initial load)
    if 'live_map_center' not in st.session_state:
        st.session_state.live_map_center = st.session_state.project_data['map_config']['center'].copy()
    if 'live_map_zoom' not in st.session_state:
        st.session_state.live_map_zoom = st.session_state.project_data['map_config']['zoom']
    
    # Define a dynamic key to force map reload when jumping
    # We'll use a session state counter for this
    if 'map_reset_counter' not in st.session_state:
        st.session_state.map_reset_counter = 0

    # Check if we should jump to a new location (from search)
    if st.session_state.get('_map_jump_requested'):
        st.session_state.live_map_center = st.session_state.project_data['map_config']['center'].copy()
        st.session_state.live_map_zoom = st.session_state.project_data['map_config']['zoom']
        st.session_state.map_reset_counter += 1  # Increment to force re-mount
        st.session_state._map_jump_requested = False
    
    # Determine current style
    selected_style = st.session_state.get("map_style_selection", "Hybrid")
    tile_url = TILE_SERVERS.get(selected_style)
    
    # Create map at live position
    m = folium.Map(
        location=st.session_state.live_map_center,
        zoom_start=st.session_state.live_map_zoom,
        tiles=tile_url,
        attr="Map data &copy; contributors" if "openstreetmap" in tile_url else "Esri",
        zoom_control=interaction_opt,
        scrollWheelZoom=interaction_opt,
        dragging=interaction_opt,
        doubleClickZoom=interaction_opt,
        zoom_snap=0.2,
        zoom_delta=0.2,
        wheel_px_per_zoom_level=120,
        attributionControl=False,
        max_zoom=22
    )
    
    LocateControl(auto_start=False).add_to(m)
    
    # Add existing markers
    _add_markers_to_map(m)
    
    # Add draft marker if exists
    _add_draft_marker(m)
    
    # Render map - don't pass center/zoom to st_folium as it forces recenter
    # The folium.Map sets initial position, key maintains state across reruns
    map_data = st_folium(
        m,
        height=700,
        width="100%",
        returned_objects=["center", "zoom", "last_clicked"],
        key=f"main_map_{st.session_state.map_reset_counter}" 
    )
    
    # Update live map state from returned data (for next render)
    _update_map_state(map_data)
    
    # Handle clicks
    _handle_map_click(map_data, map_locked)


def _add_markers_to_map(m: folium.Map) -> None:
    """Add all incident/camera markers to the map."""
    for inc in st.session_state.incidents:
        is_active = str(inc.get('id', '')) == str(st.session_state.get('active_incident_id', ''))
        icon_size = (30, 30) if is_active else (20, 20)
        
        custom_icon = get_custom_icon(inc['type'], inc['level'], size=icon_size)
        
        # Build tooltip content
        tooltip_html = _build_tooltip(inc, is_active)
        
        if custom_icon:
            folium.Marker(
                [inc['lat'], inc['lng']],
                tooltip=folium.Tooltip(tooltip_html, permanent=False),
                icon=custom_icon
            ).add_to(m)
        else:
            folium.Marker(
                [inc['lat'], inc['lng']],
                tooltip=folium.Tooltip(tooltip_html, permanent=False),
                icon=get_standard_icon(inc['type'], inc['level'])
            ).add_to(m)


def _build_tooltip(inc: dict, is_active: bool) -> str:
    """Build HTML tooltip content for a marker."""
    if inc['type'] == "Incident":
        tooltip_lines = [
            f"<b>{inc['type']} #{inc['id']}</b>",
            f"Status: {inc['level']}",
            f"Type: {inc.get('description', 'N/A')}",
            f"Date: {inc.get('date', 'N/A')}",
        ]
    else:
        tooltip_lines = [
            f"<b>{inc['type']} #{inc['id']}</b>",
            f"Status: {inc['level']}",
        ]
    
    if is_active:
        tooltip_lines.append("<span style='color: green;'>[SELECTED]</span>")
    else:
        tooltip_lines.append("<span style='color: #888;'>Click to select</span>")
    
    return "<br>".join(tooltip_lines)


def _add_draft_marker(m: folium.Map) -> None:
    """Add the draft marker for new marker creation."""
    if not st.session_state.get('draft_marker'):
        return
    
    d = st.session_state.draft_marker
    draft_icon = get_draft_marker_icon(NEW_MARKER_ICON)
    
    folium.Marker(
        [d['lat'], d['lng']],
        icon=draft_icon if draft_icon else folium.Icon(color="gray", icon="plus"),
        tooltip="New Marker (Unsaved)"
    ).add_to(m)


def _update_map_state(map_data: dict) -> None:
    """Update session state with current map center and zoom."""
    if map_data.get('center'):
        new_center = [
            map_data['center']['lat'],
            map_data['center']['lng']
        ]
        # Update live state (used for next render)
        st.session_state.live_map_center = new_center
        # Also update project config (for saving)
        st.session_state.project_data['map_config']['center'] = new_center
    
    if map_data.get('zoom'):
        # Update live state
        st.session_state.live_map_zoom = map_data['zoom']
        # Also update project config
        st.session_state.project_data['map_config']['zoom'] = map_data['zoom']


def _handle_map_click(map_data: dict, map_locked: bool) -> None:
    """Handle map click events for marker selection or creation."""
    if not map_data.get('last_clicked'):
        return
    
    c_lat = map_data['last_clicked']['lat']
    c_lng = map_data['last_clicked']['lng']
    
    # Calculate dynamic threshold based on current zoom
    # Calculate dynamic threshold based on current zoom
    # Use live zoom state if available for better accuracy
    current_zoom = st.session_state.get('live_map_zoom', st.session_state.project_data['map_config'].get('zoom', 18))
    threshold = calculate_click_threshold(current_zoom)
    
    # Check if click is near an existing marker
    found_id = None
    min_dist = threshold
    for inc in st.session_state.incidents:
        dist = ((inc['lat'] - c_lat)**2 + (inc['lng'] - c_lng)**2)**0.5
        if dist < min_dist:
            found_id = inc['id']
            min_dist = dist
    
    if found_id:
        # Select existing marker
        if str(st.session_state.active_incident_id) != str(found_id):
            st.session_state.active_incident_id = found_id
            st.session_state.draft_marker = None
            st.rerun()
    elif map_locked:
        # Create new draft marker
        last_processed = st.session_state.get('last_processed_click_coords')
        current_coords = (c_lat, c_lng)
        if last_processed != current_coords:
            st.session_state.draft_marker = {'lat': c_lat, 'lng': c_lng}
            st.session_state.active_incident_id = None
            st.session_state.last_processed_click_coords = current_coords
            st.rerun()
