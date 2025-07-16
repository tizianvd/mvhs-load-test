# MVHS Load Testing Framework

A comprehensive load testing framework for the Münchner Volkshochschule (MVHS) website using Locust.

## Quick Start - Locust Web UI

The easiest way to get started is with the Locust web interface:

### Option 1: Using the Quick Start Script
```bash
python start_web_ui.py
```

### Option 2: Direct Locust Command
```bash
python -m locust --web-host=0.0.0.0 --web-port=8089 --host=https://www.mvhs.de
```

### Option 3: Using VS Code Tasks
Use the **"Start Locust Web UI"** task from the VS Code command palette:
- Press `Ctrl+Shift+P` 
- Type "Tasks: Run Task"
- Select "Start Locust Web UI"

## Web Interface Usage

1. **Start the web interface** using one of the methods above
2. **Open your browser** to `http://localhost:8089`
3. **Configure your test**:
   - **Number of users**: Start with 10-50 users
   - **Spawn rate**: Start with 2-5 users per second
   - **Host**: Pre-configured to `https://www.mvhs.de`
4. **Click "Start swarming"** to begin the load test
5. **Monitor results** in real-time through the web dashboard

## User Types Available

The framework includes several user behavior patterns:

- **MVHSNormalUser** - Typical browsing with moderate activity
- **MVHSActiveUser** - More frequent searches and interactions  
- **MVHSPowerUser** - Rapid, focused interactions with intensive searching
- **MVHSBrowserUser** - Casual browsing with minimal search activity
- **MVHSMobileUser** - Touch-optimized behavior patterns

## Project Structure

```
├── locustfile.py           # Main Locust entry point
├── start_web_ui.py         # Quick start script for web UI
├── requirements.txt        # Python dependencies
├── config/                 # Configuration files
│   ├── locust.conf        # Locust configuration
│   ├── stress_test_config.json
│   └── website_profiles.json
├── src/                   # Source code
│   ├── users/            # User behavior definitions
│   ├── tasks/            # Task definitions
│   ├── core/             # Core framework components
│   └── config/           # Configuration managers
└── reports/              # Test reports and results
```

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Locust** (if not already installed):
   ```bash
   pip install locust
   ```

## Available VS Code Tasks

- **Start Locust Web UI** - Launch interactive web interface
- **Light/Medium/Heavy Stress Tests** - Pre-configured test scenarios
- **Generate Analytics Report** - Create comprehensive test reports
- **Clean Reports** - Clear previous test results

## Command Line Testing

For headless (non-interactive) testing:

```bash
# Quick test
python -m locust --headless -u 10 -r 2 -t 1m --html=reports/quick_test.html

# Full test  
python -m locust --headless -u 50 -r 5 -t 5m --html=reports/full_test.html
```

## Configuration

- **Website profiles**: Edit `config/website_profiles.json`
- **User behavior**: Edit `config/stress_test_config.json`
- **Locust settings**: Edit `config/locust.conf`

## Reports

Test results are automatically saved to the `reports/` directory:
- HTML reports with charts and graphs
- CSV files with detailed metrics
- Real-time metrics during web UI testing
