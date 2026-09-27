# Running with Streamlit

This guide explains how to run the Multi-Agent Software Development Team application using Streamlit.

## Prerequisites

1. **Python 3.8+** with pip installed
2. **Node.js 16+** with npm installed

## Installation Steps

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Node.js Dependencies

```bash
npm install
```

## Running the Application

### Start with Streamlit

```bash
python -m streamlit run streamlit_app.py
```

Or alternatively:

```bash
streamlit run streamlit_app.py
```

The Streamlit interface will open automatically in your browser (typically at `http://localhost:8501`).

## What Happens?

1. The Streamlit app (`streamlit_app.py`) starts on port 8501
2. It automatically launches the Node.js/Express server on port 3000
3. The Node.js server serves the React frontend
4. The React UI is embedded in the Streamlit interface via an iframe

## How It Works

- **Streamlit App** (`streamlit_app.py`): Entry point and wrapper
- **Node.js Server** (`server.ts`): Backend API that manages the Python agents
- **React Frontend** (`src/`): User interface for interacting with the multi-agent system
- **Python Agents** (`agents/`, `orchestrator.py`): The actual multi-agent software development pipeline

## Troubleshooting

### Port Already in Use

If port 3000 or 8501 is already in use:

**For Streamlit (port 8501):**
```bash
streamlit run streamlit_app.py --server.port 8502
```

**For Node.js (port 3000):**
Edit `server.ts` and change `const PORT = 3000;` to another port, then update `streamlit_app.py` to match.

### Dependencies Not Installed

The Streamlit interface will detect missing dependencies and provide an "Install Dependencies" button. Click it to automatically install Node.js packages.

### Server Won't Start

1. Make sure Node.js is installed: `node --version`
2. Make sure npm is installed: `npm --version`
3. Try restarting the server using the "🔄 Restart Server" button in the Streamlit sidebar

### The Application Doesn't Load

Wait 5-10 seconds after starting for the Node.js server to fully initialize.

## Features

The application includes:

- ✅ Requirements Analysis Agent
- ✅ Architecture Design Agent
- ✅ Code Generation Agent
- ✅ Code Review Agent
- ✅ Test Generation & Execution Agent
- ✅ Bug Fix Loop Agent
- ✅ Documentation Generation Agent
- ✅ Git Integration with Commit History
- ✅ GitHub Push Support
- ✅ Human-in-the-Loop Approval Gates

## Notes

- All existing functionality is preserved
- No changes were made to the core application logic
- The Streamlit wrapper simply provides an alternative entry point
- You can still run the application directly with `npm run dev` if preferred
