"""
PDF report generation utilities.
"""
import logging
import os
import tempfile
from datetime import date
from typing import Any, Dict, List

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for thread safety
import matplotlib.pyplot as plt
import requests
from fpdf import FPDF

from config import ASSETS_DIR, BANNER_PATH, APTOS_REGULAR, APTOS_BOLD, APTOS_ITALIC, APTOS_BOLD_ITALIC
from utils.map_utils import generate_static_map

logger = logging.getLogger(__name__)


class ReportPDF(FPDF):
    """Custom FPDF subclass for branded reports."""
    
    def __init__(self, font_name="Arial", **kwargs):
        super().__init__(**kwargs)
        self.report_font = font_name
        self.registered_styles = {''}  # Default regular
        
        # Auto-register fonts during initialization to ensure availability for footer
        if font_name == "Aptos":
            self.add_font_safe('Aptos', '', APTOS_REGULAR)
            self.add_font_safe('Aptos', 'B', APTOS_BOLD)
            self.add_font_safe('Aptos', 'I', APTOS_ITALIC)
            self.add_font_safe('Aptos', 'BI', APTOS_BOLD_ITALIC)

    def add_font_safe(self, family: str, style: str, file_path: str):
        """Add a font style only if the file exists."""
        if file_path and os.path.exists(file_path):
            try:
                self.add_font(family, style, file_path, uni=True)
                self.registered_styles.add(style)
            except Exception as e:
                logger.error(f"Failed to register font {family} {style}: {e}")

    def set_font_safe(self, style: str = '', size: float = 0):
        """Set font with a safe fallback to regular or Arial if style is missing."""
        # Use registered style if available, otherwise fall back to regular
        target_style = style if style in self.registered_styles else ''
        
        try:
            self.set_font(self.report_font, target_style, size)
        except Exception:
            # Absolute fallback to standard Arial
            try:
                fallback_style = style if style in ['', 'B', 'I', 'BI'] else ''
                self.set_font('Arial', fallback_style, size)
            except Exception:
                self.set_font('Arial', '', size)

    def header(self):
        """No header on content pages."""
        pass

    def footer(self):
        """Add proprietary notice and page number to footer."""
        # Statement Row
        self.set_y(-18)
        self.set_font_safe('I', 7)
        self.set_text_color(128, 128, 128)
        current_year = date.today().year
        footer_text = (
            f"© {current_year} Boardwalk Investments Group. Proprietary & Confidential. "
            "Internal use only. Unauthorized reproduction or distribution is strictly prohibited."
        )
        self.cell(0, 8, footer_text, align='C', ln=True)
        
        # Page Number Row
        self.set_y(-10)
        self.set_font_safe('I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')


def create_pdf(
    project_data: Dict[str, Any],
    incidents: List[Dict[str, Any]],
    project_title: str = "",
    map_tile_url: str = None,
    existing_map_image: bytes = None
) -> bytes:
    """
    Generate PDF report. Tries to use brand fonts, falls back to Arial on error.
    """
    # Determine preferred font
    preferred_font = "Arial"
    if os.path.exists(APTOS_REGULAR) and os.path.exists(APTOS_BOLD):
        preferred_font = "Aptos"
        
    try:
        return _build_pdf(
            project_data, incidents, project_title, 
            map_tile_url, existing_map_image, font_name=preferred_font
        )
    except Exception as e:
        logger.error(f"PDF generation failed with font {preferred_font}: {e}. Falling back to Arial.")
        if preferred_font != "Arial":
            return _build_pdf(
                project_data, incidents, project_title,
                map_tile_url, existing_map_image, font_name="Arial"
            )
        raise e


