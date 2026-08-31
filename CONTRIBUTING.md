# Contributing to MossClean

Thank you for your interest in MossClean.

MossClean is an autonomous surface-cleaning robotics platform combining embedded systems, edge AI, computer vision, autonomous navigation, robotic actuation, and web-based monitoring.

## Development Areas

Contributions and improvements may focus on:

- Edge AI and moss detection
- Computer vision
- Autonomous navigation
- Sensor fusion and odometry
- Obstacle avoidance
- Robot motion control
- Spray-control logic
- Raspberry Pi integration
- Flask web monitoring
- Security and authentication
- Testing and simulation
- Documentation

## Before Contributing

Please:

1. Understand the existing architecture before modifying core modules.
2. Keep hardware-specific logic separated from higher-level navigation and application logic.
3. Avoid committing passwords, API keys, email credentials, tokens, or other secrets.
4. Test changes where practical before submitting them.
5. Update documentation when a change affects system behavior or configuration.

## Pull Requests

A good pull request should include:

- A clear description of the change
- The reason for the change
- Relevant testing performed
- Any hardware or software requirements
- Screenshots or logs when they help demonstrate the change

## Commit Messages

Use clear, descriptive commit messages.

Examples:

```text
feat: improve moss detection pipeline
fix: correct ultrasonic obstacle handling
docs: update deployment instructions
refactor: separate navigation and actuation logic
test: add navigation controller tests
