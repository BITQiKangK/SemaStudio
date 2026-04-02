# LLM-based Natural Language Query Optimizer for DuckDB

## Project Structure

```text
.
├── backend/                 # Backend service
│   ├── app.py               # Flask entry point
│   ├── config.py            # Configuration settings
│   ├── db_session.py        # DuckDB session management
│   ├── duckdb_utils.py      # DuckDB utility functions
│   ├── duckdb_binary.py     # DuckDB binary handling
│   ├── requirements.txt     # Python dependencies
│   └── db/                  # DuckDB database files
├── frontend/                # Web UI
│   ├── src/
│   │   ├── components/      # Vue components
│   │   ├── pages/           # Page components
│   │   ├── router/          # Vue Router configuration
│   │   ├── utils/           # Utility functions
│   │   ├── config/          # Frontend configuration
│   │   ├── assets/          # Static assets
│   │   ├── App.vue          # Root component
│   │   └── main.js          # Entry point
│   ├── index.html           # HTML template
│   ├── package.json         # Node.js dependencies
│   └── vite.config.js       # Vite configuration
├── .gitignore               # Git ignore rules
└── README.md                # Project documentation

```

---

## Installation

### Requirements

requirements.txt

### Backend Setup

```bash
git clone git@github.com:arui408/Sigmod26demo.git
cd Sigmod26demo
pip install -r backend/requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

---

## Usage

### Start Backend

```bash
python backend/app.py
```

### Start Frontend

```bash
cd frontend
npm run dev
```

