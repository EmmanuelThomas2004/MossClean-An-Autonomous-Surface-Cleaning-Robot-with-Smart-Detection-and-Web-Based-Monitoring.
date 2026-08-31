# MossClean

### An Autonomous Surface Cleaning Robot with Smart Detection and Web-Based Monitoring

> **Edge AI • Autonomous Navigation • Precision Cleaning • IoT Monitoring**

MossClean is an autonomous mobile robotic platform designed to identify moss on paved surfaces, navigate without GPS, apply targeted cleaning solution, and provide remote monitoring and control through a web interface.

---

## ✨ Project at a Glance

| Layer | Implementation |
|---|---|
| Edge Computer | Raspberry Pi 4 Model B (4 GB) |
| Vision | OV5647 5 MP camera |
| AI Detection | YOLOv11n / Nano object detection |
| Image Processing | OpenCV |
| Navigation | GPS-independent dead reckoning + occupancy grid |
| Motion Control | Proportional heading correction + differential PWM |
| Coverage | Boustrophedon / lawnmower sweep |
| Path Planning | A* frontier recovery |
| Obstacle Safety | 4× HC-SR04 ultrasonic sensors |
| Odometry | LM393 optical encoders |
| Orientation | MPU-6050 gyroscope/accelerometer |
| Actuation | DC gear motors + L298N |
| Cleaning | 12 V diaphragm pump + relay |
| Monitoring | Flask web dashboard + live telemetry |
| Alerts | SMTP anomaly/security notifications |

The project documentation specifies the Raspberry Pi, camera, navigation sensors, motor driver, pump and monitoring stack used by MossClean. fileciteturn3file1L81-L151

---

## 🧠 System Architecture

```text
                    ┌───────────────────────────┐
                    │       MossClean Robot      │
                    └─────────────┬─────────────┘
                                  │
                 ┌────────────────┼────────────────┐
                 │                │                │
                 ▼                ▼                ▼
          ┌────────────┐   ┌────────────┐   ┌─────────────┐
          │ OV5647     │   │ Ultrasonic │   │ IMU +       │
          │ Camera     │   │ Sensors    │   │ Encoders    │
          └─────┬──────┘   └─────┬──────┘   └──────┬──────┘
                │                │                 │
                ▼                ▼                 ▼
          ┌────────────┐   ┌────────────────────────────┐
          │ YOLOv11n   │   │ World Model + Odometry     │
          │ Moss AI    │   │ Occupancy Grid + Safety    │
          └─────┬──────┘   └─────────────┬──────────────┘
                │                        │
                └──────────┬─────────────┘
                           ▼
                 ┌────────────────────┐
                 │ Raspberry Pi       │
                 │ Control Layer      │
                 └─────────┬──────────┘
                           │
              ┌────────────┼─────────────┐
              ▼            ▼             ▼
        ┌──────────┐ ┌───────────┐ ┌──────────────┐
        │ Motors   │ │ Pump/Relay│ │ Telemetry    │
        │ + L298N  │ │ Sprayer   │ │ + Alerts     │
        └──────────┘ └───────────┘ └──────┬───────┘
                                          ▼
                                ┌──────────────────┐
                                │ MossClean Web OS │
                                │ Monitor / Control│
                                └──────────────────┘
```

The implementation keeps camera/YOLO/pump functionality inside a dedicated `MossController`, separated from navigation, world-model and sensor-polling components. fileciteturn1file3L187-L229

---

## 🚀 Core Intelligence

### 1. Moss Detection
The camera captures frames and the YOLO model performs inference using a configurable confidence threshold. A detected moss patch is saved as an annotated image and can trigger the spray sequence. The current implementation uses a 0.60 confidence threshold and a 640×640 inference image size. fileciteturn1file9L491-L528

### 2. Autonomous Coverage
MossClean uses a deterministic lawnmower-style coverage pattern to systematically traverse the operating area rather than relying on random movement.

### 3. GPS-Free Navigation
Wheel encoder ticks and IMU yaw are used to estimate robot position and heading. Sensor observations are projected into a 2D grid to maintain environmental knowledge. fileciteturn1file7L402-L420

### 4. Obstacle Avoidance
Four ultrasonic sensors provide directional distance information. The navigation layer can stop, evaluate lateral clearance, bypass an obstacle, and resume its coverage path. fileciteturn1file8L459-L467

### 5. Precision Spray Actuation
When moss is detected, the robot stops and activates the pump for the configured spray duration before resuming navigation. fileciteturn1file9L530-L561

