import pandas as pd
import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
from sklearn.cluster import DBSCAN
import numpy as np

# Initialize geocoder
geolocator = Nominatim(user_agent="route_app")

# Read your CSV
df = pd.read_csv("routes.csv")

# Geocode addresses to lat/lon
def geocode_place(place):
    try:
        location = geolocator.geocode(place, timeout=10)
        if location:
            return (location.latitude, location.longitude)
        else:
            return None
    except Exception as e:
        print(f"Geocoding error for {place}: {e}")
        return None

# Add lat/lon columns for source and destination
df['source_coords'] = df['source'].apply(geocode_place)
df['destination_coords'] = df['destination'].apply(geocode_place)

# Drop rows that could not be geocoded
df = df.dropna(subset=['source_coords', 'destination_coords'])

# Prepare points for clustering (both source and dest combined)
points = np.array(list(df['source_coords']) + list(df['destination_coords']))

# DBSCAN clustering with smaller eps (~100m) and min_samples=1
db = DBSCAN(eps=0.001, min_samples=1, metric='haversine').fit(np.radians(points))
labels = db.labels_

# Map each coordinate pair to a cluster label
point_to_cluster = {tuple(points[i]): labels[i] for i in range(len(points))}

def get_cluster_label(coord):
    return point_to_cluster.get(coord, -1)

df['cluster'] = df['source_coords'].apply(get_cluster_label)

def nearest_node(G, coord):
    return ox.distance.nearest_nodes(G, X=coord[1], Y=coord[0])

def k_shortest_paths(G, source_coord, dest_coord, k=3, weight='length'):
    source_node = nearest_node(G, source_coord)
    dest_node = nearest_node(G, dest_coord)
    try:
        paths = list(nx.shortest_simple_paths(G, source_node, dest_node, weight=weight))
        paths = paths[:k]
        coords_paths = []
        for path in paths:
            coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path]
            coords_paths.append(coords)
        return coords_paths
    except Exception as e:
        print(f"Error finding paths from {source_coord} to {dest_coord}: {e}")
        return []

# Process each cluster separately
all_routes = []
for cluster_label, group in df.groupby('cluster'):
    coords_in_cluster = list(group['source_coords']) + list(group['destination_coords'])
    lats = [c[0] for c in coords_in_cluster]
    lons = [c[1] for c in coords_in_cluster]

    # Make bbox with very small padding (0.001 degrees)
    north, south = max(lats) + 0.001, min(lats) - 0.001
    east, west = max(lons) + 0.001, min(lons) - 0.001
    bbox = (north, south, east, west)

    print(f"Processing cluster {cluster_label} with {len(group)} routes, bbox={bbox}")

    # Download graph for this cluster
    G = ox.graph_from_bbox(bbox=bbox, network_type='drive', simplify=True)
    G_undir = G.to_undirected()

    for idx, row in group.iterrows():
        routes = k_shortest_paths(G_undir, row['source_coords'], row['destination_coords'], k=3)
        all_routes.append((idx, routes))

# Sort routes by original index and assign back
all_routes.sort(key=lambda x: x[0])
routes_only = [r[1] for r in all_routes]
df['paths'] = pd.Series(routes_only, index=[r[0] for r in all_routes])

# Remove cluster column before saving
df = df.drop(columns=['cluster'])

# Save to CSV
df.to_csv("routes_with_alternatives.csv", index=False)
print("Saved routes_with_alternatives.csv successfully!")
