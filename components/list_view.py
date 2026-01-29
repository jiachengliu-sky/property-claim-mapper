"""
List View component for the Property Claim Mapper.
"""
import pandas as pd
import streamlit as st

from config import INCIDENT_TYPES


def render_list_view() -> None:
    """Render the list view tab content with editable tables."""
    st.subheader("Project Incidents & Cameras")
    st.caption(
        "Edit marker data directly in the tables below. "
        "Select rows and use the delete button to remove them."
    )
    
    all_df = pd.DataFrame(st.session_state.incidents)
    
    col_inc_log, col_cam_log = st.columns(2)
    
    with col_inc_log:
        _render_incidents_table(all_df)
    
    with col_cam_log:
        _render_cameras_table(all_df)


def _render_incidents_table(all_df: pd.DataFrame) -> None:
    """Render the incidents data editor table."""
    st.markdown("**Incidents**")
    
    if all_df.empty:
        st.info("No Data.")
        return
    
    inc_df = all_df[all_df['type'] == "Incident"].copy()
    if inc_df.empty:
        st.info("No Incidents.")
        return
    
    # Add selection column for deletion
    inc_df.insert(0, 'select', False)
    
    col_config = {
        "select": st.column_config.CheckboxColumn(
            "🗑️",
            help="Select to delete",
            default=False
        ),
        "id": st.column_config.TextColumn("ID", disabled=True),
        "location": st.column_config.TextColumn("Location", disabled=True),
        "level": st.column_config.SelectboxColumn(
            "Status",
            options=["Light", "Medium", "Serious"]
        ),
        "description": st.column_config.SelectboxColumn(
            "Incident Type",
            options=INCIDENT_TYPES
        ),
        "compensation": st.column_config.NumberColumn("Comp ($)", min_value=0.0),
        "claim_filed": st.column_config.CheckboxColumn("Claim?"),
        "premium_impact": st.column_config.CheckboxColumn("Prem. Impact?"),
    }
    
    display_cols = [
        "select", "id", "location", "level", "description",
        "compensation", "claim_filed", "premium_impact"
    ]
    avail_cols = [c for c in display_cols if c in inc_df.columns]
    
    edited_inc = st.data_editor(
        inc_df[avail_cols],
        column_config=col_config,
        hide_index=True,
        height=450,
        width="stretch",
        key="inc_editor"
    )
    
    # Delete selected rows
    if edited_inc is not None:
        selected_inc_ids = edited_inc[edited_inc['select'] == True]['id'].tolist()
        if selected_inc_ids:
            if st.button(
                f"🗑️ Delete {len(selected_inc_ids)} Selected Incident(s)",
                key="delete_inc_btn",
                type="primary"
            ):
                st.session_state.incidents = [
                    inc for inc in st.session_state.incidents
                    if str(inc['id']) not in [str(x) for x in selected_inc_ids]
                ]
                st.rerun()
        
        # Sync changes back to session state
        _sync_incident_changes(edited_inc)


def _sync_incident_changes(edited_df: pd.DataFrame) -> None:
    """Sync edited incident data back to session state."""
    if edited_df is None:
        return
    
    incident_map = {str(x['id']): i for i, x in enumerate(st.session_state.incidents)}
    
    for _, row in edited_df.iterrows():
        idx = incident_map.get(str(row['id']))
        if idx is not None:
            st.session_state.incidents[idx]['level'] = row['level']
            st.session_state.incidents[idx]['description'] = row['description']
            st.session_state.incidents[idx]['compensation'] = float(row['compensation'])
            st.session_state.incidents[idx]['claim_filed'] = bool(row['claim_filed'])
            st.session_state.incidents[idx]['premium_impact'] = bool(row['premium_impact'])


def _render_cameras_table(all_df: pd.DataFrame) -> None:
    """Render the cameras data editor table."""
    st.markdown("**Cameras**")
    
    if all_df.empty:
        st.info("No Data.")
        return
    
    cam_df = all_df[all_df['type'] == "Camera"].copy()
    if cam_df.empty:
        st.info("No Cameras.")
        return
    
    # Add selection column for deletion
    cam_df.insert(0, 'select', False)
    
    col_config_cam = {
        "select": st.column_config.CheckboxColumn(
            "🗑️",
            help="Select to delete",
            default=False
        ),
        "id": st.column_config.TextColumn("ID", disabled=True),
        "location": st.column_config.TextColumn("Location", disabled=True),
        "level": st.column_config.SelectboxColumn(
            "Status",
            options=["Functioning", "Not Functioning"]
        ),
    }
    
    display_cols = ["select", "id", "location", "level"]
    avail_cols_cam = [c for c in display_cols if c in cam_df.columns]
    
    edited_cam = st.data_editor(
        cam_df[avail_cols_cam],
        column_config=col_config_cam,
        hide_index=True,
        height=450,
        width="stretch",
        key="cam_editor"
    )
    
    # Delete selected rows
    if edited_cam is not None:
        selected_cam_ids = edited_cam[edited_cam['select'] == True]['id'].tolist()
        if selected_cam_ids:
            if st.button(
                f"🗑️ Delete {len(selected_cam_ids)} Selected Camera(s)",
                key="delete_cam_btn",
                type="primary"
            ):
                st.session_state.incidents = [
                    inc for inc in st.session_state.incidents
                    if str(inc['id']) not in [str(x) for x in selected_cam_ids]
                ]
                st.rerun()
        
        # Sync changes back to session state
        _sync_camera_changes(edited_cam)


def _sync_camera_changes(edited_df: pd.DataFrame) -> None:
    """Sync edited camera data back to session state."""
    if edited_df is None:
        return
    
    incident_map = {str(x['id']): i for i, x in enumerate(st.session_state.incidents)}
    
    for _, row in edited_df.iterrows():
        idx = incident_map.get(str(row['id']))
        if idx is not None:
            st.session_state.incidents[idx]['level'] = row['level']