### 6. Web Monitoring & Security
The project documentation describes a Flask-based command center with live video, telemetry, role-based access control and SMTP alerts for events such as theft or a stuck condition. fileciteturn3file0L20-L27

---

## 📊 AI Validation Snapshot

The project report records the following YOLOv11n validation results:

- **Precision:** 64.6%
- **Recall:** 56.9%
- **mAP@50:** 58.8%
- **Configured live confidence threshold:** 60%
- **Reported Raspberry Pi inference:** approximately 130–160 ms/frame

These figures are reported as proof-of-concept validation results in the project report. fileciteturn1file2L111-L136

---

## 📁 Repository Structure

```text
MossClean/
├── README.md
├── LICENSE
├── .gitignore
├── requirements-pi.txt
├── requirements-dev.txt
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
├── src/
│   └── mossclean_robot.py
├── config/
│   └── README.md
├── tests/
│   └── README.md
├── docs/
│   ├── MossClean_Project_Report.pdf
│   └── MossClean_Phase2_Presentation.pptx
└── media/
    ├── mossclean_robot_hardware.jpeg
    ├── moss_detection_live.jpeg
    ├── moss_os_login.jpeg
    ├── moss_os_users.jpeg
    └── moss_os_dashboard.jpeg
```

---

## 🛠️ Raspberry Pi Setup

The main control program is intended for Raspberry Pi hardware and imports GPIO, OpenCV, SMBus, gpiozero, Picamera2 and Ultralytics YOLO components. fileciteturn0file1L25-L32

```bash
git clone <YOUR_REPOSITORY_URL>
cd MossClean

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-pi.txt

python3 src/mossclean_robot.py
```

> **Hardware warning:** This program directly controls motors, GPIO pins, sensors and a pump. Do not execute it on a normal PC or connected hardware without reviewing the pin map and safety conditions.

---

## 🔌 Hardware Pin Highlights

The implementation defines four ultrasonic sensor channels, two PWM motor channels, motor direction pins, encoder inputs, IMU communication and the pump relay in its configuration layer. The pump relay is assigned to **BCM GPIO 4 / physical pin 7**. fileciteturn0file1L52-L62

---

## 🔐 Security & Secrets

**Never commit:**

- SMTP passwords
- API keys
- Wi-Fi passwords
- database credentials
- private model artifacts containing sensitive data
- `.env` files
- personal credentials

Use environment variables or a local `.env` file that is excluded by `.gitignore`.

Before making this repository public, review the included project report/presentation for personal contact information and institutional material.

---

## 📸 Prototype & Dashboard

### Physical Prototype

![MossClean Robot](media/mossclean_robot_hardware.jpeg)

### Real-Time Moss Detection

![Moss Detection](media/moss_detection_live.jpeg)

### MossClean OS — Login

![MossClean Login](media/moss_os_login.jpeg)

### MossClean OS — User Management

![MossClean Users](media/moss_os_users.jpeg)

### MossClean OS — Monitoring Dashboard

![MossClean Dashboard](media/moss_os_dashboard.jpeg)

---

## 🎯 Project Objectives

1. Detect moss using edge AI.
2. Navigate autonomously without GPS.
3. Systematically cover the target surface.
4. Avoid obstacles in real time.
5. Apply cleaning solution only after a positive detection.
6. Provide live remote monitoring and control.
7. Detect operational/security anomalies and generate alerts.

The project report frames MossClean as a scalable autonomous surface-maintenance platform combining computer vision, GPS-independent navigation, targeted spraying and IoT monitoring. fileciteturn1file0L55-L64

---

## 🔭 Future Roadmap

The project documentation identifies several future upgrades, including solar-assisted operation, LiDAR/SLAM, variable-rate chemical application, automated docking/self-charging and multi-robot coordination.

---

## 👥 Team

**MossClean — SJCET Palai**

- Abhishek N B
- Emmanuel Thomas
- Hari Govind S
- Rijo Joshy



---

## 📄 Documentation

The complete Phase-II project report and presentation are included under `docs/` for reference.

---

## ⭐ Why MossClean?

MossClean brings together **robotics + edge AI + autonomous navigation + targeted actuation + IoT monitoring** into one integrated prototype. The goal is not simply to build a cleaning rover, but to demonstrate a complete edge-intelligent robotic workflow from perception → decision → navigation → actuation → monitoring.

---

## 📜 License

Released under the MIT License. See `LICENSE`.

