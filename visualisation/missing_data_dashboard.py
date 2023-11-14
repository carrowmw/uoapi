"""
Builds the dashboard for the missing data dashboard.
"""

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px


def create_dashboard(dataframes):
    # Create a Dash web app
    app = dash.Dash(__name__)

    # Layout of the web app
    app.layout = html.Div(
        children=[
            # Dropdown for selecting DataFrame
            dcc.Dropdown(
                id="dataframe-dropdown",
                options=[
                    {"label": f"DataFrame {i}", "value": i}
                    for i in range(len(dataframes))
                ],
                value=0,  # Default to the first DataFrame
                style={"width": "50%"},
            ),
            # Graph to display the selected DataFrame
            dcc.Graph(id="daily-counts-graph"),
        ]
    )

    # Callback to update the graph based on the selected DataFrame
    @app.callback(
        Output("daily-counts-graph", "figure"), [Input("dataframe-dropdown", "value")]
    )
    def update_graph(selected_dataframe):
        df = dataframes[selected_dataframe][1]
        sensor_name = dataframes[selected_dataframe][0]
        # Create a bar chart using Plotly Express
        fig = px.bar(
            df,
            x="Timestamp",
            y="Count",
            title=sensor_name,
            labels={"Count": "Total Records", "Timestamp": "Date"},
        )

        return fig

    return app
