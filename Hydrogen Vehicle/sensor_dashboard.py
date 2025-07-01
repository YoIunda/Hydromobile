import sys
import serial
import re
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QComboBox, QLabel
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
import numpy as np

SERIAL_PORT = 'COM4'
BAUD_RATE = 9600

def gauge_gradient(frac):
    # Returns a blue-black gradient color
    r = int(30 + frac*20)
    g = int(144 + frac*40)
    b = int(255 - frac*80)
    return (r, g, b)

class AnalogGauge(pg.GraphicsLayoutWidget):
    def __init__(self, title, min_value, max_value, units, color):
        super().__init__()
        self.setBackground('#181c20')
        self.plot = self.addPlot()
        self.plot.hideAxis('bottom')
        self.plot.hideAxis('left')
        self.plot.setAspectLocked()
        self.title = title
        self.min_value = min_value
        self.max_value = max_value
        self.units = units
        self.color = color
        self.value = min_value
        self.needle = pg.PlotDataItem()
        self.plot.addItem(self.needle)
        # Title label (top center)
        self.title_label = pg.TextItem(self.title, anchor=(0.5, 1.0), color=self.color)
        self.title_label.setFont(pg.QtGui.QFont("Arial", 14, pg.QtGui.QFont.Bold))
        self.title_label.setPos(0, 0.7)
        self.plot.addItem(self.title_label)
        # Value label (centered, below title)
        self.value_label = pg.TextItem("--", anchor=(0.5, 1.0), color=self.color)
        self.value_label.setFont(pg.QtGui.QFont("Arial", 18, pg.QtGui.QFont.Bold))
        self.value_label.setPos(0, 0.5)
        self.plot.addItem(self.value_label)
        # Unit label (centered, below value)
        self.unit_label = pg.TextItem(self.units, anchor=(0.5, 1.0), color=self.color)
        self.unit_label.setFont(pg.QtGui.QFont("Arial", 14, pg.QtGui.QFont.Bold))
        self.unit_label.setPos(0, 0.35)
        self.plot.addItem(self.unit_label)
        self.draw_gauge()

    def draw_gauge(self):
        angle_span = 270
        radius = 1
        angles = np.linspace(-225, 45, 100)
        # Gradient effect for arc
        for i in range(len(angles)-1):
            frac = i / (len(angles)-1)
            color = pg.mkColor(*gauge_gradient(frac))
            self.plot.plot(
                [radius * np.cos(np.radians(angles[i])), radius * np.cos(np.radians(angles[i+1]))],
                [radius * np.sin(np.radians(angles[i])), radius * np.sin(np.radians(angles[i+1]))],
                pen=pg.mkPen(color, width=8)
            )
        for i in range(11):
            angle = -225 + i * (angle_span / 10)
            x1 = 0.85 * np.cos(np.radians(angle))
            y1 = 0.85 * np.sin(np.radians(angle))
            x2 = np.cos(np.radians(angle))
            y2 = np.sin(np.radians(angle))
            frac = i / 10
            tick_color = pg.mkColor(*gauge_gradient(frac), 40)  # Lower alpha for more transparency
            self.plot.plot([x1, x2], [y1, y2], pen=pg.mkPen(tick_color, width=3, style=Qt.DotLine))
        # Draw needle with current color
        self.set_value(self.value)

    def set_value(self, value):
        self.value = float(value)
        self.needle.setData([], [])
        angle = -225 + 270 * (self.value - self.min_value) / (self.max_value - self.min_value)
        # Needle as a polygon: wide at base, thin at tip
        base_width = 0.10  # Large diameter at base
        tip_width = 0.03   # Small diameter at tip
        length = 0.7
        # Calculate points for a simple needle polygon
        x0 = 0
        y0 = 0
        x1 = (length - 0.05) * np.cos(np.radians(angle + 90)) * base_width
        y1 = (length - 0.05) * np.sin(np.radians(angle + 90)) * base_width
        x2 = length * np.cos(np.radians(angle))
        y2 = length * np.sin(np.radians(angle))
        x3 = (length - 0.05) * np.cos(np.radians(angle - 90)) * base_width
        y3 = (length - 0.05) * np.sin(np.radians(angle - 90)) * base_width
        # Polygon points: base left, tip, base right, back to base left
        needle_poly = np.array([[x0 + x1, y0 + y1], [x2, y2], [x0 + x3, y0 + y3], [x0, y0]])
        # Remove previous needle if any
        if hasattr(self, 'needle_item') and self.needle_item in self.plot.items:
            self.plot.removeItem(self.needle_item)
        self.needle_item = pg.PlotDataItem()
        self.plot.addItem(self.needle_item)
        self.needle_item.setData(needle_poly[:,0], needle_poly[:,1], pen=pg.mkPen(self.color, width=2), fillLevel=0, brush=pg.mkBrush(self.color))
        # Gradient color for value text
        frac = min(max((self.value - self.min_value) / (self.max_value - self.min_value), 0), 1)
        color = pg.mkColor(*gauge_gradient(frac))
        self.value_label.setColor(color)
        self.value_label.setText(f"{self.value:.2f}")

class SensorDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hydrogen Vehicle Dashboard")
        self.setStyleSheet("background: #181c20; color: #eeeeee;")
        self.setGeometry(50, 50, 1024, 600)
        # Gradient selection UI
        self.gradient_selector = QComboBox()
        self.gradient_selector.addItems(["Blue-Black", "Red-Orange", "Green-Yellow", "Purple-Pink"])  # Add more as desired
        self.gradient_selector.currentIndexChanged.connect(self.change_gradient)
        self.gradient_label = QLabel("Gauge Gradient:")
        self.gradient_label.setStyleSheet("color: #eeeeee; font-size: 16px; margin-right: 10px;")
        # Gauges
        self.temp_gauge = AnalogGauge("Temperature", 0, 100, "°C", "#1e90ff")
        self.h2_gauge = AnalogGauge("Hydrogen", 0, 100, "ppm", "#1e90ff")
        self.speed_gauge = AnalogGauge("Speed", 0, 200, "km/h", "#1e90ff")
        hbox = QHBoxLayout()
        hbox.addWidget(self.temp_gauge)
        hbox.addWidget(self.h2_gauge)
        hbox.addWidget(self.speed_gauge)
        # Top bar for gradient selection
        topbar = QHBoxLayout()
        topbar.addWidget(self.gradient_label)
        topbar.addWidget(self.gradient_selector)
        topbar.addStretch()
        vbox = QVBoxLayout(self)
        vbox.addLayout(topbar)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        self.serial = None
        try:
            self.serial = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        except Exception as e:
            self.temp_gauge.value_label.setText(f"Serial error: {e}")
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_serial)
        self.timer.start(500)

    def change_gradient(self, idx):
        gradients = [
            lambda frac: (int(30 + frac*20), int(144 + frac*40), int(255 - frac*80)),  # Blue-Black
            lambda frac: (255, int(100+frac*100), int(30+frac*30)),                   # Red-Orange
            lambda frac: (int(50+frac*100), 255, int(50+frac*50)),                    # Green-Yellow
            lambda frac: (int(150+frac*80), int(50+frac*100), 255)                    # Purple-Pink
        ]
        colors = ['#1e90ff', '#ff6600', '#66ff33', '#cc66ff']
        global gauge_gradient
        gauge_gradient = gradients[idx]
        # Update gauge colors to match gradient
        for gauge, color in zip([self.temp_gauge, self.h2_gauge, self.speed_gauge], [colors[idx]]*3):
            gauge.color = color
            gauge.title_label.setColor(color)
            gauge.value_label.setColor(color)
            gauge.unit_label.setColor(color)
            gauge.plot.clear()
            gauge.needle = pg.PlotDataItem()
            gauge.plot.addItem(gauge.needle)
            gauge.plot.addItem(gauge.title_label)
            gauge.plot.addItem(gauge.value_label)
            gauge.plot.addItem(gauge.unit_label)
            gauge.draw_gauge()
            gauge.set_value(gauge.value)

    def read_serial(self):
        if self.serial and self.serial.in_waiting:
            try:
                line = self.serial.readline().decode(errors='ignore').strip()
                m_temp = re.match(r"C = ([\d.]+)", line)
                if m_temp:
                    temp = m_temp.group(1)
                    self.temp_gauge.set_value(temp)
                m_h2 = re.match(r"\| Hydrogen Estimate \(ppm\): (\d+)", line)
                if m_h2:
                    h2ppm = m_h2.group(1)
                    self.h2_gauge.set_value(h2ppm)
                m_speed = re.match(r"(\d+) km/h", line)
                if m_speed:
                    speed = m_speed.group(1)
                    self.speed_gauge.set_value(speed)
            except Exception as e:
                self.temp_gauge.value_label.setText(f"Read error: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    screens = app.screens()
    if len(screens) > 1:
        screen = screens[1]
        geometry = screen.geometry()
        win = SensorDashboard()
        win.setGeometry(geometry)
        win.showFullScreen()
    else:
        win = SensorDashboard()
        win.showFullScreen()
    sys.exit(app.exec_())
