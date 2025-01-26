import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import pymongo
import paho.mqtt.client as mqtt
from datetime import datetime, timezone
import threading
import pickle

# Load ML Model
with open('sprinkler_model.pkl', 'rb') as model_file:
    model = pickle.load(model_file)
with open('scaler.pkl', 'rb') as scaler_file:
    scaler = pickle.load(scaler_file)

# MongoDB Configuration
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["TirAir"]
collection = db["sensor_data"]

# MQTT Configuration
mqtt_broker_address = "34.29.205.132"
control_topic = "cpc357/control"

# Create MQTT client for controls
client = mqtt.Client()
client.connect(mqtt_broker_address, 1883, 60)

# Dash App Configuration
app = dash.Dash(__name__)

# Dashboard layout
app.layout = html.Div([
    html.H1(
        "TirAir",
        style={
            "textAlign": "center", 
            "marginBottom": "20px", 
            "fontFamily": "Arial, sans-serif",
            "color": "white"
        }
    ),

    # ========== Top Section ==========
    html.Div([
        # Temperature vs. Humidity Chart
        html.Div([
            html.H3("Temperature vs. Humidity Over Time", 
                   style={
                       "textAlign": "center", 
                       "margin": "10px",
                       "fontFamily": "Arial, sans-serif",
                       "color": "#000000"
                   }),
            dcc.Graph(id="live-graph")
        ], style={
            "width": "75%",
            "height": "500px",
            "border": "1px solid black",
            "margin": "10px",
            "boxSizing": "border-box",
            "backgroundColor": "#E7FAFF",
            "borderRadius": "5px"
        }),

        # Current Temperature & Humidity
        html.Div([
            html.Div([
                html.H3("Current Outside Temperature", 
                       style={
                           "textAlign": "center", 
                           "margin": "10px",
                           "fontFamily": "Arial, sans-serif",
                           "color": "#000000"
                       }),
                html.P(id="current-temp", 
                      style={
                          "textAlign": "center", 
                          "fontSize": "24px", 
                          "margin": "10px",
                          "fontFamily": "Arial, sans-serif"
                      })
            ], style={
                "border": "1px solid black",
                "margin-bottom": "20px",
                "padding": "10px",
                "textAlign": "center",
                "flex": "1",
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "center",
                "alignItems": "center",
                "backgroundColor": "#E7FAFF",
                "borderRadius": "5px"
            }),

            html.Div([
                html.H3("Current Outside Humidity", 
                       style={
                           "textAlign": "center", 
                           "margin": "10px",
                           "fontFamily": "Arial, sans-serif",
                           "color": "#000000"
                       }),
                html.P(id="current-humidity", 
                      style={
                          "textAlign": "center", 
                          "fontSize": "24px", 
                          "margin": "10px",
                          "fontFamily": "Arial, sans-serif"
                      })
            ], style={
                "border": "1px solid black",
                "padding": "10px",
                "textAlign": "center",
                "flex": "1",
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "center",
                "alignItems": "center",
                "backgroundColor": "#E7FAFF",
                "borderRadius": "5px"
            })
        ], style={
            "width": "25%",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-between",
            "boxSizing": "border-box",
            "height": "500px",
            "margin": "10px"
        })
    ], style={
        "display": "flex",
        "justifyContent": "space-between",
        "alignItems": "stretch"
    }),

    # ========== Bottom Section ==========
    html.Div([
        # Controls Section
        html.Div([
            html.Div([
                html.H3("Sprinklers", 
                       style={
                           "textAlign": "center",
                           "fontFamily": "Arial, sans-serif",
                           "color": "#000000"
                       }),
                html.Button(
                    "ON", 
                    id="btn-open-sprinklers",
                    style={
                        "backgroundColor": "green", 
                        "color": "white", 
                        "margin": "5px",
                        "fontFamily": "Arial, sans-serif"
                    }
                ),
                html.Button(
                    "OFF",
                    id="btn-close-sprinklers",
                    style={
                        "backgroundColor": "red", 
                        "color": "white", 
                        "margin": "5px",
                        "fontFamily": "Arial, sans-serif"
                    }
                )
            ], style={
                "border": "1px solid black",
                "margin": "10px",
                "padding": "10px",
                "textAlign": "center",
                "backgroundColor": "#E7FAFF",
                "borderRadius": "5px"
            }),

            html.Div([
                html.H3("Water Tank", 
                       style={
                           "textAlign": "center",
                           "fontFamily": "Arial, sans-serif",
                           "color": "#000000"
                       }),
                html.Button(
                    "ON",
                    id="btn-open-lid",
                    style={
                        "backgroundColor": "green", 
                        "color": "white", 
                        "margin": "5px",
                        "fontFamily": "Arial, sans-serif"
                    }
                ),
                html.Button(
                    "OFF",
                    id="btn-close-lid",
                    style={
                        "backgroundColor": "red", 
                        "color": "white", 
                        "margin": "5px",
                        "fontFamily": "Arial, sans-serif"
                    }
                )
            ], style={
                "border": "1px solid black",
                "margin": "10px",
                "padding": "10px",
                "textAlign": "center",
                "backgroundColor": "#E7FAFF",
                "borderRadius": "5px"
            })
        ], style={"width": "30%", "display": "inline-block", "verticalAlign": "top"}),

        # Currently Raining Card
        html.Div([
            html.Div(id="rain-status-container", children=[
                html.H3(id="rain-status-text", 
                       style={
                           "textAlign": "center", 
                           "margin": "10px",
                           "fontFamily": "Arial, sans-serif",
                           "color": "#000000"
                       }),
                html.Div(id="rain-status-icon", 
                        style={
                            "fontSize": "50px", 
                            "textAlign": "center",
                            "fontFamily": "Arial, sans-serif"
                        })
            ])
        ], style={
            "border": "1px solid black",
            "margin": "10px",
            "padding": "20px",
            "width": "30%",
            "display": "inline-block",
            "backgroundColor": "#E7FAFF",
            "borderRadius": "5px"
        }),

        # Next Sprinkler Activation
        html.Div([
            html.H3("Next Sprinkler Activation", 
                   style={
                       "textAlign": "center",
                       "fontFamily": "Arial, sans-serif",
                       "color": "#000000"
                   }),
            html.P(id="next-sprinkler-prediction", 
                  style={
                      "fontSize": "24px", 
                      "textAlign": "center",
                      "fontFamily": "Arial, sans-serif"
                  }),
        ], style={
            "border": "1px solid black",
            "margin": "10px",
            "padding": "20px",
            "width": "30%",
            "display": "inline-block",
            "backgroundColor": "#E7FAFF",
            "borderRadius": "5px"
        })
    ], style={"display": "flex", "justifyContent": "space-between"}),

    # Add interval component for updates
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # Update every minute
        n_intervals=0
    )
], style={
    "backgroundColor": "#062472",
    "padding": "20px",
    "minHeight": "100vh"
})

