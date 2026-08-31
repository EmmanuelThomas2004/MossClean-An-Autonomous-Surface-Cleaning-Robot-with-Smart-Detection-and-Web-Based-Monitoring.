# MossClean Web Architecture

## Overview

MossClean includes a Flask-based web interface for monitoring and controlling the robot.

The web layer provides:

- User authentication
- Role-based access
- Live monitoring
- Robot telemetry
- Camera/video display
- User management
- Alert visibility
- Robot control

## Architecture

```text
                MossClean Robot
                      │
        ┌─────────────┼─────────────┐
        │             │             │
     Camera        Sensors       Robot State
        │             │             │
        └─────────────┼─────────────┘
                      ↓
                Flask Backend
                      │
          ┌───────────┼───────────┐
          ↓           ↓           ↓
     Authentication  API      Telemetry
          │           │           │
          └───────────┼───────────┘
                      ↓
               Web Interface
                      │
          ┌───────────┼───────────┐
          ↓           ↓           ↓
       Dashboard    Users       Alerts

       Technology Stack
Component	Technology
Backend	Flask
Language	Python
Frontend	HTML5 / CSS3
Client Updates	AJAX
Database	SQLite
Authentication	Werkzeug password hashing
Camera	Picamera2 / OpenCV
Alerts	SMTP
Web Pages

The interface contains pages for:

Login
Dashboard
User management
User editing
Monitoring
Administrative controls
Authentication

Users authenticate through the Flask application.

Passwords should be stored using secure password hashing rather than plain text.

Administrative functionality should be restricted to authorized users.

Monitoring

The dashboard is designed to expose robot information such as:

Robot movement state
Detection state
Camera feed
Alerts
Operational information
Alerts

The system can record operational/security events and send email notifications through SMTP.

Examples include:

Stuck condition
Theft/security event
Low liquid condition
Static Assets

Website CSS is stored under:

web/static/css/

Website images are stored under:

web/static/images/
Templates

HTML templates are stored under:

web/templates/

The base template provides the shared visual structure used by the other pages.

Security Notes

Never commit:

SMTP passwords
API keys
Database credentials
.env files
User passwords
Other private credentials

Production deployments should use environment variables for secrets and should run behind appropriate transport and application security controls.
