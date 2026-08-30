# simulator.py
# Entry point for the sensor simulator.
# Instantiates all sensors from config, then runs an async loop that
# fires every SEND_INTERVAL_SECONDS and POSTs each sensor's latest reading
# to the backend API.
# Replace this file (or just BACKEND_URL in config.py) to swap in real hardware.
