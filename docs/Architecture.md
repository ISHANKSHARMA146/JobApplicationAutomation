# Architecture Documentation

## System Overview

The Job Application Automation system is designed with a hybrid architecture that combines rule-based automation with AI-driven decision making. This document outlines the high-level architecture, component interactions, and workflow of the system.

## Components

### 1. Core Components

#### Automation Layer
- **Browser Automation Module**: Manages browser interactions using Selenium WebDriver
- **Login Module**: Handles authentication on Naukri.com
- **Resume Upload Module**: Manages resume uploading and updating
- **Job Navigation Module**: Handles navigation through job listings

#### AI Layer
- **OCR Module**: Extracts textual information from web page screenshots
- **Object Detection Module**: Identifies UI elements on the page
- **LLM Decision Module**: Makes decisions based on page context and system state

#### Orchestration
- **Decision Engine**: Coordinates between automation and AI components
- **Feedback Loop Handler**: Manages verification of actions and next steps

### 2. Support Components

- **Logger**: Maintains detailed logs of system operations
- **Configuration Manager**: Handles system settings and credentials
- **Utility Functions**: Provides helper functions for common tasks

## Workflow

```
┌────────────────────┐
│  Initialization &  │
│   Configuration    │
└──────────┬─────────┘
           │
┌──────────▼─────────┐
│    Selenium-based  │
│      Login         │
└──────────┬─────────┘
           │
┌──────────▼─────────┐
│  Navigate to Job   │
│     Listings       │
└──────────┬─────────┘
           │
┌──────────▼─────────┐    ┌────────────────────┐
│   Capture Screen   │◄───┤   Feedback Loop    │
└──────────┬─────────┘    └────────┬───────────┘
           │                       ▲
┌──────────▼─────────┐             │
│    OCR & Object    │             │
│     Detection      │             │
└──────────┬─────────┘             │
           │                       │
┌──────────▼─────────┐             │
│  LLM Decision for  │             │
│    Next Action     │             │
└──────────┬─────────┘             │
           │                       │
┌──────────▼─────────┐             │
│  Execute Action    ├─────────────┘
│  (Click, Type, etc)│
└──────────┬─────────┘
           │
┌──────────▼─────────┐
│    Application     │
│     Complete?      │
└──────────┬─────────┘
           │
      ┌────▼───┐
      │  End   │
      └────────┘
```

## Data Flow

1. **Input**: Configuration settings, credentials, job search criteria
2. **Processing**:
   - Browser state is captured as screenshots
   - OCR extracts text from screenshots
   - Object detection identifies UI elements
   - LLM analyzes the extracted data and decides the next action
   - Decision engine translates LLM output to Selenium actions
3. **Output**: Completed job applications, logs of system activity

## Decision Making Process

The system uses a combination of deterministic rules and AI inference:

1. **Rule-based decisions** for stable, predictable UI elements (login forms, resume upload)
2. **AI-based decisions** for dynamic content (job descriptions, application questions)

The LLM decision module follows this process:
- Receives OCR output and object detection results
- Analyzes the current state of the page
- Determines the appropriate action (click, type, select, etc.)
- Generates coordinates or element selectors for the action

## Error Handling

The system implements robust error handling:

1. **Retry Mechanism**: Retries failed operations with exponential backoff
2. **Error Recovery**: Attempts to recover from errors by returning to known states
3. **Logging**: Detailed logging of all operations for debugging

## Extensibility

The modular architecture allows for easy extension:
- Support for additional job portals beyond Naukri.com
- Integration with other AI services
- Custom application strategies for different job types 