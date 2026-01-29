"""
Sidebar UI component for the Property Claim Mapper.
"""
import json
import os
from datetime import date
from typing import Any, Dict, List

import pandas as pd
import streamlit as st
import folium
import io

from config import (
    BANNER_PATH, INCIDENT_TYPES, DEFAULT_LOCATION,
    CAMERA_REQUIRED_COLS, INCIDENT_REQUIRED_COLS,
    get_default_project_data, TILE_SERVERS
)
from utils.data_helpers import get_next_id
from utils.pdf_generator import create_pdf
from utils.map_utils import generate_static_map


def render_sidebar() -> bool:
    """
    Render the sidebar UI components.
    
    Returns:
        Boolean indicating if map is locked
    """
    # Banner
    if os.path.exists(BANNER_PATH):
        st.sidebar.image(BANNER_PATH, width="stretch")
    else:
        st.sidebar.title("Boardwalk Property Management")
    
    # Incident Workflow Section
    st.sidebar.markdown("---")
    st.sidebar.subheader("Incident Workflow")
    
    map_locked = st.sidebar.toggle(
        "🔒 Lock Map & Place Markers",
        value=False,
        key="map_locked_toggle"
    )
    
    if not map_locked:
        st.sidebar.info(
            "1. Navigate map to your area.\n"
            "2. Toggle switch above to freeze map and place markers."
        )
        st.session_state.draft_marker = None
    else:
        st.sidebar.success("Map Frozen. Click on map to place a NEW marker.")
    
    # Map Style Selection
    st.sidebar.divider()
    st.sidebar.subheader("Map Layer")
    st.sidebar.radio(
        "🗺️ Map Style",
        options=list(TILE_SERVERS.keys()),
        index=2, # Default to Hybrid
        key="map_style_selection",
        horizontal=True
    )
    
    # Selected Marker (for deletion)
    _render_selected_marker_section()
    
    # Creating New Marker (Draft)
    _render_draft_marker_section(map_locked)
    
    # Project Controls Section
    st.sidebar.markdown("---")
    _render_project_controls()
    
    # Data Import Section
    st.sidebar.markdown("---")
    _render_data_import()
    
    # PDF Generation
    st.sidebar.markdown("---")
    _render_pdf_section()
    
    return map_locked


def _render_selected_marker_section() -> None:
    """Render the selected marker section for deletion."""
    if not st.session_state.get('active_incident_id'):
        return
    
    active_idx = -1
    active_inc = None
    for i, inc in enumerate(st.session_state.incidents):
        if str(inc['id']) == str(st.session_state.active_incident_id):
            active_idx = i
            active_inc = inc
            break
    
    if not active_inc:
        return
    
    st.sidebar.divider()
    st.sidebar.markdown(f"**Selected: {active_inc['type']} #{active_inc['id']}**")
    st.sidebar.caption(f"Location: {active_inc['lat']:.5f}, {active_inc['lng']:.5f}")
    
    if st.sidebar.button("🗑️ Delete This Marker", type="primary", width="stretch"):
        st.session_state.incidents.pop(active_idx)
        st.session_state.active_incident_id = None
        st.rerun()
    
    if st.sidebar.button("Clear Selection", width="stretch"):
        st.session_state.active_incident_id = None
        st.rerun()


