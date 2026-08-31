# MossClean Algorithms

This document describes the core algorithms used by MossClean for autonomous navigation, localization, perception, obstacle handling, and targeted cleaning.

---

## 1. Boustrophedon Coverage

### Purpose

Provides systematic coverage of the target surface.

### Principle

The robot follows an alternating lawnmower-style traversal pattern:

```text
→ → → → → → →
              ↓
← ← ← ← ← ← ←
              ↓
→ → → → → → →

The alternating sweep pattern is designed to reduce unnecessary random movement while systematically traversing the available surface.

Role in MossClean

Boustrophedon coverage forms the primary coverage strategy during autonomous surface traversal.

2. A* Search
Purpose

Provides point-to-point pathfinding when the robot needs to reach a particular unexplored or required region.

Cost Function

A* evaluates a path using:

f(n) = g(n) + h(n)

Where:

g(n) = accumulated path cost
h(n) = estimated remaining cost
f(n) = total estimated path cost

MossClean uses a Manhattan-distance heuristic for its grid-based navigation.

Role in MossClean

A* complements the coverage planner by providing pathfinding toward frontier or missed regions.

3. Proportional Heading Control
Purpose

Corrects mechanical drift during straight-line traversal.

The controller compares the desired heading with the measured heading and calculates an error.

Heading Error
      │
      ▼
 Proportional Gain
      │
      ▼
 Motor Correction
   ┌──┴──┐
   ▼     ▼
Left    Right
PWM     PWM

The motor PWM values are dynamically adjusted according to the heading error.

Role in MossClean

This helps maintain approximately parallel coverage rows during long navigation sweeps.

4. Kinematic Odometry / Dead Reckoning
Purpose

Estimates the robot's position without GPS.

The system combines:

Wheel encoder measurements
IMU heading information
Robot motion parameters

The robot updates its estimated position based on movement and heading.

Conceptually:

Encoder Pulses ──┐
                 ├──► State Estimation ──► X, Y, Heading
IMU Heading ─────┘
Role in MossClean

This provides GPS-independent position tracking for autonomous navigation.

5. Raycasting
Purpose

Projects distance measurements from ultrasonic sensors into the internal occupancy grid.

Conceptually:

Robot
  │
  ├──────────────► FREE
  │
  │
  └──────────────► OBSTACLE

The sensor measurement is projected outward from the robot's estimated position.

Traversed cells can be marked as free space while the detected terminal region can be represented as an obstacle.

Role in MossClean

Raycasting allows the robot to progressively build a representation of its surrounding environment.

6. YOLO Moss Detection
Purpose

Detect moss patches from camera images.

The MossClean perception pipeline follows:

Camera Frame
     │
     ▼
Preprocessing
     │
     ▼
YOLOv11n
     │
     ▼
Bounding Boxes
     │
     ▼
Confidence Filtering
     │
     ▼
Moss Detection

The lightweight YOLOv11n model is intended for edge-based inference on the Raspberry Pi platform.

The documented detection threshold is 60% confidence.

Role in MossClean

The detector provides the visual input used by the cleaning decision logic.

7. Reactive Obstacle Avoidance
Purpose

Prevents collisions during autonomous movement.

The robot continuously evaluates ultrasonic sensor measurements.

When an obstacle is detected:

Obstacle Detected
       │
       ▼
     STOP
       │
       ▼
Evaluate Surroundings
       │
   ┌───┴───┐
   ▼       ▼
 Left     Right
   │       │
   └───┬───┘
       ▼
 Select Safer Direction
       │
       ▼
   Bypass Obstacle
       │
       ▼
 Resume Navigation

The documented system performs a bypass maneuver and attempts to realign with the original navigation direction after clearing the obstacle.

An anti-trap behavior is also included for repeated unsuccessful bypass attempts.

8. Moss Detection and Spray Decision

The cleaning decision pipeline connects perception to physical actuation.

        Camera
           │
           ▼
      YOLO Detection
           │
           ▼
     Moss Detected?
       ┌───┴───┐
      NO       YES
       │         │
       │         ▼
       │      Stop Robot
       │         │
       │         ▼
       │      Activate Pump
       │         │
       │         ▼
       │    Targeted Spray
       │         │
       └─────────┴──────► Resume

The implemented MossController performs a detection window while the robot is stationary. When moss is detected, the controller activates the pump for the configured spray duration and then switches the pump off.

9. Algorithm Integration

The algorithms operate as a coordinated robotics pipeline:

                  ┌──────────────┐
                  │ Camera + AI  │
                  │ YOLOv11n     │
                  └──────┬───────┘
                         │
                         ▼
                  Moss Detection
                         │
                         ▼
                  Spray Decision
                         │
                         ▼
                     Pump ON


Encoders + IMU ──► Odometry ──► Position
                              │
                              ▼
                       Occupancy Grid
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
         Coverage Planner              A* Search
                │                           │
                └─────────────┬─────────────┘
                              ▼
                       Motion Controller
                              │
                              ▼
                    Obstacle Avoidance
                              │
                              ▼
                           Motors
10. Algorithmic Design Philosophy

MossClean does not depend on a single algorithm.

Instead, specialized algorithms are combined so that each subsystem performs a specific responsibility:

Algorithm	Primary Responsibility
Boustrophedon	Surface coverage
A*	Point-to-point pathfinding
Proportional Control	Heading correction
Kinematic Odometry	Position estimation
Raycasting	Occupancy-grid projection
YOLOv11n	Moss detection
Reactive Avoidance	Collision prevention
Anti-Trap Logic	Recovery from blocked environments

This layered approach allows perception, localization, planning, control, and actuation to cooperate while remaining conceptually separated.

11. Implementation Notes

The current implementation separates moss perception and spray actuation into a dedicated MossController.

The controller owns:

Camera initialization
YOLO model loading
Moss inference
Detection image storage
Pump relay control
Spray timing
Camera cleanup

Navigation and world-model responsibilities remain outside this controller.

This separation supports modular development and future optimization of individual subsystems.

12. Future Algorithm Improvements

Potential future improvements include:

More robust localization
Improved sensor fusion
Adaptive coverage planning
Dynamic obstacle prediction
Improved moss segmentation
Confidence-aware spray control
Closed-loop spray verification
Simulation-based navigation testing
Edge inference optimization
Learning-based navigation policies

These are potential development directions and are not presented as currently implemented features.
