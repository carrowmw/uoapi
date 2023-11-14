import dash
import plotly.express as px
from dash import dcc, html
from dash.dependencies import Input, Output, State


def create_dashboard(dataframes, last_n_days):
    # Extract sensor names from dataframes
    sensor_names = [df[0] for df in dataframes]

    # Create a Dash web app
    app = dash.Dash(__name__)

    # Layout of the web app
    app.layout = html.Div(
        children=[
            # Container for the search bar
            html.Div(
                children=[
                    # Dropdown for selecting DataFrame
                    dcc.Dropdown(
                        id="dataframe-dropdown",
                        options=[
                            {"label": name, "value": name} for name in sensor_names
                        ],
                        value=sensor_names[0],  # Default to the first sensor
                        placeholder="Click to search",  # Set placeholder text
                        style={
                            "width": "60%",  # Adjust the width as needed
                            "margin": "auto",  # Center the dropdown bar
                            "padding": "10px",  # Increase padding to 10px
                            "fontSize": "18px",  # Set font size to 18px
                            "fontFamily": "Arial, sans-serif",  # Set font family
                        },
                    ),
                    dcc.Interval(
                        id="interval-component",
                        interval=1000,  # in milliseconds
                        n_intervals=0,
                    ),
                ],
                style={
                    "backgroundColor": "#f8f9fa",  # Set background color
                    "textAlign": "center",  # Center the content
                    "marginBottom": "20px",  # Add margin at the bottom
                },
            ),
            # Container for the list of graphs
            html.Div(
                id="graphs-container",
                style={
                    "maxWidth": "2400",
                    "margin": "auto",
                    "textAlign": "center",
                },  # Center the content
            ),
        ]
    )

    # Callback to update the graph based on the selected DataFrame
    @app.callback(
        Output("graphs-container", "children"),
        [Input("dataframe-dropdown", "value")],
    )
    def update_graph(selected_sensor):
        try:
            # Check if selected_sensor is not in the expected range
            if selected_sensor not in sensor_names:
                raise ValueError(f"Invalid selected_sensor value: {selected_sensor}")

            selected_index = sensor_names.index(selected_sensor)

            # Create a list of html.Div elements for each graph
            graph_divs = [
                html.Div(
                    children=[
                        dcc.Graph(
                            id=f"graph-{i}",
                            figure=px.bar(
                                dataframes[i][1],
                                x="Timestamp",
                                y="Count",
                                title=(
                                    f"{dataframes[i][0]}   |   "
                                    f"{len(dataframes[selected_index][1])/(last_n_days*96)}% Complete"
                                ),
                                labels={"Count": "Total Records", "Timestamp": "Date"},
                            ).update_layout(
                                title={
                                    "text": dataframes[i][0],
                                    "font": {"size": 36},
                                    "x": 0.5,  # Center the title horizontally
                                }  # Set font size
                            ),
                            style={"width": "100%"},  # Make each graph 100% width
                        ),
                    ],
                    id=f"section-{i}",
                    style={
                        "padding": "20px",
                        "border": "1px solid #ddd",
                        "height": "500px",
                        "width": "100%",  # Make each graph 100% width
                    },
                )
                for i in range(len(dataframes))
            ]

            return graph_divs
        except Exception as e:
            print(f"Error updating graphs-container.children: {str(e)}")
            return []

    print("\n \n    Web-app succressfully initialised...")
    return app