def _render_draft_marker_section(map_locked: bool) -> None:
    """Render the draft marker creation form."""
    if not map_locked:
        return
    
    if not st.session_state.get('draft_marker'):
        st.sidebar.info("Click on the map to place a new marker.")
        return
    
    draft = st.session_state.draft_marker
    st.sidebar.divider()
    st.sidebar.markdown("**Create New Marker**")
    
    n_type = st.sidebar.radio(
        "Type",
        ["Incident", "Camera"],
        horizontal=True,
        key="new_type_radio"
    )
    
    with st.sidebar.form(key="create_form"):
        st.text_input(
            "Location (Coordinates)",
            value=f"{draft['lat']:.5f}, {draft['lng']:.5f}",
            disabled=True
        )
        
        if n_type == "Incident":
            n_level = st.selectbox("Status / Level", ["Light", "Medium", "Serious"], index=1)
            n_date = st.date_input("Date", date.today())
            n_desc = st.selectbox("Incident Type", INCIDENT_TYPES)
            n_claim = st.checkbox("Claim Filed")
            n_impact = st.checkbox("Premium Impact")
            n_comp = st.number_input("Compensation ($)", min_value=0.0, step=100.0, value=None, placeholder="0")
        else:
            n_level = st.selectbox("Status", ["Functioning", "Not Functioning"])
            n_date = str(date.today())
            n_desc = "Camera Feed"
            n_claim, n_impact, n_comp = False, False, 0.0
        
        if st.form_submit_button("Create Marker"):
            new_id = get_next_id(st.session_state.incidents, n_type)
            new_inc = {
                "id": new_id,
                "lat": draft['lat'],
                "lng": draft['lng'],
                "type": n_type,
                "level": n_level,
                "location": f"{draft['lat']:.5f}, {draft['lng']:.5f}",
                "date": str(n_date),
                "parties": "",
                "claim_filed": bool(n_claim),
                "premium_impact": bool(n_impact),
                "description": n_desc,
                "compensation": float(n_comp) if n_comp is not None else 0.0
            }
            st.session_state.incidents.append(new_inc)
            st.session_state.draft_marker = None
            st.success("Created!")
            st.rerun()
    
    if st.sidebar.button("Cancel"):
        st.session_state.draft_marker = None
        st.rerun()


def _render_project_controls() -> None:
    """Render project control buttons."""
    st.sidebar.title("Project Controls")
    
    # Create New Project
    def reset_project_data():
        """Callback to reset project data safely before rerun."""
        st.session_state.project_data = get_default_project_data()
        st.session_state.incidents = []
        st.session_state.active_incident_id = None
        st.session_state.draft_marker = None
        
        # Explicitly reset input fields in session state
        st.session_state.prop_input = "New Property"
        st.session_state.year_input = str(date.today().year)
        
        # Reset Map Style to Hybrid
        st.session_state.map_style_selection = "Hybrid"
        
        # Ensure project data reflects these defaults
        st.session_state.project_data['property'] = "New Property"
        st.session_state.project_data['year'] = str(date.today().year)

        # Clear persistent map state
        if 'live_map_center' in st.session_state:
            del st.session_state.live_map_center
        if 'live_map_zoom' in st.session_state:
            del st.session_state.live_map_zoom
        if 'generated_pdf_bytes' in st.session_state:
            del st.session_state.generated_pdf_bytes
            
        st.session_state._map_jump_requested = True  # Signal map to jump to default

    if st.sidebar.button("📄 Create New", width="stretch", on_click=reset_project_data):
        # The callback runs before this, ensuring state is ready.
        # We just need to rerun to refresh the UI with new state.
        pass # Rerun happens automatically if key changed? No, explicit rerun might be needed if values changed affect current run widgets but callback runs before...
        # Actually callback runs before rerun. Streamlit automatically reruns when button is clicked. 
        # But if we change state in callback, the NEXT run sees it. 
        # The button click triggers a rerun. The callback runs at start of that rerun.
        # So we don't strictly need st.rerun() if the button click itself triggers logic, 
        # but explicit rerun ensures everything refreshes properly.
        # Wait, if callback runs, the script re-executes. We don't need another st.rerun().
        pass
    if 'prop_input' in st.session_state:
        st.session_state.project_data['property'] = st.session_state.prop_input
    if 'year_input' in st.session_state:
        st.session_state.project_data['year'] = st.session_state.year_input
        
    # Sync current map state if available
    map_key = f"main_map_{st.session_state.get('map_reset_counter', 0)}"
    
    if map_key in st.session_state and st.session_state[map_key]:
        m_state = st.session_state[map_key]
        if m_state.get('center'):
            st.session_state.project_data['map_config']['center'] = [
                m_state['center']['lat'], m_state['center']['lng']
            ]
        if m_state.get('zoom'):
            st.session_state.project_data['map_config']['zoom'] = m_state['zoom']

    st.session_state.project_data['incidents'] = st.session_state.incidents
    
    # Save Current Project
    st.sidebar.download_button(
        "💾 Save Current",
        data=json.dumps(st.session_state.project_data, indent=4),
        file_name=f"{st.session_state.project_data['name'].replace(' ', '_')}_project.json",
        mime="application/json",
        width="stretch"
    )
    
    # Load Project
    if st.sidebar.button("📂 Load Project", width="stretch"):
        st.session_state.show_load_project = not st.session_state.get('show_load_project', False)
    
    if st.session_state.get('show_load_project'):
        load_file = st.sidebar.file_uploader(
            "Upload Project JSON",
            type=['json'],
            key="load_project_uploader"
        )
        if load_file:
            try:
                d = json.load(load_file)
                st.session_state.project_data = d
                st.session_state.incidents = d.get('incidents', [])
                
                # Update UI fields if they exist in loaded data
                if 'property' in d:
                    st.session_state.prop_input = d['property']
                if 'year' in d:
                    st.session_state.year_input = d['year']
                
                st.session_state.active_incident_id = None
                st.session_state.show_load_project = False
                st.session_state._map_jump_requested = True  # Jump to project's map location
                st.success("Project loaded!")
                st.rerun()
            except Exception as e:
                st.error(f"Invalid project file: {e}")


