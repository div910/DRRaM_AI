import requests
import networkx as nx
from datetime import datetime, timedelta, time
from math import radians, sin, cos, sqrt, atan2
from queue import PriorityQueue
from flask import jsonify, request
import folium
import random
from sklearn.cluster import KMeans
API_KEY = "TkJNeMv0lEO00urfRPxkgCbaZvHpHCYp"

class RoutingOptimizer:
    def __init__(self, tomtom_api_key, hubLatitude, hubLongitude):
        self.tomtom_api_key = tomtom_api_key
        self.hubLatitude = hubLatitude
        self.hubLongitude = hubLongitude
        self.base_url_traffic = "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json?point="
        self.base_url_route = "https://api.tomtom.com/routing/1/calculateRoute/"
        self.extra_route = "/json?&vehicleHeading=90&sectionType=traffic&report=effectiveSettings&routeType=eco&traffic=true&travelMode=car&vehicleMaxSpeed=120&vehicleCommercial=false&vehicleEngineType=combustion&key="
        self.cache = {}

    def calculate_time_priority(self, current_time, deadline):
        time_to_deadline = (deadline - current_time).total_seconds() / 3600
        return max(0, min(1, 1 - (time_to_deadline / 24)))

    def get_route_details(self, start_coords, end_coords):
        cache_key = (start_coords, end_coords)
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            start_lat, start_long = start_coords
            end_lat, end_long = end_coords

            traffic_response = requests.get(
                f"{self.base_url_traffic}{start_lat}%2C{start_long}&unit=KMPH&openLr=false&key={self.tomtom_api_key}")
            route_response = requests.get(
                f"{self.base_url_route}{start_lat},{start_long}:{end_lat},{end_long}{self.extra_route}{self.tomtom_api_key}")

            if traffic_response.status_code == 200 and route_response.status_code == 200:
                traffic_data = traffic_response.json()
                route_data = route_response.json()

                route_info = {
                    'travel_time': route_data['routes'][0]['summary']['travelTimeInSeconds'],
                    'distance': route_data['routes'][0]['summary']['lengthInMeters'] / 1000,
                    'current_speed': traffic_data['flowSegmentData']['currentSpeed']
                }

                self.cache[cache_key] = route_info
                return route_info
            else:
                raise Exception("API error")
        except Exception as e:
            print(f"Exception in get_route_details: {e}")
            return {'travel_time': float('inf'), 'distance': float('inf'), 'current_speed': 0}

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def heuristic_cost(self, start_dest, end_dest):
        geo_distance = self.haversine(start_dest['latitude'], start_dest['longitude'], end_dest['latitude'], end_dest['longitude'])
        if start_dest['deadline'] is None or end_dest['deadline'] is None:
            time_priority = 0.01  # or another default value
        else:
            time_priority = max(0.01, self.calculate_time_priority(datetime.now(), start_dest['deadline']))
        
        route_info = self.get_route_details((start_dest['latitude'], start_dest['longitude']), (end_dest['latitude'], end_dest['longitude']))

        heuristic_value = (
            geo_distance * 0.3 +
            (1 / time_priority) * 0.4 +
            (route_info['travel_time'] / 3600) * 0.3
        )

        return heuristic_value

    def a_star(self, destinations):
       # Initialize nodes and graph
        hub = {'latitude': float(self.hubLatitude), 'longitude': float(self.hubLongitude), 'deadline': datetime.now()}
        destinations.insert(0, hub)  # Add the hub at the beginning
        G = nx.DiGraph()
        
        # Add nodes for each destination (including hub)
        for i, dest in enumerate(destinations):
            G.add_node(i, **dest)

        # Add edges based on heuristic cost
        for start_idx, start_dest in enumerate(destinations):
            for end_idx, end_dest in enumerate(destinations):
                if start_idx != end_idx:
                    heuristic_weight = self.heuristic_cost(start_dest, end_dest)
                    G.add_edge(start_idx, end_idx, weight=heuristic_weight)

        all_paths = []
        for start in range(1, len(destinations)):  # Exclude the hub from the start
            try:
                current_path = [0]  # Start from the hub (index 0)
                unvisited = set(range(1, len(destinations)))  # All other destinations

                while unvisited:
                    next_dest = min(
                        unvisited,
                        key=lambda x: self.heuristic_cost(destinations[current_path[-1]], destinations[x])
                    )
                    current_path.append(next_dest)
                    unvisited.remove(next_dest)

                path_cost = sum(
                    self.heuristic_cost(destinations[current_path[i]], destinations[current_path[i + 1]])
                    for i in range(len(current_path) - 1)
                )

                all_paths.append((current_path, path_cost))

            except Exception as e:
                print(f"Error calculating path from {start}: {e}")

        if all_paths:
            optimal_path, path_cost = min(all_paths, key=lambda x: x[1])
            return optimal_path  # Return indices relative to the destinations list (including hub)

        return None



