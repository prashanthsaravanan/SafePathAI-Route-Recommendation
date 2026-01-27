import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
import matplotlib.pyplot as plt

# Initialize geocoder
geolocator = Nominatim(user_agent="route_app")

def geocode_place(place):
    location = geolocator.geocode(place, timeout=10)
    return (location.latitude, location.longitude) if location else None

source_place = "T Nagar, Chennai, India"
destination_place = "Guindy, Chennai, India"

source_coord = geocode_place(source_place)
destination_coord = geocode_place(destination_place)

print(f"Source: {source_coord}")
print(f"Destination: {destination_coord}")


north = max(source_coord[0], destination_coord[0]) 
south = min(source_coord[0], destination_coord[0]) 
east = max(source_coord[1], destination_coord[1]) 
west = min(source_coord[1], destination_coord[1]) 

# Print bounding box size for diagnostics
lat_span = north - south
lon_span = east - west
print(f"Bounding box latitude span: {lat_span} degrees")
print(f"Bounding box longitude span: {lon_span} degrees")

G = ox.graph_from_bbox(bbox=(north, south, east, west), network_type="drive", simplify=True)
G_undir = G.to_undirected()

def nearest_node(G, coord):
    return ox.distance.nearest_nodes(G, X=coord[1], Y=coord[0])

source_node = nearest_node(G_undir, source_coord)
dest_node = nearest_node(G_undir, destination_coord)

k = 3
paths = list(nx.shortest_simple_paths(G_undir, source_node, dest_node, weight="length"))[:k]

# Plot base graph
fig, ax = ox.plot_graph(G_undir, show=False, close=False)

# Plot multiple routes with distinct colors
colors = ['r', 'g', 'b']
for i, path in enumerate(paths):
    ox.plot_graph_route(G_undir, path, route_color=colors[i % len(colors)], route_linewidth=4, ax=ax, show=False)

plt.title(f'Alternative Routes from {source_place} to {destination_place}')
plt.show()