# Fetch data from MongoDB
def fetch_data():
    data = list(collection.find())
    for doc in data:
        doc['_id'] = str(doc['_id'])
    return data

# Callback to update all components
@app.callback(
    [
        Output("live-graph", "figure"),
        Output("current-temp", "children"),
        Output("current-humidity", "children"),
        Output("rain-status-text", "children"),
        Output("rain-status-icon", "children"),
        Output("next-sprinkler-prediction", "children")
    ],
    [
        Input("interval-component", "n_intervals"),
        Input("btn-open-sprinklers", "n_clicks"),
        Input("btn-close-sprinklers", "n_clicks"),
        Input("btn-open-lid", "n_clicks"),
        Input("btn-close-lid", "n_clicks")
    ]
)
def update_dashboard(n, open_sprinklers, close_sprinklers, open_lid, close_lid):
    # Fetch data from MongoDB
    data = fetch_data()
    df = pd.DataFrame(data)

    # Create the temperature and humidity chart
    fig = px.line(df, x='timestamp', y=['temperature', 'humidity'], 
                 title='Temperature & Humidity Over Time')
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Value",
        legend_title="Metrics",
        plot_bgcolor="#E7FAFF",
        paper_bgcolor="#E7FAFF"
    )

    # Get the latest data
    latest_data = df.iloc[-1]
    current_temp = f"{latest_data['temperature']} °C"
    current_humidity = f"{latest_data['humidity']} %"
    
    # Set rain status with text and icon
    if latest_data['raining']:
        rain_status_text = "Currently Raining"
        rain_status_icon = "☔"
    else:
        rain_status_text = "No Rain Detected"
        rain_status_icon = "☀️"

    # Handle button clicks for controls
    ctx = dash.callback_context
    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'btn-open-sprinklers':
            client.publish(control_topic, "open_sprinklers")
        elif button_id == 'btn-close-sprinklers':
            client.publish(control_topic, "close_sprinklers")
        elif button_id == 'btn-open-lid':
            client.publish(control_topic, "open_lid")
        elif button_id == 'btn-close-lid':
            client.publish(control_topic, "close_lid")

    # Make ML prediction
    temperature = latest_data['temperature']
    input_data = pd.DataFrame([[temperature]], columns=['temperature'])
    input_data_scaled = scaler.transform(input_data)
    prediction = model.predict(input_data_scaled)
    next_activation = f"In {max(prediction[0], 0):.2f} hours"

    return fig, current_temp, current_humidity, rain_status_text, rain_status_icon, next_activation

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)
