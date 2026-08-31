# MossClean Software Architecture

> **Software architecture and technology stack of the MossClean autonomous surface-cleaning robot.**

---

## 1. Software Overview

MossClean is built around a modular software architecture that integrates embedded robotics, edge artificial intelligence, computer vision, autonomous navigation, hardware control, web technologies, telemetry, and security.

The software runs primarily on a Raspberry Pi 4 using Python.

The architecture is organized around the following functional domains:

- Embedded hardware control
- Computer vision
- Edge AI inference
- Autonomous navigation
- Localization and odometry
- Occupancy-grid mapping
- Obstacle avoidance
- Cleaning actuation
- Web-based monitoring
- Authentication and access control
- Telemetry
- Security and anomaly alerts

---

## 2. Software Stack

| Layer | Technology | Purpose |
|---|---|---|
| Operating System | Raspberry Pi OS 64-bit | Embedded execution environment |
| Programming Language | Python | Core system implementation |
| Computer Vision | OpenCV | Image processing and motion analysis |
| Object Detection | YOLOv11n | Real-time moss detection |
| AI Runtime | PyTorch / ONNX | Edge inference |
| Web Backend | Flask | Monitoring and command interface |
| Frontend | HTML5 / CSS3 | Dashboard interface |
| Client Communication | AJAX | Dynamic dashboard updates |
| Database | SQLite | Application and authentication data |
| Notifications | SMTP | Automated alerts |
| Hardware Interface | GPIO / sensor interfaces | Robot hardware control |

The project documentation identifies Raspberry Pi OS 64-bit, Python, OpenCV, YOLOv11n, PyTorch/ONNX, Flask, HTML5/CSS3/AJAX, SQLite, and SMTP as major software technologies used by the system. :contentReference[oaicite:0]{index=0}

---

## 3. High-Level Software Architecture

