# IMX219 Camera Calibration for Jetson Nano

Complete calibration workflow for the IMX219 camera module on Jetson Nano, achieving **0.052 pixel reprojection error** 
---

## Calibration Results

### Camera Matrix (Intrinsic Parameters)

[[641.21 0.00 323.35]
[ 0.00 852.57 224.79]
[ 0.00 0.00 1.00]]


### Distortion Coefficients

| Parameter | Type | Value |
|-----------|------|------|
| k1 | Radial | 0.1162 |
| k2 | Radial | 0.0961 |
| p1 | Tangential | -0.00545 |
| p2 | Tangential | 0.00191 |
| k3 | Radial (High Order) | -2.3726 |

**Reprojection Error:** `0.052 pixels`

---

# Getting Started

### Clone Repository

```bash
git clone https://github.com/yourusername/imx219-jetson-calibration
cd imx219-jetson-calibration
pip3 install -r requirements.txt



# Steps
1) Capture
 
python3 scripts/capture_calib_images.py
2) Calibrate

python3 scripts/calibrate.py
This will calibrate using jpg images and generate calibration.json
3) Roi Selector

python3 scripts/roi_selector.py
Since the undistorted images looks wraped, this script allows you to select ROI and save it roi_settings.json, which can be used later.

#  Requirement
1) Jetson nano
2) Imx219 camera sensor
3) Chess board pattern 9x6

This repo is based on work by : https://github.com/parlaynu/jetson-camcal 