def _render_data_import() -> None:
    """Render data import section."""
    st.sidebar.title("Data Import")
    st.sidebar.caption(
        "Import CSV files to add cameras or incidents. "
        "CSV must have matching column headers."
    )
    
    # --- Camera Data Section ---
    st.sidebar.divider()
    st.sidebar.markdown("**📷 Camera Data**")
    
    c1, c2 = st.sidebar.columns(2)
    
    with c1:
        if st.button("Load List", key="btn_load_cam", use_container_width=True):
            st.session_state.show_camera_import = not st.session_state.get('show_camera_import', False)
            st.session_state.show_incident_import = False
            
    with c2:
        cam_template = "level,lat,lng,location\nFunctioning,33.6450,-117.9329,Main Entrance\nNot Functioning,33.6455,-117.9330,Back Lot"
        st.download_button(
            label="Template",
            data=cam_template,
            file_name="camera_import_template.csv",
            mime="text/csv",
            key="dl_cam_template",
            use_container_width=True
        )
    
    if st.session_state.get('show_camera_import'):
        _render_camera_import()
    
    # --- Incident Data Section ---
    # st.sidebar.divider()
    st.sidebar.markdown("**🚨 Incident Data**")
    
    i1, i2 = st.sidebar.columns(2)
    
    with i1:
        if st.button("Load List", key="btn_load_inc", use_container_width=True):
            st.session_state.show_incident_import = not st.session_state.get('show_incident_import', False)
            st.session_state.show_camera_import = False
            
    with i2:
        inc_template = (
            "level,description,lat,lng,date,compensation,claim_filed,premium_impact,parties,location\n"
            "Medium,Slip,33.6450,-117.9329,2023-10-25,500.00,True,False,,Lobby\n"
            "Serious,Fire,33.6460,-117.9340,2023-11-01,15000.00,True,True,,Kitchen"
        )
        st.download_button(
            label="Template",
            data=inc_template,
            file_name="incident_import_template.csv",
            mime="text/csv",
            key="dl_inc_template",
            use_container_width=True
        )
    
    if st.session_state.get('show_incident_import'):
        _render_incident_import()


