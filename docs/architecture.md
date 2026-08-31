# MossClean System Architecture

> **An autonomous surface-cleaning robotics platform integrating edge AI, GPS-independent navigation, targeted cleaning, and web-based monitoring.**

---

## 1. System Overview

MossClean is designed as an autonomous mobile robotic platform for identifying and treating moss growth on paved surfaces.

The system integrates:

- Edge AI-based moss detection
- GPS-independent localization
- Autonomous coverage navigation
- Real-time obstacle avoidance
- Targeted spray actuation
- Robot telemetry
- Web-based monitoring
- Security and anomaly alerts

The Raspberry Pi 4 acts as the central processing hub coordinating the major software and hardware subsystems.

---

## 2. High-Level Architecture

```text
                         ┌─────────────────────────┐
                         │       MossClean         │
                         │ Autonomous Robot        │
                         └────────────┬────────────┘
                                      │
                ┌─────────────────────┼─────────────────────┐
                │                     │                     │
                ▼                     ▼                     ▼
        ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
        │   Perception  │     │   Navigation  │     │   Monitoring  │
        │   & AI        │     │   & Mapping    │     │   & Security  │
        └───────┬───────┘     └───────┬───────┘     └───────┬───────┘
                │                     │                     │
                ▼                     ▼                     ▼
        ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
        │ Camera        │     │ Encoders      │     │ Flask         │
        │ YOLOv11n      │     │ MPU-6050      │     │ Dashboard     │
        │ OpenCV        │     │ Ultrasonic    │     │ Telemetry     │
        └───────┬───────┘     └───────┬───────┘     │ Alerts        │
                │                     │              └───────┬───────┘
                └──────────────┬──────┘                      │
                               ▼                             │
                     ┌──────────────────┐                    │
                     │ Raspberry Pi 4   │◄───────────────────┘
                     │ Central Control   │
                     └────────┬─────────┘
                              │
                 ┌────────────┼────────────┐
                 │            │            │
                 ▼            ▼            ▼
          ┌───────────┐ ┌───────────┐ ┌───────────┐
          │   Motors  │ │   Pump    │ │  Sensors  │
          │  + L298N  │ │  + Relay  │ │  + Safety │
          └───────────┘ └───────────┘ └───────────┘

          3. Perception & AI Layer

The perception subsystem provides the robot with visual intelligence.

Camera

An onboard camera captures surface imagery for moss detection.

YOLOv11n

MossClean uses the lightweight YOLOv11n model for edge-based moss detection.

The model processes camera frames and produces detection bounding boxes and confidence scores.

OpenCV

OpenCV supports image processing and motion-analysis functionality.

The project also uses frame differencing as part of its anomaly/theft detection mechanism.

4. Navigation & Localization Layer

MossClean is designed to operate without GPS.

The navigation system combines:

LM393 optical wheel encoders
MPU-6050 IMU
Dead-reckoning odometry
Occupancy-grid mapping
Raycasting
Autonomous exploration

Encoder measurements provide wheel-motion information while IMU measurements provide heading information.

The combined state estimate allows the robot to maintain an internal representation of its position.

5. Mapping & Environment Representation

MossClean maintains a 2D occupancy grid representing the discovered environment.

Sensor measurements are projected into the grid using raycasting.

Conceptually:
Unknown ──► Sensor Observation ──► Raycasting
                         │
                         ▼
                 Occupancy Grid
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
            FREE                OBSTACLE
            This allows the robot to progressively construct an internal representation of its surroundings.

6. Autonomous Navigation

The navigation architecture incorporates coverage planning and point-to-point pathfinding.

Coverage Planning

The Boustrophedon coverage pattern provides systematic lawnmower-style traversal.
→ → → → → → →
              ↓
← ← ← ← ← ← ←
↓
→ → → → → → →
This approach is intended to provide systematic surface coverage rather than random movement.

A* Pathfinding

A* search is used for point-to-point navigation toward unexplored or required regions.

The project documentation describes a Manhattan-distance heuristic and a dynamic cost layer for safer path selection.

7. Motion Control

The motion-control subsystem regulates the robot's movement using motor PWM.

A proportional controller uses heading error to dynamically adjust the left and right motor commands.
Target Heading
       │
       ▼
  Heading Error
       │
       ▼
 P Controller
       │
 ┌─────┴─────┐
 ▼           ▼
Left PWM   Right PWM
       │
       ▼
    Motors

The objective is to reduce mechanical drift and maintain straight traversal during coverage sweeps.

8. Safety & Obstacle Avoidance

The robot continuously monitors its surroundings using ultrasonic sensors.

When an obstacle is detected:

Robot movement is interrupted.
Surrounding sensor measurements are evaluated.
A safer direction is selected.
The robot performs a bypass maneuver.
The original navigation direction is restored when possible.

The system also incorporates anti-trap behavior for repeated unsuccessful bypass attempts.

9. Moss Detection → Cleaning Pipeline

The core cleaning workflow is:
Camera Frame
     │
     ▼
Image Processing
     │
     ▼
YOLOv11n Inference
     │
     ▼
Moss Detected?
   ┌─┴─┐
  NO  YES
   │    │
   │    ▼
   │  Robot Stop
   │    │
   │    ▼
   │  Pump Activate
   │    │
   │    ▼
   │ Targeted Spray
   │    │
   └────┴──────► Resume Navigation
   The implemented MossController encapsulates camera, YOLO inference, and pump-control functionality.

10. Cleaning Actuation

A relay-controlled pump provides the cleaning-fluid actuation mechanism.

The implemented controller ensures that the pump is explicitly switched off during cleanup and after spraying.

The spraying operation is executed only after the robot has stopped for the detection cycle.
11. Web Monitoring Architecture

The monitoring subsystem connects the physical robot to a Flask-based web interface.
Robot Sensors
     │
     ▼
Telemetry State
     │
     ▼
 JSON Data
     │
     ▼
 Flask Backend
     │
     ├──────────────► Dashboard
     │
     ├──────────────► Live Video
     │
     └──────────────► Alerts
     The dashboard provides remote visibility into robot operation and telemetry.

12. Security & Alerts

MossClean includes mechanisms for detecting operational anomalies and unauthorized movement.

The project documentation describes:

Role-Based Access Control
SQLite-backed authentication
Hashed passwords
SMTP notifications
Stuck detection
Theft/anomaly detection
Administrative controls

Security-sensitive configuration must remain outside the public repository.

13. Hardware–Software Boundary

The architecture deliberately separates physical hardware control from higher-level decision logic.
┌─────────────────────────────────────┐
│           Application Layer          │
│       Web / Monitoring / Alerts      │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│          Intelligence Layer          │
│     YOLO / Vision / Decisions        │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│          Navigation Layer            │
│ Mapping / Odometry / Path Planning   │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│            Hardware Layer            │
│ Motors / Sensors / Pump / Camera     │
└─────────────────────────────────────┘
This separation improves maintainability and allows individual subsystems to be developed and tested independently.

14. Core Technology Stack
Layer	Technology
Compute	Raspberry Pi 4
Operating System	Raspberry Pi OS 64-bit
Primary Language	Python
Computer Vision	OpenCV
Object Detection	YOLOv11n
AI Runtime	PyTorch / ONNX
Web Backend	Flask
Web Interface	HTML / CSS / AJAX
Localization	Encoder + IMU
Mapping	2D Occupancy Grid
Path Planning	A*
Coverage Planning	Boustrophedon
Motor Control	L298N + PWM
Cleaning Actuation	Relay + Pump
Alerts	SMTP
15. Design Philosophy

MossClean follows a modular robotics architecture where perception, localization, navigation, actuation, monitoring, and security are treated as distinct but cooperating subsystems.

The architecture is designed to support future improvements in:

Detection accuracy
Navigation robustness
Mapping
Edge inference performance
Hardware diagnostics
Remote monitoring
Autonomous cleaning efficiency
16. Engineering Summary

MossClean brings together embedded robotics, computer vision, edge AI, autonomous navigation, IoT monitoring, and targeted actuation into a single autonomous surface-maintenance platform.

The architecture is intended to provide a foundation that can evolve from a prototype into a more capable autonomous maintenance system.
