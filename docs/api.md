# MossClean Web API

## Overview

The MossClean web application provides HTTP routes for authentication, monitoring, user management, and robot control.

## Backend

The API is implemented using Flask.

```text
Browser
   ↓
HTTP Request
   ↓
Flask Route
   ↓
Application Logic
   ↓
Robot / Database
   ↓
HTTP Response
Main API Areas
Authentication

Handles:

User login
Session management
Logout
Access control
Monitoring

Provides information used by the monitoring dashboard, including robot status and operational information.

Robot Control

Control routes can be used by authorized users to interact with robot operations such as movement and stopping.

User Management

Administrative users can manage registered users and their roles.

Alerts

The application records operational/security alerts and can send notifications through SMTP.

Security

API endpoints that control the robot should be protected from unauthorized access.

Sensitive values must be stored in environment variables and should never be committed to the repository.

Example Request Flow
User Login
    ↓
Authenticated Session
    ↓
Dashboard
    ↓
Robot Status / Control Request
    ↓
Flask Backend
    ↓
Robot State / Hardware
    ↓
Dashboard Update
Development Notes

The API is intended to operate as part of the MossClean web application and should be tested with the robot hardware disconnected before hardware control is enabled.

For the exact route implementation, refer to:
