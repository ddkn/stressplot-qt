#! /usr/bin/env python3
# coding: utf-8
# -
# Copyright (c) 2021-2022, David Kalliecharan <dave@dal.ca>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the
#    distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE
#
# SPDX-License-Identifier: BSD-2-Clause

import sys

from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QFileDialog,
    QProgressBar,
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

from waterjetstress import WaterJetStress

COLOR = "C0"
CROSS_COLOR = "C1"

X_COLUMNS = ["Time (s)", "x (mm)"]

# Matplotlib configuration
mpl.use("Qt5Agg")
style.use("stressplot.mplstyle")


class MPLCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes = fig.add_subplot(111)
        super(MPLCanvas, self).__init__(fig)


class StressPlot(QMainWindow):
    def __init__(self):
        super(StressPlot, self).__init__()
        self.load_ui()

    def load_ui(self):
        loader = QUiLoader()
        path = Path(__file__).parent
        ui_file = QFile(str(path / "stressplot.ui"))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        self.fig_data = MPLCanvas(self, width=5, height=4, dpi=90)
        self.fig_data.axes.set_xlabel("Time (s)")
        self.toolbar_data = NavigationToolbar(self.fig_data, self)

        layout_data = QVBoxLayout()
        layout_data.addWidget(self.fig_data)
        layout_data.addWidget(self.toolbar_data)
        self.ui.wgt_data.setLayout(layout_data)

        self.ui.output_path.setText(str(Path.home()))

        self.ui.btn_save.setDisabled(True)

        self.ui.btn_file.clicked.connect(self.set_file)
        self.ui.btn_data_out.clicked.connect(self.select_output_path)
        self.ui.btn_save.clicked.connect(self.save_data)
        self.ui.btn_load.clicked.connect(self.analyze)
        self.ui.combo_xaxis.currentIndexChanged.connect(self.update_plot)
        self.ui.combo_yaxis.currentIndexChanged.connect(self.update_plot)

        self.setWindowIcon(QIcon(str(path / "assets/icon.svg")))
        self.setWindowTitle("StressPlot")
        self.setCentralWidget(self.ui.wgt_central)

    def set_file(self):
        filename = QFileDialog.getOpenFileName(
            self,
            caption=str("Open CSV File"),
            filter=str("CSV files (*.csv)"),
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

    def analyze(self):
        print("Loading data")
        input_file = Path(self.ui.filename.text())
        if not input_file.is_file():
            print("Please specify a file!")
            return

        vtr = self.ui.vtr.value()
        dia_app = self.ui.dia_app.value()
        self.stress = WaterJetStress(
            input_file, 
            vtr, 
            diameter_kws=dict(dia_app=dia_app, scaled=True)
        )

        # Create a cumulative sum of time from sample rate
        print(self.stress.df.head())

        self.ui.combo_xaxis.clear()
        self.ui.combo_yaxis.clear()
        
        self.ui.combo_xaxis.addItems(X_COLUMNS)
        self.ui.combo_yaxis.addItems(
            self.stress.df.columns.drop(X_COLUMNS).to_list()
        )

        self.ui.btn_save.setDisabled(False)
        self.update_plot()

    def save_data(self):
        input_file = Path(self.ui.filename.text())
        filename = input_file.name.lower().replace(".csv", "")

        vtr = self.ui.vtr.value()
        sd = self.ui.standoff_dist.value()
        dia = self.ui.dia_app.value()
        name = f"{filename}_vtr{vtr}_sd{sd}_dia{dia}"

        timestamp = pydt.now().strftime("%Y%b%d_%H:%M:%S:%f")
        output_name = f"{name}_{timestamp}.feather"

        output_path = Path(self.ui.output_path.text())
        output_file = output_path / output_name
        print(f"Saving {output_file}")
        self.stress.df.to_feather(output_file)

    def update_plot(self):
        xlabel = self.ui.combo_xaxis.currentText()
        if xlabel not in self.stress.df.columns:
            return
        ylabel = self.ui.combo_yaxis.currentText()
        if ylabel not in self.stress.df.columns:
            return

        print(f"Setting data to {xlabel} vs {ylabel}")
        self.span = None
        self.fig_data.axes.cla()

        self.stress.df.plot(
            x=xlabel,
            y=ylabel,
            color=COLOR,
            ax=self.fig_data.axes,
            legend=False,
        )
        
        idx = self.stress.get_feature_indices()
        xdata = self.stress.df[xlabel][idx["mid"]]
        ydata = self.stress.df[ylabel][idx["mid"]]
        
        xmin, xmax = self.fig_data.axes.get_xlim()
        ymin, ymax = self.fig_data.axes.get_ylim()
        self.fig_data.axes.hlines(0, xmin, xmax, color=CROSS_COLOR, linestyle="--")
        self.fig_data.axes.hlines(ydata, xmin, xmax, color=CROSS_COLOR, linestyle=":")
        self.fig_data.axes.vlines(xdata, ymin, ymax, color=CROSS_COLOR, linestyle=":")
        self.fig_data.axes.set_ylabel(ylabel)
        self.fig_data.axes.grid()
        xorigin = 0
        if xlabel == "x (mm)":
            xorigin = -28.0 
        self.fig_data.axes.annotate(
            f"{ydata:0.2f}", 
            (xorigin, ydata * 1.2), 
            color=CROSS_COLOR,
            fontsize="large",
        )
        
        pressure = self.ui.input_pressure.value()
        vtr = self.ui.vtr.value()
        sd = self.ui.standoff_dist.value()
        dia_app = self.ui.dia_app.value()
        title = f"{pressure:0.1f} kPSI - VTR: {vtr:0.1f} mm/s - SD: {sd} mm - $\\phi_{{\\rm app}}$ {dia_app:0.1f} mm"
        self.fig_data.axes.set_title(title)
        
        self.fig_data.draw()

        def span_select(xmin, xmax):
            x = self.stress.df["Time (s)"]
            idxmin, idxmax = np.searchsorted(x, (xmin, xmax))
            idxmax = min(x.shape[0] - 1, idxmax)
            x_min = x.iloc[idxmin]
            x_max = x.iloc[idxmax]

        self.span = SpanSelector(
            self.fig_data.axes,
            span_select,
            "horizontal",
            useblit=True,
            interactive=True,
            props=dict(alpha=0.5, facecolor="C2", edgecolor="C2"),
        )


if __name__ == "__main__":
    app = QApplication([])
    widget = StressPlot()
    widget.show()
    sys.exit(app.exec_())
