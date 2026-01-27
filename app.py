import streamlit as st
import joblib
import folium
from streamlit_folium import st_folium
import osmnx as ox
import networkx as nx
from networkx.algorithms.simple_paths import shortest_simple_paths
from geopy.geocoders import Nominatim
import pandas as pd
import math
from streamlit_geolocation import streamlit_geolocation
import random
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="🚦 SafePathAI – Route Risk Recommender", layout="wide")

# CSS styling for neat UI
st.markdown('''
<style>
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background: linear-gradient(135deg, #ece9e6, #ffffff);
    }
    .stButton>button {
        background-color: #0078d7;
        color: white;
        border-radius: 10px;
        padding: 10px 25px;
        font-size: 16px;
        font-weight: 600;
        transition: background-color 0.3s ease;
        box-shadow: 0 4px 12px rgb(0 0 0 / 0.1);
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #005ea5;
        color: #e0e0e0;
        box-shadow: 0 6px 16px rgb(0 0 0 / 0.15);
    }
    .block-container {
        padding-top: 2rem !important;
    }
</style>
''', unsafe_allow_html=True)

# Helper functions
def to_simple_digraph(G_multi):
    G_simple = nx.DiGraph()
    for u, v, data in G_multi.edges(data=True):
        length = data.get('length', 1)
        if G_simple.has_edge(u, v):
            if G_simple[u][v]['length'] > length:
                G_simple[u][v].update(data)
        else:
            G_simple.add_edge(u, v, **data)
    for node, data in G_multi.nodes(data=True):
        G_simple.add_node(node, **data)
    G_simple.graph.update(G_multi.graph)
    return G_simple

def haversine(coord1, coord2):
    R = 6371
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def geocode_place(place):
    try:
        location = geolocator.geocode(place, timeout=10)
        if location:
            return (location.latitude, location.longitude)
    except:
        return None
    return None

# Fixed simulation function - removed keys=True
def simulate_traffic(G):
    for u, v, data in G.edges(data=True):
        congestion = random.choices(['Low', 'Medium', 'High'], weights=[0.6, 0.3, 0.1])[0]
        data['congestion'] = congestion
        base_len = data.get('length', 1)
        factor = {'Low': 1, 'Medium': 1.5, 'High': 2}[congestion]
        data['length'] = base_len * factor

@st.cache_resource(show_spinner="Loading road network and model...")
def load_data():
    G_multi = ox.load_graphml("chennai_drive.graphml")
    G = to_simple_digraph(G_multi)
    model = joblib.load("model.pkl")
    return G, model

G, model = load_data()
geolocator = Nominatim(user_agent="route_app")

default_places = [
    "T Nagar, Chennai, India",
    "Guindy, Chennai, India",
    "Saidapet, Chennai, India",
    "Ashok Nagar, Chennai, India",
    "Adyar, Chennai, India",
    "Velachery, Chennai, India",
    "Nungambakkam, Chennai, India",
    "Anna Nagar, Chennai, India",
    "Mylapore, Chennai, India",
]

congestion_map = {"Low": 0, "Medium": 1, "High": 2}
time_map = {"Morning": 0, "Afternoon": 1, "Evening": 2, "Night": 3}

# Initialize session state keys
for key in ["results_df", "coord_routes", "source_coord_saved", "colors_saved", "route_results"]:
    if key not in st.session_state:
        st.session_state[key] = None

st.title("🚦 SafePathAI – Route Risk Recommender with Simulated Traffic")

# Sidebar controls with periodic refresh for live location (every 5s)
with st.sidebar:
    st.markdown("## Route Settings")
    count = st_autorefresh(interval=5000, limit=None, key="location_refresh")

    use_live_location = st.toggle("📡 Use My Live Location as Source")

    if use_live_location:
        location = streamlit_geolocation()
        if location:
            source_coord = (location["latitude"], location["longitude"])
            st.success(f"Using live location: {source_coord}")
            source_place = "Live Location"
        else:
            source_coord = None
            st.info("Waiting for location or permission denied.")
            source_place = None
    else:
        source_place = st.selectbox("📍 Source", default_places)
        source_coord = geocode_place(source_place)

    if not use_live_location:
        destination_place = st.selectbox("🎯 Destination", [p for p in default_places if p != source_place])
    else:
        destination_place = st.selectbox("🎯 Destination", default_places)

    time_of_travel = st.radio("🕒 Time of Travel", ["Morning", "Afternoon", "Evening", "Night"], horizontal=True)

    show_table = st.checkbox("Show Route Table", value=True)
    show_map = st.checkbox("Show Route Map", value=True)

    generate_button = st.button("🚦 Generate Safe Routes", key="generate")

