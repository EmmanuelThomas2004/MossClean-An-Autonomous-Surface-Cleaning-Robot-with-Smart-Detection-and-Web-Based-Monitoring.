# MossClean Hardware

## Overview

MossClean combines a Raspberry Pi-based computing platform with sensors, motor control, computer vision, and a cleaning system.

## Main Components

| Component | Purpose |
|---|---|
| Raspberry Pi 4 Model B (4 GB) | Main edge computer |
| OV5647 5 MP Camera | Image capture and moss detection |
| HC-SR04 ×4 | Obstacle and distance sensing |
| LM393 Optical Encoders | Wheel odometry |
| MPU-6050 | Orientation and motion sensing |
| L298N | DC motor driver |
| DC Gear Motors | Robot movement |
| 12 V Diaphragm Pump | Cleaning solution delivery |
| Relay Module | Pump switching |
| 3S Li-Ion Battery Pack | Main power source |
| LM2596 Buck Converter | Voltage regulation |

## Computing

The Raspberry Pi performs:

- Sensor processing
- Robot-state management
- Navigation
- Computer vision
- YOLO inference
- Motor control
- Pump control
- Web monitoring

## Vision System

The OV5647 camera captures surface images for the AI detection pipeline.

The detection system uses:

```text
Camera
  ↓
OpenCV
  ↓
YOLOv11n
  ↓
Moss Detection
  ↓
Cleaning Decision
Navigation Sensors

Four HC-SR04 ultrasonic sensors provide directional distance measurements.

The LM393 optical encoders provide wheel movement information, while the MPU-6050 provides orientation data.

Together these sensors support GPS-independent navigation.

Drive System

The robot uses DC gear motors controlled through an L298N motor driver.

Differential motor control allows the robot to:

Drive forward
Drive backward
Turn
Correct heading
Stop during obstacle detection
Stop during cleaning
Cleaning System

A 12 V diaphragm pump delivers cleaning solution through the spray system.

The Raspberry Pi controls the pump through a relay.

The pump relay is:

BCM GPIO 4
Physical Pin 7

The robot activates the cleaning system after a valid moss detection.

Power System

The documented prototype uses a 3S Li-Ion battery pack with an LM2596 buck converter for regulated power delivery.

Safety

The hardware should be tested progressively:

Verify power connections.
Test sensors independently.
Test motors with the robot lifted.
Test navigation without the pump connected.
Test the relay separately.
Test the pump only after the control logic is verified.
Perform autonomous testing in a controlled area.

Never connect motors or pumps directly to Raspberry Pi GPIO pins.
