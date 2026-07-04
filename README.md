# ERP IDOC Monitor

A Python tool that generates, parses, and analyzes SAP IDOC (Intermediate Document) XML files to detect and report integration errors, built as a portfolio project simulating a real-world ERP monitoring workflow.

## Overview

SAP IDOCs are the standard format for exchanging data between SAP and external systems. In production, failed or malformed IDOCs can silently break downstream processes. This tool simulates that pipeline end to end:

1. **Generate** a batch of sample IDOC XML files (including intentionally malformed ones)
2. **Parse** each IDOC into a structured record
3. **Detect errors** across the batch, classified by severity
4. **Report** results as both console output and saved report files

## How It Works

```
main.py
├── src/generator.py       # Generates a batch of sample IDOC XML files
├── src/parser.py          # Parses IDOC XML into structured data
├── src/error_detector.py  # Analyzes parsed batch and flags errors by severity
└── src/reporter.py        # Writes reports to output/
```

Running the tool executes all four stages in sequence, then prints a summary like:

```
========= FINAL SUMMARY =========
 Total Processed  : 50
 Successful       : 42
 Errors           : 8
 High Severity    : 3
 Medium Severity  : 5
==================================

Full reports saved to output/
```

## Getting Started

### Prerequisites

- Python 3.8+

### Installation

```bash
git clone https://github.com/Rishin05/erp-idoc-monitor.git
cd erp-idoc-monitor
pip install -r requirements.txt
```

### Usage

Generate 50 sample IDOCs (default) and run the full pipeline:

```bash
python main.py
```

Generate a custom number of IDOCs:

```bash
python main.py --count 100
```

Skip generation and analyze existing files already in `sample_idocs/`:

```bash
python main.py --skip-gen
```

## Project Structure

```
erp-idoc-monitor/
├── main.py            # Entry point, orchestrates the pipeline
├── src/                # Core generation, parsing, and analysis logic
├── sample_idocs/       # Generated/sample IDOC XML files
├── output/             # Generated reports
└── requirements.txt
```

## Tech Stack

- **Language:** Python
- **XML Parsing:** lxml

## Contact

- **Portfolio:** [rishin.info](https://rishin.info)
- **LinkedIn:** [linkedin.com/in/patelrishin](https://www.linkedin.com/in/patelrishin/)
- **GitHub:** [github.com/Rishin05](https://github.com/Rishin05)