```text
                         MOSS CLEAN
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        PERCEPTION       NAVIGATION     MONITORING
              │              │              │
              ▼              ▼              ▼
        YOLOv11n          Odometry        Flask
        OpenCV            Mapping         Dashboard
        Camera            Planning        Telemetry
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                     DECISION & CONTROL
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
                 Motors             Pump
                    │                 │
                    ▼                 ▼
                 Motion            Cleaning

                 4. Perception Layer

The perception layer converts physical observations into information that the robot can use for decision-making.

Components
Camera interface
OpenCV processing
YOLOv11n inference
Detection confidence filtering
Visual anomaly detection
Camera
   │
   ▼
Image Acquisition
   │
   ▼
OpenCV Processing
   │
   ▼
YOLOv11n
   │
   ▼
Detection Results
   │
   ▼
Decision Layer
5. Computer Vision
OpenCV

OpenCV is used for image-processing and visual-analysis operations.

Its documented roles include:

Frame preprocessing
Color-space conversion
Image manipulation
Motion analysis
Anomaly detection

OpenCV is also used as part of the theft/anomaly detection mechanism through frame differencing.

6. Edge AI
YOLOv11n

MossClean uses the lightweight YOLOv11n model for real-time moss detection.

The model receives camera frames and produces detection information such as:

Bounding boxes
Detection classes
Confidence scores

The lightweight architecture is intended for deployment on resource-constrained edge hardware such as the Raspberry Pi.

Detection Pipeline
             Camera Frame
                   │
                   ▼
             Preprocessing
                   │
                   ▼
              YOLOv11n
                   │
                   ▼
          Detection Candidates
                   │
                   ▼
         Confidence Filtering
                   │
                   ▼
             Moss Detected

The documented operating confidence threshold is 60%.

7. AI Inference

The project documentation identifies PyTorch and ONNX as part of the model-inference stack.

The intended architecture supports edge inference directly on the robotic platform rather than requiring continuous cloud-based image processing.

Camera
  │
  ▼
Raspberry Pi
  │
  ▼
AI Runtime
  │
  ▼
YOLOv11n
  │
  ▼
Detection
8. Navigation Software

The navigation subsystem provides autonomous movement without relying on GPS.

It integrates:

Encoder measurements
IMU data
Dead-reckoning odometry
Occupancy-grid mapping
Raycasting
Coverage planning
A* pathfinding
Heading control
Reactive obstacle avoidance

The project documentation describes encoder-based odometry and IMU information as the basis for GPS-independent localization.

9. Localization

MossClean estimates its position using kinematic dead reckoning.

LM393 Encoders ─────┐
                    │
                    ▼
              State Estimation
                    │
                    ▼
              Robot Position
                    ▲
                    │
MPU-6050 ───────────┘

Encoder pulses provide wheel-motion information while the IMU contributes heading information.

10. Mapping

The navigation subsystem maintains a 2D occupancy grid.

Ultrasonic measurements are projected into the grid using raycasting.

Sensor Measurement
        │
        ▼
    Raycasting
        │
        ▼
Occupancy Grid
   │          │
   ▼          ▼
 FREE      OBSTACLE

This allows the robot to progressively represent its discovered environment.

11. Coverage Planning

MossClean uses a systematic coverage strategy based on a Boustrophedon/lawnmower traversal pattern.

→ → → → → → →
              ↓
← ← ← ← ← ← ←
              ↓
→ → → → → → →

The objective is to systematically traverse the target surface while reducing unnecessary random movement.

12. A* Pathfinding

A* provides point-to-point navigation when the robot needs to reach a particular location or unexplored region.

The algorithm uses:

f(n) = g(n) + h(n)

Where:

g(n) represents accumulated path cost.
h(n) represents estimated remaining cost.
f(n) represents the total estimated cost.

The documented implementation uses a Manhattan-distance heuristic for grid-based pathfinding.

13. Motion Control

The motion-control layer converts navigation commands into motor-control signals.

The system uses proportional heading correction to reduce mechanical drift.

Target Heading
      │
      ▼
Heading Error
      │
      ▼
P Controller
      │
 ┌────┴────┐
 ▼         ▼
Left PWM  Right PWM
      │
      ▼
DC Motors

The proportional controller dynamically adjusts motor PWM according to heading error.

14. Obstacle Avoidance

The robot continuously evaluates ultrasonic sensor measurements.

The reactive avoidance pipeline is:

Obstacle Detected
       │
       ▼
     STOP
       │
       ▼
Evaluate Surroundings
       │
       ▼
Choose Safer Direction
       │
       ▼
Bypass Obstacle
       │
       ▼
Re-align
       │
       ▼
Resume Navigation

The documented system also includes anti-trap behavior for repeated unsuccessful bypass attempts.

15. Cleaning Decision Pipeline

Moss detection is connected to the cleaning actuator through a dedicated decision process.

Camera
   │
   ▼
YOLOv11n
   │
   ▼
Moss Detected?
   │
 ┌─┴─┐
NO   YES
│     │
│     ▼
│   Stop Robot
│     │
│     ▼
│   Activate Pump
│     │
│     ▼
│ Targeted Spray
│     │
└─────┴──────► Resume

The implemented MossController handles camera capture, YOLO inference, detection storage, and pump control.

16. Pump Control

The software controls the cleaning pump through a relay.

The implementation provides explicit pump ON and OFF operations.

During cleanup, the pump is placed into a safe OFF state and the camera is released.

This provides a clear software safety boundary between decision-making and physical cleaning actuation.

17. Web Application

The MossClean web platform provides the human–robot interaction layer.

The project documentation specifies Flask as the backend framework supporting:

Web command center
Remote operations
Live MJPEG video
Responsive user interface
Robot monitoring

18. Web Architecture
                 ROBOT
                   │
                   │ Wi-Fi
                   ▼
            ┌─────────────┐
            │    Flask    │
            │   Backend   │
            └──────┬──────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
    Telemetry    Video     Commands
        │          │          │
        └──────────┼──────────┘
                   ▼
             Web Dashboard
                   │
                   ▼
                Operator
19. Telemetry

Robot state is converted into structured telemetry information.

The documented telemetry includes information such as:

Battery voltage
Water depth
Moss detection count
Robot operational state
Sensors
   │
   ▼
Robot State
   │
   ▼
Telemetry
   │
   ▼
JSON
   │
   ▼
Flask
   │
   ▼
Dashboard

The project documentation specifies JSON-based telemetry communication with the Flask dashboard.

20. Live Video

The web monitoring architecture supports live MJPEG video streaming.

This provides the operator with remote visual awareness of the robot's environment.

Camera
   │
   ▼
Raspberry Pi
   │
   ▼
MJPEG Stream
   │
   ▼
Flask
   │
   ▼
Browser
21. Authentication

The monitoring system incorporates role-based access control.

Operator

Standard operators can perform normal monitoring and driving operations.

Administrator

Administrators receive elevated privileges for:

User management
Manual robot control
Emergency hardware overrides
Safety procedures
Security/operational logs

The project documentation specifies SQLite-backed authentication with hashed passwords.

22. Alert System

MossClean includes automated email notifications using SMTP.

Documented alert conditions include:

Stuck robot
Unauthorized movement / theft
Low liquid level
Robot Event
     │
     ▼
Anomaly Detection
     │
     ▼
Alert Manager
     │
     ▼
SMTP
     │
     ▼
User / Administrator
23. Anomaly Detection

The system uses visual frame differencing to identify potential unauthorized movement.

Conceptually:

Baseline Frame
      │
      │
      ▼
Current Frame
      │
      ▼
Frame Difference
      │
      ▼
Significant Change?
      │
      ▼
Security Alert

The documented system compares the current camera frame with a baseline background frame and can trigger an SMTP notification when significant changes are detected.

24. Software Modularity

MossClean follows a modular architecture.

Major responsibilities are separated into:

Perception
     │
     ▼
Localization
     │
     ▼
Navigation
     │
     ▼
Decision
     │
     ▼
Actuation
     │
     ▼
Monitoring

The implemented MossController specifically isolates camera, YOLO, and pump functionality rather than directly owning navigation or the world model.

25. Configuration Management

Runtime configuration should remain separate from application source code where practical.

Sensitive information must never be committed to the public repository.

Examples include:

Passwords
SMTP credentials
Secret keys
Authentication tokens
Private API credentials

The repository provides .env.example as a configuration template.

26. Software Safety

Because MossClean controls physical actuators, software safety is treated as a core design concern.

Important safeguards include:

Explicit pump OFF state
Robot stopping before moss detection
Obstacle-triggered stopping
Hardware cleanup routines
Sensor-based safety checks
Controlled actuator activation

The robot should always be tested in a controlled environment before autonomous deployment.

27. Software Data Flow
                 ┌─────────────┐
                 │   Camera    │
                 └──────┬──────┘
                        ▼
                 ┌─────────────┐
                 │  OpenCV     │
                 └──────┬──────┘
                        ▼
                 ┌─────────────┐
                 │  YOLOv11n   │
                 └──────┬──────┘
                        ▼
                 Moss Detection
                        │
                        ▼
                 Decision Layer
                        │
                        ▼
                     Pump


Encoders ──┐
           ├──► Localization ──► Navigation ──► Motors
IMU ───────┘
                       ▲
                       │
Ultrasonic ──► Mapping / Avoidance


Robot State
     │
     ▼
 Telemetry
     │
     ▼
 Flask Backend
     │
     ▼
 Dashboard
     │
     ▼
 Operator
28. Technology Integration

MossClean integrates several engineering disciplines:

                 MOSS CLEAN
                     │
       ┌─────────────┼─────────────┐
       │             │             │
       ▼             ▼             ▼
    ROBOTICS          AI           IoT
       │             │             │
 Navigation       YOLOv11n       Flask
 Sensors          OpenCV         Telemetry
 Motors           PyTorch        Dashboard
 Mapping          ONNX           SMTP
       │             │             │
       └─────────────┼─────────────┘
                     ▼
              Raspberry Pi 4
29. Development Principles

MossClean software development follows these principles:

Modularity

Each subsystem should have a clear responsibility.

Separation of Concerns

Perception, navigation, actuation, and monitoring should remain logically separated.

Safety

Physical hardware should have explicit safe states.

Reproducibility

Configuration, dependencies, and system behavior should be documented.

Maintainability

Code should remain readable and extensible.

Transparency

Implemented capabilities should be distinguished from future development ideas.

30. Future Software Development

Potential future improvements include:

Automated unit testing
Integration testing
Hardware-in-the-loop testing
Simulation environments
Improved localization
Advanced sensor fusion
AI inference optimization
Historical telemetry analytics
Interactive mapping
Cleaning-coverage visualization
Hardware diagnostics
Automated CI validation
Model-version management

These are potential future development directions and are not claimed as currently implemented functionality.

31. Software Architecture Summary

MossClean combines:

Embedded Systems + Edge AI + Computer Vision + Autonomous Robotics + IoT + Web Engineering

into one integrated platform.

The overall software pipeline can be summarized as:

PERCEIVE
   ↓
UNDERSTAND
   ↓
LOCALIZE
   ↓
PLAN
   ↓
AVOID
   ↓
ACT
   ↓
MONITOR
   ↓
ALERT

This architecture provides the software foundation for MossClean's autonomous surface-cleaning mission while maintaining a modular structure suitable for continued research and engineering development.
