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
