import pathlib
import re
import yaml
import shutil
from PyPDF2 import PdfReader, PdfWriter
import sys

# TODO
# - Refactor to separate core, UI, PDF handling, config handling, helper functions
# - Softcode config
# - Remove window decoration, improve UI
# - Package as executable

from PyQt6 import QtCore, QtGui, QtWidgets


class Table(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        # TODO - DRY this function
        read_file = open("config.yaml", "r")
        config = yaml.full_load(read_file.read())
        read_file.flush()
        read_file.close()

        # TODO - Improve UI

        super(Table, self).__init__(len(config["drawings"]), 5, parent)
        self.setFont(QtGui.QFont("Helvetica", 10, italic=False))
        headertitle = ("Number", "Title", "Scale", "Discipline", "Type")
        self.setHorizontalHeaderLabels(headertitle)
        self.verticalHeader().hide()
        self.horizontalHeader().setHighlightSections(False)

        self.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.setColumnWidth(0, 100)
        self.setColumnWidth(1, 250)
        self.setColumnWidth(2, 75)
        self.setColumnWidth(3, 100)
        self.setColumnWidth(4, 100)
        self.cellChanged.connect(self._cellclicked)

        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                current = list(config["drawings"].keys())[row]
                if (col == 4):
                    combox_lay = QtWidgets.QComboBox(self)
                    combox_lay.addItems(["legend", "layout", "details", "SLD"])
                    combox_lay.setCurrentText(
                        config["drawings"][current]["type"])
                    self.setCellWidget(row, col, combox_lay)
                else:
                    item = QtWidgets.QTableWidgetItem()
                    if (col == 0):
                        item.setText(current)
                    if (col == 1):
                        item.setText(config["drawings"][current]["title"])
                    if (col == 2):
                        item.setText(config["drawings"][current]["scale"])
                    if (col == 3):
                        item.setText(config["drawings"][current]["discipline"])
                    self.setItem(row, col, item)

    def _cellclicked(self, r, c):
        it = self.item(r, c)
        it.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

    def _addrow(self):
        rowcount = self.rowCount()
        self.insertRow(rowcount)
        combox_add = QtWidgets.QComboBox(self)
        combox_add.addItems(["legend", "layout", "details", "SLD"])
        self.setCellWidget(rowcount, 4, combox_add)

    def _removerow(self):
        if self.rowCount() > 0:
            self.removeRow(self.rowCount()-1)


def _saveConfig(form, table):
    # TODO - DRY this function
    read_file = open("config.yaml", "r")
    config = yaml.full_load(read_file.read())
    read_file.flush()
    read_file.close()

    # TODO - need to check safety of this as well similar to table
    config["meta"].update({
        "project name": form.itemAt(1).widget().text(),
        "project number": form.itemAt(3).widget().text(),
        "client": form.itemAt(5).widget().text(),
        "issue date": form.itemAt(7).widget().text(),
        "issue description": form.itemAt(9).widget().text(),
        "construction status": form.itemAt(11).widget().text(),
        "stamp": form.itemAt(13).widget().text(),
        "approved by": form.itemAt(15).widget().text(),
        "drawn by": form.itemAt(17).widget().text(),
        "rev": form.itemAt(19).widget().text()
    })

    for row in range(table.rowCount()):

        legal = re.compile(r"[<>/{}[\]\\~`]")
        if (not table.item(row, 0).text() or
                not table.item(row, 1).text() or
                not table.item(row, 2).text() or
                not table.item(row, 3).text() or
                legal.search(table.item(row, 0).text()) or
                legal.search(table.item(row, 1).text()) or
                legal.search(table.item(row, 2).text()) or
                legal.search(table.item(row, 3).text())
                ):
            _error("Data is empty or contains illegal characters")
            return

        config["drawings"].update({
            table.item(row, 0).text(): {
                "title": table.item(row, 1).text(),
                "scale": table.item(row, 2).text(),
                "discipline": table.item(row, 3).text(),
                "type": table.cellWidget(row, 4).currentText()
            }
        })
    with open(r'config.yaml', 'w') as file:
        file.write(r"%YAML 1.2")
        file.write("\n---\n")
        yaml.dump(config, file)


class Window(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        table = Table()
        tablehbox = QtWidgets.QHBoxLayout()
        formlayout = QtWidgets.QFormLayout()
        button_layout = QtWidgets.QVBoxLayout()

        add_button = QtWidgets.QPushButton("Add")
        add_button.clicked.connect(table._addrow)

        delete_button = QtWidgets.QPushButton("Delete")
        delete_button.clicked.connect(table._removerow)

        save_button = QtWidgets.QPushButton("Save Config")
        save_button.clicked.connect(lambda: _saveConfig(formlayout, table))

        run_button = QtWidgets.QPushButton("Run Setup")
        run_button.clicked.connect(populate_form_fields)

        button_layout.addWidget(
            add_button, alignment=QtCore.Qt.AlignmentFlag.AlignBottom)
        button_layout.addWidget(
            delete_button, alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        button_layout.addWidget(
            save_button, alignment=QtCore.Qt.AlignmentFlag.AlignBottom)
        button_layout.addWidget(
            run_button, alignment=QtCore.Qt.AlignmentFlag.AlignBottom)

        tablehbox.setContentsMargins(10, 10, 10, 10)
        tablehbox.addWidget(table)

        # TODO - move form to its own class and stop repeating this file read
        read_file = open("config.yaml", "r")
        config = yaml.full_load(read_file.read())
        read_file.flush()
        read_file.close()

        formlayout.addRow(QtWidgets.QLabel("Project name:"),
                          QtWidgets.QLineEdit(f'{config["meta"]["project name"]}'))
        formlayout.addRow(QtWidgets.QLabel("Project number:"),
                          QtWidgets.QLineEdit(f'{config["meta"]["project number"]}'))
        formlayout.addRow(QtWidgets.QLabel("Client:"),
                          QtWidgets.QLineEdit(f'{config["meta"]["client"]}'))
        formlayout.addRow(QtWidgets.QLabel("Issue date:"),
                          QtWidgets.QLineEdit(f'{config["meta"]["issue date"]}'))
        formlayout.addRow(QtWidgets.QLabel("Issue description:"),
                          QtWidgets.QLineEdit(f'{config["meta"]["issue description"]}'))
        formlayout.addRow(QtWidgets.QLabel("Construction status:"),
                          QtWidgets.QLineEdit(f'{config["meta"]["construction status"]}'))
        formlayout.addRow(QtWidgets.QLabel("Stamp:"),
                          QtWidgets.QLineEdit(f'{config["meta"]["stamp"]}'))
        formlayout.addRow(QtWidgets.QLabel("Approved by:"),
                          QtWidgets.QLineEdit(f'{config["meta"]["approved by"]}'))
        formlayout.addRow(QtWidgets.QLabel("Drawn by:"),
                          QtWidgets.QLineEdit(f'{config["meta"]["drawn by"]}'))
        formlayout.addRow(QtWidgets.QLabel("Rev:"),
                          QtWidgets.QLineEdit(f'{config["meta"]["rev"]}'))

        # TODO enforce validation using QSpinBox / QComboBox / etc.

        grid = QtWidgets.QGridLayout(self)
        self.resize(800, 550)
        grid.addLayout(formlayout, 0, 0)
        grid.addLayout(button_layout, 1, 1)
        grid.addLayout(tablehbox, 1, 0)


def _error(code):
    msg = QtWidgets.QMessageBox()
    msg.setWindowTitle("Error")
    msg.setText("Something went wrong: {0}".format(code))
    x = msg.exec_()


def copy_files():
    # Todo - split this functionality out of populate_form_fields
    pass


def populate_form_fields():

    # TODO - do I need to do this really?
    # Check for directory structure
    pattern = re.compile(
        r".*[0-9]+\\Project Documents\\Electrical\\Design\\Sketches.*")
    folder = __file__
    print(__file__)
    if (not pattern.match(folder)):
        _error("Not in correct folder structure. Place in sketches directory.")
        return
    if (not pathlib.Path("./config.yaml").exists()):
        _error("No config file exists")
        return

    read_file = open("config.yaml", "r")
    config = yaml.full_load(read_file.read())
    read_file.flush()
    read_file.close()

    # Todo combine source files into .dll or refer to Sharepoint site?

    # Copy pdfs
    mapping = {
        "legend": r"bin\config - Legend.pdf",
        "layout": r"bin\config - Layout.pdf",
        "details": r"bin\config - Details.pdf",
        "SLD": r"bin\config - SLD.pdf"
    }

    for drawing in (config["drawings"].items()):
        copyfile = mapping[drawing[1]["type"]]
        dest = "{0} - {1}_{2}.pdf".format(drawing[0],
                                          drawing[1]["title"], config["meta"]["rev"])

        config["drawings"][drawing[0]].update({
            "path": dest
        })

        if (not pathlib.Path(copyfile).exists()):
            _error("Can't find templates.")
            return
        if (pathlib.Path(dest).exists()):
            _error("Not allowed to overwrite files (yet)")
            return

        shutil.copyfile(copyfile, dest)

        # TODO - Check all files before copying any

    # Modify pdf form fields

    for drawing in (config["drawings"].items()):
        reader = PdfReader(drawing[1]["path"])
        writer = PdfWriter()

        page = reader.pages[0]

        writer.add_page(page)

        writer.update_page_form_field_values(
            writer.pages[0], {
                "PROJECT NUMBER": config["meta"]["project number"],
                "PROJECT NAME": config["meta"]["project name"],

                "SHEET NUMBER": drawing[0],
                "SHEET NAME": drawing[1]["title"],

                "SCALE": drawing[1]["scale"],
                "REVISION": config["meta"]["rev"],

                # "CLIENT": config["meta"]["revision"]["id"],  # TODO - form templates currently don't have clients

                "STAMP": config["meta"]["stamp"],
                "CONSTRUCTION STATUS": config["meta"]["construction status"],
                "DISCIPLINE": drawing[1]["discipline"],

                "REV1": config["meta"]["rev"],
                "DESCRIPTION1": config["meta"]["issue description"],
                "DRAWN1": config["meta"]["drawn by"],
                "APPROVED1": config["meta"]["approved by"],
                "DATE1": config["meta"]["issue date"]
            }
        )

        with open(drawing[1]["path"], "wb") as output_stream:
            writer.write(output_stream)

    # Summarize output


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.ColorRole.WindowText,
                     QtGui.QColorConstants.LightGray)
    palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(25, 25, 25))
    palette.setColor(QtGui.QPalette.ColorRole.AlternateBase,
                     QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase,
                     QtGui.QColorConstants.Black)
    palette.setColor(QtGui.QPalette.ColorRole.ToolTipText,
                     QtGui.QColorConstants.LightGray)
    palette.setColor(QtGui.QPalette.ColorRole.Text,
                     QtGui.QColorConstants.LightGray)
    palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.ColorRole.ButtonText,
                     QtGui.QColorConstants.LightGray)
    palette.setColor(QtGui.QPalette.ColorRole.BrightText,
                     QtGui.QColorConstants.Red)
    palette.setColor(QtGui.QPalette.ColorRole.Link, QtGui.QColor(42, 130, 218))
    palette.setColor(QtGui.QPalette.ColorRole.Highlight,
                     QtGui.QColor(42, 130, 218))
    palette.setColor(QtGui.QPalette.ColorRole.HighlightedText,
                     QtGui.QColorConstants.Black)
    app.setPalette(palette)

    w = Window()
    w.show()
    sys.exit(app.exec())
