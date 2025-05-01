import subprocess
import os
from xml.etree import ElementTree as ET
import osmnx as ox
import folium
import webbrowser

def extract_osm_data(pbf_path, output_osm_path):
    # Define the bounding box string
    bbox = f"{min_lat},{min_lon},{max_lat},{max_lon}"
    
    # Construct the osmconvert command
    command = [
        './osmconvert.exe',
        pbf_path,
        f'-b={bbox}',
        '--complete-ways',
        f'-o={output_osm_path}'
    ]
    
    # Execute the command
    try:
        subprocess.run(command, check=True)
        print(f"OSM data extracted successfully to {output_osm_path}")

        # Check if the OSM file contains nodes or ways
        if not contains_nodes_or_ways(output_osm_path):
            print("Warning: The extracted .osm file contains no <node> or <way> elements.")

    except subprocess.CalledProcessError as e:
        print(f"Error occurred while extracting OSM data: {e}")

def contains_nodes_or_ways(file_path):
    """Check if the OSM file contains at least one node or way."""
    try:
        context = ET.iterparse(file_path, events=("start",))
        for event, elem in context:
            if elem.tag in ('node', 'way'):
                return True
        return False
    except ET.ParseError:
        print("Error: The file is not a valid XML.")
        return False
    



#from osmnx import utils_graph

def plot_osm_with_osmnx(osm_file, min_lat, min_lon, max_lat, max_lon, output_html="map.html", ):
    try:
        # Load graph from OSM file
        G = ox.graph_from_xml(osm_file)
        if len(G) == 0:
            print("Loaded graph is empty.")
            return

        # Reproject and make undirected
#        G_drive = ox.project_graph(G, to_crs="EPSG:4326")
#        G_drive = ox.utils_graph.get_undirected(G_drive)

        G = G.to_undirected()



        # Filter edges by road type (keep only drivable roads)
        allowed_highways = [
            'motorway', 'trunk', 'primary', 'secondary', 'tertiary',
            'unclassified', 'residential', 'motorway_link', 'trunk_link',
            'primary_link', 'secondary_link', 'tertiary_link', 'living_street'
        ]

        for u, v, k, d in list(G.edges(keys=True, data=True)):
            if d.get('highway') not in allowed_highways:
                G.remove_edge(u, v, k)

        # Convert nodes and edges to GeoDataFrames
        nodes, edges = ox.graph_to_gdfs(G)

        # Create a Folium map centered on the first node
        first_point = nodes.iloc[0]
        m = folium.Map(location=[first_point['y'], first_point['x']], zoom_start=14)

        # Plot nodes
        for idx, row in nodes.iterrows():
            folium.CircleMarker(
                location=(row['y'], row['x']),
                radius=2,
                color='blue',
                tooltip=str(idx),
                fill=True
            ).add_to(m)

        # Plot edges
        for idx, row in edges.iterrows():
            coords = [(point[1], point[0]) for point in list(row['geometry'].coords)]
            """
            folium.PolyLine(
                coords,
                color="gray",
                weight=12
            ).add_to(m)
            """
            # Get the 'name' attribute if available
            name = row.get('name', 'Unnamed')
            highway_type = row.get('highway', 'Unknown')

            popup_html = f"<strong>Name:</strong> {name}<br><strong>Type:</strong> {highway_type}"
            folium.PolyLine(
                coords,
                color="green",
                weight=5,
                opacity=1,
                tooltip=name,           # Show only name on hover
                popup=folium.Popup(popup_html, max_width=300)  # Show more info on click
            ).add_to(m)

        # Using folium.Rectangle
        rectangle_bounds = [(min_lon, min_lat), (max_lon, max_lat)]
        folium.Rectangle(
            bounds=rectangle_bounds,
            color='purple',
            fill=True,
            fill_opacity=0.1,
            opacity=1,
            tooltip="Bounding Box",
            dash_array='10'
        ).add_to(m)

        # Save map
        m.save(output_html)
        print(f"Map saved to {output_html}")

        webbrowser.open(output_html)  # Automatically open in browser

    except Exception as e:
        print(f"Error plotting OSM file with OSMnx: {e}")

# Example usage
pbf_input = 'mongolia-latest.osm.pbf'
osm_output = 'inn.osm'

# 西、南、东、北
min_lat, min_lon, max_lat, max_lon = 106.87541553986095,47.91294367810841,106.89557986259717,47.91883172854061  # Example coordinates

extract_osm_data(pbf_input, osm_output)

plot_osm_with_osmnx(osm_output, min_lat, min_lon, max_lat, max_lon)
