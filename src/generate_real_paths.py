import pandas as pd
import ast
import osmnx as ox
import networkx as nx
from networkx.algorithms.simple_paths import shortest_simple_paths

# Load CSV
df = pd.read_csv("routes_with_paths.csv")

# Simplify graph helper
def simplify_graph(G):
    G_simple = nx.DiGraph()
    for u, v, data in G.edges(data=True):
        w = data.get("length", 1)
        if G_simple.has_edge(u, v):
            if w < G_simple[u][v]["length"]:
                G_simple[u][v]["length"] = w
        else:
            G_simple.add_edge(u, v, **data)
    return G_simple

# Generate k routes
def get_osmnx_routes(start_lat, start_lon, end_lat, end_lon, k=3, dist=8000):
    # Build the driving network (no manual CRS)
    G = ox.graph_from_point((start_lat, start_lon), dist=dist, network_type="drive", simplify=True)
    
    G_simple = simplify_graph(G)

    orig = ox.distance.nearest_nodes(G_simple, start_lon, start_lat)
    dest = ox.distance.nearest_nodes(G_simple, end_lon, end_lat)

    routes = list(shortest_simple_paths(G_simple, orig, dest, weight="length"))[:k]
    coords_list = [[(G_simple.nodes[n]["y"], G_simple.nodes[n]["x"]) for n in route] for route in routes]
    return coords_list

# Generate routes
new_rows = []

for idx, row in df.iterrows():
    try:
        old_path = ast.literal_eval(row["path"])
        start_lat, start_lon = old_path[0]
        end_lat, end_lon = old_path[-1]

        new_paths = get_osmnx_routes(start_lat, start_lon, end_lat, end_lon, k=3)

        for i, path in enumerate(new_paths, start=1):
            new_row = row.copy()
            new_row["route_id"] = f"{row['route_id']}_{i}"
            new_row["path"] = str(path)
            new_rows.append(new_row)

        print(f"✅ Generated {len(new_paths)} routes for {row['route_id']}")

    except Exception as e:
        print(f"⚠️ Could not generate route for {row['route_id']}: {e}")

# Save CSV
df_new = pd.DataFrame(new_rows)
df_new.to_csv("routes_with_paths_real.csv", index=False)
print("🎯 New CSV saved as routes_with_paths_real.csv")
