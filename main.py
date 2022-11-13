# This Python file uses the following encoding: utf-8
import sys
import os


from PySide2.QtWidgets import (
    QApplication, 
    QMainWindow,
    QVBoxLayout,
    QWidget
)
from PySide2.QtCore import QFile
from PySide2.QtUiTools import QUiLoader

import matplotlib as mpl

mpl.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
)
from matplotlib.figure import Figure


class MPLCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes = fig.add_subplot(111)
        super(MPLCanvas, self).__init__(fig)


class PWJPlot(QMainWindow):
    def __init__(self):
        super(PWJPlot, self).__init__()
        self.load_ui()


    def load_ui(self):
        loader = QUiLoader()
        path = os.path.join(os.path.dirname(__file__), "pwjplot.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        ui = loader.load(ui_file, self)
        ui_file.close()

        self.fig_raw = MPLCanvas(self, width=5, height=4, dpi=100)
        self.fig_raw.axes.set_xlabel("Time (s)")
        self.toolbar_raw = NavigationToolbar(self.fig_raw, self)
        
        layout_raw = QVBoxLayout()
        layout_raw.addWidget(self.fig_raw)
        layout_raw.addWidget(self.toolbar_raw)
        ui.wgt_raw.setLayout(layout_raw)
        
        self.fig_fft = MPLCanvas(self, width=5, height=4, dpi=100)
        self.fig_fft.axes.set_xlabel("Frequency (kHz)")
        self.toolbar_fft = NavigationToolbar(self.fig_fft, self)

        layout_fft = QVBoxLayout()
        layout_fft.addWidget(self.fig_fft)
        layout_fft.addWidget(self.toolbar_fft)
        ui.wgt_fft.setLayout(layout_fft)
        
        self.setCentralWidget(ui.wgt_central)


if __name__ == "__main__":
    app = QApplication([])
    widget = PWJPlot()
    widget.show()
    sys.exit(app.exec_())
