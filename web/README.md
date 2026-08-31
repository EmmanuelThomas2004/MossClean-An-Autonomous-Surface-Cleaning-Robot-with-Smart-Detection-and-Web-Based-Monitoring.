# MossClean Web Platform

> **Human–robot interaction, monitoring, telemetry, and supervisory control interface for MossClean.**

## Overview

The MossClean Web Platform provides a browser-based interface for monitoring and interacting with the autonomous cleaning robot.

It is designed to connect the operator with the onboard robotic system through a Flask-based application.

## Core Functions

- Real-time robot monitoring
- Live camera visualization
- Robot telemetry
- Remote control
- Authentication
- Role-based access control
- Operational alerts
- Security notifications
- System status visualization

## Architecture

```text
MossClean Robot
       │
       │ Wi-Fi
       ▼
┌─────────────────┐
│ Flask Backend   │
│                 │
│ Authentication  │
│ Robot Control   │
│ Telemetry       │
│ Video           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Web Dashboard   │
│                 │
│ Robot Status    │
│ Live Video      │
│ Telemetry       │
│ Controls        │
│ Alerts          │
└─────────────────┘
         │
         ▼
      Operator
      Technology Stack
Component	Technology
Backend	Flask
Language	Python
Frontend	HTML5
Styling	CSS3
Client Updates	AJAX
Database	SQLite
Authentication	Role-Based Access Control
Video	MJPEG
Notifications	SMTP
Connectivity	Wi-Fi
Planned Structure
web/
├── README.md
├── app.py
├── requirements.txt
│
├── templates/
│   ├── login.html
│   └── dashboard.html
│
└── static/
    ├── css/
    ├── js/
    └── images/
Monitoring

The dashboard is designed to expose important robot information including:

Robot operating state
Battery status
Cleaning-fluid level
Moss detection count
Navigation state
Sensor information
Live camera feed
Remote Control

The web interface can provide authorized users with supervisory control over the robot.

Control capabilities depend on the user's access level and the implemented robot-control interface.

Authentication

The web platform supports role-based access.

Operator

Provides access to normal monitoring and operational functions.

Administrator

Provides elevated access to functions such as:

User management
Manual robot control
Emergency hardware operations
Safety procedures
Security and operational logs
Telemetry

Robot information is transferred from the onboard system to the Flask application.

Sensors
   ↓
Robot State
   ↓
Telemetry
   ↓
Flask Backend
   ↓
Web Dashboard
Security

Sensitive information must never be committed to the repository.

Examples include:

Passwords
SMTP credentials
Secret keys
Authentication tokens
Private configuration

Environment variables should be used for sensitive runtime configuration.

Development

The web platform will be integrated progressively with the MossClean robot software.

Backend, templates, stylesheets, JavaScript, authentication, telemetry, and supporting resources will be maintained as separate components where practical.

Engineering Objective

The MossClean Web Platform serves as the human–robot interaction layer, providing operators with visibility into autonomous operation while enabling controlled supervisory interaction with the physical robot.
