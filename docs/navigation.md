# MossClean Navigation System

## Overview

MossClean is designed to navigate autonomously without relying on GPS.

The navigation system combines:

- Wheel encoder odometry
- MPU-6050 IMU
- Ultrasonic obstacle sensing
- Occupancy-grid mapping
- Boustrophedon coverage
- A* path planning
- Proportional heading correction

## Navigation Pipeline

```text
Encoder + IMU + Ultrasonic Sensors
                ↓
          Robot State
                ↓
        Odometry Update
                ↓
        Occupancy Grid
                ↓
      Coverage Planner
                ↓
       Motion Controller
                ↓
       Motor Commands
       This provides systematic traversal of the target surface.

Odometry

Wheel encoder ticks and gyroscope measurements are used to estimate the robot's position and heading.

The implementation uses encoder-based dead reckoning together with IMU yaw information.

Occupancy Grid

The robot maintains a grid representation of the environment.

Cells can represent:

Free space
Obstacles
Unknown areas
Higher-cost regions near obstacles

Ultrasonic measurements are used to update the environmental model.

Obstacle Avoidance

Four HC-SR04 ultrasonic sensors provide directional distance measurements:

Front
Back
Left
Right

The robot can stop when an obstacle becomes too close, evaluate available clearance, perform an avoidance maneuver, and resume its planned route.

A* Frontier Recovery

A* search is used when the robot needs to reach a missed or unexplored frontier area.

The project uses a grid-based Manhattan-distance heuristic and an obstacle cost layer.

Proportional Heading Control

A proportional controller corrects heading errors during straight coverage rows.

The controller adjusts left and right motor power to compensate for mechanical drift.

Safety

The navigation system includes:

Emergency distance thresholds
Drive and turn timeouts
Watchdog monitoring
Obstacle checks
Motor stop handling

Hardware-dependent navigation should always be tested in a controlled environment before autonomous operation.
