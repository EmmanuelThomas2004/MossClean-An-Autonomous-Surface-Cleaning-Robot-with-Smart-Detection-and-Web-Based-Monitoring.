# MossClean Setup Guide

## 1. Hardware

Prepare the Raspberry Pi, camera, ultrasonic sensors, encoders, MPU-6050, motor driver, motors, relay and pump.

Review the GPIO assignments in:

`docs/pinout.md`

## 2. Operating System

The documented software environment uses Raspberry Pi OS (64-bit) and Python 3.9.

## 3. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd MossClean
4. Create a Virtual Environment
python3 -m venv .venv
source .venv/bin/activate
5. Install Python Dependencies
pip install -r requirements-pi.txt

Install Raspberry Pi-specific system packages required by the camera and GPIO stack according to the Raspberry Pi OS environment.

6. Configure Secrets

Do not place passwords or API credentials directly in source code.

Use environment variables for:

SMTP credentials
Database credentials
Application secrets
Other private configuration

The repository includes .env.example as a configuration reference.

7. Run the Robot Controller
python3 src/mossclean_robot.py
8. Run the Web Application

From the web application directory:

python3 mossclean_server.py

The exact deployment command may vary depending on the Flask configuration.

9. Initial Testing

Perform testing in this order:

Test the software without connected actuators.
Test individual sensors.
Test camera capture.
Test AI inference.
Test motor control with the robot safely lifted.
Test obstacle detection.
Test pump/relay control.
Perform supervised autonomous testing.
⚠️ Hardware Safety

MossClean controls physical motors, sensors and a cleaning pump.

Never run autonomous operation for the first time without:

Reviewing the GPIO pinout.
Checking motor direction.
Checking emergency stop behavior.
Verifying obstacle sensor readings.
Confirming the pump remains OFF during navigation tests.
