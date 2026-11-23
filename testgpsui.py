import sys
import json

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QComboBox,
    QLabel
)


class ZoneSelector(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Zone Selector")
        self.setGeometry(100, 100, 400, 300)

        # Create widgets
        self.zone_combo = QComboBox()
        self.zone_combo.addItem("Select a zone...", None)

        self.info_label = QLabel("Choose a zone.")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.zone_combo)
        layout.addWidget(self.info_label)

        self.setLayout(layout)

        # Load JSON data
        self.load_zones()

        # Connect selection event
        self.zone_combo.currentIndexChanged.connect(
            self.on_zone_selected
        )

    def load_zones(self):

        try:
            with open("zones.json", "r") as file:
                data = json.load(file)

            for zone_data in data["zones"]:

                zone_name = zone_data["zone"]

                # Display zone name, store all zone data
                self.zone_combo.addItem(
                    zone_name,
                    zone_data
                )

        except FileNotFoundError:
            self.info_label.setText(
                "Error: zones.json not found."
            )

        except (json.JSONDecodeError, KeyError) as error:
            self.info_label.setText(
                f"Error loading zones: {error}"
            )

    def on_zone_selected(self, index):

        # Retrieve the complete data for the selected zone
        zone_data = self.zone_combo.itemData(index)

        if zone_data is None:
            self.info_label.setText("Choose a zone.")
            return

        zone_name = zone_data["zone"]
        coordinates = zone_data["coordinates"]

        # Display the selected zone and its coordinates
        text = f"{zone_name}\n\n"

        for i, point in enumerate(coordinates, start=1):
            text += (
                f"Point {i}: "
                f"Latitude: {point['latitude']}, "
                f"Longitude: {point['longitude']}\n"
            )

        self.info_label.setText(text)

        # You can also access the coordinates individually
        point1 = coordinates[0]
        point2 = coordinates[1]
        point3 = coordinates[2]
        point4 = coordinates[3]

        print("Selected zone:", zone_name)
        print("All coordinates:", coordinates)


app = QApplication(sys.argv)

window = ZoneSelector()
window.show()

sys.exit(app.exec())