def _build_pdf(
    project_data: Dict[str, Any],
    incidents: List[Dict[str, Any]],
    project_title: str = "",
    map_tile_url: str = None,
    existing_map_image: bytes = None,
    font_name: str = "Arial"
) -> bytes:
    """Internal function to build the PDF with a specific font."""
    pdf = ReportPDF(font_name=font_name)
    
    # === TITLE PAGE ===
    pdf.add_page()
    if os.path.exists(BANNER_PATH):
        pdf.image(BANNER_PATH, x=25, y=100, w=160)
    
    pdf.set_y(150)
    pdf.set_font_safe('B', 28)
    prop_name = project_data.get('property', project_data.get('name', 'Property'))
    pdf.cell(0, 20, prop_name, ln=True, align='C')
    
    pdf.set_font_safe('', 16)
    year_val = project_data.get('year', str(date.today().year))
    pdf.cell(0, 10, f"{year_val} - Incidents & Claims Map", ln=True, align='C')
    
    pdf.ln(10)
    pdf.set_font_safe('', 12)
    pdf.cell(0, 10, f"Date: {date.today().strftime('%B %d, %Y')}", ln=True, align='C')
    
    if project_data.get('author'):
        pdf.ln(5)
        pdf.cell(0, 10, f"Prepared by: {project_data['author']}", ln=True, align='C')

    # Separate cameras and incidents
    cameras = [i for i in incidents if i.get('type') == 'Camera']
    incident_list = [i for i in incidents if i.get('type') == 'Incident']

    # === CONTENT PAGES ===
    # Start first content page (Map)
    pdf.add_page()
    
    # --- PAGE 2: MAP overview ---
    _add_section_header(pdf, font_name, "Location Map")
    
    _add_location_map(
        pdf, font_name, incidents, cameras, 
        incident_list, project_data.get('map_config'),
        map_tile_url=map_tile_url,
        existing_map_image=existing_map_image
    )
    pdf.ln(8)
    
    # === CAMERA STATISTICS ===
    _add_section_header(pdf, font_name, "Camera Statistics")
    _add_camera_stats(pdf, font_name, cameras)
    pdf.ln(5)
    
    # === INCIDENT STATISTICS ===
    _add_section_header(pdf, font_name, "Incident Statistics")
    _add_incident_stats(pdf, font_name, incident_list)
    pdf.ln(5)
    
    # === INCIDENT DETAILS TABLE ===
    _add_section_header(pdf, font_name, "Incident Details")
    _add_incident_table(pdf, font_name, incident_list)
    
    return pdf.output(dest='S').encode('latin-1')


def _add_section_header(pdf: FPDF, font_name: str, title: str) -> None:
    """Add a styled section header to the PDF."""
    pdf.set_font(font_name, 'B', 14)
    pdf.set_fill_color(50, 50, 50)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, f"  {title}", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)


def _add_location_map(
    pdf: FPDF,
    font_name: str,
    incidents: List[Dict],
    cameras: List[Dict],
    incident_list: List[Dict],
    map_config: Dict = None,
    map_tile_url: str = None,
    existing_map_image: bytes = None
) -> None:
    """Add a real map snapshot to the PDF using Static Maps API."""
    if not incidents:
        pdf.set_font(font_name, '', 10)
        pdf.cell(0, 10, "No markers to display.", ln=True)
        return

    # Attempt to fetch high-res static map snapshot
    try:
        if existing_map_image:
            # Use pre-generated image
            # We need to save it to a temp file for FPDF
            image = None # Placeholder so we don't trip up the save logic below if we were reusing it
            
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                tmp_file.write(existing_map_image)
                tmp_file_path = tmp_file.name
                
            pdf.image(tmp_file_path, x=10, w=190)
            os.unlink(tmp_file_path)
            
        else:
            image = generate_static_map(
                incidents=incident_list,
                cameras=cameras,
                map_config=map_config,
                url=map_tile_url
            )

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                image.save(tmp_file.name)
                pdf.image(tmp_file.name, x=10, w=190)
                os.unlink(tmp_file.name)
        
        # Add Interactive Portal Note


        
        return  # Success!
            
    except Exception as e:
        logger.warning(f"StaticMap generation failed, falling back to schematic: {e}")

    # --- FALLBACK: Schematic Map (Matplotlib) ---
    try:
        with plt.ioff():
            fig_map, ax_map = plt.subplots(figsize=(10, 6))
            # ... (the rest of the matplotlib logic)
            fig_map.patch.set_facecolor('#f0f0f0')
            ax_map.set_facecolor('#e8e8e8')
            
            # Simple scatter plot logic merged here
            for c in cameras:
                color = '#28a745' if c['level'] == 'Functioning' else '#6c757d'
                ax_map.scatter(c['lng'], c['lat'], c=color, s=100, marker='s', edgecolors='black')
                
            for i in incident_list:
                color = '#dc3545' if i['level'] == 'Serious' else '#fd7e14' if i['level'] == 'Medium' else '#28a745'
                ax_map.scatter(i['lng'], i['lat'], c=color, s=120, edgecolors='black')
                ax_map.annotate(str(i['id']), (i['lng'], i['lat']), fontsize=7, ha='center', xytext=(0, 5), textcoords='offset points')
            
            ax_map.set_xlabel("Longitude")
            ax_map.set_ylabel("Latitude")
            ax_map.grid(True, alpha=0.3)
            ax_map.set_title("Property Overview (Schematic)")
            
            plt.tight_layout()
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                fig_map.savefig(tmp_file.name, dpi=120)
                pdf.image(tmp_file.name, x=10, w=190)
                os.unlink(tmp_file.name)
            plt.close(fig_map)
    except Exception as e:
        pdf.set_font_safe('', 10)
        pdf.cell(0, 10, "[Map Generation Error - No details available]", ln=True)


