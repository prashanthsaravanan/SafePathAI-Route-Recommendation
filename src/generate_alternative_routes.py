import pandas as pd
import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
import folium
from itertools import islice

# Load CSV
df = pd.read_csv("routes.csv")  # Make sure columns: 'source', 'destination'

# Initialize geocoder
geolocator = Nominatim(user_agent="safe_path_ai")

# Geocode unique locations
locations = pd.concat([df['source'], df['destination']]).unique()
location_coords = {}

for loc in locations:
    try:
        loc_obj = geolocator.geocode(loc)
        if loc_obj:
            location_coords[loc] = (loc_obj.latitude, loc_obj.longitude)
            print(f"Geocoded '{loc}' to {location_coords[loc]}")
        else:
            print(f"Could not geocode '{loc}'")
    except Exception as e:
        print(f"Error geocoding '{loc}': {e}")

# Define bounding box
lats = [lat for lat, lon in location_coords.values()]
lons = [lon for lat, lon in location_coords.values()]
north, south = max(lats) + 0.01, min(lats) - 0.01
east, west = max(lons) + 0.01, min(lons) - 0.01

# Download graph using keyword arguments (correct for OSMnx 2.0.6)
print("📥 Downloading graph...")
G = ox.graph_from_bbox(north=north, south=south, east=east, west=west, network_type='drive')
G = ox.add_edge_speeds(G)
G = ox.add_edge_travel_times(G)

# Function for k-shortest paths
def k_shortest_paths(G, orig_node, dest_node, k=3, weight='travel_time'):
    try:
        return list(islice(nx.shortest_simple_paths(G, orig_node, dest_node, weight=weight), k))
    except nx.NetworkXNoPath:
        print(f"No path between {orig_node} and {dest_node}")
        return []

# Create folium map
m = folium.Map(location=list(location_coords.values())[0], zoom_start=12)

# Generate routes
for _, row in df.iterrows():
    source = row['source']
    dest = row['destination']

    orig_node = ox.nearest_nodes(G, X=location_coords[source][1], Y=location_coords[source][0])
    dest_node = ox.nearest_nodes(G, X=location_coords[dest][1], Y=location_coords[dest][0])

    paths = k_shortest_paths(G, orig_node, dest_node, k=3)
    colors = ['blue', 'green', 'red']

    for i, path in enumerate(paths):
        route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path]
        folium.PolyLine(route_coords, color=colors[i % len(colors)], weight=5, opacity=0.7).add_to(m)

# Save map
m.save("alternative_routes_map.html")
print("Map saved as alternative_routes_map.html")
