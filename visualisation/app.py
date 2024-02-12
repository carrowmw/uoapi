import dash
import plotly.express as px
from dash import dcc, html
from dash.dependencies import Input, Output
from datetime import datetime, timedelta


def create_dashboard(dataframes, last_n_days):
    # Create a Dash web app
    app = dash.Dash(__name__)

    # Layout of the web app
    app.layout = html.Div(
        children=[
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
        [Input("graphs-container", "id")],  # Use any input to trigger the callback
    )
    def update_graph(_):
        try:
            # Create a list of html.Div elements for each graph
            graph_divs = []
            for i, _ in enumerate(dataframes):
                df = dataframes[i][1]
                sensor_name = dataframes[i][0]

                # Set x-axis and y-axis limits
                today = datetime.now()
                x_max = today.strftime("%Y-%m-%d")
                x_min = (today - timedelta(days=last_n_days)).strftime("%Y-%m-%d")
                y_max = 96
                y_min = 0

                graph_divs.append(
                    html.Div(
                        children=[
                            dcc.Graph(
                                id=f"graph-{i}",
                                figure=px.bar(
                                    df,
                                    x="Timestamp",
                                    y="Count",
                                    title=(
                                        f"{sensor_name}   |   "
                                        f"{len(df)/(last_n_days*96)}% Complete"
                                    ),
                                    labels={
                                        "Count": "Total Records",
                                        "Timestamp": "Date",
                                    },
                                ).update_layout(
                                    title={
                                        "text": sensor_name,
                                        "font": {"size": 36},
                                        "x": 0.5,  # Center the title horizontally
                                    },
                                    xaxis=dict(
                                        range=[x_min, x_max],
                                        title="Date",
                                    ),
                                    yaxis=dict(
                                        range=[y_min, y_max],
                                        title="Count",
                                    ),
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
                )

            return graph_divs
        except Exception as e:
            print(f"Error updating graphs-container.children: {str(e)}")
            return []

    print("\n \n    Web-app successfully initialized...")
    return app
