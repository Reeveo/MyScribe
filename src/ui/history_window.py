from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QApplication, QHeaderView
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QColor, QFont
from src.utils import db

class HistoryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyScribe - History")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                gridline-color: #F0F0F0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 10pt;
            }
            QHeaderView::section {
                background-color: #F7F7F7;
                padding: 4px;
                border: 1px solid #E0E0E0;
                font-weight: bold;
            }
            QTableWidgetItem {
                padding: 5px;
            }
            QPushButton {
                background-color: #F0F0F0;
                border: 1px solid #D0D0D0;
                border-radius: 4px;
                padding: 5px 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
            QPushButton:pressed {
                background-color: #D0D0D0;
            }
        """)

        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Table for transcriptions
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Transcription", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self.populate_history()

    def populate_history(self):
        self.table.setRowCount(0) # Clear existing rows
        transcriptions = db.fetch_all_transcriptions()
        for row_num, row_data in enumerate(transcriptions):
            self.table.insertRow(row_num)
            
            # Timestamp
            timestamp_item = QTableWidgetItem(row_data[2])
            timestamp_item.setFlags(timestamp_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_num, 0, timestamp_item)

            # Transcription
            transcription_item = QTableWidgetItem(row_data[3])
            transcription_item.setFlags(transcription_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_num, 1, transcription_item)

            # Copy button
            copy_button = QPushButton("Copy")
            copy_button.clicked.connect(lambda checked, text=row_data[3]: self.copy_to_clipboard(text))
            self.table.setCellWidget(row_num, 2, copy_button)

    def copy_to_clipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)