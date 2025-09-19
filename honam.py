import pandas as pd
import itertools
import numpy as np
import matplotlib.pyplot as plt

# Load station data
hsr_location_data = pd.read_excel('datasets/HSR_Locations.xlsx')

# Define station list in Gyeongbu Line order
stations = ['Seoul', 'Gwangmyeong', 'Cheonan-Asan', 'Osong', 'Gongju', 
            'Iksan', 'Jeongeup', 'Gyeongju', 'Ulsan (Tongdosa)', 'Busan']

# Mandatory stops
mandatory_stops = {'Seoul', 'Daejeon', 'Dongdaegu', 'Busan'}

# Optional stops
optional_stops = [s for s in stations if s not in mandatory_stops]

# Mapping station name to spacing
station_spacing = dict(zip(hsr_location_data['Station'], hsr_location_data['Station Spacing (km)']))


# Speed and penalties assumptions
cruise_speed = 305  # km/h assumed outside slow zones
accel_decel_penalty_min = 5  # minutes per intermediate stop
slow_zone_penalty_per_city_min = 10  # minutes for slow passage through Daejeon and Dongdaegu

speed_limit = 110 
seoul_to_gwangmyeong_dist = station_spacing['Gwangmyeong']
seoul_slow = seoul_to_gwangmyeong_dist/speed_limit

# Function to get dwell time at each station
def get_dwell_time(station_name):
    if station_name in ['Daejeon', 'Dongdaegu']:
        return 5
    elif station_name in ['Seoul', 'Busan']:
        return 0
    else:
        return 2

# Enumerate all combinations of optional stops
all_stop_plans = list(itertools.product([0, 1], repeat=len(optional_stops)))

results = []
seen_stop_plans = set()

for plan in all_stop_plans:
    stops = list(mandatory_stops)
    for idx, choice in enumerate(plan):
        if choice == 1:
            stops.append(optional_stops[idx])
    stops_ordered = [s for s in stations if s in stops]
    stop_plan_tuple = tuple(stops_ordered)
    if stop_plan_tuple in seen_stop_plans:
        continue
    seen_stop_plans.add(stop_plan_tuple)

    total_time = 0.0  # hours
    for i in range(len(stops_ordered) - 1):
        from_station = stops_ordered[i]
        to_station = stops_ordered[i + 1]
        idx_from = stations.index(from_station)
        idx_to = stations.index(to_station)
        if idx_from > idx_to:
            idx_from, idx_to = idx_to, idx_from
        distance = sum([station_spacing[stations[j]] for j in range(idx_from + 1, idx_to + 1)])
        time_segment = distance / cruise_speed
        total_time += time_segment

    intermediate_stops = stops_ordered[1:-1]
    total_dwell_min = sum([get_dwell_time(station) for station in intermediate_stops])
    total_accel_decel_min = accel_decel_penalty_min * len(intermediate_stops)

    slow_zone_min = 0
    if 'Daejeon' in stops_ordered:
        slow_zone_min += slow_zone_penalty_per_city_min
    if 'Dongdaegu' in stops_ordered:
        slow_zone_min += slow_zone_penalty_per_city_min

    total_time += (total_dwell_min + total_accel_decel_min + slow_zone_min) / 60
    total_time += seoul_slow

    total_time_hours = int(total_time)
    total_time_minutes = int(round((total_time - total_time_hours) * 60))

    results.append({
        'stop_plan': stops_ordered,
        'total_time_hours': total_time,
        'total_time_min': total_time * 60,
        'formatted_time': f"{total_time_hours} hr {total_time_minutes} min"
    })

# Sort by total time
results_sorted = sorted(results, key=lambda x: x['total_time_min'])

# Export to CSV
df = pd.DataFrame(results_sorted)
df.to_csv('optimized_hsr_stop_plans.csv', index=False)
print("\nResults exported to 'optimized_hsr_stop_plans.csv'.")

# Add number_of_stops to each result
for r in results_sorted:
    r['number_of_stops'] = len(r['stop_plan']) - 2  # exclude Seoul and Busan

# Sort by number_of_stops then time
results_sorted = sorted(results_sorted, key=lambda x: (x['number_of_stops'], x['total_time_min']))

# Pareto optimal selection
pareto_optimal = []
best_time_so_far = float('inf')

for r in results_sorted:
    if r['total_time_min'] < best_time_so_far:
        pareto_optimal.append(r)
        best_time_so_far = r['total_time_min']

# Print Pareto optimal results
print("\nPareto Optimal Stop Plans:")
for r in pareto_optimal:
    print(f"Stops: {r['stop_plan']} | Stops: {r['number_of_stops']} | Total Time: {r['formatted_time']}")



# -------------- PLOT TRAJECTORIES ------------------

def get_cumulative_distances(stops_ordered, station_spacing, stations):
    distances = [0]
    for i in range(1, len(stops_ordered)):
        idx_from = stations.index(stops_ordered[i - 1])
        idx_to = stations.index(stops_ordered[i])
        if idx_from > idx_to:
            idx_from, idx_to = idx_to, idx_from
        distance = sum([station_spacing[stations[j]] for j in range(idx_from + 1, idx_to + 1)])
        distances.append(distances[-1] + distance)
    return distances

# Plot 3 fastest and 3 slowest
plans_to_plot = results_sorted[:3] + results_sorted[-3:]

plt.figure(figsize=(12, 6))

for r in plans_to_plot:
    stops_ordered = r['stop_plan']
    cumulative_distances = get_cumulative_distances(stops_ordered, station_spacing, stations)
    times = []
    current_time = seoul_slow * 60  # in minutes

    for i in range(len(stops_ordered)):
        if i > 0:
            idx_from = stations.index(stops_ordered[i - 1])
            idx_to = stations.index(stops_ordered[i])
            if idx_from > idx_to:
                idx_from, idx_to = idx_to, idx_from
            distance = sum([station_spacing[stations[j]] for j in range(idx_from + 1, idx_to + 1)])
            travel_time = distance / cruise_speed * 60  # minutes
            current_time += travel_time

        if 0 < i < len(stops_ordered) - 1:
            current_time += get_dwell_time(stops_ordered[i])
            current_time += accel_decel_penalty_min

        if stops_ordered[i] in ['Daejeon', 'Dongdaegu']:
            current_time += slow_zone_penalty_per_city_min

        times.append(current_time)

    label = f"{', '.join(stops_ordered)} ({r['formatted_time']})"
    plt.plot(times, cumulative_distances, marker='o', label=label)

plt.xlabel("Time (minutes)")
plt.ylabel("Distance from Seoul (km)")
plt.title("HSR Train Trajectories: Time vs Distance from Seoul")
plt.legend(loc='upper left', fontsize='small')
plt.grid(True)
plt.tight_layout()
plt.savefig('figures/KTX_Trajectories.png')
