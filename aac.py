import sys
import os

from predictor import Predictor
from train import train_model

from settings import Ui_Dialog
from aas import Ui_Form
from aasBnW import Ui_FormBW
from profile2 import Ui_Profile
from login import Ui_Login
from gpscopy import gpsQ
import json

from database import save_message
from database import init_database
from database import get_userinfo
from database import get_usernames
from database import changename
from database import changepass

import subprocess
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton,QMessageBox
import math
from PyQt5.QtCore import QThread,pyqtSignal,Qt
from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QStackedWidget,
    QApplication
)

import serial
import pynmea2

from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize

class TrainingWorker(QThread):

    finished = pyqtSignal()
    error = pyqtSignal(str)

    def run(self):

        try:
            train_model()

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

class SpeechThread(QThread):

    def __init__(self, text,male):
        super().__init__()
        self.text = text
        self.male = male

    def run(self):
        if(self.male):
            subprocess.run(
                ["espeak",'-v', 'en+m3', "-s", "150", self.text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            subprocess.run(
                ["espeak",'-v', 'en+f3', "-s", "150", self.text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

class OptionsDialog(QDialog):
    def __init__(self,profile_id, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.profile_id = profile_id
        self.ui.bw.clicked.connect(self.toggle_bw_mode)
        self.ui.pushButton_2.clicked.connect(self.open_vocab_manager)
        self.ui.pushButton_3.clicked.connect(self.savechanges)
        self.ui.pushButton_4.clicked.connect(self.opengps)
        self.ui.pushButton.clicked.connect(self.logout)
        self.ui.pushButton_5.clicked.connect(self.toggleVoice)
        self.ui.pushButton_6.clicked.connect(self.end)
        
    def logout(self):
         self.parent().logout()
         self.accept()
        
    def end(self):
        QApplication.quit()
        
    def toggleVoice(self):
        self.parent().toggleVoice()
    
    def savechanges(self):
        if self.ui.lineEdit.text().strip() == "" and self.ui.lineEdit_2.text().strip() == "":
            return
        
        changepass(self.ui.lineEdit_2.text(),self.profile_id)
        changename(self.ui.lineEdit.text(),self.profile_id)
        
        QMessageBox.warning(
            self,
            "Info Changed",
            "Your information has been changed successfully."
        )
        
    def toggle_bw_mode(self):
        self.parent().toggle_bw_mode()
        self.accept()
        
    def opengps(self):
        self.parent().gpsmenu()
        self.accept()

    def open_vocab_manager(self):
        try:
            subprocess.Popen([
                sys.executable,
                "vocalMan.py",
                str(self.profile_id)
            ])
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Could not open Vocabulary Manager:\n\n{e}"
            )

class LoginDialog(QDialog):
    def __init__(self, profile_id, parent=None):
        super().__init__(parent)

        self.profile_id = profile_id

        self.ui = Ui_Login()
        self.ui.setupUi(self)

        self.info = get_userinfo(profile_id)

        self.ui.login.clicked.connect(self.login)
        self.ui.quit.clicked.connect(self.reject)

    def login(self):
        password = self.ui.passwordText.text()

        if password == self.info[2]:
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Login Failed",
                "Incorrect password."
            )
            self.ui.passwordText.clear()

class ProfileSelector(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.ui = Ui_Profile()
        self.ui.setupUi(self)
        
        self.usernames=get_usernames()
        self.ui.profile1.setText(self.usernames[0])
        self.ui.profile2.setText(self.usernames[1])
        self.ui.profile3.setText(self.usernames[2])
        self.ui.profile4.setText(self.usernames[3])
        self.ui.profile5.setText(self.usernames[4])
        
        self.ui.profile1.clicked.connect(
            lambda: self.select_profile(1)
        )

        self.ui.profile2.clicked.connect(
            lambda: self.select_profile(2)
        )

        self.ui.profile3.clicked.connect(
            lambda: self.select_profile(3)
        )

        self.ui.profile4.clicked.connect(
            lambda: self.select_profile(4)
        )

        self.ui.profile5.clicked.connect(
            lambda: self.select_profile(5)
        )

    def select_profile(self, profile_id):

        login = LoginDialog(
            profile_id,
            self
        )

        if login.exec_() == QDialog.Accepted:

            self.main_window = MainWindow(
                profile_id,self
            )

            self.main_window.show()

            self.hide()

class GPSReader(QThread):
    coordinates_received = pyqtSignal(float, float)

    def run(self):
        try:
            with serial.Serial(
                "/dev/serial0",
                baudrate=9600,
                timeout=1
            ) as gps:

                while not self.isInterruptionRequested():
                    line = gps.readline().decode(
                        "ascii",
                        errors="replace"
                    ).strip()

                    if not line:
                        continue

                    if line.startswith(("$GPGGA", "$GNGGA")):
                        try:
                            msg = pynmea2.parse(line)

                            # Only use coordinates when GPS has a valid fix
                            if msg.gps_qual > 0:
                                latitude = float(msg.latitude)
                                longitude = float(msg.longitude)

                                self.coordinates_received.emit(
                                    latitude,
                                    longitude
                                )

                        except (
                            pynmea2.ParseError,
                            ValueError,
                            TypeError
                        ):
                            continue

        except (serial.SerialException, OSError) as error:
            print(error)

class GPSmenu(QDialog):

    def __init__(self,parent=None):

        super().__init__(parent)
        
        self.ui = gpsQ()
        self.ui.setupUi(self)
        self.load_zones()
        self.ui.saveBtn.clicked.connect(self.addZone)
        self.ui.deleteBtn.clicked.connect(self.delete_selected_zone)
        self.ui.pushButton.clicked.connect(lambda: self.get_gps_coordinates(self.ui.piont1Edit,self.ui.piont1Edit_2))
        self.ui.pushButton_2.clicked.connect(lambda: self.get_gps_coordinates(self.ui.piont2Edit,self.ui.piont2Edit_2))
        self.ui.pushButton_3.clicked.connect(lambda: self.get_gps_coordinates(self.ui.piont3Edit,self.ui.piont3Edit_2))
        self.ui.pushButton_4.clicked.connect(lambda: self.get_gps_coordinates(self.ui.piont4Edit,self.ui.piont4Edit_2))
        
        # Connect selection event
        self.ui.ZoneCombo.currentIndexChanged.connect(
            self.on_zone_selected
        )
        
    def load_zones(self):
        self.ui.ZoneCombo.clear()
        self.ui.ZoneCombo.addItem("Select a zone...", None)

        try:
            with open("zones.json", "r") as file:
                data = json.load(file)

            for zone_data in data.get("zones", []):
                self.ui.ZoneCombo.addItem(
                    zone_data["zone"],
                    zone_data
                )

        except FileNotFoundError:
            print("Error: zones.json not found.")

        except (json.JSONDecodeError, KeyError) as error:
            print(f"Error loading zones: {error}")

    def on_zone_selected(self, index):
        zone_data = self.ui.ZoneCombo.itemData(index)

        if not zone_data:
            return

        zone_name = zone_data["zone"]
        zone_id = zone_data["id"]
        coordinates = zone_data["coordinates"]

        self.ui.nameEdit.setText(zone_name)
        self.ui.idEdit.setText(str(zone_id))

        self.ui.piont1Edit.setText(str(coordinates[0]["latitude"]))
        self.ui.piont2Edit.setText(str(coordinates[1]["latitude"]))
        self.ui.piont3Edit.setText(str(coordinates[2]["latitude"]))
        self.ui.piont4Edit.setText(str(coordinates[3]["latitude"]))

        self.ui.piont1Edit_2.setText(str(coordinates[0]["longitude"]))
        self.ui.piont2Edit_2.setText(str(coordinates[1]["longitude"]))
        self.ui.piont3Edit_2.setText(str(coordinates[2]["longitude"]))
        self.ui.piont4Edit_2.setText(str(coordinates[3]["longitude"]))

        print("Selected zone:", zone_name)
        print("All coordinates:", coordinates)

    def addZone(self):
        if os.path.exists("zones.json"):
            with open("zones.json", "r") as file:
                data = json.load(file)
        else:
            data = {"zones": []}
        
        lat1 = self.ui.piont1Edit.text().strip()
        lat2 = self.ui.piont2Edit.text().strip()
        lat3 = self.ui.piont3Edit.text().strip()
        lat4 = self.ui.piont4Edit.text().strip()
        lon1 = self.ui.piont1Edit_2.text().strip()
        lon2 = self.ui.piont2Edit_2.text().strip()
        lon3 = self.ui.piont3Edit_2.text().strip()
        lon4 = self.ui.piont4Edit_2.text().strip()
        zone_name = self.ui.nameEdit.text().strip()
            
        zone_id = max(
            (zone.get("id", 0) for zone in data["zones"]),
            default=0
        ) + 1  
        
        new_zone = {
                "zone": zone_name,
                "id": zone_id,
                "coordinates": [
                    {"latitude": lat1, "longitude": lon1},
                    {"latitude": lat2, "longitude": lon2},
                    {"latitude": lat3, "longitude": lon3},
                    {"latitude": lat4, "longitude": lon4}
                ]
            }

        data["zones"].append(new_zone)

        with open("zones.json", "w") as file:
            json.dump(data, file, indent=4)
            
        print("saved")
        self.ui.ZoneCombo.addItem(
            new_zone["zone"],
            new_zone
        )
    
    def delete_zone(self,zone_name):

        if not os.path.exists("zones.json"):
            print("JSON file does not exist.")
            return

        # Load existing data
        with open("zones.json", "r") as file:
            data = json.load(file)

        # Remove the specified zone
        original_count = len(data["zones"])

        data["zones"] = [
            zone for zone in data["zones"]
            if zone["zone"] != zone_name
        ]

        # Check whether a zone was deleted
        if len(data["zones"]) == original_count:
            print(f"{zone_name} was not found.")
            return

        # Save the updated data
        with open("zones.json", "w") as file:
            json.dump(data, file, indent=4)

        print(f"{zone_name} deleted successfully!")
        
    def delete_selected_zone(self):

        zone_name = self.ui.ZoneCombo.currentText()

        # Prevent deleting the placeholder
        if self.ui.ZoneCombo.currentIndex() <= 0:
            QMessageBox.warning(
                self,
                "No Zone Selected",
                "Please select a zone to delete."
            )
            return

        # Ask for confirmation
        answer = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {zone_name}?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        # Delete from JSON
        self.delete_zone(zone_name)

        # Remove from the ComboBox
        self.ui.ZoneCombo.removeItem(
            self.ui.ZoneCombo.currentIndex()
        )

        QMessageBox.information(
            self,
            "Success",
            f"{zone_name} has been deleted."
        )
    
    def refresh_zone_combo(self):

        self.ui.ZoneCombo.clear()
        self.ui.ZoneCombo.addItem("Select a zone...", None)

        with open("zones.json", "r") as file:
            data = json.load(file)

        for zone_data in data["zones"]:
            self.ui.ZoneCombo.addItem(
                zone_data["zone"],
                zone_data
            )
            
    def get_gps_coordinates(self,line1,line2):
        mom = self.parent() 
        line1.setText(str(mom.long))
        line2.setText(str(mom.lat))


def generate_pages(
    json_file,
    textbox,
    stacked_widget,
    bw_mode=False,
    vocab_folder="/.",
    buttons_per_page=6,
    columns=3,
    active_zone_id=None
):

    filepath = os.path.join(vocab_folder, json_file)

    with open(filepath, "r", encoding="utf-8") as file:
        button_data = json.load(file)

    # Prioritize words belonging to the active zone
    if active_zone_id is not None:
        button_data.sort(
            key=lambda item: (
                str(item.get("zone_id")) != str(active_zone_id)
            )
        )

    # Remove duplicate words
    unique_words = []
    seen_words = set()

    for item in button_data:
        word_key = str(item.get("text", "")).strip().casefold()

        if not word_key or word_key in seen_words:
            continue

        seen_words.add(word_key)
        unique_words.append(item)

    button_data = unique_words

    total_pages = math.ceil(len(button_data) / buttons_per_page)
    all_buttons = []

    for page_num in range(total_pages):

        page = QWidget()
        page_layout = QVBoxLayout()

        group_box = QGroupBox()
        grid_layout = QGridLayout()

        group_box.setLayout(grid_layout)
        page_layout.addWidget(group_box)
        page.setLayout(page_layout)

        start = page_num * buttons_per_page
        end = start + buttons_per_page

        current_buttons = button_data[start:end]

        row = 0
        col = 0

        for item in current_buttons:

            text = item.get("text", "Button")

            color = "gray" if bw_mode else item.get("color", "gray")
            icon_path = item.get("icon", "")

            button = QPushButton(text)
            button.setFixedHeight(120)

            if icon_path:
                button.setIcon(QIcon(icon_path))
                button.setIconSize(QSize(40, 40))

            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding-top: 20px;
                    padding-bottom: 20px;
                    font-size: 28px;
                    text-align: center;
                }}

                QPushButton:hover {{
                    background-color: lightgray;
                    color: black;
                }}
            """)

            button.setMinimumHeight(60)

            button.clicked.connect(
                lambda checked, t=text:
                    textbox.setText(textbox.text() + " " + t)
            )

            grid_layout.addWidget(button, row, col)
            all_buttons.append(button)

            col += 1

            if col >= columns:
                col = 0
                row += 1

        stacked_widget.addWidget(page)

    return all_buttons


def clear_stacked_widget(stacked_widget):
    while stacked_widget.count():
        widget = stacked_widget.widget(0)
        stacked_widget.removeWidget(widget)
        widget.deleteLater()

class MainWindow(QWidget):
    def __init__(self, profile_id, profile_selector=None):
        super().__init__()
        self.profile_id = profile_id

        self.vocab_folder = os.path.join(
            "profiles",
            str(profile_id)
        )
        self.profile_selector = profile_selector
        self.bw_mode = False
        self.lat = 0
        self.long = 0
        self.male = True
        
        self.ui = Ui_Form()        
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |Qt.WindowType.Window)
        self.showFullScreen()
        self.threads = []
        self.predictor = Predictor()
        self.messages_since_training = 0
        self.training_worker = None
        
        self.zones = []

        self.active_zone_id = None
        self.current_category_file = None
        self.all_buttons = []

        self.load_zones()

        self.start_gps()
        
        self.setUpUI()
        
    def toggleVoice(self):
        self.male = not self.male
        
    def refresh_current_category(self):

        if not hasattr(self, "current_category_file"):
            return

        clear_stacked_widget(self.ui.stackedWidget)

        self.all_buttons = generate_pages(
            self.current_category_file,
            self.ui.lineEdit,
            self.ui.stackedWidget,
            self.bw_mode,
            self.vocab_folder,
            active_zone_id=self.active_zone_id
        )
        
    def show_category(self, filename, title):

        self.current_category_file = filename

        self.ui.label.setText(title)

        clear_stacked_widget(self.ui.stackedWidget)

        self.all_buttons = generate_pages(
            filename,
            self.ui.lineEdit,
            self.ui.stackedWidget,
            self.bw_mode,
            self.vocab_folder,
            active_zone_id=self.active_zone_id
        )
        
    
    def check_all_zones(self):

        matched_zone = None

        point = (self.long, self.lat)

        for zone_data in self.zones:

            coordinates = zone_data.get("coordinates", [])

            if len(coordinates) < 3:
                continue

            polygon = [
                (
                    float(coord["longitude"]),
                    float(coord["latitude"])
                )
                for coord in coordinates
            ]

            if self.point_in_polygon(point, polygon):
                matched_zone = zone_data
                break

        # Get the matched zone ID
        new_zone_id = (
            matched_zone.get("id")
            if matched_zone else None
        )

        # Only refresh the vocabulary when the zone changes
        if new_zone_id != self.active_zone_id:

            self.active_zone_id = new_zone_id

            if matched_zone:
                print(
                    "Entered zone:",
                    matched_zone.get("zone"),
                    "ID:",
                    new_zone_id
                )
            else:
                print("Outside all zones")

            self.refresh_current_category()


    def point_in_polygon(self, point, polygon):
        x, y = point
        inside = False

        j = len(polygon) - 1

        for i in range(len(polygon)):
            xi, yi = polygon[i]
            xj, yj = polygon[j]

            intersects = (
                (yi > y) != (yj > y)
                and x < (xj - xi) * (y - yi) / (yj - yi) + xi
            )

            if intersects:
                inside = not inside

            j = i

        return inside
        
    def load_zones(self):
        file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "zones.json"
        )

        try:
            with open(file_path, "r") as file:
                data = json.load(file)

            self.zones = data.get("zones", [])

            print(f"Successfully loaded {len(self.zones)} zones.")

        except (FileNotFoundError, json.JSONDecodeError) as error:
            self.zones = []
            print(f"Failed to load zones: {error}")

    def start_gps(self):
        self.gps_thread = GPSReader()

        self.gps_thread.coordinates_received.connect(
            self.on_coordinates_received
        )

        self.gps_thread.start()
        
    def on_coordinates_received(self,long,lat):
        self.long = long
        self.lat = lat
        self.check_all_zones()
    
    def gpsmenu(self):
        dialog = GPSmenu(self)
        dialog.exec_()
    
    def toggle_bw_mode(self):
        # Set window flags BEFORE rebuilding
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Window
        )

        self.bw_mode = not self.bw_mode

        clear_stacked_widget(self.ui.stackedWidget)
        self.clear_ui()

        # Build the other UI
        if self.bw_mode:
            self.ui = Ui_FormBW()
        else:
            self.ui = Ui_Form()

        self.ui.setupUi(self)
        self.setUpUI()
        self.showFullScreen()

    def clear_ui(self):
    # Remove all widgets from the current window
        for widget in self.findChildren(QWidget):
            if widget.parent() == self:
                widget.deleteLater()

        # Remove the existing layout
        old_layout = self.layout()

        if old_layout is not None:
            QWidget().setLayout(old_layout)
    
    def setUpUI(self):
        self.ui.pushButton_5.clicked.connect(self.next_page)
        self.ui.pushButton_6.clicked.connect(self.prev_page)
        self.ui.pushButton_9.clicked.connect(self.talk)
        self.ui.pushButton.clicked.connect(self.pplBtn)
        self.ui.pushButton_2.clicked.connect(self.foodBtn)
        self.ui.pushButton_3.clicked.connect(self.actionBtn)
        self.ui.pushButton_4.clicked.connect(self.feelingsBtn)
        self.ui.pushButton_10.clicked.connect(self.customBtn)
        self.ui.pushButton_7.clicked.connect(self.delete_last_word)
        self.ui.pushButton_8.clicked.connect(self.clearBtn)
        self.ui.pushButton_11.clicked.connect(self.show_options)
        
        self.ui.lineEdit.textChanged.connect(self.update_predictions)
        
        self.prediction_layout = self.ui.groupBox_3.layout()

        # Create one only if it doesn't exist
        if self.prediction_layout is None:
            self.prediction_layout = QGridLayout(self.ui.groupBox_3)

        self.prediction_buttons = []

        for i in range(3):
            button = QPushButton()
            button.setFixedHeight(25)
            button.setStyleSheet(f"""
                            QPushButton {{
                                background-color: grey;
                                color: white;
                                border: none;
                                border-radius: 10px;
                                padding-top: 20px;
                                padding-bottom: 20px;
                                font-size: 14px;
                                text-align: left;
                            }}
            
                            QPushButton:hover {{
                                background-color: lightgray;
                                color: black;
                            }}
                        """)
            button.hide()

            button.clicked.connect(lambda checked=False,b=button:self.ui.lineEdit.setText(self.ui.lineEdit.text() + " " + b.text()))
            self.prediction_buttons.append(button)
            self.prediction_layout.addWidget(button,0,i)
            
        self.pplBtn()
    
    def show_options(self):
        dialog = OptionsDialog(self.profile_id,self)
        dialog.exec_()
        
    def logout(self):
        if self.profile_selector is not None:
            self.profile_selector.show()
            
        self.close()
                
    def update_predictions(self):
        text = self.ui.lineEdit.text().strip()
        predictions = self.predictor.predict(text, amount=3)

        for i, button in enumerate(self.prediction_buttons):
            if i < len(predictions):
                word = predictions[i]
                button.setText(word)
                button.show()
            else:
                button.hide()
    
    def talk(self):
        print(self.ui.lineEdit.text())
        save_message(self.ui.lineEdit.text())
        thread = SpeechThread(self.ui.lineEdit.text(),self.male)

        self.threads.append(thread)

        thread.finished.connect(
            lambda: self.threads.remove(thread)
        )

        thread.start()
        
        self.messages_since_training += 1
        # Retrain after 100 messages
        if self.messages_since_training >= 100:
            self.messages_since_training = 0
            self.start_training()

    def start_training(self):

        # Don't start another training process
        # if one is already running.

        if (
            self.training_worker is not None
            and self.training_worker.isRunning()
        ):
            return


        self.training_worker = TrainingWorker()

        self.training_worker.finished.connect(
            self.training_finished
        )

        self.training_worker.error.connect(
            self.training_error
        )

        self.training_worker.start()
    
    def training_finished(self):
        print("Training finished.")
        # Load the newly trained model
        self.predictor.reload()
        # Update suggestions
        self.update_predictions()
        self.training_worker = None
        
    def training_error(self, message):
        print(
            "Training error:",
            message
        )
        self.training_worker = None
    
    def next_page(self):
        current = self.ui.stackedWidget.currentIndex()
        total = self.ui.stackedWidget.count()
        self.ui.stackedWidget.setCurrentIndex(
            (current + 1) % total
        )

    def prev_page(self):
        current = self.ui.stackedWidget.currentIndex()
        total = self.ui.stackedWidget.count()

        self.ui.stackedWidget.setCurrentIndex(
            (current - 1) % total
        )
    
    def pplBtn(self):
        self.show_category("people.json", "People")


    def foodBtn(self):
        self.show_category("food.json", "Food")


    def actionBtn(self):
        self.show_category("actions.json", "Action")


    def feelingsBtn(self):
        self.show_category("feelings.json", "Feelings")


    def customBtn(self):
        self.show_category("custom.json", "Custom")
        
    def clearBtn(self):
        self.ui.lineEdit.setText("")
        
    def delete_last_word(self):
        text = self.ui.lineEdit.text().strip()
        if not text:
            return
        words = text.split()
        words.pop()
        self.ui.lineEdit.setText(" ".join(words))
        
    def closeEvent(self, event):
        print("Closing application...")

        # Stop GPS thread
        if hasattr(self, "gps_thread") and self.gps_thread.isRunning():
            self.gps_thread.requestInterruption()
            self.gps_thread.wait()

        # Stop any speech threads
        for thread in self.threads:
            if thread.isRunning():
                thread.wait()

        # Stop training worker
        if (
            self.training_worker is not None
            and self.training_worker.isRunning()
        ):
            self.training_worker.wait()

        event.accept()    
        
if __name__ == '__main__':
    init_database()
    app = QApplication(sys.argv)

    selector = ProfileSelector()
    selector.show()

    sys.exit(app.exec_())