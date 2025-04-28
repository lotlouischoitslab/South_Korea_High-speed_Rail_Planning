import pandas as pd
import itertools
import numpy as np

# Load station data
hsr_location_data = pd.read_excel('datasets/HSR_Locations.xlsx')

# Define station list in Gyeongbu Line order
stations = ['Seoul', 'Gwangmyeong', 'Cheonan-Asan', 'Osong', 'Daejeon', 'Gimcheon-Gumi', 'Dongdaegu', 'Gyeongju', 'Ulsan (Tongdosa)', 'Busan']

# Mandatory stops
mandatory_stops = {'Seoul', 'Daejeon', 'Dongdaegu', 'Busan'}

# Optional stops
optional_stops = [s for s in stations if s not in mandatory_stops]

# Mapping station name to spacing (be careful with units)
station_spacing = dict(zip(hsr_location_data['Station'], hsr_location_data['Station Spacing (km)']))

# Speed and dwell time assumptions
cruise_speed = 300  # km/h
dwell_time_per_stop = 5  # minutes

# Enumerate all combinations of optional stops (stop or skip)
all_stop_plans = list(itertools.product([0, 1], repeat=len(optional_stops)))

results = []

for plan in all_stop_plans:
    stops = list(mandatory_stops)  # always include mandatory
    for idx, choice in enumerate(plan):
        if choice == 1:
            stops.append(optional_stops[idx])
    
    # Sort stops based on original order
    stops_ordered = [s for s in stations if s in stops]
    
    # Compute total travel time
    total_time = 0.0  # hours
    for i in range(len(stops_ordered) - 1):
        from_station = stops_ordered[i]
        to_station = stops_ordered[i+1]
        
        # Sum distances between from_station and to_station
        idx_from = stations.index(from_station)
        idx_to = stations.index(to_station)
        
        if idx_from > idx_to:
            idx_from, idx_to = idx_to, idx_from
        
        distance = sum([station_spacing[stations[j]] for j in range(idx_from+1, idx_to+1)])
        
        time_segment = distance / cruise_speed
        total_time += time_segment
    
    # Add dwell times (except Seoul, no dwell at start)
    total_dwell = dwell_time_per_stop * (len(stops_ordered) - 1) / 60  # minutes to hours
    total_time += total_dwell
    
    results.append({
        'stop_plan': stops_ordered,
        'total_time_hours': total_time,
        'total_time_min': total_time * 60  # convert to minutes
    })

# Sort results by travel time
results_sorted = sorted(results, key=lambda x: x['total_time_min'])

# Show best few
for r in results_sorted[:5]:
    print(f"Stops: {r['stop_plan']} | Total Time: {r['total_time_hours']:.2f} hours | {r['total_time_min']:.2f} minutes")
