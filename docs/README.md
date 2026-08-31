# MossClean Technical Documentation

This directory contains the technical documentation for the MossClean autonomous surface-cleaning robot.

## Documentation Scope

The documentation covers the major engineering layers of the system:

- System architecture
- Hardware architecture
- Software architecture
- Computer vision and AI
- Autonomous navigation
- Sensor fusion and localization
- Obstacle avoidance
- Cleaning and spraying subsystem
- Web-based monitoring
- Security and alerting
- Testing and validation

## System Architecture

MossClean uses a Raspberry Pi 4 as the central processing platform. It coordinates perception, navigation, sensing, actuation, and web-based monitoring. :contentReference[oaicite:0]{index=0}

## Edge AI

The vision subsystem uses YOLOv11n for real-time moss detection on resource-constrained hardware, with OpenCV handling image-processing operations and PyTorch/ONNX supporting model inference. :contentReference[oaicite:1]{index=1}

## Autonomous Navigation

The robot uses GPS-independent navigation with encoder-based odometry, IMU heading information, occupancy-grid mapping, and autonomous exploration. :contentReference[oaicite:2]{index=2}

## Robotic Cleaning

When moss is detected, the control system can activate the pump and deliver the cleaning solution through the spraying assembly. :contentReference[oaicite:3]{index=3}

## Web Monitoring

The monitoring subsystem provides a web-based interface for telemetry, video surveillance, remote operation, and system alerts. :contentReference[oaicite:4]{index=4}

## Documentation Principles

Technical documentation should remain:

- Accurate to the implemented system
- Reproducible
- Modular
- Clearly structured
- Explicit about hardware dependencies
- Clear about experimental results and limitations

Further documentation will be organized into dedicated technical sections as the repository evolves.
