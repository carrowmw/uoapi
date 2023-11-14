from api_requests import (
    sensor_types_api,
    themes_api,
    variables_api,
)
from data_processing.json_to_dataframe import json_to_dataframe


def execute_sensor_type_request():
    # Sensor Types (also called Variables?!)
    PARAMS = {"theme": "People"}
    sensor_types_dict = sensor_types_api.request(PARAMS)
    print(sensor_types_dict)
    sensor_types_df = json_to_dataframe(sensor_types_dict["Variables"])
    print("Sensor Types Request Sucessful...")
    print(f"    Length of Sensor Types: {len(sensor_types_df)}")


def execute_variables_request():
    # Variables
    PARAMS = {"theme": "People"}
    variables_json = variables_api.request(PARAMS)
    variables_df = json_to_dataframe(variables_json["Variables"])
    print("Variables Request Sucessful...")
    print(f"    Length of Variables DataFrame: {len(variables_df)}")


def execute_htemes_request():
    # Themes
    PARAMS = None
    themes_dict = themes_api.request(PARAMS)
    themes_df = json_to_dataframe(themes_dict["Themes"])
    print("Themes Request Sucessful...")
    print(f"    Length of Themes DataFrame: {len(themes_df)}")
    return themes_df
