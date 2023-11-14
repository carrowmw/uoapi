"""
This script orchestrates the API requests and data processing
"""


from utils.polygon_utils import create_wkb_polygon

from api_requests import sensors_api
from data_processing.json_to_dataframe import json_to_dataframe
from data_processing.process_sensor_data import (
    get_all_sensors_data_parallel,
    print_sensor_request_metrics,
)
from data_processing.process_missing_data import (
    save_daily_counts_dataframes,
    get_daily_counts_dataframes,
)
from visualisation.missing_data_dashboard import create_dashboard

# Bounding box
MIN_LON = -1.6226
MIN_LAT = 54.9719
MAX_LON = -1.6058
MAX_LAT = 54.9808
bbox = create_wkb_polygon(MIN_LON, MIN_LAT, MAX_LON, MAX_LAT)

# Sensors
PARAMS = {"theme": "People", "polygon_wkb": bbox}
sensors_json = sensors_api.request(PARAMS)
sensors_df = json_to_dataframe(sensors_json["sensors"])
print(f"Length of Sensors: {len(sensors_df)}")

# Data
LAST_N_DAYS = 20
params = {"last_n_days": LAST_N_DAYS}
series_of_sensor_names = sensors_df["Sensor Name"]
list_of_dataframes = get_all_sensors_data_parallel(series_of_sensor_names, params)
print_sensor_request_metrics(list_of_dataframes, series_of_sensor_names)


list_of_daily_count_data_frames = get_daily_counts_dataframes(list_of_dataframes)

dashboard_app = create_dashboard(
    list_of_daily_count_data_frames,
    last_n_days=LAST_N_DAYS,
)

# Run the web app
if __name__ == "__main__":
    dashboard_app.run_server(debug=True)
