#include <ESP32Servo.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include "DHT.h"

#define DHTTYPE DHT11
#define DHTPIN 7       // Pin for the DHT11 sensor
#define RELAY_PIN 16   // Pin that connects the water valve via the relay
#define RAIN_SENSOR_PIN 41  // Pin for the rain sensor
#define SERVO_PIN 9         // Pin for controlling the servo
#define TEMP_THRESHOLD 25.0  // Temperature threshold (in Celsius)

const char* WIFI_SSID = "sarah";           
const char* WIFI_PASSWORD = "abc12345";  
const char* MQTT_SERVER = "34.29.205.132";
const char* MQTT_TOPIC = "cpc357";            // MQTT topic for sensor data
const char* CONTROL_TOPIC = "cpc357/control"; // MQTT topic for control commands
const int MQTT_PORT = 1883;                   // Non-TLS communication port

char buffer[256] = "";
unsigned long rain_start_time = 0; // To track rain duration
const unsigned long rain_duration_threshold = 5000; // Duration threshold for rain (5 seconds)
bool valveOpened = false;  // To track the valve state
bool manualControl = false; // To indicate if manual control is active

WiFiClient espClient;
PubSubClient client(espClient);
DHT dht(DHTPIN, DHTTYPE);
Servo tap_servo;

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  Serial.println(message);

  // Handle control commands
  if (String(topic) == CONTROL_TOPIC) {
    if (message == "open_lid") {
      Serial.println("Opening lid...");
      tap_servo.write(180); // Open the lid
      manualControl = true;

    } else if (message == "close_lid") {
      Serial.println("Closing lid...");
      tap_servo.write(0); // Close the lid
      manualControl = true;
      
    } else if (message == "open_sprinklers") {
      Serial.println("Opening sprinklers...");
      digitalWrite(RELAY_PIN, HIGH); // Open sprinklers
      valveOpened = true;

    } else if (message == "close_sprinklers") {
      Serial.println("Closing sprinklers...");
      digitalWrite(RELAY_PIN, LOW); // Close sprinklers
      valveOpened = false;
    }
  }
}

// Initialize components
void setup() {
  
  pinMode(RELAY_PIN, OUTPUT);      // Relay pin as output
  pinMode(RAIN_SENSOR_PIN, INPUT); // Rain sensor as input
  tap_servo.attach(SERVO_PIN);     // Attach the servo
  dht.begin();                     // Initialize the DHT11 sensor
  Serial.begin(115200);            // Initialize Serial communication for logging

  setup_wifi(); // Connect to the WiFi network
  client.setServer(MQTT_SERVER, MQTT_PORT); // Set up the MQTT client
  client.setCallback(callback); // Set MQTT callback function

  // Ensure initial states
  digitalWrite(RELAY_PIN, LOW); // Ensure solenoid valve is closed initially
  tap_servo.write(0);           // Ensure servo is in the initial position

  Serial.println("System initialized. Waiting for sensor data...");
}

void loop() {
  if(!client.connected()) {
    reconnect();
  }
  client.loop();
  
  delay(2000); // Delay 2 seconds before reading again

  // Read temperature from DHT11 sensor
  float t = dht.readTemperature();

  // Check if reading was successful
  if (isnan(t)) {
    Serial.println("Failed to read temperature from DHT sensor!");
    return;
  }

  // Read rain sensor
  int rain_sensor_value = digitalRead(RAIN_SENSOR_PIN);
  bool isRaining = false;

  // If rain is detected and not in manual control, start the timer for rain duration
  if (rain_sensor_value == LOW && !manualControl) { // Assuming LOW means rain detected
    if (rain_start_time == 0) {
      rain_start_time = millis(); // Start the rain duration timer
    }

    // If rain duration exceeds the threshold, move the servo 180 degrees
    if (millis() - rain_start_time > rain_duration_threshold) {
      tap_servo.write(180); // Move servo to simulate tap being open
      Serial.println("Rain detected. Servo moved.");
      isRaining = true;
    }

    // No rain detected and not in manual control
  } else if (!manualControl) { 
    rain_start_time = 0;  // Reset rain timer
    tap_servo.write(0);   // Move the servo back to the initial position
    Serial.println("Rain not detected. Servo reset.");
  }

  // Print the current temperature to the Serial Monitor for logging
  Serial.print("Temperature: ");
  Serial.print(t);
  Serial.println(" °C");

  // Control the solenoid valve based on the temperature threshold
  if (t >= TEMP_THRESHOLD) {
    // Open the valve (relay ON)
    digitalWrite(RELAY_PIN, HIGH);
    Serial.println("Valve Opened - Temperature above threshold");
    valveOpened = true;

  } else {
    // Close the valve (relay OFF)
    digitalWrite(RELAY_PIN, LOW);
    Serial.println("Valve Closed - Temperature below threshold");
    valveOpened = false;
  }

  // Publish temperature, humidity, and rain and valve status data to MQTT
  float h = dht.readHumidity(); // Read humidity
  if (isnan(h)) {
    Serial.println("Failed to read humidity from DHT sensor!");
    return;
  }
  
  sprintf(buffer, "Temperature: %.2f degree Celsius, Humidity: %.2f %%, Raining: %s, Valve: %s", t, h, isRaining ? "Yes" : "No", valveOpened ? "Opened" : "Closed");
  client.publish(MQTT_TOPIC, buffer);
  Serial.println(buffer);

  // Reset manual control if no command received for 10 seconds
  static unsigned long lastManualControlTime = 0;
  if (millis() - lastManualControlTime > 10000) {
    manualControl = false;
    lastManualControlTime = millis();
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.println("Attempting MQTT connection...");
    String clientId = "ESP32Client-" + String(random(0xffff), HEX);
    if(client.connect(clientId.c_str())) {
      Serial.println("Connected to MQTT server");
      client.subscribe(CONTROL_TOPIC); // Subscribe to control commands
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(" Retrying in 5 seconds...");
      delay(5000);
    }
  }
}