def _add_camera_stats(pdf: FPDF, font_name: str, cameras: List[Dict]) -> None:
    """Add camera statistics section to the PDF."""
    total_cameras = len(cameras)
    functioning = len([c for c in cameras if c['level'] == 'Functioning'])
    dysfunctioning = len([c for c in cameras if c['level'] == 'Not Functioning'])
    
    pdf.set_font_safe('', 10)
    pdf.cell(60, 8, f"Total Cameras: {total_cameras}", ln=False)
    pdf.cell(60, 8, f"Functioning: {functioning}", ln=False)
    pdf.cell(60, 8, f"Dysfunctioning: {dysfunctioning}", ln=True)


def _add_incident_stats(pdf: FPDF, font_name: str, incident_list: List[Dict]) -> None:
    """Add incident statistics section to the PDF."""
    total_claims = len(incident_list)
    total_comp = sum(i.get('compensation', 0) for i in incident_list)
    serious_count = len([i for i in incident_list if i['level'] == 'Serious'])
    medium_count = len([i for i in incident_list if i['level'] == 'Medium'])
    light_count = len([i for i in incident_list if i['level'] == 'Light'])
    
    pdf.set_font_safe('', 10)
    pdf.cell(95, 8, f"Total Claims: {total_claims}", ln=False)
    pdf.cell(95, 8, f"Total Compensation: ${total_comp:,.2f}", ln=True)
    pdf.cell(60, 8, f"Serious: {serious_count}", ln=False)
    pdf.cell(60, 8, f"Medium: {medium_count}", ln=False)
    pdf.cell(60, 8, f"Light: {light_count}", ln=True)
    
    # Top 5 by Compensation
    if incident_list:
        pdf.ln(3)
        pdf.set_font_safe('B', 10)
        pdf.cell(0, 8, "Top 5 Claims by Compensation:", ln=True)
        sorted_inc = sorted(incident_list, key=lambda x: x.get('compensation', 0), reverse=True)[:5]
        pdf.set_font_safe('', 9)
        for idx, inc in enumerate(sorted_inc, 1):
            pdf.cell(
                0, 6,
                f"  {idx}. {inc['id']} - {inc.get('description', 'N/A')} - ${inc.get('compensation', 0):,.2f}",
                ln=True
            )


def _add_incident_table(pdf: FPDF, font_name: str, incident_list: List[Dict]) -> None:
    """Add incident details table to the PDF."""
    if not incident_list:
        pdf.set_font_safe('', 10)
        pdf.cell(0, 10, "No incidents recorded.", ln=True)
        return
    
    # Table header - BLACK background, WHITE text
    pdf.set_fill_color(0, 0, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font_safe('B', 9)
    pdf.cell(15, 8, "ID", 1, 0, 'C', fill=True)
    pdf.cell(20, 8, "Level", 1, 0, 'C', fill=True)
    pdf.cell(25, 8, "Date", 1, 0, 'C', fill=True)
    pdf.cell(30, 8, "Comp ($)", 1, 0, 'C', fill=True)
    pdf.cell(100, 8, "Incident Type", 1, 1, 'C', fill=True)
    
    # Table rows
    pdf.set_text_color(0, 0, 0)
    pdf.set_font_safe('', 8)
    
    for inc in incident_list:
        pdf.cell(15, 7, str(inc.get('id', '?')), 1, 0, 'C')
        pdf.cell(20, 7, str(inc.get('level', '')), 1, 0, 'C')
        pdf.cell(25, 7, str(inc.get('date', ''))[:10], 1, 0, 'C')
        pdf.cell(30, 7, f"${inc.get('compensation', 0):,.2f}", 1, 0, 'R')
        desc = str(inc.get('description', ''))
        pdf.cell(100, 7, desc[:50] + "..." if len(desc) > 50 else desc, 1, 1, 'L')
