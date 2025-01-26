import pymongo
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import pickle

# MongoDB configuration
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["TirAir"]
collection = db["sensor_data"]

# Fetch data from MongoDB
def fetch_data():
    data = list(collection.find())
    for doc in data:
        doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
    return data

# Train the model using MongoDB data
def train_model():
    data = fetch_data()
    df = pd.DataFrame(data)
    
    # Ensure data is properly formatted
    df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['valve_open'] = df['valve'].apply(lambda x: 1 if x == "Open" else 0)
    
    # Prepare features and target
    df['time_diff'] = df['timestamp'].diff().dt.total_seconds() / 3600  # Time difference in hours
    df['time_diff'] = df['time_diff'].fillna(0)
    
    X = df[['temperature']]
    y = df['time_diff']
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train model
    model = LinearRegression()
    model.fit(X_scaled, y)
    
    # Save the model and scaler to files
    with open('sprinkler_model.pkl', 'wb') as model_file:
        pickle.dump(model, model_file)
    with open('scaler.pkl', 'wb') as scaler_file:
        pickle.dump(scaler, scaler_file)

    print("Model and scaler saved successfully")

if __name__ == '__main__':
    train_model()
