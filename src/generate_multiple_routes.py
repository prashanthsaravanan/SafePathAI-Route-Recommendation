import osmnx as ox
import networkx as nx
import pandas as pd

# ---------------- CONFIG ----------------
# Replace with YOUR chosen coordinates (lat, lon)
origin_point = (13.0827, 80.2707)   # Chennai Central
destination_point = (13.0358, 80.2444)  # Guindy
dist = 3000      # meters radius around origin to download
k = 3            # number of alternative routes to generate
output_file = "routes_dataset.csv"
# ----------------------------------------

print("📥 Downloading graph...")
G = ox.graph_from_point(origin_point, dist=dist, network_type="drive")
print("✅ Graph downloaded.")

# Convert MultiDiGraph to a simple weighted DiGraph
# Keeps only the shortest edge between nodes (weight = length)
G_simple = nx.DiGraph()
for u, v, data in G.edges(data=True):
    w = data.get("length", 1)
    if G_simple.has_edge(u, v):
        if w < G_simple[u][v]["weight"]:
            G_simple[u][v]["weight"] = w
    else:
        G_simple.add_edge(u, v, weight=w)

# Find nearest nodes to origin/destination
orig_node = ox.distance.nearest_nodes(G, origin_point[1], origin_point[0])
dest_node = ox.distance.nearest_nodes(G, destination_point[1], destination_point[0])
print(f"Origin node: {orig_node}, Destination node: {dest_node}")

# Generate k shortest simple paths
routes = []
for i, path in enumerate(
    list(nx.shortest_simple_paths(G_simple, orig_node, dest_node, weight="weight"))[:k]
):
    length = nx.path_weight(G_simple, path, weight="weight")
    coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in path]
    routes.append({"route_id": i + 1, "length_m": round(length, 2), "nodes": path, "coords": coords})

# Save dataset
pd.DataFrame(routes).to_csv(output_file, index=False)
print(f"✅ Saved {len(routes)} routes to {output_file}")
