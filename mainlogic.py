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
