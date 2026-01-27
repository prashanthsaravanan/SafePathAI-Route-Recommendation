import osmnx as ox

# This creates a new, full driving road network for all of Chennai
G = ox.graph_from_place('Chennai, India', network_type='drive')
ox.save_graphml(G, 'chennai_drive.graphml')
print("Downloaded and saved Chennai driving graph as chennai_drive.graphml")
