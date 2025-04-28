import pandas as pd
import itertools
import numpy as np

# Load station data
hsr_location_data = pd.read_excel('datasets/HSR_Locations.xlsx')

# Define station list in Gyeongbu Line order
stations = ['Seoul', 'Gwangmyeong', 'Cheonan-Asan', 'Osong', 'Daejeon', 
            'Gimcheon-Gumi', 'Dongdaegu', 'Gyeongju', 'Ulsan (Tongdosa)', 'Busan']

# Mandatory stops
mandatory_stops = {'Seoul', 'Daejeon', 'Dongdaegu', 'Busan'}

# Optional stops
optional_stops = [s for s in stations if s not in mandatory_stops]

# Mapping station name to spacing
station_spacing = dict(zip(hsr_location_data['Station'], hsr_location_data['Station Spacing (km)']))

# Speed and penalties assumptions
cruise_speed = 300  # km/h assumed outside slow zones
accel_decel_penalty_min = 5  # minutes per intermediate stop
slow_zone_penalty_per_city_min = 10  # minutes for slow passage through Daejeon and Dongdaegu

speed_limit = 110 
seoul_to_gwangmyeong_dist = station_spacing['Gwangmyeong']
seoul_slow = seoul_to_gwangmyeong_dist/speed_limit



# Function to get dwell time at each station
def get_dwell_time(station_name):
    if station_name in ['Daejeon', 'Dongdaegu']:
        return 5  # 5 minutes for major transfer stations
    elif station_name in ['Seoul', 'Busan']:
        return 0  # No dwell at origin and destination
    else:
        return 2  # 2 minutes at minor optional stops

# Enumerate all combinations of optional stops
all_stop_plans = list(itertools.product([0, 1], repeat=len(optional_stops)))

results = []
seen_stop_plans = set()  # track seen plans to avoid duplicates

for plan in all_stop_plans:
    # Build stop list
    stops = list(mandatory_stops)
    for idx, choice in enumerate(plan):
        if choice == 1:
            stops.append(optional_stops[idx])

    # Sort stops according to station order
    stops_ordered = [s for s in stations if s in stops]

  

    # Check for duplicate stop plans
    stop_plan_tuple = tuple(stops_ordered)
    if stop_plan_tuple in seen_stop_plans:
        continue  # skip if already processed
    seen_stop_plans.add(stop_plan_tuple)

    # Compute total moving time
    total_time = 0.0  # hours
    for i in range(len(stops_ordered) - 1):
        from_station = stops_ordered[i]
        to_station = stops_ordered[i + 1]

        idx_from = stations.index(from_station)
        idx_to = stations.index(to_station)

        if idx_from > idx_to:
            idx_from, idx_to = idx_to, idx_from

        distance = sum([station_spacing[stations[j]] for j in range(idx_from + 1, idx_to + 1)])
        speed = cruise_speed

        time_segment = distance / speed  # time = distance / speed
        total_time += time_segment

    # Add dwell times (for intermediate stops only)
    intermediate_stops = stops_ordered[1:-1]
    total_dwell_min = sum([get_dwell_time(station) for station in intermediate_stops])

    # Add acceleration/deceleration penalties at intermediate stops
    total_accel_decel_min = accel_decel_penalty_min * len(intermediate_stops)

    # Add slow zone penalties if passing Daejeon or Dongdaegu
    slow_zone_min = 0
    if 'Daejeon' in stops_ordered:
        slow_zone_min += slow_zone_penalty_per_city_min
    if 'Dongdaegu' in stops_ordered:
        slow_zone_min += slow_zone_penalty_per_city_min

    # Update total time
    total_time += (total_dwell_min + total_accel_decel_min + slow_zone_min) / 60  # convert minutes to hours
    total_time += seoul_slow

    # Format time nicely
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

# Print results
for r in results_sorted:
    print(f"Stops: {r['stop_plan']} | Total Time: {r['formatted_time']}")

# Export to CSV
df = pd.DataFrame(results_sorted)
df.to_csv('optimized_hsr_stop_plans.csv', index=False)
print("\nResults exported to 'optimized_hsr_stop_plans.csv'.")