def _render_camera_import() -> None:
    """Render camera CSV import interface."""
    st.sidebar.info(
        "**Camera CSV columns:**\n"
        "- `level` (required): Functioning / Not Functioning\n"
        "- `lat`, `lng` (optional): Coordinates\n"
        "- `location` (optional): Address text"
    )
    
    cam_file = st.sidebar.file_uploader(
        "Upload Camera CSV",
        type=['csv'],
        key="camera_csv_uploader"
    )
    if cam_file:
        try:
            df_cam = pd.read_csv(cam_file)
            
            missing_cols = [col for col in CAMERA_REQUIRED_COLS if col not in df_cam.columns]
            if missing_cols:
                st.sidebar.error(f"Missing required columns: {missing_cols}")
            else:
                if st.sidebar.button("✅ Import Cameras", key="import_cam_btn", type="primary"):
                    count = _import_cameras(df_cam)
                    st.sidebar.success(f"Imported {count} cameras!")
                    st.session_state.show_camera_import = False
                    st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error reading CSV: {e}")


def _import_cameras(df_cam: pd.DataFrame) -> int:
    """Import cameras from DataFrame."""
    count = 0
    center = st.session_state.project_data['map_config']['center']
    
    for _, row in df_cam.iterrows():
        lat = float(row['lat']) if 'lat' in df_cam.columns and pd.notna(row.get('lat')) else center[0]
        lng = float(row['lng']) if 'lng' in df_cam.columns and pd.notna(row.get('lng')) else center[1]
        
        level = str(row['level']).strip()
        if level not in ['Functioning', 'Not Functioning']:
            level = 'Functioning' if level.lower() in ['yes', 'true', '1', 'working', 'active'] else 'Not Functioning'
        
        new_camera = {
            "id": get_next_id(st.session_state.incidents, "Camera"),
            "lat": lat,
            "lng": lng,
            "type": "Camera",
            "level": level,
            "location": row.get('location', f"{lat:.5f}, {lng:.5f}"),
            "date": str(date.today()),
            "parties": "",
            "claim_filed": False,
            "premium_impact": False,
            "description": "Camera Feed",
            "compensation": 0.0
        }
        st.session_state.incidents.append(new_camera)
        count += 1
    
    return count


def _render_incident_import() -> None:
    """Render incident CSV import interface."""
    st.sidebar.info(
        "**Incident CSV columns:**\n"
        "- `level` (required): Light / Medium / Serious\n"
        "- `description` (required): Incident type\n"
        "- `lat`, `lng` (optional): Coordinates\n"
        "- `date`, `compensation`, `claim_filed`, `premium_impact`, `parties` (optional)"
    )
    
    inc_file = st.sidebar.file_uploader(
        "Upload Incident CSV",
        type=['csv'],
        key="incident_csv_uploader"
    )
    if inc_file:
        try:
            df_inc = pd.read_csv(inc_file)
            
            missing_cols = [col for col in INCIDENT_REQUIRED_COLS if col not in df_inc.columns]
            if missing_cols:
                st.sidebar.error(f"Missing required columns: {missing_cols}")
            else:
                if st.sidebar.button("✅ Import Incidents", key="import_inc_btn", type="primary"):
                    count = _import_incidents(df_inc)
                    st.sidebar.success(f"Imported {count} incidents!")
                    st.session_state.show_incident_import = False
                    st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error reading CSV: {e}")


