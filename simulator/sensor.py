# sensor.py
# Sensor class responsible for generating realistic water level readings.
# Uses a Brownian-motion walk so readings fluctuate naturally around a trend
# rather than jumping randomly — makes the data look like real sensor drift.
# This class has no knowledge of HTTP or the database; it only produces values.
