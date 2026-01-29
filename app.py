"""
Property Claim Mapper - Main Application

A Streamlit-based web application for mapping and managing property incidents
and security cameras. Designed for property managers to visualize, track,
and report claims and camera locations on an interactive map.
"""
import logging
from datetime import date

import streamlit as st

from config import (
    CUSTOM_CSS,
    get_default_project_data,
    BANNER_PATH
)
from components import (
    render_sidebar,
    render_map_view,
    render_list_view,
    render_statistics
)
from utils.geocoding import search_location

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Boardwalk Incident Map")

# --- Custom CSS ---
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =============================================================================
# Session State Initialization
# =============================================================================

if 'project_data' not in st.session_state:
    st.session_state.project_data = get_default_project_data()

if 'incidents' not in st.session_state:
    st.session_state.incidents = []
    if st.session_state.project_data.get('incidents'):
        st.session_state.incidents = st.session_state.project_data['incidents']

if 'search_result_status' not in st.session_state:
    st.session_state.search_result_status = None
if 'search_result_message' not in st.session_state:
    st.session_state.search_result_message = ""


# =============================================================================
# Sidebar
# =============================================================================

map_locked = render_sidebar()


# =============================================================================
# Main Area - Header
# =============================================================================

# Custom CSS for the rounded label boxes
st.markdown("""
<style>
.label-box {
    background-color: #000000;
    color: #ffffff;
    font-weight: bold;
    padding: 0 15px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    text-align: center;
    font-size: 0.9rem;
    height: 38px;
    margin: 0;
    margin-top: -2px; /* Nudge up to match text input baseline */
}
    /* Global Font Overrides handled in config.py */
    
    /* Label Box Styling */
    .label-box {
        background-color: black;
        color: white;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
        text-align: center;
        white-space: nowrap;
        height: 42px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 0px; /* Removing auto-margin */
    }
    
    /* Success/Error Box Styling for Horizontal Layout */
    .status-box-success {
        background-color: #d1e7dd;
        color: #0f5132;
        padding: 8px 12px;
        border-radius: 8px;
        border: 1px solid #badbcc;
        font-size: 14px;
        height: 42px;
        display: flex;
        align-items: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .status-box-error {
        background-color: #f8d7da;
        color: #842029;
        padding: 8px 12px;
        border-radius: 8px;
        border: 1px solid #f5c2c7;
        font-size: 14px;
        height: 42px;
        display: flex;
        align-items: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# App Header & Inputs
# =============================================================================

st.title("Property Claim Mapper")

# Project Basics
c1, c2, c3, c4 = st.columns([1.2, 4, 1.2, 4], vertical_alignment="center")

with c1:
    st.markdown('<div class="label-box">Property</div>', unsafe_allow_html=True)
with c2:
    st.text_input(
        "Property Name",
        value=st.session_state.project_data['property'],
        label_visibility="collapsed",
        key="prop_input"
    )
    # Update project_data from the widget's session state key
    st.session_state.project_data['property'] = st.session_state.prop_input

with c3:
    st.markdown('<div class="label-box">Year</div>', unsafe_allow_html=True)
with c4:
    st.text_input(
        "Year",
        value=st.session_state.project_data['year'],
        label_visibility="collapsed",
        key="year_input"
    )
    # Update project_data from the widget's session state key
    st.session_state.project_data['year'] = st.session_state.year_input

# For backward compatibility and PDF generation override
st.session_state.current_project_title = f"{st.session_state.prop_input} - {st.session_state.year_input} - Incidents & Claims Map"


# =============================================================================
# Location Search
# =============================================================================

# Define columns: Label | Input | Search Button | Result Box
c_s_label, c_s_input, c_s_btn, c_s_result = st.columns([1.2, 3, 1, 3], vertical_alignment="center")

with c_s_label:
    st.markdown('<div class="label-box">Location</div>', unsafe_allow_html=True)
with c_s_input:
    search_query = st.text_input(
        "📍 Find Location",
        placeholder="Enter full address, e.g. 123 Main St, City, State",
        label_visibility="collapsed"
    )

do_search = False
with c_s_btn:
    if st.button("Search", width="stretch"):
        do_search = True

# Also trigger search on new query
if search_query and search_query != st.session_state.get('last_search_query', ''):
    do_search = True

if do_search and search_query:
    try:
        st.session_state.last_search_query = search_query
        with st.spinner("Searching..."):
            result = search_location(search_query)
        
        if result:
            lat, lng, address = result
            st.session_state.search_result_status = 'success'
            st.session_state.search_result_message = f"Found: {address}"
            
            # Update Map
            st.session_state.project_data['map_config']['center'] = [lat, lng]
            st.session_state.project_data['map_config']['zoom'] = 18
            st.session_state._map_jump_requested = True 
        else:
            st.session_state.search_result_status = 'error'
            st.session_state.search_result_message = "No matching address found."
            
    except Exception as e:
        logger.error(f"Search error: {e}")
        st.session_state.search_result_status = 'error'
        st.session_state.search_result_message = "Search Error"

# Render Persistent Result Box in 4th Column
with c_s_result:
    if st.session_state.search_result_status == 'success':
        st.markdown(
            f'<div class="status-box-success">✅ {st.session_state.search_result_message}</div>', 
            unsafe_allow_html=True
        )
    elif st.session_state.search_result_status == 'error':
        st.markdown(
            f'<div class="status-box-error">❌ {st.session_state.search_result_message}</div>', 
            unsafe_allow_html=True
        )


# =============================================================================
# Tabs
# =============================================================================

tab_map, tab_list, tab_stats = st.tabs([
    "🗺️ Map View",
    "📋 List View",
    "📊 Statistics"
])

with tab_map:
    @st.fragment
    def _map_fragment(locked):
        render_map_view(locked)
    
    _map_fragment(map_locked)

with tab_list:
    render_list_view()

with tab_stats:
    render_statistics()
