#! /usr/bin/env python3
# coding: utf-8
import sys

from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QFileDialog,
)
from PySide2.QtCore import QFile
from PySide2.QtGui import QIcon
from PySide2.QtUiTools import QUiLoader
from datetime import datetime as pydt
import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg,
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from matplotlib.pyplot import style
from matplotlib.widgets import SpanSelector
import numpy as np
from pandas import DataFrame
from pathlib import Path
from scipy.fft import fft, fftfreq
from bin2data import read_bin

COLOR = "C1"
ADC_COUNT_MAX = 4096  # Count
VOLTAGE_MAX = 3.3  # V
COUNTS_TO_VOLTS = VOLTAGE_MAX / ADC_COUNT_MAX  # V / Count
SAMPLE_RATE_KHZ_DFLT = 180  # 180 kHz
RG_OPTIONS = [50, 75, 100, 150, 300, 500, 750, 1000]
RG_DEFAULT_INDEX = 1

# Matplotlib configuration
mpl.use("Qt5Agg")
style.use("pwjplot.mplstyle")


class MPLCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes = fig.add_subplot(111)
        super(MPLCanvas, self).__init__(fig)


class PWJPlot(QMainWindow):
    df: DataFrame = DataFrame()
    df_fft: DataFrame = DataFrame()

    def __init__(self):
        super(PWJPlot, self).__init__()
        self.load_ui()

    def load_ui(self):
        loader = QUiLoader()
        path = Path(__file__).parent
        ui_file = QFile(str(path / "pwjplot.ui"))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        self.fig_raw = MPLCanvas(self, width=5, height=4, dpi=100)
        self.fig_raw.axes.set_xlabel("Time (s)")
        self.toolbar_raw = NavigationToolbar(self.fig_raw, self)

        layout_raw = QVBoxLayout()
        layout_raw.addWidget(self.fig_raw)
        layout_raw.addWidget(self.toolbar_raw)
        self.ui.wgt_raw.setLayout(layout_raw)

        self.fig_fft = MPLCanvas(self, width=5, height=4, dpi=100)
        self.fig_fft.axes.set_xlabel("Frequency (kHz)")
        self.toolbar_fft = NavigationToolbar(self.fig_fft, self)

        layout_fft = QVBoxLayout()
        layout_fft.addWidget(self.fig_fft)
        layout_fft.addWidget(self.toolbar_fft)
        self.ui.wgt_fft.setLayout(layout_fft)

        self.ui.gain_resistor.addItems([str(r) for r in RG_OPTIONS])
        self.ui.gain_resistor.setCurrentIndex(RG_DEFAULT_INDEX)
        self.ui.combo_fft_scale.addItems(["Linear", "Log"])
        self.ui.output_path.setText(str(Path.home()))

        self.ui.btn_fft.setDisabled(True)
        self.ui.btn_save.setDisabled(True)

        self.ui.btn_file.clicked.connect(self.set_file)
        self.ui.btn_data_out.clicked.connect(self.select_output_path)
        self.ui.btn_save.clicked.connect(self.save_data)
        self.ui.btn_load.clicked.connect(self.load_dataframe)
        self.ui.btn_fft.clicked.connect(self.calculate_fft)
        self.ui.combo_data.currentIndexChanged.connect(self.change_ydata)
        self.ui.combo_fft_scale.currentIndexChanged.connect(self.set_fft_scale)

        self.setWindowIcon(QIcon(str(path / "assets/icon.svg")))
        self.setWindowTitle("PWJPlot")
        self.setCentralWidget(self.ui.wgt_central)

    def set_fft_scale(self):
        scale = self.ui.combo_fft_scale.currentText().lower()
        print(f"Setting FFT y scale to {scale}")
        self.fig_fft.axes.set_yscale(f"{scale}")
        self.fig_fft.draw()

    def set_file(self):
        filename = QFileDialog.getOpenFileName(
            self,
            caption=str("Open Binary File"),
            filter=str("Binary files (*.bin, *.BIN)"),
        )
        print(f"Setting filename: {filename[0]}")

        self.ui.filename.setText(filename[0])

    def select_output_path(self):
        output_path = QFileDialog.getExistingDirectory(
            self,
            caption=str("Select output directory"),
            dir=str(Path.home()),
            options=QFileDialog.ShowDirsOnly,
        )
        if output_path == "":
            return

        print(f"Setting output path: {output_path}")

        self.ui.output_path.setText(output_path)

    def load_dataframe(self):
        print("Loading data")
        input_file = Path(self.ui.filename.text())
        if not input_file.is_file():
            print("Please specify a file!")
            return
        x = read_bin(input_file)

        # Create a cumulative sum of time from sample rate
        self.sample_rate_hz = self.ui.sample_rate_khz.value() * 1e3
        dt = 1 / self.sample_rate_hz
        t = np.ones(x.shape)
        t[0] = 0.0
        t = np.cumsum(t * dt)

        data = {
            "Time (s)":       t,
            "ADC value":      x,
            "Voltage (V)":    x * COUNTS_TO_VOLTS,
            "Pressure (MPa)": x,
        }

        self.df = DataFrame.from_dict(data)
        print(self.df.head())

        self.ui.combo_data.clear()
        self.ui.combo_data.addItems(
            self.df.drop("Time (s)", axis=1).columns.to_list()
        )

        self.fig_fft.axes.cla()
        self.fig_fft.draw()
        self.df_fft = DataFrame()

        self.ui.fft_start.setValue(self.df["Time (s)"].min())
        self.ui.fft_end.setValue(self.df["Time (s)"].max())

        self.ui.btn_fft.setDisabled(False)
        self.ui.btn_save.setDisabled(False)

    def save_data(self):
        input_file = Path(self.ui.filename.text())
        filename = input_file.name.lower().replace(".bin", "")

        rod_id = self.ui.rod_id.value()
        gain_resistor = self.ui.gain_resistor.currentText().lower()
        sample_rate = self.ui.sample_rate_khz.value()
        name = f"{filename}_r{rod_id}_rg{gain_resistor}_{sample_rate}khz"

        timestamp = pydt.now().strftime("%Y%b%d_%H:%M:%S:%f")
        output_name = f"{name}_{timestamp}.feather"

        output_path = Path(self.ui.output_path.text())
        output_file = output_path / output_name
        print(f"Saving {output_file}")
        self.df.to_feather(output_file)

        if self.df_fft.shape[0] > 0:
            output_fft_name = f"{name}_{timestamp}_fft.feather"
            output_file = output_path / output_fft_name
            print(f"Saving {output_file}")
            self.df_fft.to_feather(output_file)

    def change_ydata(self):
        col = self.ui.combo_data.currentText()
        if col not in self.df.columns.to_list():
            return

        print(f"Setting ydata to {col}")
        self.span = None
        self.fig_raw.axes.cla()

        self.df.plot(
            x="Time (s)",
            y=col,
            color=COLOR,
            ax=self.fig_raw.axes,
            legend=False,
        )
        self.fig_raw.axes.set_ylabel(col)
        self.fig_raw.draw()

        def span_select(xmin, xmax):
            x = self.df["Time (s)"]
            idxmin, idxmax = np.searchsorted(x, (xmin, xmax))
            idxmax = min(x.shape[0] - 1, idxmax)
            x_min = x.iloc[idxmin]
            x_max = x.iloc[idxmax]
            self.ui.fft_start.setValue(x_min)
            self.ui.fft_end.setValue(x_max)

        self.span = SpanSelector(
            self.fig_raw.axes,
            span_select,
            "horizontal",
            useblit=True,
            interactive=True,
            props=dict(alpha=0.5, facecolor="C2", edgecolor="C2"),
        )

    def calculate_fft(self):
        print("Calculating FFT")
        self.fig_fft.axes.cla()

        x_min = self.ui.fft_start.value()
        x_max = self.ui.fft_end.value()

        # Generate mask within specified time range
        mask = self.df["Time (s)"] > x_min
        mask &= self.df["Time (s)"] < x_max

        x = self.df["ADC value"][mask]
        t = self.df["Time (s)"][mask]
        dt = t.diff().iloc[-1]

        X = fft(x)
        X = np.abs(X)
        f = fftfreq(X.size, dt)

        data = {"Frequency (kHz)": f / 1e3, "FFT(ADC value)": X}
        self.df_fft = DataFrame.from_dict(data)

        self.fig_fft.axes.vlines(
            x=self.df_fft["Frequency (kHz)"],
            ymin=0,
            ymax=self.df_fft["FFT(ADC value)"],
            color=COLOR,
        )
        self.df_fft.plot(
            x="Frequency (kHz)",
            y="FFT(ADC value)",
            color=COLOR,
            marker="o",
            linestyle="none",
            markerfacecolor="white",
            ax=self.fig_fft.axes,
            legend=False,
        )
        self.set_fft_scale()
        self.fig_fft.axes.set_ylabel("FFT(ADC value)")
        self.fig_fft.draw()


if __name__ == "__main__":
    app = QApplication([])
    widget = PWJPlot()
    widget.show()
    sys.exit(app.exec_())
