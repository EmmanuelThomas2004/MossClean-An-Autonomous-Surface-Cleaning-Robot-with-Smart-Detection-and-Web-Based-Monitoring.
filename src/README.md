# MossClean Source Code

This directory contains the core software components of the MossClean autonomous surface-cleaning robot.

## Responsibilities

The source layer covers:

- Robot hardware control
- Sensor acquisition
- Autonomous navigation
- Localization and odometry
- Obstacle avoidance
- Moss detection
- Precision spray control
- Web-based monitoring
- Robot telemetry
- Safety and anomaly handling

## Architecture

MossClean is designed around modular software components so that perception, navigation, actuation, and monitoring can evolve independently.

The Raspberry Pi 4 acts as the central processing platform, running the robot's Python-based control and AI workloads. :contentReference[oaicite:0]{index=0}
