# ITGC Dashboard: User Access, Change & Incident Management

This Streamlit-based application supports three primary IT Governance tasks:

1. **User Access Review**
2. **Change Management Review**
3. **Incident Management Review**

## Features

### User Access Review
- Upload and merge HR, User Access, and Active Directory files
- Perform left joins with optional column selection
- Calculate dormancy, AD-HR joining differences, and GAP days
- Identify access inconsistencies between IT and non-IT users
- Generate random samples
- Export final datasets

### Change Management
- Detect missing or inconsistent change request dates
- Analyze turnaround time (days to resolve)
- Support for data checks and sampling
- Export results

### Incident Management
- Analyze duration from start to resolved and resolved to closed
- Simple date-based validation
- Export enhanced data

## How to Use
1. Run the application:
   ```bash
   streamlit run app.py
