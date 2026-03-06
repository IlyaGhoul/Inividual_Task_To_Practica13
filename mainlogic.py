import os
import sqlite3
import sys
from pathlib import Path

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QDoubleSpinBox,
    QTableWidgetItem,
)

from main_ui import Ui_MainWindow
from record_ui import Ui_RecordDialog

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "БД" / "parfumery.db"
IMAGES_DIR = BASE_DIR / "БД" / "perfumery_images"


def connect_db():
    return sqlite3.connect(str(DB_PATH))


def list_tables(conn):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    )
    return [row[0] for row in cursor.fetchall()]


def table_info(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()


def fetch_rows(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    return cursor.fetchall()


class RecordDialog(QDialog):
    def __init__(self, conn, table_name, columns, row=None, parent=None):
        super().__init__(parent)
        self.ui = Ui_RecordDialog()
        self.ui.setupUi(self)
        self.conn = conn
        self.table_name = table_name
        self.columns = columns
        self.row = row
        self.widgets = {}

        self.ui.buttonBox.accepted.connect(self.save)
        self.ui.buttonBox.rejected.connect(self.reject)

        self._build_form()

    def _build_form(self):
        for index, col in enumerate(self.columns):
            _cid, name, col_type, _notnull, _default, pk = col
            widget = self._create_widget(col_type)
            self.widgets[name] = (widget, pk)
            self.ui.formLayout.addRow(name, widget)

            if self.row is not None:
                self._set_widget_value(widget, self.row[index])
                if pk:
                    widget.setEnabled(False)
            else:
                if pk and self._is_integer(col_type):
                    widget.setEnabled(False)

    def _create_widget(self, col_type):
        if self._is_integer(col_type):
            widget = QSpinBox()
            widget.setMaximum(10**9)
            return widget
        if self._is_real(col_type):
            widget = QDoubleSpinBox()
            widget.setMaximum(10**9)
            widget.setDecimals(2)
            return widget
        return QLineEdit()

    def _set_widget_value(self, widget, value):
        if isinstance(widget, QSpinBox):
            widget.setValue(int(value or 0))
        elif isinstance(widget, QDoubleSpinBox):
            widget.setValue(float(value or 0))
        elif isinstance(widget, QLineEdit):
            widget.setText("" if value is None else str(value))

    def _get_widget_value(self, widget):
        if isinstance(widget, QSpinBox):
            return int(widget.value())
        if isinstance(widget, QDoubleSpinBox):
            return float(widget.value())
        return widget.text().strip()

    @staticmethod
    def _is_integer(col_type):
        return "INT" in (col_type or "").upper()

    @staticmethod
    def _is_real(col_type):
        t = (col_type or "").upper()
        return "REAL" in t or "FLOA" in t or "DOUB" in t
