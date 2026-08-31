# MossClean Hardware Architecture

> **Hardware architecture of the MossClean autonomous surface-cleaning robot.**

---

## 1. Hardware Overview

MossClean is built as an autonomous mobile robotic platform with a Raspberry Pi 4 serving as the central processing and control unit.

The hardware architecture integrates:

- Embedded computing
- Computer vision
- Inertial sensing
- Wheel odometry
- Ultrasonic obstacle sensing
- Motor control
- Cleaning-fluid actuation
- Power management
- Fluid-level monitoring

The system is designed to allow the robot to perceive its environment, estimate its movement, avoid obstacles, identify moss, and perform targeted cleaning.

---

## 2. Central Processing Unit

### Raspberry Pi 4 Model B

The Raspberry Pi 4 acts as the primary computing platform.

### Responsibilities

The Raspberry Pi coordinates:

- Sensor acquisition
- Robot navigation
- Localization
- Computer vision
- YOLO inference
- Motor control
- Pump control
- Telemetry
- Web-server operation
- Security and alert processing

### Key Specifications

| Parameter | Specification |
|---|---|
| Platform | Raspberry Pi 4 Model B |
| RAM | 4 GB |
| CPU | Quad-core 1.5 GHz |
| Connectivity | Dual-band Wi-Fi |
| Operating System | Raspberry Pi OS 64-bit |
| Primary Language | Python |

The Raspberry Pi 4 is specified as the central processing unit for YOLOv11n inference, sensor fusion, and web-server hosting.

---

## 3. Vision System

### OV5647 Camera

The onboard camera provides the visual input required for moss detection.

### Responsibilities

- Capture surface images
- Provide frames for AI inference
- Support real-time moss detection
- Support visual anomaly detection

The camera operates as part of the edge-AI perception pipeline.

---

## 4. Moss Detection Hardware Interface

The camera is connected to the Raspberry Pi, where captured frames are processed by the computer-vision and AI software stack.

