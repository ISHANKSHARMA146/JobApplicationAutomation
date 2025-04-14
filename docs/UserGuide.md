# User Guide

This guide provides instructions for setting up, configuring, and using the Job Application Automation system for Naukri.com.

## Prerequisites

Before using this system, ensure you have the following:

1. **Python 3.8 or higher** installed on your system
2. **Chrome or Firefox browser** installed
3. **Tesseract OCR** installed
   - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - Linux: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`
4. **Valid Naukri.com account** with login credentials
5. **An up-to-date resume file** (PDF format recommended)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/job-application-automation.git
   cd job-application-automation
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a configuration file:
   ```
   cp config.yaml.example config.yaml
   ```

4. Edit the configuration file with your details (see Configuration section below)

## Configuration

The system is configured through the `config.yaml` file. Here's what each section means:

### Credentials
```yaml
credentials:
  username: "your_email@example.com"
  password: "your_password"
```
Enter your Naukri.com login credentials.

### File Paths
```yaml
files:
  resume_path: "path/to/your/resume.pdf"
  log_directory: "logs/"
  screenshot_directory: "screenshots/"
```
Specify the path to your resume file and directories for logs and screenshots.

### Browser Settings
```yaml
browser:
  type: "chrome"  # or "firefox"
  headless: false  # set to true to run without UI
  timeout: 30  # seconds
```
Choose your browser and configure if it should run headlessly.

### Tesseract OCR Configuration
```yaml
ocr:
  tesseract_path: "C:/Program Files/Tesseract-OCR/tesseract.exe"  # Update with your path
  language: "eng"
```
Set the path to your Tesseract OCR installation.

### LLM API Configuration
```yaml
llm:
  provider: "openai"
  api_key: "your_api_key_here"
  model: "gpt-4"
  max_tokens: 1000
  temperature: 0.7
```
Configure your LLM API access. You will need a valid API key.

### Job Search Criteria
```yaml
job_criteria:
  keywords: ["python", "software engineer", "developer"]
  experience: "3-5 years"
  locations: ["Bangalore", "Mumbai", "Remote"]
  exclude_terms: ["senior", "principal", "manager"]
  max_applications_per_session: 10
```
Define your job search parameters.

### Application Preferences
```yaml
application:
  cover_letter: true
  auto_fill_questions: true
  max_retries: 3
  delay_between_actions: 2  # seconds
```
Configure how the system handles applications.

## Usage

### Basic Usage

To start the application automation:

```
python src/main.py
```

This will:
1. Log into Naukri.com with your credentials
2. Navigate to the job search page
3. Apply filters based on your criteria
4. Process job listings and apply to suitable positions

### Advanced Usage

#### Resume Update Only Mode

To only update your resume without applying to jobs:

```
python src/main.py --update-resume-only
```

#### Specific Job Search

To search for specific job types:

```
python src/main.py --keywords "data scientist,machine learning"
```

#### Limiting Applications

To limit the number of applications in a session:

```
python src/main.py --max-applications 5
```

## Monitoring

The system creates detailed logs in the specified log directory. You can monitor progress in real-time:

```
tail -f logs/latest.log
```

Screenshots of each step are saved in the screenshots directory for later review.

## Troubleshooting

### Common Issues

#### Browser Driver Issues

If you encounter browser driver errors:

1. Check that you have the correct WebDriver for your browser version
2. Try updating your browser to the latest version
3. Use the `webdriver-manager` to automatically download the correct driver:
   ```python
   from webdriver_manager.chrome import ChromeDriverManager
   driver = webdriver.Chrome(ChromeDriverManager().install())
   ```

#### OCR Recognition Problems

If OCR is not recognizing text correctly:

1. Check that Tesseract is correctly installed and the path is properly set
2. Adjust browser window size to ensure content is clearly visible
3. Try increasing the screenshot quality in the configuration

#### API Rate Limiting

If you encounter LLM API rate limits:

1. Reduce the frequency of API calls by increasing delay settings
2. Consider using a different API provider or upgrading your plan
3. Implement caching for common LLM queries

### Getting Help

If you encounter issues not covered here:

1. Check the detailed logs for error messages
2. Open an issue on the GitHub repository with:
   - Description of the problem
   - Relevant log excerpts
   - Screenshots if applicable
   - Steps to reproduce the issue 