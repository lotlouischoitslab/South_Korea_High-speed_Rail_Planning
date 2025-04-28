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

# Mapping station name to spacing
station_spacing = dict(zip(hsr_location_data['Station'], hsr_location_data['Station Spacing (km)']))

# Speed and dwell time assumptions
cruise_speed = 300  # km/h
dwell_time_per_stop = 5  # minutes
accel_decel_penalty_min = 5  # minutes per stop (acceleration and deceleration time)

# Function to get speed limit per segment
def get_speed_limit(from_station, to_station):
    if (from_station == 'Seoul' and to_station == 'Gwangmyeong') or (from_station == 'Gwangmyeong' and to_station == 'Seoul'):
        return 100  # km/h
    else:
        return cruise_speed  # km/h

# Enumerate all combinations
all_stop_plans = list(itertools.product([0, 1], repeat=len(optional_stops)))

results = []

for plan in all_stop_plans:
    stops = list(mandatory_stops)  # always include mandatory
    for idx, choice in enumerate(plan):
        if choice == 1:
            stops.append(optional_stops[idx])
    
    stops_ordered = [s for s in stations if s in stops]
    
    total_time = 0.0  # hours
    for i in range(len(stops_ordered) - 1):
        from_station = stops_ordered[i]
        to_station = stops_ordered[i+1]
        
        idx_from = stations.index(from_station)
        idx_to = stations.index(to_station)
        
        if idx_from > idx_to:
            idx_from, idx_to = idx_to, idx_from
        
        distance = sum([station_spacing[stations[j]] for j in range(idx_from+1, idx_to+1)])
        
        speed = get_speed_limit(from_station, to_station)
        
        time_segment = distance / speed
        total_time += time_segment
    
    # Add dwell times (except first station)
    total_dwell_min = dwell_time_per_stop * (len(stops_ordered) - 1)
    # Add acceleration/deceleration penalties (except first station)
    total_accel_decel_min = accel_decel_penalty_min * (len(stops_ordered) - 1)
    
    total_time += (total_dwell_min + total_accel_decel_min) / 60  # convert minutes to hours
    
    total_time_hours = int(total_time)
    total_time_minutes = int(round((total_time - total_time_hours) * 60))
    
    results.append({
        'stop_plan': stops_ordered,
        'total_time_hours': total_time,
        'total_time_min': total_time * 60,
        'formatted_time': f"{total_time_hours} hr {total_time_minutes} min"
    })

# Sort by travel time
results_sorted = sorted(results, key=lambda x: x['total_time_min'])

# Show best few
for r in results_sorted:
    print(f"Stops: {r['stop_plan']} | Total Time: {r['formatted_time']}")
