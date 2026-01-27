import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
import matplotlib.pyplot as plt

# Load full original MultiDiGraph with edge geometries
G = ox.load_graphml("chennai_drive.graphml")

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

def nearest_node(G, coord):
    return ox.distance.nearest_nodes(G, X=coord[1], Y=coord[0])

print("Finding nearest nodes...")
source_node = nearest_node(G, source_coord)
dest_node = nearest_node(G, destination_coord)
print(f"Source node: {source_node}, Destination node: {dest_node}")

try:
    print("Calculating shortest path on full graph...")
    path = nx.shortest_path(G, source_node, dest_node, weight='length')
    print(f"Path length: {len(path)} nodes")

    # Plot route on full graph with edge geometries
    fig, ax = ox.plot_graph_route(G, path, route_color='r', route_linewidth=4, show=False, close=False)
    plt.title(f'Shortest Route from {source_place} to {destination_place}')
    plt.show()

except nx.NetworkXNoPath:
    print("No path found between source and destination on full graph.")
