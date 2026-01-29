# Property Claim Mapper

A Streamlit-based web application for mapping and managing property incidents and security cameras. Designed for property managers to visualize, track, and report claims and camera locations on an interactive map.

## Features

- **Interactive Map View**: Navigate and place markers on a Folium map with satellite imagery
- **Incident Management**: Track incidents with severity levels (Light, Medium, Serious)
- **Camera Tracking**: Monitor camera locations and their operational status
- **List View**: Editable data tables for incidents and cameras
- **Statistics Dashboard**: Visual analytics with charts and key metrics
- **PDF Reports**: Generate professional PDF reports with maps and statistics
- **Project Management**: Save/load projects as JSON files
- **CSV Import**: Bulk import incidents and cameras from CSV files
- **Location Search**: Geocoding to quickly navigate to addresses

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Quick Setup

```bash
# Clone or download the repository
cd property-claim-mapper

# Run the setup script
chmod +x setup_env.sh
./setup_env.sh
```

### Manual Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Start the Streamlit server
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## Usage

### Adding Markers
1. Navigate the map to your desired location
2. Toggle **"Lock Map & Place Markers"** in the sidebar
3. Click on the map to place a new marker
4. Fill in the marker details and click **"Create Marker"**

### Editing Data
- Use the **List View** tab to edit incident and camera data directly
- Select rows and click delete buttons to remove markers

### Generating Reports
- Click **"Generate PDF Report"** in the sidebar
- Download the generated PDF with map, statistics, and incident details

### Importing Data
- Use the **"Load Camera List"** or **"Load Incident List"** buttons
- Upload a CSV file with the required columns (see sidebar for format)

## Project Structure

```
property-claim-mapper/
├── app.py                 # Main Streamlit application
├── config.py              # Configuration and constants
├── requirements.txt       # Python dependencies
├── setup_env.sh          # Environment setup script
├── components/           # UI components
│   ├── sidebar.py        # Sidebar UI
│   ├── map_view.py       # Map tab
│   ├── list_view.py      # List view tab
│   └── statistics.py     # Statistics tab
├── utils/                # Utility functions
│   ├── icons.py          # Icon handling
│   ├── pdf_generator.py  # PDF generation
│   ├── geocoding.py      # Location services
│   └── data_helpers.py   # Data utilities
└── assets/               # Static assets
    ├── fonts/            # Aptos font family
    └── *.svg             # Marker icons
```

## CSV Import Format

### Camera CSV
| Column | Required | Values |
|--------|----------|--------|
| level | Yes | "Functioning" / "Not Functioning" |
| lat | No | Latitude coordinate |
| lng | No | Longitude coordinate |
| location | No | Address text |

### Incident CSV
| Column | Required | Values |
|--------|----------|--------|
| level | Yes | "Light" / "Medium" / "Serious" |
| description | Yes | Incident type |
| lat | No | Latitude coordinate |
| lng | No | Longitude coordinate |
| date | No | Date string |
| compensation | No | Dollar amount |
| claim_filed | No | "yes" / "no" |
| premium_impact | No | "yes" / "no" |

## License

This project uses Microsoft Aptos fonts. See `assets/fonts/Microsoft Aptos Fonts EULA.rtf` for font licensing terms.

## Support

For issues or feature requests, please contact the development team.
