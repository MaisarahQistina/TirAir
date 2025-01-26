# TirAir
An IoT-Based Rainwater Harvesting and Roof Cooling System using ESP32.

TirAir is designed to efficiently utilize rainwater for cooling zinc roofs of houses during hot weather to regulate the house temperature. The system integrates various sensors and actuators to trigger the cooling process based on predefined conditions. Additionally, a dashboard is implemented to display the collected data and allow users to manage the system's actions.

**Note:** Refer to Report.pdf for the hardware setup guide

## Installation Steps

Below are the steps to run the dashboard:

i)	Start the VM instance to open up the SSH-in-browser.

ii)	Make sure all needed libraries are installed.
    
    $ pip3 install dash plotly pandas pymongo paho-mqtt scikit-learn

iii) Create or upload the python scripts to the current directory: store_mongo.py, train_model.py, dashboard.py.

iv)	Upload and run the Arduino code: sensor_reading.ino.

v)	Start data ingestion to allow data from sensor readings to store into MongoDB.
    
    $ python3 store_mongo.py
 
iv)	Train the machine learning model after gathering data in MongoDB.

    $ python3 train_model.py
    
v)	Start the dashboard and keep data running inMongoDB.

    $ python3 dashboard.py

