import osmnx as ox

G = ox.load_graphml("chennai_drive.graphml")
gdf_nodes = ox.graph_to_gdfs(G, edges=False)
print("Graph extent (minx, miny, maxx, maxy):")
print(gdf_nodes.total_bounds)