def get_coordinates(source, destination):
    # TomTom API endpoint
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{source[0]},{source[1]}:{destination[0]},{destination[1]}/json"

    # Parameters for the API request
    params = {
        "key": API_KEY,
        "routeType": "fastest",
        "travelMode": "car"
    }

    # Make API request
    response = requests.get(url, params=params)

    # Check response status
    if response.status_code == 200:
        data = response.json()
        # Extract route geometry (polyline of the route)
        route_points = data["routes"][0]["legs"][0]["points"]
        coordinates = [(point["latitude"], point["longitude"]) for point in route_points]
    else:
        print("Error:", response.status_code, response.text)
        exit()

    return coordinates
def string_to_datetime(deadline_str):
    """Convert a time string in 'HH:MM' format to a datetime object with today's date."""
    today = datetime.today().date()
    hour, minute = map(int, deadline_str.split(':'))
    deadline_time = time(hour, minute)  # Create a time object
    return datetime.combine(today, deadline_time)  # Combine with today's date

def kmeans_clustering(destinations, n_clusters):
    coordinates = [(dest['latitude'], dest['longitude']) for dest in destinations]
    kmeans = KMeans(n_clusters=n_clusters)
    kmeans.fit(coordinates)
    labels = kmeans.labels_
    
    # Map each cluster to a list of (original_index, destination) pairs
    clustered_destinations = [[] for _ in range(n_clusters)]
    for idx, label in enumerate(labels):
        clustered_destinations[label].append((idx, destinations[idx]))  # Keep track of the original index
    
    return clustered_destinations

def plan_optimized_route(allDestinations, hubLatitude, hubLongitude, numRoutes):
    #print(f"allDestinations:{allDestinations}")
    destinations = []
    for destination in allDestinations:
        #print(f"Processing destination: {destination}")
        id,latitude, longitude, deadline = destination
        destinations.append({'id':id,'latitude': float(latitude), 'longitude': float(longitude), 'deadline': string_to_datetime(deadline)})

    clusters = kmeans_clustering(destinations, int(numRoutes))
    optimizer = RoutingOptimizer('mTrA9kG5mGHYEIBmGPkwvCIAQ0DlARhJ', hubLatitude, hubLongitude)
    optimized_routes = []
    routes_coordinates = []  # List to store coordinates for each route
    check = []
    hub_coords = (float(hubLatitude), float(hubLongitude))

    # Process each cluster as a separate route
    for cluster_idx, cluster in enumerate(clusters):
        print(f"Processing cluster {cluster_idx + 1} with {len(cluster)} points...")
        cluster_destinations = [d[1] for d in cluster]
        optimized_route = optimizer.a_star(cluster_destinations)

        if optimized_route:
            route_coords = [hub_coords]  # Start with hub
            # Add each destination in the optimized order
            checks=[]
            for bin_index in optimized_route[1:]:
                if bin_index < len(cluster_destinations):
                    dest = cluster_destinations[bin_index]
                    coord = (dest['latitude'], dest['longitude'])
                    route_coords.append(coord)
                    checks.append(dest['id'])

            routes_coordinates.append(route_coords)
            optimized_routes.append(optimized_route)
            check.append(checks)

    try:
        print(routes_coordinates) 
        generate_map_html(routes_coordinates)
    except Exception as e:
        print(f"Error generating map: {e}")

    #return optimized_routes
    return check

def generate_map_html(routes):
    if not routes or not routes[0]:
        return

    map_route = folium.Map(location=routes[0][0], zoom_start=12)

    colors = ["blue", "red", "green", "purple", "orange", "darkred", "pink", "lightred", "beige", "darkblue", "darkgreen"]

    for route_idx, route_coords in enumerate(routes):
        route_color = colors[route_idx % len(colors)]
        
        for idx, coord in enumerate(route_coords):
            if idx == 0:
                folium.Marker(
                    location=coord,
                    popup="Hub",
                    icon=folium.Icon(color='red')
                ).add_to(map_route)
            else:
                folium.Marker(
                    location=coord,
                    popup=f"Route {route_idx + 1} - Stop {idx}",
                    icon=folium.Icon(color=route_color)
                ).add_to(map_route)
                
        for idx, coord in enumerate(route_coords):
            if idx == len(route_coords) - 1:
                break   
            folium.PolyLine(locations=get_coordinates(route_coords[idx], route_coords[idx+1]), color=route_color, weight=5).add_to(map_route)

    map_route.save("route_map.html")
    print("Map saved as route_map.html. Open it in your browser.")