```text
Surface
   │
   ▼
Camera
   │
   ▼
Raspberry Pi
   │
   ▼
YOLOv11n
   │
   ▼
Moss Detection
This architecture keeps image processing and inference close to the physical sensing hardware.

5. Inertial Measurement Unit
MPU-6050

The MPU-6050 provides motion and orientation information for the navigation subsystem.

Role

The IMU contributes to:

Heading estimation
Motion tracking
Heading correction
Dead-reckoning navigation
Robot movement analysis

The project uses IMU information together with wheel encoder measurements for GPS-independent localization.

6. Wheel Encoders
LM393 Optical Encoders

LM393-based optical wheel encoders provide wheel-rotation feedback.

Role

Encoder measurements are used to estimate:

Wheel movement
Distance travelled
Robot displacement
Position relative to the starting point
Wheel Rotation
      │
      ▼
Optical Encoder
      │
      ▼
Encoder Pulses
      │
      ▼
Odometry
      │
      ▼
Robot Position
7. Ultrasonic Obstacle Sensors
HC-SR04

Multiple HC-SR04 ultrasonic sensors provide distance measurements around the robot.

Responsibilities
Detect nearby obstacles
Maintain safety clearance
Support reactive obstacle avoidance
Provide environmental measurements for mapping

The project documentation specifies multiple ultrasonic sensors for obstacle detection and environmental mapping.

8. Navigation Sensor Fusion

MossClean combines wheel-encoder and IMU information to support GPS-independent navigation.

             ┌──────────────────┐
             │   LM393 Encoders │
             └────────┬─────────┘
                      │
                      ▼
                ┌───────────┐
                │           │
                │  Odometry │
                │           │
                └─────┬─────┘
                      │
                      ▼
              Robot State Estimate
                      ▲
                      │
                ┌─────┴─────┐
                │  MPU-6050 │
                └───────────┘

This enables the robot to estimate its movement without depending on GPS.

9. Drive System
DC Gear Motors

The robot uses high-torque DC gear motors for mobility.

The motors provide the mechanical drive required for:

Forward movement
Reverse movement
Turning
Coverage sweeps
Obstacle bypass maneuvers
10. Motor Driver
L298N

The L298N dual H-bridge motor driver interfaces the Raspberry Pi control logic with the DC motors.

Responsibilities
Motor direction control
Motor speed control
PWM-based speed regulation
Differential motor control

The motor controller receives commands from the robot's motion-control layer.

Raspberry Pi
     │
     │ PWM / Direction
     ▼
  L298N Driver
     │
 ┌───┴───┐
 ▼       ▼
Motor   Motor
11. Cleaning Actuation System
12V Diaphragm Pump

The pump provides the physical mechanism for delivering the cleaning solution.

The project uses targeted spraying rather than continuously spraying the surface.

Operating Principle
Moss Detected
      │
      ▼
Robot Stops
      │
      ▼
Pump Activated
      │
      ▼
Cleaning Solution
      │
      ▼
Spray Nozzle
      │
      ▼
Targeted Surface

The implemented software activates the pump through a relay and switches it off after the configured spray interval.

12. Relay Control

A relay module provides electrical isolation and switching control between the Raspberry Pi and the pump circuit.

The pump-control interface uses a dedicated GPIO control line.

The software explicitly places the pump into an OFF state during initialization and cleanup to reduce the risk of unintended activation.

13. Spray Assembly

The spraying assembly consists of:

12V diaphragm pump
Relay module
Cleaning-fluid reservoir
Flat-fan nozzle
Tubing and associated plumbing

The project documentation specifies a flat-fan nozzle designed to provide a broad spray pattern over the target surface.

14. Fluid-Level Monitoring

A water-level/depth sensor provides feedback regarding the remaining liquid in the reservoir.

Monitoring Function

The sensor allows the system to determine whether the cleaning reservoir is approaching a low-level condition.

The documented monitoring threshold is:

< 20%  →  Low-Level Alert

The corresponding status can be communicated to the web monitoring interface.

15. Power System
3S 18650 Lithium-Ion Battery Pack

The robot uses a 3S lithium-ion battery configuration.

Parameter	Value
Configuration	3S
Nominal voltage	11.1 V
Maximum voltage	12.6 V

The battery provides the primary energy source for the robotic platform.

16. Voltage Regulation
LM2596 Buck Converter

A buck converter provides regulated low-voltage power for the Raspberry Pi and associated electronics.

The project documentation specifies a regulated 5 V rail for the computing and sensor electronics.

3S Battery
    │
    ├──────────────► High-current actuator supply
    │
    ▼
LM2596 Buck Converter
    │
    ▼
  Regulated 5 V
    │
    ├──► Raspberry Pi
    ├──► Sensors
    └──► Logic Electronics

Separating high-current actuator loads from sensitive computing electronics helps reduce the risk of processor instability caused by actuator current demand.

17. Mechanical Structure

The robot uses a four-wheel mechanical chassis designed to support:

Computing electronics
Battery system
Motors
Sensors
Cleaning-fluid reservoir
Pump
Spray assembly

The structure provides the mechanical platform on which the sensing, computing, and actuation subsystems are mounted.

18. Hardware–Software Interface

The Raspberry Pi provides the central interface between software decisions and physical hardware.

                 Raspberry Pi
                      │
       ┌──────────────┼──────────────┐
       │              │              │
       ▼              ▼              ▼
   Sensors         Actuators      Network
       │              │              │
       ▼              ▼              ▼
  Environment      Motors/Pump   Dashboard
Inputs
Camera frames
IMU measurements
Encoder pulses
Ultrasonic distances
Fluid-level measurements
Outputs
Motor commands
Pump activation
Telemetry
Web responses
Alert notifications
19. Hardware Safety Considerations

MossClean contains physical actuators capable of generating mechanical movement and fluid discharge.

Before operation:

Verify motor wiring.
Verify relay wiring.
Confirm the pump defaults to OFF.
Verify sensor connections.
Confirm battery polarity.
Check voltage-regulator output.
Test emergency stopping behavior.
Keep the robot in a controlled test environment.

Hardware-control modifications should be validated before autonomous operation.

20. Hardware Summary
Subsystem	Component	Primary Function
Compute	Raspberry Pi 4 Model B	Central processing
Vision	OV5647 Camera	Surface perception
IMU	MPU-6050	Motion/orientation sensing
Odometry	LM393 Encoders	Wheel-motion feedback
Obstacle Detection	HC-SR04	Distance sensing
Motors	DC Gear Motors	Robot movement
Motor Driver	L298N	Motor control
Pump	12V Diaphragm Pump	Cleaning-fluid delivery
Relay	5V Relay Module	Pump switching
Nozzle	Flat-Fan Nozzle	Spray distribution
Fluid Monitor	Depth Sensor	Reservoir monitoring
Battery	3S 18650 Pack	Main power source
Regulator	LM2596	Voltage regulation
21. Engineering Perspective

The MossClean hardware architecture is designed around a clear separation between:

Perception → Localization → Decision → Actuation → Monitoring

This allows the physical platform to support the project's edge-AI, autonomous-navigation, targeted-cleaning, and IoT-monitoring objectives while maintaining modularity for future development.
