# MossClean Raspberry Pi Pinout

## Overview

This document records the GPIO assignments used by the MossClean robot controller.

> **Warning:** These GPIO pins directly interface with motors, sensors and the cleaning pump. Verify the wiring before powering the system.

## Ultrasonic Sensors

| Sensor | Trigger | Echo |
|---|---:|---:|
| Front | GPIO 17 | GPIO 27 |
| Back | GPIO 5 | GPIO 6 |
| Left | GPIO 26 | GPIO 21 |
| Right | GPIO 9 | GPIO 11 |

## Motor Control

| Function | GPIO |
|---|---:|
| Left PWM | GPIO 19 |
| Right PWM | GPIO 13 |
| Motor IN1 | GPIO 24 |
| Motor IN2 | GPIO 16 |
| Motor IN3 | GPIO 22 |
| Motor IN4 | GPIO 23 |

The motor driver is an L298N.

## Wheel Encoders

| Encoder | GPIO |
|---|---:|
| Left encoder | GPIO 20 |
| Right encoder | GPIO 25 |

## Cleaning Pump

| Function | GPIO |
|---|---:|
| Pump relay | GPIO 4 |

The pump relay uses **BCM GPIO 4**, which corresponds to **physical pin 7**.

## IMU

The MPU-6050 is connected through the Raspberry Pi's I²C interface.

## Camera

The OV5647 camera is used for image capture and AI-based moss detection.

## Safety

Before testing:

1. Disconnect the pump.
2. Lift the robot from the ground during initial motor tests.
3. Verify GPIO numbering.
4. Check motor-driver wiring.
5. Test emergency stop behavior.
6. Confirm the pump relay is OFF before connecting the cleaning system.

Never connect motors or the pump directly to Raspberry Pi GPIO pins.
