# MossClean Configuration

This directory documents the configuration parameters used by the MossClean robotic platform.

## Configuration Domains

MossClean configuration is organized around the following system layers:

### 🤖 Robot Hardware

Hardware configuration includes:

- Raspberry Pi GPIO assignments
- Motor-driver control
- Pump and relay control
- Ultrasonic sensors
- Wheel encoders
- IMU
- Camera interface

### 🧠 Vision & AI

The vision subsystem uses a lightweight YOLOv11n model for edge-based moss detection.

Key parameters include:

- Model path
- Input image size
- Detection confidence threshold
- Detection output directory

The documented operating confidence threshold is **60%**. :contentReference[oaicite:0]{index=0}

### 🧭 Navigation

Navigation configuration covers:

- Robot dimensions
- Wheel parameters
- Encoder settings
- Grid resolution
- Heading control
- Obstacle safety distances
- Coverage-planning parameters

MossClean uses GPS-independent localization based on wheel encoder odometry and IMU information. :contentReference[oaicite:1]{index=1}

### 🌐 Web Monitoring

The monitoring layer includes configuration for:

- Flask server
- Dashboard communication
- Telemetry
- Authentication
- Database
- Alert notifications

The project uses Flask for the web command center and real-time monitoring interface. :contentReference[oaicite:2]{index=2}

## Security

Sensitive values must never be committed to the repository.

Use environment variables for:

- Secret keys
- SMTP credentials
- Authentication secrets
- API credentials
- Other private configuration values

Refer to the root `.env.example` file for the configuration template.

## Hardware Deployment

Configuration values should be validated against the actual MossClean hardware before deployment.

Incorrect GPIO assignments, motor parameters, sensor thresholds, or actuator settings may cause unexpected physical behavior.

## Configuration Philosophy

The goal is to keep system-specific parameters configurable while keeping the core MossClean control architecture modular, reproducible, and maintainable.