# Show results from session state if available
if st.session_state.results_df is not None:
    df = st.session_state.results_df
    coord_routes = st.session_state.coord_routes
    source_coord = st.session_state.source_coord_saved
    colors = st.session_state.colors_saved
    results = st.session_state.route_results

    st.markdown("### 🗺️ Route Results")
    best_idx = df["Predicted Risk"].idxmin()
    best_route_id = df.loc[best_idx, "Route"]
    st.success(f"**Safest Route:** {best_route_id}")

    tabs_labels = []
    if show_table:
        tabs_labels.append("📝 Route Table")
    if show_map:
        tabs_labels.append("🗺️ Route Map")

    if tabs_labels:
        tabs = st.tabs(tabs_labels)
        tab_index = 0
        if show_table:
            with tabs[tab_index]:
                st.dataframe(df, use_container_width=True, hide_index=True)
            tab_index += 1
        if show_map:
            with tabs[tab_index if show_table else 0]:
                map_obj = folium.Map(location=source_coord, zoom_start=13)
                for i, coords in enumerate(coord_routes):
                    popup = folium.Popup(f"<b>Route: R{i+1}</b><br>Distance: {results[i]['Distance (km)']} km<br>Risk: {results[i]['Predicted Risk']}", max_width=300)
                    folium.PolyLine(coords, color=colors[i % len(colors)], weight=7, opacity=0.8, popup=popup).add_to(map_obj)
                    folium.Marker(coords[0], popup=f"Start - R{i+1}", icon=folium.Icon(color="blue", icon="play")).add_to(map_obj)
                    folium.Marker(coords[-1], popup=f"End - R{i+1}", icon=folium.Icon(color="red", icon="stop")).add_to(map_obj)
                folium.LayerControl().add_to(map_obj)
                st_folium(map_obj, width=900, height=600)

# Compute routes and simulate traffic on button press
if generate_button:
    with st.spinner("Simulating traffic, calculating safest routes..."):
        # Simulate traffic congestion on graph edges before routing
        simulate_traffic(G)

        # Determine source coordinates from live or geocoded input
        if use_live_location:
            if source_coord is None:
                st.error("Live location not available. Please allow location permissions.")
                st.stop()
        else:
            source_coord = geocode_place(source_place)
            if source_coord is None:
                st.error("Could not geocode source location.")
                st.stop()

        destination_coord = geocode_place(destination_place)
        if destination_coord is None:
            st.error("Could not geocode destination.")
            st.stop()

        source_node = ox.distance.nearest_nodes(G, X=source_coord[1], Y=source_coord[0])
        dest_node = ox.distance.nearest_nodes(G, X=destination_coord[1], Y=destination_coord[0])

        try:
            path_gen = shortest_simple_paths(G, source_node, dest_node, weight='length')
            routes = [next(path_gen) for _ in range(3)]
            results = []
            coord_routes = []

            colors = ['#ef4444', '#f59e0b', '#10b981']
            congestion_vals = ["Medium", "High", "Low"]

            for i, path in enumerate(routes):
                coords = [[G.nodes[n]['y'], G.nodes[n]['x']] for n in path]
                coord_routes.append(coords)
                dist_km = sum(haversine(coords[j], coords[j+1]) for j in range(len(coords)-1))
                features = [dist_km, congestion_map[congestion_vals[i % len(congestion_vals)]], 0, time_map[time_of_travel]]
                prediction = model.predict([features])[0]
                results.append({
                    "Route": f"R{i+1}",
                    "Distance (km)": f"{dist_km:.2f}",
                    "Congestion": congestion_vals[i % len(congestion_vals)],
                    "Accidents": 0,
                    "Predicted Risk": prediction
                })

            df = pd.DataFrame(results)

            # Store results for session persistence
            st.session_state.results_df = df
            st.session_state.coord_routes = coord_routes
            st.session_state.source_coord_saved = source_coord
            st.session_state.colors_saved = colors
            st.session_state.route_results = results

            st.stop()
        except nx.NetworkXNoPath:
            st.error("No path found between source and destination.")
