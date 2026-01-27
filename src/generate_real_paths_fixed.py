import pandas as pd
import osmnx as ox
import networkx as nx

# ------------------------------
# Load CSV
# ------------------------------
df = pd.read_csv("routes_with_paths.csv")

# ------------------------------
# Helper: convert MultiDiGraph -> DiGraph
# ------------------------------
def convert_to_digraph(G):
    """Convert MultiDiGraph to DiGraph keeping shortest edge between nodes."""
    if isinstance(G, nx.DiGraph):
        return G
    G_simple = nx.DiGraph()
    G_simple.graph.update(G.graph)  # preserve attributes
    for u, v, data in G.edges(data=True):
        w = data.get("length", 1)
        if G_simple.has_edge(u, v):
            if w < G_simple[u][v]["length"]:
                G_simple[u][v]["length"] = w
        else:
            G_simple.add_edge(u, v, **data)
    return G_simple

# ------------------------------
# Function: get shortest route
# ------------------------------
def get_shortest_route(G, start_lat, start_lon, end_lat, end_lon):
    try:
        orig = ox.distance.nearest_nodes(G, X=start_lon, Y=start_lat)
        dest = ox.distance.nearest_nodes(G, X=end_lon, Y=end_lat)
        path = nx.shortest_path(G, orig, dest, weight="length")
        coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in path]
        return coords
    except Exception as e:
        return None

# ------------------------------
# Determine graph area (bounding box)
# ------------------------------
all_coords = [eval(row["path"]) for _, row in df.iterrows()]
lats = [lat for path in all_coords for lat, lon in path]
lons = [lon for path in all_coords for lat, lon in path]
center_lat = sum(lats)/len(lats)
center_lon = sum(lons)/len(lons)
max_dist = max(
    max(abs(lat - center_lat) for lat in lats),
    max(abs(lon - center_lon) for lon in lons)
) * 111000 + 500  # meters

# ------------------------------
# Download graph once
# ------------------------------
print("📥 Downloading graph...")
G = ox.graph_from_point((center_lat, center_lon), dist=max_dist, network_type="drive")
G = convert_to_digraph(G)
print("✅ Graph downloaded and converted to DiGraph.")

# ------------------------------
# Generate shortest route for all rows
# ------------------------------
new_rows = []

for _, row in df.iterrows():
    try:
        old_path = eval(row["path"])
        start_lat, start_lon = old_path[0]
        end_lat, end_lon = old_path[-1]

        coords = get_shortest_route(G, start_lat, start_lon, end_lat, end_lon)
        if coords is None:
            print(f"⚠️ Could not generate route for {row['route_id']}")
            continue

        new_row = row.copy()
        new_row["path"] = str(coords)
        new_rows.append(new_row)
        print(f"✅ Generated route for {row['route_id']}")

    except Exception as e:
        print(f"⚠️ Error for {row['route_id']}: {e}")

# ------------------------------
# Save new CSV
# ------------------------------
df_new = pd.DataFrame(new_rows)
df_new.to_csv("routes_with_paths_real.csv", index=False)
print("🎯 New CSV saved as routes_with_paths_real.csv")
