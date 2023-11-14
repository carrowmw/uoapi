"""
Calculates the amount of missing data each day.
"""

import pandas


def get_daily_counts_dataframes(list_of_dataframes):
    """
    Get daily counts dataframes.

    Parameters:
    - list_of_dataframes (list): A list of tuples containing DataFrame name and DataFrame.

    Returns:
    list: A list of daily counts DataFrames.

    For each DataFrame in the list, this function calculates daily counts based on the 'Timestamp'
    column, creates a new DataFrame with 'Timestamp' and 'Count' columns, and appends it to a list.

    Example:
    get_daily_counts_dataframes([('Sensor1', df1), ('Sensor2', df2)])
    """
    daily_counts_list = []
    for df in list_of_dataframes:
        name, df = df[0], df[1]
        # Group by the date part of the timestamp and count the rows
        daily_counts = (
            df.groupby(df["Timestamp"].dt.date).size().reset_index(name="Count")
        )
        daily_counts_list.append((name, daily_counts))

    return daily_counts_list


def save_daily_counts_dataframes(list_of_dataframes):
    """
    Save daily counts dataframes to CSV files.

    Parameters:
    - list_of_dataframes (list): A list of tuples containing DataFrame name and DataFrame.

    Returns:
    None

    For each DataFrame in the list, this function calculates daily counts based on the 'Timestamp'
    column, creates a new DataFrame with 'Timestamp' and 'Count' columns, and saves it to a CSV file
    in the 'daily_counts' directory.

    Example:
    save_daily_counts_dataframes([('Sensor1', df1), ('Sensor2', df2)])
    """
    for df in list_of_dataframes:
        name, df = df[0], df[1]
        # Group by the date part of the timestamp and count the rows
        daily_counts = (
            df.groupby(df["Timestamp"].dt.date).size().reset_index(name="Count")
        )
        daily_counts.to_csv(f".\\data\\daily_counts\\{name}.csv")
    print("All daily counts saved in .\\data\\daily_counts")
