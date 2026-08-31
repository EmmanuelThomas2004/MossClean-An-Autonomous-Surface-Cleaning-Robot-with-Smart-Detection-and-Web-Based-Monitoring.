# MossClean AI Detection

## Overview

MossClean uses edge-based computer vision to identify moss on target surfaces.

The vision pipeline combines:

- OV5647 camera
- OpenCV
- YOLOv11n
- Raspberry Pi edge processing

## Detection Pipeline

```text
Camera Frame
     ↓
Image Capture
     ↓
OpenCV Processing
     ↓
YOLOv11n Inference
     ↓
Confidence Filtering
     ↓
Moss Detection
     ↓
Annotated Detection Image
     ↓
Cleaning/Spray Decision
odel

The project uses YOLOv11n, a lightweight object-detection model intended for edge deployment.

The configured live detection confidence threshold is:

0.60

Inference images are configured at:

640 × 640
Reported Validation

The project documentation reports:

Metric	Result
Precision	64.6%
Recall	56.9%
mAP@50	58.8%

The reported Raspberry Pi inference time is approximately 130–160 ms per frame.

These values represent the project's proof-of-concept validation results.

Detection and Cleaning

When a valid moss detection is obtained, the MossController handles the camera and cleaning sequence.

The robot can:

Capture a frame.
Run YOLO inference.
Check the detection confidence.
Save an annotated detection image.
Stop the robot.
Activate the cleaning pump.
Complete the spray duration.
Resume autonomous operation.
Edge AI Design

Processing the detection pipeline locally on the Raspberry Pi reduces dependence on a remote AI server and allows the robot to make detection decisions at the edge.

Future Improvements

Potential improvements include:

Larger and more diverse moss datasets
Additional environmental conditions
Model quantization
TensorRT/ONNX optimization
Improved precision and recall
Density-based spray control
Better low-light detection
