import sys
import os
import json
from vocalUI import Ui_Form

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QColorDialog,
    QMessageBox,
    QFileDialog
)

from PyQt5.QtGui import (
    QColor,
    QPixmap,
    QPainter,
)

from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer

from PyQt5.QtCore import (
    Qt,
)


# ============================================================
# SETTINGS
# ============================================================

ICON_FOLDER = "icons"

MAX_JSON_FILES = 5

if len(sys.argv) < 2:
    print("No profile ID provided.")
    sys.exit(1)

profile_id = int(sys.argv[1])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_FOLDER = os.path.join(BASE_DIR, "profiles")

VOCAB_FOLDER = os.path.join(
    PROFILES_FOLDER,
    str(profile_id)
)

os.makedirs(VOCAB_FOLDER, exist_ok=True)
# ============================================================
# MAIN WINDOW
# ============================================================

class VocabularyManager(QWidget):

    def __init__(self):

        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.file_list.currentIndexChanged.connect(self.file_selected)
        self.ui.word_list.currentItemChanged.connect(self.word_selected)
        self.ui.add_button.clicked.connect(self.add_word)
        self.ui.delete_button.clicked.connect(self.delete_word)
        self.ui.word_edit.setPlaceholderText("Enter word...")
        self.ui.color_edit.setReadOnly(True)
        self.ui.color_button.clicked.connect(self.choose_color)
        self.ui.icon_edit.setReadOnly(True)
        self.ui.icon_button.clicked.connect(self.choose_icon)
        self.ui.save_button.clicked.connect(self.save_word)
        self.load_zones()
        #self.ui.ZoneCombo.currentIndexChanged.connect(self.on_zone_selected)
        self.current_file = None
        self.current_index = None
        self.zoneId = None
        self.words = []

        self.load_json_files()

        
    # ========================================================
    # LOAD JSON FILES
    # ========================================================
    
    def load_zones(self):
        self.ui.ZoneCombo.clear()
        try:
            with open("zones.json", "r") as file:
                data = json.load(file)

            for zone_data in data["zones"]:

                zone_name = zone_data["zone"]
                
                zone_id = zone_data["id"]

                # Display zone name, store all zone data
                self.ui.ZoneCombo.addItem(
                    zone_name,
                    zone_id,
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
            zone_data = self.ui.ZoneCombo.itemData(index)
    
            self.zoneId = zone_data[1]
    
    

    # ========================================================
    # LOAD JSON FILES
    # ========================================================

    def load_json_files(self):
        self.ui.file_list.clear()

        os.makedirs(
            VOCAB_FOLDER,
            exist_ok=True
        )

        files = [
            file
            for file in os.listdir(VOCAB_FOLDER)
            if file.lower().endswith(".json")
        ]

        files.sort()

        for filename in files:
            self.ui.file_list.addItem(filename)

        if self.ui.file_list.count() > 0:
            self.ui.file_list.setCurrentIndex(0)


    # ========================================================
    # JSON FILE SELECTED
    # ========================================================

    def file_selected(self, index):
        if index < 0:
            return

        filename = self.ui.file_list.currentText()

        self.current_file = os.path.join(
            VOCAB_FOLDER,
            filename
        )

        self.load_words()


    # ========================================================
    # LOAD WORDS
    # ========================================================

    def load_words(self):

        self.ui.word_list.clear()

        self.words = []

        self.current_index = None


        if not self.current_file:
            return


        try:

            with open(
                self.current_file,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)


            if not isinstance(
                data,
                list
            ):

                raise ValueError(
                    "JSON must contain a list of words."
                )


            self.words = data


            for item in self.words:

                word = item.get(
                    "text",
                    ""
                )

                self.ui.word_list.addItem(
                    word
                )


        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                f"Could not load JSON:\n\n{e}"
            )

            return


        self.clear_editor()


        if self.ui.word_list.count() > 0:

            self.ui.word_list.setCurrentRow(
                0
            )


    # ========================================================
    # WORD SELECTED
    # ========================================================

    def word_selected(
        self,
        current,
        previous
    ):

        if current is None:

            self.clear_editor()

            return


        index = self.ui.word_list.row(
            current
        )


        if index < 0 or index >= len(
            self.words
        ):

            return


        self.current_index = index


        data = self.words[
            index
        ]
        
        zone_id = data.get("zoneid")

        combo_index = self.ui.ZoneCombo.findData(zone_id)

        
        if combo_index >= 0:
            self.ui.ZoneCombo.setCurrentIndex(combo_index)
        else:
            self.ui.ZoneCombo.setCurrentIndex(-1)

        self.ui.word_edit.setText(
            data.get(
                "text",
                ""
            )
        )
        
        self.ui.word_edit.setText(
            data.get(
                "text",
                ""
            )
        )


        color = data.get(
            "color",
            "#ffffff"
        )


        self.ui.color_edit.setText(
            color
        )


        self.update_color_preview(
            color
        )


        icon = data.get(
            "icon",
            ""
        )


        self.ui.icon_edit.setText(
            icon
        )


        self.show_icon(
            icon
        )


    # ========================================================
    # ADD WORD
    # ========================================================

    def add_word(self):

        if not self.current_file:

            QMessageBox.warning(
                self,
                "No JSON selected",
                "Please select a JSON file first."
            )

            return


        new_word = {
            "text": "new word",
            "color": "#ffffff",
            "icon": ""
        }


        self.words.append(
            new_word
        )


        self.ui.word_list.addItem(
            "new word"
        )


        new_index = (
            self.ui.word_list.count() - 1
        )


        self.ui.word_list.setCurrentRow(
            new_index
        )


        self.current_index = new_index


        self.ui.word_edit.setFocus()

        self.ui.word_edit.selectAll()


    # ========================================================
    # DELETE WORD
    # ========================================================

    def delete_word(self):

        if self.current_index is None:
            return


        word = self.words[
            self.current_index
        ].get(
            "text",
            ""
        )


        answer = QMessageBox.question(
            self,
            "Delete Word",
            f"Delete '{word}'?",
            QMessageBox.Yes | QMessageBox.No
        )


        if answer != QMessageBox.Yes:
            return


        del self.words[
            self.current_index
        ]


        self.ui.word_list.takeItem(
            self.current_index
        )


        self.current_index = None

        self.clear_editor()


        if self.ui.word_list.count() > 0:

            self.ui.word_list.setCurrentRow(
                0
            )


        self.write_json()


    # ========================================================
    # SAVE WORD
    # ========================================================

    def save_word(self):

        if self.current_index is None:
            return


        word = self.ui.word_edit.text().strip()


        if not word:

            QMessageBox.warning(
                self,
                "Invalid Word",
                "The word cannot be empty."
            )

            return


        # ----------------------------------------------------
        # Check duplicates
        # ----------------------------------------------------

        for i, item in enumerate(
            self.words
        ):

            if i == self.current_index:
                continue


            existing = item.get(
                "text",
                ""
            ).strip().lower()


            if existing == word.lower():

                QMessageBox.warning(
                    self,
                    "Duplicate Word",
                    "That word already exists."
                )

                return


        # ----------------------------------------------------
        # Update JSON object
        # ----------------------------------------------------

        self.words[
            self.current_index
        ]["text"] = word
        
        self.words[
            self.current_index
        ]["zoneid"] = self.zoneId


        self.words[
            self.current_index
        ]["color"] = self.ui.color_edit.text()


        self.words[
            self.current_index
        ]["icon"] = self.ui.icon_edit.text()


        # ----------------------------------------------------
        # Update list
        # ----------------------------------------------------

        item = self.ui.word_list.item(
            self.current_index
        )


        item.setText(
            word
        )


        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        self.write_json()


        QMessageBox.information(
            self,
            "Saved",
            "Word saved successfully."
        )


    # ========================================================
    # WRITE JSON
    # ========================================================

    def write_json(self):

        if not self.current_file:
            return


        try:

            with open(
                self.current_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    self.words,
                    file,
                    indent=4,
                    ensure_ascii=False
                )


        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                f"Could not save JSON:\n\n{e}"
            )


    # ========================================================
    # CHOOSE COLOR
    # ========================================================

    def choose_color(self):

        current_color = QColor(
            self.ui.color_edit.text()
        )


        color = QColorDialog.getColor(
            current_color,
            self,
            "Choose Word Color"
        )


        if not color.isValid():
            return


        hex_color = color.name()


        self.ui.color_edit.setText(
            hex_color
        )


        self.update_color_preview(
            hex_color
        )


    # ========================================================
    # COLOR BUTTON PREVIEW
    # ========================================================

    def update_color_preview(
        self,
        color
    ):

        self.ui.color_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {color};
                color: black;
            }}
            """
        )


    # ========================================================
    # CHOOSE SVG ICON
    # ========================================================

    def show_icon(self, icon_path):

        self.ui.icon_preview.clear()

        if not icon_path:
            return

        path = os.path.normpath(icon_path)

        if not os.path.exists(path):
            self.ui.icon_preview.setText("File not found")
            return

        extension = os.path.splitext(path)[1].lower()

        # SVG FILES
        if extension == ".svg":

            renderer = QSvgRenderer(path)

            if not renderer.isValid():
                self.ui.icon_preview.setText("Invalid SVG")
                return

            pixmap = QPixmap(self.ui.icon_preview.size())
            pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()

        # REGULAR IMAGE FILES
        else:

            pixmap = QPixmap(path)

            if pixmap.isNull():
                self.ui.icon_preview.setText("Unsupported or invalid file")
                return

            pixmap = pixmap.scaled(
                self.ui.icon_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

        self.ui.icon_preview.setPixmap(pixmap)
        
    def choose_icon(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.svg *.png *.jpg *.jpeg *.bmp *.gif *.webp *.tiff);;All Files (*)"
        )

        if file_path:
            self.show_icon(file_path)
            self.ui.icon_edit.setText(file_path)

    # ========================================================
    # CLEAR EDITOR
    # ========================================================

    def clear_editor(self):

        self.current_index = None

        self.ui.word_edit.clear()

        self.ui.color_edit.clear()

        self.ui.icon_edit.clear()

        self.ui.icon_preview.clear()

        self.ui.color_button.setStyleSheet("")


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    app = QApplication(
        sys.argv
    )

    window = VocabularyManager()

    window.show()

    sys.exit(
        app.exec()
    )