
import sys
import serial
import pynmea2
from datetime import datetime

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel,
    QVBoxLayout, QGridLayout
)

GPS_PORT = "/dev/serial0"
GPS_BAUD = 9600


class GPSReader(QThread):
    coordinates_received = pyqtSignal(float, float)
    status_received = pyqtSignal(str)
    details_received = pyqtSignal(str, str, str)

    def run(self):
        try:
            with serial.Serial(
                GPS_PORT,
                GPS_BAUD,
                timeout=1
            ) as gps:

                self.status_received.emit(
                    "Connected - Waiting for GPS fix..."
                )

                while not self.isInterruptionRequested():
                    line = gps.readline().decode(
                        "ascii", errors="replace"
                    ).strip()

                    if not line.startswith(("$GPGGA", "$GNGGA")):
                        continue

                    try:
                        msg = pynmea2.parse(line)

                        if not msg.latitude or not msg.longitude:
                            self.status_received.emit(
                                "Connected - No GPS fix yet"
                            )
                            continue

                        latitude = float(msg.latitude)
                        longitude = float(msg.longitude)

                        satellites = str(msg.num_sats or "N/A")
                        altitude = str(msg.altitude or "N/A")

                        self.coordinates_received.emit(
                            latitude, longitude
                        )

                        self.details_received.emit(
                            satellites,
                            altitude,
                            datetime.now().strftime("%H:%M:%S")
                        )

                        self.status_received.emit(
                            "GPS FIX ACQUIRED"
                        )

                    except pynmea2.ParseError:
                        continue

        except serial.SerialException as error:
            self.status_received.emit(f"GPS ERROR: {error}")


class GPSWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Raspberry Pi GPS Tester")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)
        grid = QGridLayout()

        self.status_label = QLabel("Starting GPS...")
        self.status_label.setStyleSheet(
            "font-size: 16px; font-weight: bold;"
        )

        self.latitude_label = QLabel("--")
        self.longitude_label = QLabel("--")
        self.satellites_label = QLabel("--")
        self.altitude_label = QLabel("--")
        self.time_label = QLabel("--")

        grid.addWidget(QLabel("Latitude:"), 0, 0)
        grid.addWidget(self.latitude_label, 0, 1)

        grid.addWidget(QLabel("Longitude:"), 1, 0)
        grid.addWidget(self.longitude_label, 1, 1)

        grid.addWidget(QLabel("Satellites:"), 2, 0)
        grid.addWidget(self.satellites_label, 2, 1)

        grid.addWidget(QLabel("Altitude:"), 3, 0)
        grid.addWidget(self.altitude_label, 3, 1)

        grid.addWidget(QLabel("Last Update:"), 4, 0)
        grid.addWidget(self.time_label, 4, 1)

        layout.addWidget(self.status_label)
        layout.addLayout(grid)

        self.gps_thread = GPSReader()

        self.gps_thread.status_received.connect(
            self.status_label.setText
        )

        self.gps_thread.coordinates_received.connect(
            self.update_coordinates
        )

        self.gps_thread.details_received.connect(
            self.update_details
        )

        self.gps_thread.start()

    def update_coordinates(self, latitude, longitude):
        self.latitude_label.setText(f"{latitude:.7f}")
        self.longitude_label.setText(f"{longitude:.7f}")

    def update_details(self, satellites, altitude, timestamp):
        self.satellites_label.setText(satellites)
        self.altitude_label.setText(f"{altitude} m")
        self.time_label.setText(timestamp)

    def closeEvent(self, event):
        self.gps_thread.requestInterruption()
        self.gps_thread.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = GPSWindow()
    window.show()

    sys.exit(app.exec_())
