import os
import pandas as pd
import osmnx as ox
import networkx as nx

# ---------------- CONFIG ----------------
input_csv  = "routes_with_paths_real.csv"   # Your input file
output_csv = "routes_with_alternative_paths.csv"  # Output dataset
k_routes   = 3      # Number of alternative routes for each pair
dist       = 5000   # Download radius (meters) around the origin
# ----------------------------------------

def simplify_graph(G):
    """Convert MultiDiGraph to simple DiGraph keeping shortest edges."""
    G_simple = nx.DiGraph()
    for u, v, data in G.edges(data=True):
        w = data.get("length", 1)
        if G_simple.has_edge(u, v):
            if w < G_simple[u][v]["weight"]:
                G_simple[u][v]["weight"] = w
        else:
            G_simple.add_edge(u, v, weight=w)
    return G_simple

def generate_alternative_routes(origin, destination, k=3, dist=18000):
    """
    Generate k alternative routes between origin and destination.
    origin, destination: (lat, lon)
    Returns a list of route dictionaries.
    """
    try:
        # Download a drivable graph around the midpoint
        center_point = ((origin[0] + destination[0]) / 2,
                        (origin[1] + destination[1]) / 2)
        G = ox.graph_from_point(center_point, dist=dist, network_type="drive")
        G_simple = simplify_graph(G)

        # Find nearest nodes
        orig_node = ox.distance.nearest_nodes(G, origin[1], origin[0])
        dest_node = ox.distance.nearest_nodes(G, destination[1], destination[0])

        routes = []
        for i, path in enumerate(
            list(nx.shortest_simple_paths(G_simple, orig_node, dest_node, weight="weight"))[:k]
        ):
            length = nx.path_weight(G_simple, path, weight="weight")
            coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in path]
            routes.append({
                "origin_lat": origin[0],
                "origin_lon": origin[1],
                "dest_lat": destination[0],
                "dest_lon": destination[1],
                "route_id": i + 1,
                "length_m": round(length, 2),
                "nodes": path,
                "coords": coords
            })
        return routes
    except Exception as e:
        print(f"⚠️ Skipping pair {origin}->{destination}: {e}")
        return []

def main():
    df = pd.read_csv(input_csv)
    all_routes = []

    # Expecting columns: origin_lat, origin_lon, dest_lat, dest_lon
    for idx, row in df.iterrows():
        origin = (row["origin_lat"], row["origin_lon"])
        destination = (row["dest_lat"], row["dest_lon"])
        print(f"📍 Processing {idx+1}/{len(df)}: {origin} -> {destination}")
        routes = generate_alternative_routes(origin, destination,
                                             k=k_routes, dist=dist)
        all_routes.extend(routes)

    if all_routes:
        pd.DataFrame(all_routes).to_csv(output_csv, index=False)
        print(f"✅ Saved {len(all_routes)} total routes to {output_csv}")
    else:
        print("⚠️ No routes generated. Check input coordinates or increase dist.")

if __name__ == "__main__":
    main()
