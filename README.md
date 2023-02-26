# StressPlot-qt

A tool for rapidly analyzing data collected from the PWJ Strain Logger. Data traverses over the cylindrical cross-sectional area, giving a unique force pattern. The center determines the *true* applied force. The traverse is required due to the turbulance and complex fluid dynamics of ultrasonic water jets, otherwise, the applied force is lower than anticipated and out of the operational procedures of the technology. In applications of shot peening -- via sand blasting -- this is not required.

## Requirements

* matplotlib
* waterjetstress
* numpy
* pandas
* pyarrow
* PySide2
* scipy
* Qt5

## Run

```
cd <PATH_TO_PROJECT>
python3 main.py
```
