import streamlit as st
import pyrebase
import time
import plotly.graph_objects as go
import plotly.express as px
from collections import deque

# Set page configuration
st.set_page_config(page_title="Real-time Traffic Monitoring System", layout="wide")

# Firebase configuration
config = {
    "apiKey": "AIzaSyCUZ6SqIPcPuWXgf0gx9PkM6nXtnEtEIKg",
    "authDomain": "traffic-system-database-2f687.firebaseapp.com",
    "databaseURL": "https://traffic-system-database-2f687-default-rtdb.firebaseio.com/",
    "projectId": "traffic-system-database-2f687",
    "storageBucket": "traffic-system-database-2f687.appspot.com",
}

# Initialize Firebase
try:
    firebase = pyrebase.initialize_app(config)
    db = firebase.database()
    st.sidebar.success("Connected to Firebase successfully.")
except Exception as e:
    st.sidebar.error(f"Failed to connect to Firebase: {str(e)}")

# Function to fetch data from Firebase
def get_realtime_data():
    try:
        # Fetch traffic light data
        traffic_light_data = db.child("trafficLight").get().val()
        if traffic_light_data:
            light = traffic_light_data.get("light", "N/A")
            countdown = traffic_light_data.get("countdown", "N/A")
        else:
            light = "N/A"
            countdown = "N/A"

        # Fetch ultrasonic sensor data
        ultrasonic_data = db.child("ultrasonicSensor").get().val()
        if ultrasonic_data:
            distance = ultrasonic_data.get("distance", 0)
            pulse_duration = ultrasonic_data.get("pulseDuration", 0)
        else:
            distance = 0
            pulse_duration = 0

        return {
            "light": light,
            "countdown": countdown,
            "distance": distance,
            "pulse_duration": pulse_duration
        }

    except Exception as e:
        st.error(f"Error fetching data from Firebase: {str(e)}")
        return None

# Function to update distance in Firebase
def update_distance(value):
    try:
        db.child("ultrasonicSensor").update({"distance": value})
        st.sidebar.success(f"Updated distance to {value} cm in Firebase.")
    except Exception as e:
        st.sidebar.error(f"Failed to update distance: {str(e)}")

# Initialize session state for distance if not already initialized
if "distance" not in st.session_state:
    st.session_state["distance"] = 0  # Default initial value

# Initialize session state for historical data tracking
if "distance_history" not in st.session_state:
    st.session_state["distance_history"] = deque(maxlen=50)  # Store last 50 readings

# Main title
st.title("🚦 Real-time Traffic Monitoring System")

# Create placeholders to update data
traffic_placeholder = st.empty()
sensor_placeholder = st.empty()

# Set the refresh interval (in seconds)
refresh_interval = 1  # Adjust the interval as needed

# Slider to adjust distance
st.sidebar.subheader("Adjust Distance Value")
distance_value = st.sidebar.slider("Distance (cm)", min_value=0, max_value=100, value=st.session_state["distance"], step=1)

# Update Firebase when the slider changes
if distance_value != st.session_state["distance"]:
    st.session_state["distance"] = distance_value
    update_distance(distance_value)

# Traffic light status counter
light_status_counter = {"Red": 0, "Yellow": 0, "Green": 0}

# Main update loop to refresh data without full page refresh
while True:
    # Fetch the data
    data = get_realtime_data()

    # Update historical distance data
    st.session_state["distance_history"].append(data["distance"])

    # Track light status count
    light_status_counter[data['light'].capitalize()] += 1

    # Update Traffic Light Data
    with traffic_placeholder.container():
        st.subheader("🚦 Traffic Light Status")
        light_color = data['light']
        light_display = "🔴" if light_color == "red" else "🟢" if light_color == "green" else "🟡" if light_color == "yellow" else "⚪"
        st.markdown(f"### Light: {light_display} {light_color.capitalize()}")
        st.markdown(f"**Countdown**: {data['countdown']} seconds")

        # Traffic light gauge visual
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=int(data['countdown']),
            delta={'reference': 0},
            gauge={'axis': {'range': [0, 30]}, 'bar': {'color': light_color}},
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Countdown Timer"}
        ))
        st.plotly_chart(fig, use_container_width=True)

        # Pie chart for traffic light status distribution
        light_fig = px.pie(values=list(light_status_counter.values()), names=list(light_status_counter.keys()), 
                           title="Traffic Light Status Distribution")
        st.plotly_chart(light_fig, use_container_width=True)

    # Update Ultrasonic Sensor Data
    with sensor_placeholder.container():
        st.subheader("📡 Ultrasonic Sensor Data")
        st.markdown(f"**Distance**: {data['distance']} cm")
        st.markdown(f"**Pulse Duration**: {data['pulse_duration']} ms")

        # Line chart for historical distance measurements
        history_fig = px.line(x=range(len(st.session_state["distance_history"])), 
                              y=list(st.session_state["distance_history"]), 
                              labels={'x': 'Time', 'y': 'Distance (cm)'}, 
                              title="Historical Distance Measurements")
        st.plotly_chart(history_fig, use_container_width=True)

        # Distance bar chart visualization
        fig = go.Figure(go.Bar(
            x=['Distance (cm)'],
            y=[data['distance']],
            marker=dict(color='royalblue')
        ))
        fig.update_layout(title="Distance Measurement", xaxis_title="Parameter", yaxis_title="Value (cm)")
        st.plotly_chart(fig, use_container_width=True)

    # Sleep before the next update
    time.sleep(refresh_interval)