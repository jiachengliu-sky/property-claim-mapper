"""
Shared utilities for static map generation.
"""
import math
from typing import Dict, List, Any
from staticmap import StaticMap
from staticmap.staticmap import _lon_to_x, _lat_to_y
from PIL import Image, ImageDraw

def generate_static_map(
    incidents: List[Dict],
    cameras: List[Dict],
    map_config: Dict = None,
    width: int = 1200,
    height: int = 800,
    auto_fit: bool = True,
    url: str = None
) -> Image.Image:
    """
    Generate a high-fidelity StaticMap image.
    """
    all_markers = incidents + cameras
    
    # Extract base center/zoom from config if available
    config_center = map_config.get('center', [0, 0]) if map_config else [0, 0]
    config_zoom = map_config.get('zoom', 15) if map_config else 15

    # Determine zoom and center
    if auto_fit and all_markers:
        lats = [m['lat'] for m in all_markers]
        lngs = [m['lng'] for m in all_markers]
        min_lat, max_lat = min(lats), max(lats)
        min_lng, max_lng = min(lngs), max(lngs)
        
        center_lat = (min_lat + max_lat) / 2
        center_lng = (min_lng + max_lng) / 2
        
        lat_diff = max_lat - min_lat
        lng_diff = (max_lng - min_lng) * math.cos(math.radians(center_lat))
        max_diff = max(lat_diff, lng_diff)
        
        if max_diff == 0:
            zoom = 18
        else:
            zoom = int(math.log2(360 / max_diff)) - 4
            zoom = max(2, min(zoom, 18))
            
        if len(all_markers) == 1:
            zoom = config_zoom
    else:
        center_lat = config_center[0]
        center_lng = config_center[1]
        zoom = config_zoom

    # Initialize map
    m = StaticMap(width, height, 20, url_template=url) 
    
    # We MUST add at least one feature (even if dummy) or specify center/zoom to render
    # Since we draw manually, we'll just render with the calculated center/zoom.
    # Ensure zoom is an integer for tile servers
    zoom = int(zoom)
    image = m.render(zoom=zoom, center=(center_lng, center_lat))
    draw = ImageDraw.Draw(image)

    # Project coordinates to pixels and draw custom shapes
    # Projection math from staticmap internals
    def project(lat, lng):
        x = (_lon_to_x(lng, zoom) - m.x_center) * m.tile_size + m.width / 2
        y = (_lat_to_y(lat, zoom) - m.y_center) * m.tile_size + m.height / 2
        return int(round(x)), int(round(y))

    for c in cameras:
        x, y = project(c['lat'], c['lng'])
        # Green square for functioning, Black square for not functioning
        color = '#28a745' if c['level'] == 'Functioning' else '#000000'
        size = 14
        half = size // 2
        draw.rectangle([x - half, y - half, x + half, y + half], fill=color, outline="black", width=1)
        
    for i in incidents:
        x, y = project(i['lat'], i['lng'])
        # Yellow, orange, red triangle for incidents (Low, Medium, Serious)
        color = '#dc3545' if i['level'] == 'Serious' else '#fd7e14' if i['level'] == 'Medium' else '#ffc107'
        size = 18
        h = size // 2
        points = [(x, y - h), (x - h, y + h), (x + h, y + h)]
        draw.polygon(points, fill=color, outline="black", width=1)
        
    return image
