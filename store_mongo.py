import pymongo
import paho.mqtt.client as mqtt
from datetime import datetime, timezone

# MongoDB configuration
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["TirAir"]
collection = db["sensor_data"]

# MQTT configuration
mqtt_broker_address = "34.29.205.132" 
mqtt_topic = "cpc357"

# Define the callback function for connection
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Successfully connected")
        client.subscribe(mqtt_topic)
    else:
        print("Connection failed with code:", reason_code)

# Define the callback function for ingesting data into MongoDB
def on_message(client, userdata, message):
    payload = message.payload.decode("utf-8")
    print(f"Received message: {payload}")
    
    # Parse the message
    data = {}
    parts = payload.split(", ")
    for part in parts:
        key, value = part.split(": ")
        data[key.lower()] = value
    
    # Convert MQTT timestamp to datetime
    timestamp = datetime.now(timezone.utc)
    datetime_obj = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    
    # Process the payload and insert into MongoDB with proper timestamp
    document = {
        "timestamp": datetime_obj,
        "temperature": float(data["temperature"].split(" ")[0]),
        "humidity": float(data["humidity"].split(" ")[0]),
        "raining": data["raining"],
        "valve": data["valve"]
    }
    
    collection.insert_one(document)
    print("Data inserted into MongoDB")

# Initialize MQTT client and set callback functions
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
client.connect(mqtt_broker_address, 1883, 60)

# Start the MQTT client loop
client.loop_forever()
