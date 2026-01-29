"""
Configuration constants and settings for the Property Claim Mapper application.
"""
import os
from datetime import date
from typing import Dict, List

# --- Asset Paths ---
ASSETS_DIR = "assets"
BANNER_PATH = os.path.join(ASSETS_DIR, "boardwalk_banner.png")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
APTOS_REGULAR = os.path.join(FONTS_DIR, "Aptos.ttf")
APTOS_BOLD = os.path.join(FONTS_DIR, "Aptos-Bold.ttf")
APTOS_ITALIC = os.path.join(FONTS_DIR, "Aptos-Italic.ttf")
APTOS_BOLD_ITALIC = os.path.join(FONTS_DIR, "Aptos-Bold-Italic.ttf")

# --- Default Map Configuration ---
DEFAULT_LOCATION: List[float] = [33.645003281720776, -117.93291469288867]  # Boardwalk Property
DEFAULT_ZOOM: int = 18

TILE_SERVERS: Dict[str, str] = {
    "Street View": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    "Topographic": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
    "Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    "Hybrid": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
}

# --- Icon Paths ---
ICONS: Dict[str, Dict[str, str]] = {
    "Camera": {
        "Functioning": os.path.join(ASSETS_DIR, "functioning_camera.svg"),
        "Not Functioning": os.path.join(ASSETS_DIR, "disfunctioning_camera.svg")
    },
    "Incident": {
        "Light": os.path.join(ASSETS_DIR, "light_incident.svg"),
        "Medium": os.path.join(ASSETS_DIR, "medium_incident.svg"),
        "Serious": os.path.join(ASSETS_DIR, "serious_incident.svg")
    }
}

NEW_MARKER_ICON = os.path.join(ASSETS_DIR, "new_marker.svg")

# --- Incident Types ---
INCIDENT_TYPES: List[str] = sorted([
    "Leak", "Spill", "Slip", "Trip", "Fall", "Dog Bite",
    "Property Damage", "Food Poisoning", "Physical Harassment",
    "Verbal Harassment", "Vandalism", "Theft", "Fire", "Flood",
    "Car Crash", "Intoxication/Drug Use", "Loss of Consciousness",
    "Incident Involving A Minor"
])

# --- CSV Import Configuration ---
CAMERA_REQUIRED_COLS: List[str] = ["level"]
CAMERA_OPTIONAL_COLS: List[str] = ["lat", "lng", "location"]

INCIDENT_REQUIRED_COLS: List[str] = ["level", "description"]
INCIDENT_OPTIONAL_COLS: List[str] = [
    "lat", "lng", "location", "date", "compensation",
    "claim_filed", "premium_impact", "parties"
]

# --- Custom CSS ---
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Apply Aptos font with fallbacks */
    html, body, [class*="css"], .stMarkdown, .stText, .stMetric, .stDataFrame, 
    .stSelectbox, .stTextInput, .stButton, .stRadio, .stCheckbox, .stCaption,
    h1, h2, h3, h4, h5, h6, p, td, th {
        font-family: 'Aptos', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg, [data-testid="stSidebar"] {
        font-family: 'Aptos', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }

    /* Reduce main container padding */
    .stMainBlockContainer {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
    }
</style>
"""


def get_default_project_data() -> dict:
    """Return default project data structure."""
    return {
        'name': 'New Project',
        'property': 'New Property',
        'year': str(date.today().year),
        'author': '',
        'date': str(date.today()),
        'incidents': [],
        'map_config': {
            'center': DEFAULT_LOCATION.copy(),
            'zoom': DEFAULT_ZOOM,
            'source_type': 'map_api',
        }
    }
