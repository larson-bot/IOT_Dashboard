import streamlit as st
import firebase_admin
from firebase_admin import credentials, storage
import pyrebase
import time
import plotly.graph_objects as go
import plotly.express as px

# Set page configuration
st.set_page_config(page_title="Real-time Traffic Monitoring System", layout="wide")

# Firebase configuration using Pyrebase for Realtime Database
config = {
    "apiKey": "AIzaSyCUZ6SqIPcPuWXgf0gx9PkM6nXtnEtEIKg",
    "authDomain": "traffic-system-database-2f687.firebaseapp.com",
    "databaseURL": "https://traffic-system-database-2f687-default-rtdb.firebaseio.com/",
    "projectId": "traffic-system-database-2f687",
    "storageBucket": "traffic-system-database-2f687.appspot.com",
}

# Initialize Pyrebase
try:
    firebase = pyrebase.initialize_app(config)
    db = firebase.database()
    st.sidebar.success("Connected to Firebase successfully.")
except Exception as e:
    st.sidebar.error(f"Failed to connect to Firebase: {str(e)}")

# Initialize Firebase Admin SDK with service account credentials
try:
    # Check if Firebase Admin is already initialized to avoid reinitialization
    if not firebase_admin._apps:
        cred = credentials.Certificate("C:/Users/mhtan/Documents/BAIT 2123 Internet of Things/serviceAccountKey.json")  # Replace with your correct service account key path
        firebase_admin.initialize_app(cred, {'storageBucket': 'traffic-system-database-2f687.appspot.com'})
    bucket = storage.bucket()
    st.sidebar.success("Firebase Admin SDK initialized successfully.")
except Exception as e:
    st.sidebar.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")

# Sidebar navigation
page = st.sidebar.selectbox("Select Page", ["Dashboard", "Media"])

# Dashboard Page
if page == "Dashboard":
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

    # Function to update traffic light countdown in Firebase
    def update_countdown(countdown_value):
        try:
            db.child("trafficLight").update({"countdown": countdown_value})
            st.sidebar.success(f"Updated countdown to {countdown_value} seconds in Firebase.")
        except Exception as e:
            st.sidebar.error(f"Failed to update countdown: {str(e)}")

    # Initialize session state for distance and countdown settings if not already initialized
    if "distance" not in st.session_state:
        st.session_state["distance"] = 0  # Default initial value

    if "countdown" not in st.session_state:
        st.session_state["countdown"] = 10  # Default initial countdown value

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

    # Slider to adjust traffic light countdown
    st.sidebar.subheader("Adjust Traffic Light Countdown Time")
    countdown_value = st.sidebar.slider("Countdown (seconds)", min_value=1, max_value=60, value=st.session_state["countdown"], step=1)

    # Update Firebase when the countdown slider changes
    if countdown_value != st.session_state["countdown"]:
        st.session_state["countdown"] = countdown_value
        update_countdown(countdown_value)

    # Main update loop to refresh data without full page refresh
    while True:
        # Fetch the data
        data = get_realtime_data()

        # Update Traffic Light Data
        with traffic_placeholder.container():
            st.subheader("🚦 Traffic Light Status")
            light_color = data['light']
            light_display = "🔴" if light_color == "red" else "🟢" if light_color == "green" else "🟡" if light_color == "yellow" else "⚪"
            st.markdown(f"### Light: {light_display} {light_color.capitalize()}")
            st.markdown(f"**Countdown**: {data['countdown']} seconds")

            # Traffic light gauge visual
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=int(data['countdown']),
                gauge={'axis': {'range': [0, 60]}, 'bar': {'color': "red" if light_color == "red" else "green" if light_color == "green" else "yellow"}}))
            st.plotly_chart(fig, use_container_width=True)

        # Update Ultrasonic Sensor Data
        with sensor_placeholder.container():
            st.subheader("📡 Ultrasonic Sensor Data")
            st.markdown(f"**Distance**: {data['distance']} cm")
            st.markdown(f"**Pulse Duration**: {data['pulse_duration']} ms")

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

# Media Page
elif page == "Media":
    st.title("📷 Real-time Media from Firebase Storage")

    # Display images from Firebase Storage
    st.subheader("Images")
    try:
        if 'bucket' in locals():  # Check if bucket is correctly initialized
            blobs = bucket.list_blobs(prefix="images/")
            for blob in blobs:
                if blob.name.endswith(('.jpg', '.jpeg', '.png')):
                    image_url = blob.generate_signed_url(expiration=3600)
                    # Debug: Print the generated URL
                    st.text(f"Generated URL: {image_url}")
                    st.image(image_url, caption=blob.name, use_column_width=True)
        else:
            st.error("Bucket is not defined.")
    except Exception as e:
        st.error(f"Error loading images: {str(e)}")

    # Display videos from Firebase Storage
    st.subheader("Videos")
    try:
        if 'bucket' in locals():  # Check if bucket is correctly initialized
            blobs = bucket.list_blobs(prefix="videos/")
            for blob in blobs:
                if blob.name.endswith(('.mp4', '.mov')):
                    video_url = blob.generate_signed_url(expiration=3600)
                    # Debug: Print the generated URL
                    st.text(f"Generated Video URL: {video_url}")
                    st.video(video_url)
        else:
            st.error("Bucket is not defined.")
    except Exception as e:
        st.error(f"Error loading videos: {str(e)}")
        fig.update_layout(title="Distance Measurement", xaxis_title="Parameter", yaxis_title="Value (cm)")
        st.plotly_chart(fig, use_container_width=True)

    # Sleep before the next update
    time.sleep(refresh_interval)
