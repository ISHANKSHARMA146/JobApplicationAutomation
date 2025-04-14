# Job Application Automation System

An AI-driven, fully autonomous system for applying to jobs on Naukri.com. This system combines traditional Selenium automation with an AI decision engine for handling dynamic interactions.

## Features

- Automated login and resume upload on Naukri.com
- Intelligent job navigation and filtering based on preferences
- Computer vision (OCR) for extracting information from web pages
- LLM-powered decision making for dynamic interactions
- Iterative feedback loop for reliable job application process

## Requirements

- Python 3.8+
- Chrome/Firefox browser
- Tesseract OCR engine installed

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/job-application-automation.git
   cd job-application-automation
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Update the configuration file:
   ```
   cp config.example.yaml config.yaml
   ```
   Edit `config.yaml` with your Naukri.com credentials, resume path, and API keys.

## Usage

Run the main application:
```
python src/main.py
```

For more detailed usage, see the [User Guide](docs/UserGuide.md).

## Architecture

This system follows a hybrid approach combining:
- Rule-based automation for stable UI interactions
- AI-powered decision making for dynamic elements
- Computer vision for interpreting the UI

See [Architecture Documentation](docs/Architecture.md) for more details.

## License

MIT 