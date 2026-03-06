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

    def save(self):
        cursor = self.conn.cursor()
        try:
            if self.row is None:
                columns = []
                values = []
                for (col, (widget, pk)), col_info in zip(self.widgets.items(), self.columns):
                    if pk and widget.isEnabled() is False and self._is_integer(col_info[2]):
                        continue
                    columns.append(col)
                    values.append(self._get_widget_value(widget))
                placeholders = ", ".join(["?"] * len(columns))
                sql = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                cursor.execute(sql, values)
            else:
                set_parts = []
                values = []
                where_parts = []
                where_values = []
                for index, col_info in enumerate(self.columns):
                    _cid, col_name, col_type, _notnull, _default, pk = col_info
                    widget, _ = self.widgets[col_name]
                    if pk:
                        where_parts.append(f"{col_name}=?")
                        where_values.append(self.row[index])
                    else:
                        set_parts.append(f"{col_name}=?")
                        values.append(self._get_widget_value(widget))
                sql = f"UPDATE {self.table_name} SET {', '.join(set_parts)} WHERE {' AND '.join(where_parts)}"
                cursor.execute(sql, values + where_values)
            self.conn.commit()
        except sqlite3.Error as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {exc}", QMessageBox.Ok)
            return
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.conn = connect_db()
        self.table_name = None
        self.table_columns = []
        self.table_rows = []

        self._setup_table()
        self._set_logo()
        self._connect_actions()
        self._load_tables()

    def closeEvent(self, event):
        try:
            self.conn.close()
        finally:
            super().closeEvent(event)

    def _setup_table(self):
        table = self.ui.tableData
        table.setIconSize(QSize(90, 90))
        table.setColumnWidth(0, 120)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.verticalHeader().setDefaultSectionSize(100)

    def _set_logo(self):
        logo_path = IMAGES_DIR / "perfumery_01.png"
        if logo_path.exists():
            self.ui.labelLogo.setPixmap(QPixmap(str(logo_path)))
            self.setWindowIcon(QIcon(str(logo_path)))

    def _connect_actions(self):
        self.ui.cbTables.currentTextChanged.connect(self.select_table)
        self.ui.btnAdd.clicked.connect(self.add_record)
        self.ui.btnEdit.clicked.connect(self.edit_record)
        self.ui.btnDelete.clicked.connect(self.delete_record)
        self.ui.tableData.cellDoubleClicked.connect(lambda _r, _c: self.edit_record())

    def _load_tables(self):
        self.ui.cbTables.blockSignals(True)
        self.ui.cbTables.clear()
        tables = list_tables(self.conn)
        self.ui.cbTables.addItems(tables)
        self.ui.cbTables.blockSignals(False)
        if tables:
            self.select_table(tables[0])

    def select_table(self, table_name):
        if not table_name:
            return
        self.table_name = table_name
        self.table_columns = table_info(self.conn, table_name)
        self.refresh_table()

    def refresh_table(self):
        if not self.table_name:
            return
        self.table_rows = fetch_rows(self.conn, self.table_name)
        self._render_table()

    def _render_table(self):
        table = self.ui.tableData
        table.setRowCount(len(self.table_rows))
        for row_index, row in enumerate(self.table_rows):
            item_id = QTableWidgetItem()
            if len(row) > 0:
                item_id.setText(str(row[0]))
            table.setItem(row_index, 0, item_id)

            parts = []
            for col_info, value in zip(self.table_columns, row):
                name = col_info[1]
                text_value = "" if value is None else str(value)
                parts.append(f"<b>{name}</b>: {text_value}")
            label = QLabel("<br>".join(parts))
            label.setTextFormat(Qt.RichText)
            label.setWordWrap(True)
            table.setCellWidget(row_index, 1, label)

    def _current_row(self):
        row_index = self.ui.tableData.currentRow()
        if row_index < 0 or row_index >= len(self.table_rows):
            return None
        return self.table_rows[row_index]

    def add_record(self):
        if not self.table_name:
            return
        dialog = RecordDialog(self.conn, self.table_name, self.table_columns, None, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_table()

    def edit_record(self):
        row = self._current_row()
        if row is None:
            QMessageBox.information(self, "Информация", "Выберите запись.", QMessageBox.Ok)
            return
        dialog = RecordDialog(self.conn, self.table_name, self.table_columns, row, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_table()

    def delete_record(self):
        row = self._current_row()
        if row is None:
            QMessageBox.information(self, "Информация", "Выберите запись.", QMessageBox.Ok)
            return
        cursor = self.conn.cursor()
        pk_columns = [c for c in self.table_columns if c[5] == 1]
        where_parts = []
        values = []
        if pk_columns:
            for col in pk_columns:
                index = col[0]
                where_parts.append(f"{col[1]}=?")
                values.append(row[index])
        else:
            for index, col in enumerate(self.table_columns):
                where_parts.append(f"{col[1]}=?")
                values.append(row[index])
        sql = f"DELETE FROM {self.table_name} WHERE {' AND '.join(where_parts)}"
        try:
            cursor.execute(sql, values)
            self.conn.commit()
            self.refresh_table()
        except sqlite3.Error as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить: {exc}", QMessageBox.Ok)
