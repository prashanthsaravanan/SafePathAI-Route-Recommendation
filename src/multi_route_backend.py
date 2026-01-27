import osmnx as ox
import networkx as nx
from networkx.algorithms.simple_paths import shortest_simple_paths

def get_k_routes(G, source_coord, dest_coord, k=3):
    # Find nearest nodes
    source_node = ox.distance.nearest_nodes(G, X=source_coord[1], Y=source_coord[0])
    dest_node = ox.distance.nearest_nodes(G, X=dest_coord[1], Y=dest_coord[0])

    # Generate k shortest simple paths
    routes = []
    try:
        generator = shortest_simple_paths(G, source_node, dest_node, weight='length')
        for i in range(k):
            route = next(generator)
            routes.append(route)
    except (StopIteration, nx.NetworkXNoPath):
        pass  # Not enough paths found
    
    # Convert node paths to coordinate paths for folium (lat, lon)
    coord_routes = []
    for route in routes:
        coords = []
        for node in route:
            n = G.nodes[node]
            coords.append([n['y'], n['x']])
        coord_routes.append(coords)
    return coord_routes