def _import_incidents(df_inc: pd.DataFrame) -> int:
    """Import incidents from DataFrame."""
    count = 0
    center = st.session_state.project_data['map_config']['center']
    
    for _, row in df_inc.iterrows():
        lat = float(row['lat']) if 'lat' in df_inc.columns and pd.notna(row.get('lat')) else center[0]
        lng = float(row['lng']) if 'lng' in df_inc.columns and pd.notna(row.get('lng')) else center[1]
        
        level = str(row['level']).strip()
        if level not in ['Light', 'Medium', 'Serious']:
            if level.lower() in ['emergency', 'critical', 'high']:
                level = 'Serious'
            elif level.lower() in ['low', 'minor']:
                level = 'Light'
            else:
                level = 'Medium'
        
        new_incident = {
            "id": get_next_id(st.session_state.incidents, "Incident"),
            "lat": lat,
            "lng": lng,
            "type": "Incident",
            "level": level,
            "location": row.get('location', f"{lat:.5f}, {lng:.5f}"),
            "date": str(row.get('date', date.today())),
            "parties": str(row.get('parties', '')),
            "claim_filed": str(row.get('claim_filed', '')).lower() in ['yes', 'true', '1'],
            "premium_impact": str(row.get('premium_impact', '')).lower() in ['yes', 'true', '1'],
            "description": str(row['description']),
            "compensation": float(row.get('compensation', 0)) if pd.notna(row.get('compensation')) else 0.0
        }
        st.session_state.incidents.append(new_incident)
        count += 1
    
    return count


def _render_pdf_section() -> None:
    """Render PDF and Interactive Map export section."""
    if not st.session_state.incidents:
        st.sidebar.warning("No data to generate report.")
        return

    st.sidebar.title("Export Report")
    st.sidebar.caption("Generate a professional PDF report with a companion map.")

    # PDF Report Section
    # PDF Report Section
    # Unified Generate & Download Button
    
    # We use a cached function to generate the PDF bytes. 
    # This ensures that we don't re-generate the map/PDF on every rerun, 
    # but only when the inputs (map center/zoom/incidents) change.
    
    @st.cache_data(show_spinner="Generating Report...", ttl=300)
    def _get_pdf_payload(
        incidents: List[Dict],
        project_data: Dict,
        current_center: List[float],
        current_zoom: int,
        style_selection: str
    ) -> bytes:
        """Cached helper to generate the PDF report payload."""
        # 1. Generate PNG Map
        incidents_only = [i for i in incidents if i.get('type') == 'Incident']
        cameras_only = [i for i in incidents if i.get('type') == 'Camera']
        
        tile_url = TILE_SERVERS.get(style_selection)
        
        live_config = {
            'center': current_center,
            'zoom': current_zoom
        }
        
        img = generate_static_map(
            incidents=incidents_only,
            cameras=cameras_only,
            map_config=live_config,
            auto_fit=False,
            url=tile_url
        )
        
        buf_png = io.BytesIO()
        img.save(buf_png, format="PNG")
        bytes_png = buf_png.getvalue()
        
        # 2. Generate PDF
        title = project_data.get('name', 'Report')
        if 'current_project_title' in st.session_state:
             title = st.session_state.current_project_title
             
        pdf_bytes = create_pdf(
            project_data,
            incidents,
            project_title=title,
            map_tile_url=tile_url,
            existing_map_image=bytes_png
        )
        return pdf_bytes

    # Collect current state for the cache key
    live_center = st.session_state.get('live_map_center', DEFAULT_LOCATION)
    live_zoom = st.session_state.get('live_map_zoom', 13)
    curr_style = st.session_state.get("map_style_selection", "Hybrid")
    
    # We pass the incidents list directly. Since it's a list of dicts, 
    # st.cache_data will hash it correctly to detect changes.
    
    # WARNING: This call is "lazy" inside the download_button logic in a way, 
    # but to make it truly unified, we calculate it here.
    # Because it is cached, it will be instant on subsequent reruns if nothing changed.
    # When something changes (e.g. pan map), this line will run and show the spinner.
    
    try:
        pdf_payload = _get_pdf_payload(
            st.session_state.incidents,
            st.session_state.project_data,
            live_center,
            live_zoom,
            curr_style
        )
        
        st.sidebar.download_button(
            label="📄 Export PDF Report",
            data=pdf_payload,
            file_name="report.pdf",
            mime="application/pdf",
            width="stretch",
            type="primary"
        )
    except Exception as e:
        st.sidebar.error(f"Failed to generate report: {e}")
