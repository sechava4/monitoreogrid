import osmnx as ox
import networkx as nw
import numpy as np
import geopandas as gpd
import matplotlib as mpl
from googlemaps import Client

ox.config(log_file=True, log_console=True, use_cache=True)

import googlemaps as gm

mapService = Client(
    "AIzaSyChV7Sy3km3Fi8hGKQ8K9t7n7J9f6yq9cI", client_id="santiago171cc@gmail.com"
)

# get the street network for san francisco
"""
place = 'San Francisco'
place_query = {'city':'San Francisco', 'state':'California', 'country':'USA'}
G = ox.graph_from_place(place_query, network_type='drive')

# add elevation to each of the nodes, using the google elevation API, then calculate edge grades
G = ox.add_node_elevations(G, api_key="AIzaSyChV7Sy3km3Fi8hGKQ8K9t7n7J9f6yq9cI")
G = ox.add_edge_grades(G)

# project the street network to UTM
G_proj = ox.project_graph(G)

# get one color for each node, by elevation, then plot the network
nc = ox.plot.get_node_colors_by_attr(G_proj, 'elevation', cmap='plasma', num_bins=20)
fig, ax = ox.plot_graph(G_proj, node_color=nc, node_size=12, node_zorder=2, edge_color='#dddddd')
"""

# create the street network within Medellin city borders. Distance 20km from the center.
MDE = ox.graph_from_address(
    "Medellin, Colombia", dist=11000, network_type="drive"
)  # vehicles
MDE_ELE = ox.add_node_elevations(MDE, api_key="AIzaSyChV7Sy3km3Fi8hGKQ8K9t7n7J9f6yq9cI")
MDE_ELE = ox.add_edge_grades(MDE_ELE)


MDE_projected = ox.project_graph(MDE_ELE)
med_colors = ox.plot.get_node_colors_by_attr(
    MDE_projected, "elevation", cmap="plasma", num_bins=20
)
fig, ax = ox.plot_graph(
    MDE_projected,
    node_color=med_colors,
    node_size=12,
    node_zorder=2,
    edge_color="#dddddd",
)

# save Medellin M2 street network as ESRI shapefile to work with in GIS
# ox.io.save_graph_shapefile(MDE_ELE, filepath='MDE_ELE')

# get a color for each edge, by grade, then plot the network
ec = ox.plot.get_edge_colors_by_attr(MDE_projected, "grade", cmap="plasma")
fig, ax = ox.plot_graph(MDE_projected, edge_color=ec, edge_linewidth=0.8, node_size=0)
# G2 = ox.load_graphml('MDEgr.graphml')
# fig, ax = ox.plot_graph(G2, fig_height=30, node_size=0, edge_linewidth=0.5)

MDE_ELE_SPEED = ox.speed.add_edge_speeds(MDE_ELE)
MDE_ELE_SPEED_TIME = ox.speed.add_edge_travel_times(MDE_ELE_SPEED)
ec3 = ox.plot.get_edge_colors_by_attr(MDE_ELE_SPEED_TIME, "speed_kph", cmap="rainbow")

filepath = "osm_data/medellin.graphml"
ox.save_graphml(MDE_ELE_SPEED_TIME, filepath)
G = ox.load_graphml(filepath)
# Speed - se puede dar input del vector de velocidades
# https://osmnx.readthedocs.io/en/stable/osmnx.html#module-osmnx.speed

point_o = (6.197740, -75.589708)
point_d = (6.210548, -75.570576)
nearest_node_o = ox.distance.get_nearest_node(
    G, point_o, method="haversine", return_dist=True
)
nearest_node_d = ox.distance.get_nearest_node(
    G, point_d, method="haversine", return_dist=True
)
ox.plot_graph_route(G, [ox.get_nearest_node(G, (39.982066, -81.11861))])

shortest_path = nw.algorithms.shortest_paths.weighted.dijkstra_path(
    G=G, source=nearest_node_o[0], target=nearest_node_d[0], weight="travel_time"
)
"""
amva = gpd.read_file('osm_data/AMVA.shp')
mission_district = amva[(amva['CITY']=='Medellin') & (amva['NAME']=='Mission')]
polygon = mission_district['geometry'].iloc[0]
M6 = ox.graph_from_polygon(polygon, network_type='all')
M6_projected = ox.project_graph(G6)
#fig, ax = ox.plot_graph(G6_projected)
"""

# M1 = ox.graph_from_address('Medellin, Colombia', distance=4500, network_type='all')
# M1_projected = ox.project_graph(M1)
# fig, ax = ox.plot.plot_graph(M1_projected, node_size=20, edge_linewidth=1)
# add elevation to each of the nodes, using the google elevation API, then calculate edge grades

"""

# get one color for each node, by elevation, then plot the network
nc = ox.get_node_colors_by_attr(G_proj, 'elevation', cmap='plasma', num_bins=20)
fig, ax = ox.plot_graph(G_proj, node_color=nc, node_size=20, node_zorder=2, edge_color='#dddddd')


edge_grades = [osm_data['grade_abs'] for u, v, k, osm_data in ox.get_undirected(G).edges(keys=True, osm_data=True)]

avg_grade  = np.mean(edge_grades)
print('Average street grade in {} is {:.1f}%'.format(place, avg_grade*100))

med_grade = np.median(edge_grades)
print('Median street grade in {} is {:.1f}%'.format(place, med_grade*100))

# get a color for each edge, by grade, then plot the network
ec = ox.get_edge_colors_by_attr(G_proj, 'grade_abs', cmap='plasma', num_bins=100)
fig, ax = ox.plot_graph(G_proj, fig_height=30, edge_color=ec, edge_linewidth=0.8, node_size=0)


# save Medellin M1 street network as ESRI shapefile to work with in GIS
ox.save_graph_shapefile(G, filename='G')

# create the street network within Medellin city borders. Distance 10km from the center.
M3 = ox.graph_from_place('Medellin, Colombia', network_type='all', which_result=2)
M3_projected = ox.project_graph(M3)
fig, ax = ox.plot_graph(M3_projected, fig_height=30, node_size=0, edge_linewidth=0.5)


"""
