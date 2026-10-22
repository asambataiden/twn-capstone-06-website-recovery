# TWN Capstone 06 — Website Monitoring and Recovery

## Overview

This project is my independent implementation of the **Website Monitoring and Recovery** capstone from the TechWorld with Nana DevOps Bootcamp.

The goal is to develop a Python-based solution that monitors a web application, detects persistent availability failures, notifies an operator, and performs controlled recovery when appropriate.

## Learning Objectives

- Implement HTTP health checks with timeouts.
- Distinguish transient failures from persistent outages.
- Apply retry thresholds and recovery cooldowns.
- Separate monitoring from privileged recovery operations.
- Implement notifications and recovery reporting.
- Automate recovery of a Docker-based application.
- Write automated tests and document verification evidence.

## Architecture

The planned system consists of four logical components:

1. Health Monitor — checks application availability.
2. Recovery Policy — determines whether recovery is appropriate.
3. Recovery Executor — performs explicitly authorized actions.
4. Notification Service — reports failures and recovery outcomes.

The monitor will not have unrestricted Docker daemon access.

## Current Status

**Phase:** Project initialization.

Python project configuration and Git repository setup are in progress. Application monitoring, alerting and recovery features have not yet been implemented.

## Development Environment

- Python 3.13
- uv for environment and dependency management
- Git for version control
- Docker for the target application environment

## Local Setup

```bash
uv sync
uv run python --version
```

## Verification

```bash
uv lock --check
```

Automated application tests will be introduced as functionality is implemented.

## Course Attribution

Inspired by the Website Monitoring and Recovery capstone in the TechWorld with Nana DevOps Bootcamp.

The project is being rebuilt independently, with implementation decisions, changes and verification documented through Git commits and project documentation.

## Security

- No credentials or secrets are committed to Git.
- Monitoring and recovery responsibilities are separated.
- Recovery permissions will be restricted.
- Logs and validation evidence will be reviewed for sensitive information before publication.