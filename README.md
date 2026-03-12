# IMX219 Camera Calibration for Jetson Nano

Complete calibration workflow for the IMX219 camera module on Jetson Nano, achieving **0.052 pixel reprojection error** 

## Calibration Results
Camera Matrix (Intrinsic Parameters):
[[641.21 0. 323.35]
[ 0. 852.57 224.79]
[ 0. 0. 1. ]]

Distortion Coefficients:
k1 = 0.1162 (radial)
k2 = 0.0961 (radial)
p1 = -0.00545 (tangential)
p2 = 0.00191 (tangential)
k3 = -2.3726 (radial - high order)

Reprojection Error: 0.052 pixels

##  Start

```bash
# Clone and install
git clone https://github.com/yourusername/imx219-jetson-calibration
cd imx219-jetson-calibration
pip3 install -r requirements.txt

# Test live calibration
python3 scripts/test_calib_vid.py

## Steps
1) Capture
```bash
python3 scripts/capture_calib_images.py
2) Calibrate
```bash
python3 scripts/calibrate.py
This will calibrate using jpg images and generate calibration.json
3) Roi Selector
```bash
python3 scripts/roi_selector.py
Since the undistorted images looks wraped, this script allows you to select ROI and save it roi_settings.json, which can be used later.

##  Requirement
1) Jetson nano
2) Imx219 camera sensor
3) Chess board pattern 9x6

This repo is based on work by : https://github.com/parlaynu/jetson-camcal 


