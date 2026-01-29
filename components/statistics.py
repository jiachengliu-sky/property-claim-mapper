"""
Statistics component for the Property Claim Mapper.
"""
import logging

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


def render_statistics() -> None:
    """Render the statistics tab content."""
    st.subheader("Project Statistics")
    
    if not st.session_state.incidents:
        st.info("No data available for statistics.")
        return
    
    stats_df = pd.DataFrame(st.session_state.incidents)
    
    # Separate cameras and incidents
    cameras_df = (
        stats_df[stats_df['type'] == 'Camera']
        if 'type' in stats_df.columns
        else pd.DataFrame()
    )
    incidents_df = (
        stats_df[stats_df['type'] == 'Incident']
        if 'type' in stats_df.columns
        else pd.DataFrame()
    )
    
    # Camera Stats Panel
    _render_camera_stats(cameras_df)
    
    st.divider()
    
    # Incident Stats Panel
    _render_incident_stats(incidents_df)


def _render_camera_stats(cameras_df: pd.DataFrame) -> None:
    """Render the camera statistics section."""
    st.markdown("### 📷 Camera Stats")
    
    if cameras_df.empty:
        st.info("No camera data available.")
        return
    
    total_cameras = len(cameras_df)
    functioning_cameras = (
        len(cameras_df[cameras_df['level'] == 'Functioning'])
        if 'level' in cameras_df.columns
        else 0
    )
    dysfunctioning_cameras = (
        len(cameras_df[cameras_df['level'] == 'Not Functioning'])
        if 'level' in cameras_df.columns
        else 0
    )
    
    # Metrics row
    cam_c1, cam_c2, cam_c3 = st.columns(3)
    cam_c1.metric("Total Cameras", total_cameras)
    cam_c2.metric("Functioning", functioning_cameras)
    cam_c3.metric("Dysfunctioning", dysfunctioning_cameras)
    
    # Pie chart
    if 'level' in cameras_df.columns and total_cameras > 0:
        _render_camera_pie_chart(cameras_df)


def _render_camera_pie_chart(cameras_df: pd.DataFrame) -> None:
    """Render the camera status distribution pie chart."""
    try:
        cam_status_counts = cameras_df['level'].value_counts()
        
        with plt.ioff():
            fig_cam, ax_cam = plt.subplots(figsize=(2.5, 2))
            fig_cam.patch.set_alpha(0.0)
            
            colors_cam = [
                '#28a745' if label == 'Functioning' else '#dc3545'
                for label in cam_status_counts.index
            ]
            
            ax_cam.pie(
                cam_status_counts,
                labels=cam_status_counts.index,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors_cam
            )
            ax_cam.axis('equal')
            ax_cam.set_title("Camera Status Distribution")
            
            st.pyplot(fig_cam)
            plt.close(fig_cam)
            
    except Exception as e:
        logger.error(f"Failed to render camera pie chart: {e}")
        st.warning("Could not render camera chart.")


def _render_incident_stats(incidents_df: pd.DataFrame) -> None:
    """Render the incident statistics section."""
    st.markdown("### 🚨 Incident Stats")
    
    if incidents_df.empty:
        st.info("No incident data available.")
        return
    
    total_claims = len(incidents_df)
    total_compensation = (
        incidents_df['compensation'].sum()
        if 'compensation' in incidents_df.columns
        else 0.0
    )
    
    # Metrics row
    inc_c1, inc_c2 = st.columns(2)
    inc_c1.metric("Total Claims", total_claims)
    inc_c2.metric("Total Compensation", f"${total_compensation:,.2f}")
    
    # Top 5 Claims by Compensation
    _render_top_claims(incidents_df)
    
    # Top 5 Incident Types by Count
    _render_incident_type_chart(incidents_df)


def _render_top_claims(incidents_df: pd.DataFrame) -> None:
    """Render the top 5 claims by compensation table."""
    st.markdown("##### Top 5 Claims by Compensation")
    
    if 'compensation' not in incidents_df.columns:
        st.info("No compensation data.")
        return
    
    top5_comp = incidents_df.nlargest(5, 'compensation')[
        ['id', 'description', 'level', 'date', 'compensation']
    ].copy()
    
    top5_comp['compensation'] = top5_comp['compensation'].apply(
        lambda x: f"${x:,.2f}"
    )
    top5_comp.columns = ['ID', 'Incident Type', 'Level', 'Date', 'Compensation']
    
    st.dataframe(top5_comp, hide_index=True, width="stretch")


def _render_incident_type_chart(incidents_df: pd.DataFrame) -> None:
    """Render the top 5 incident types horizontal bar chart."""
    st.markdown("##### Top 5 Incident Types by Count")
    
    if 'description' not in incidents_df.columns:
        st.info("No incident type data.")
        return
    
    try:
        incident_type_counts = incidents_df['description'].value_counts().head(5)
        
        with plt.ioff():
            fig_inc, ax_inc = plt.subplots(figsize=(4, 2))
            fig_inc.patch.set_alpha(0.0)
            
            bars = ax_inc.barh(
                incident_type_counts.index[::-1],
                incident_type_counts.values[::-1],
                color='#FF6B6B'
            )
            
            ax_inc.set_xlabel("Count")
            ax_inc.xaxis.set_major_locator(MaxNLocator(integer=True))
            ax_inc.set_title("Top 5 Incident Types")
            
            for bar, val in zip(bars, incident_type_counts.values[::-1]):
                ax_inc.text(
                    bar.get_width() + 0.1,
                    bar.get_y() + bar.get_height() / 2,
                    str(val),
                    va='center',
                    fontsize=10
                )
            
            plt.tight_layout()
            st.pyplot(fig_inc)
            plt.close(fig_inc)
            
    except Exception as e:
        logger.error(f"Failed to render incident type chart: {e}")
        st.warning("Could not render incident chart.")
