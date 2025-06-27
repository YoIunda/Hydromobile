import sys
import serial
import re
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame
from PyQt5.QtGui import QFont, QColor, QPalette, QPixmap
from PyQt5.QtCore import Qt, QTimer

SERIAL_PORT = 'COM4'  # Change this to your Arduino's port
BAUD_RATE = 9600

class DashboardCard(QFrame):
    def __init__(self, title, value, unit, color):
        super().__init__()
        self.setObjectName("card")
        self.setStyleSheet(f"""
            QFrame#card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #232526, stop:1 #414345);
                border-radius: 30px;
                border: 2px solid {color};
                min-width: 250px;
                min-height: 180px;
            }}
        """)
        vbox = QVBoxLayout(self)
        self.title = QLabel(title)
        self.title.setFont(QFont("Arial", 20, QFont.Bold))
        self.title.setStyleSheet(f"color: {color};")
        self.title.setAlignment(Qt.AlignCenter)
        self.value = QLabel(value)
        self.value.setFont(QFont("Arial", 48, QFont.Bold))
        self.value.setStyleSheet(f"color: {color};")
        self.value.setAlignment(Qt.AlignCenter)
        self.unit = QLabel(unit)
        self.unit.setFont(QFont("Arial", 20))
        self.unit.setStyleSheet("color: #eeeeee;")
        self.unit.setAlignment(Qt.AlignCenter)
        vbox.addWidget(self.title)
        vbox.addWidget(self.value)
        vbox.addWidget(self.unit)
        vbox.addStretch()

    def set_value(self, value):
        self.value.setText(value)

class SensorDisplay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hydrogen Vehicle Dashboard")
        self.setGeometry(50, 50, 1024, 600)
        self.setStyleSheet("background: qradialgradient(cx:0.5, cy:0.5, radius:1, fx:0.5, fy:0.5, stop:0 #393e46, stop:1 #222831);")

        # Logo (optional, comment out if not needed)
        # logo = QLabel()
        # logo.setPixmap(QPixmap("car_logo.png").scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        # logo.setAlignment(Qt.AlignCenter)

        # Cards
        self.temp_card = DashboardCard("Temperature", "--", "°C", "#f8b400")
        self.h2_card = DashboardCard("Hydrogen", "--", "ppm", "#ff6363")
        self.ratio_card = DashboardCard("Sensor Ratio", "--", "", "#00adb5")

        # Layout
        hbox = QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(self.temp_card)
        hbox.addSpacing(30)
        hbox.addWidget(self.h2_card)
        hbox.addSpacing(30)
        hbox.addWidget(self.ratio_card)
        hbox.addStretch()

        vbox = QVBoxLayout(self)
        # vbox.addWidget(logo)
        vbox.addSpacing(30)
        vbox.addLayout(hbox)
        vbox.addStretch()
        self.setLayout(vbox)

        self.serial = None
        try:
            self.serial = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        except Exception as e:
            self.temp_card.set_value(f"Serial error")
            self.h2_card.set_value("")
            self.ratio_card.set_value(str(e))

        self.timer = QTimer()
        self.timer.timeout.connect(self.read_serial)
        self.timer.start(500)

    def read_serial(self):
        if self.serial and self.serial.in_waiting:
            try:
                line = self.serial.readline().decode(errors='ignore').strip()
                m_temp = re.match(r"C = ([\d.]+)", line)
                if m_temp:
                    temp = m_temp.group(1)
                    self.temp_card.set_value(temp)
                m_h2 = re.match(r"\| Sensor Ratio \(RS/R0\): ([\d.]+) \| Hydrogen Estimate \(ppm\): (\d+)", line)
                if m_h2:
                    ratio = m_h2.group(1)
                    h2ppm = m_h2.group(2)
                    self.ratio_card.set_value(ratio)
                    self.h2_card.set_value(h2ppm)
            except Exception as e:
                self.temp_card.set_value("Read error")
                self.h2_card.set_value("")
                self.ratio_card.set_value(str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    screens = app.screens()
    if len(screens) > 1:
        # Display 2 (index 1)
        screen = screens[1]
        geometry = screen.geometry()
        win = SensorDisplay()
        win.setGeometry(geometry)
        win.showFullScreen()
    else:
        win = SensorDisplay()
        win.showFullScreen()
    sys.exit(app.exec_())
