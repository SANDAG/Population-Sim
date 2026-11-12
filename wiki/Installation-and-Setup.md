# Installation & Setup

Complete guide to installing and configuring SANDAG PopulationSim.

## System Requirements

### Hardware Requirements
- **CPU:** Minimum 22 logical processors (for full parallelization)
  - Recommended: 28+ cores (Intel Xeon or AMD EPYC)
  - Fewer cores supported but slower
- **Memory:** Minimum 64 GB RAM
  - Recommended: 128 GB RAM for optimal performance
  - Each parallel process uses ~3 GB memory
- **Storage:** Minimum 50 GB free disk space
  - SSD strongly recommended
  - ~5 GB for seed data, ~10 GB for outputs per run

### Software Requirements
- **Operating System:** Windows 10/11 or Windows Server 2016+
- **Python:** 3.9, 3.10, 3.11, or 3.12 (3.13+ not yet supported)
- **Package Manager:** [uv](https://docs.astral.sh/uv/) (recommended)
- **Database:** Microsoft SQL Server (any edition)
- **ODBC Driver:** ODBC Driver 17 or 18 for SQL Server

### Network Access
- SQL Server instance with ACS PUMS data
- SQL Server instance with UDM staging forecasts
- GitHub (for repository cloning)
- PyPI (for package downloads)

## Installation Steps

### Step 1: Clone Repository

```powershell
# Navigate to desired installation directory
cd C:\Projects

# Clone from GitHub
git clone https://github.com/SANDAG/Population-Sim.git
cd Population-Sim

# Verify repository structure
dir
# Should see: main.py, pyproject.toml, config.yml, python/, sql/, populationsim/, etc.
```

### Step 2: Install uv Package Manager

```powershell
# Install uv (if not already installed)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify installation
uv --version
# Should output: uv 0.x.x
```

**Why uv?**
- Fast dependency resolution (10-100x faster than pip)
- Automatic virtual environment management
- Lock file for reproducible environments
- Better handling of complex dependency trees

### Step 3: Create Python Environment

```powershell
# uv automatically creates .venv/ and installs dependencies
uv sync

# This command:
# 1. Creates .venv/ directory
# 2. Installs Python 3.9-3.12 if needed
# 3. Installs all dependencies from pyproject.toml
# 4. Installs dev dependencies (black, pytest, ruff)

# Typical output:
# Resolved 45 packages in 2.3s
# Installed 45 packages in 8.7s
```

### Step 4: Activate Virtual Environment

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Command Prompt
.venv\Scripts\activate.bat

# Verify activation (prompt should show (.venv))
python --version
# Should output: Python 3.x.x

# Verify key packages
python -c "import populationsim; print(populationsim.__version__)"
# Should output: 0.10.0
```

### Step 5: Install ODBC Driver (if not present)

```powershell
# Check if ODBC Driver 17 installed
Get-OdbcDriver | Where-Object {$_.Name -like "*SQL Server*"}

# If not present, download and install:
# https://go.microsoft.com/fwlink/?linkid=2249006
# Run installer: msodbcsql_17.x.x.x_x64.msi

# After installation, verify:
python -c "import pyodbc; print(pyodbc.drivers())"
# Should list: 'ODBC Driver 17 for SQL Server'
```

### Step 6: Test Database Connectivity

```powershell
# Test SQL Server connection
python -c "
import sqlalchemy as sql
engine = sql.create_engine('mssql+pyodbc://@YOUR_SERVER/master?trusted_connection=yes&driver=ODBC Driver 17 for SQL Server')
with engine.connect() as conn:
    result = conn.execute(sql.text('SELECT @@VERSION'))
    print('Connection successful:', result.fetchone()[0][:50])
"
```

## Configuration Files

### Creating secrets.yml

⚠️ **CRITICAL:** This file must be created locally and **NEVER** committed to Git

**Template:**

```yaml
sql:
  server: "<SQLInstanceName>"
  schema: "<UDMStagingSchema>"
  output_database: "<SQLoutputDatabaseName>"
```

**Example:**

```yaml
sql:
  server: "SANDAG-SQL01"
  schema: "[udm_staging].[sr15]"
  output_database: "PopulationSim_Production"
```

**Create the file:**

```powershell
# Create secrets.yml from template
@"
sql:
  server: "YOUR_SERVER_NAME"
  schema: "[your_database].[your_schema]"
  output_database: "YOUR_OUTPUT_DB"
"@ | Out-File -FilePath secrets.yml -Encoding utf8

# Edit with your actual credentials
notepad secrets.yml

# Verify it's ignored by git
git check-ignore secrets.yml
# Should output: secrets.yml
```

### Verifying config.yml

The `config.yml` file is version-controlled and should already exist. Verify it contains:

```yaml
version: "v1.0.3-prerelease"
seed_data: "ACS PUMS 5 year 2021"
comments: "No Comments"

sql:
  seed_households: "sql/seed_households.sql"
  seed_persons: "sql/seed_persons.sql"
  mgra_controls: "sql/mgra_controls.sql"
  region_controls: "sql/region_controls.sql"
  mgrabase: "sql/mgrabase.sql"
  load_to_database: False

economic_controls: "data/Economic Team Region Controls.csv"

years:
  - 2022
  - 2026
  - 2029
  - 2032
  - 2035
  - 2040
  - 2050
```

## Environment Verification

Run this verification script before your first run:

```powershell
python -c "
import sys
import importlib

# Check Python version
print(f'Python: {sys.version}')
assert sys.version_info >= (3, 9), 'Python 3.9+ required'
assert sys.version_info < (3, 13), 'Python 3.13+ not yet supported'

# Check key packages
packages = ['populationsim', 'pandas', 'sqlalchemy', 'pyodbc', 'streamlit']
for pkg in packages:
    mod = importlib.import_module(pkg)
    version = getattr(mod, '__version__', 'unknown')
    print(f'{pkg}: {version}')

# Check ODBC drivers
import pyodbc
drivers = [d for d in pyodbc.drivers() if 'SQL Server' in d]
print(f'ODBC Drivers: {drivers}')
assert len(drivers) > 0, 'No SQL Server ODBC driver found'

print('\nAll checks passed! ✓')
"
```

**Expected Output:**
```
Python: 3.11.x (main, ...) [MSC v.xxxx 64 bit (AMD64)]
populationsim: 0.10.0
pandas: 2.2.x
sqlalchemy: 2.0.x
pyodbc: 5.0.x
streamlit: 1.20.x
ODBC Drivers: ['ODBC Driver 17 for SQL Server']

All checks passed! ✓
```

## Common Installation Issues

| Issue | Symptom | Resolution |
|-------|---------|------------|
| uv not found | Command not recognized | Add uv to PATH or reinstall |
| Python version mismatch | uv sync fails with version error | Install Python 3.9-3.12 |
| ODBC driver missing | pyodbc.Error: Data source name not found | Install ODBC Driver 17 |
| SQL connection fails | Login timeout or access denied | Verify SQL Server name and permissions |
| Memory error during sync | Package installation crashes | Close other applications, increase virtual memory |
| Permission denied | Cannot create .venv/ | Run PowerShell as administrator |

## Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| populationsim | 0.10.0 | Core synthesis engine |
| pandas | ≥2.2.0 | Data manipulation |
| sqlalchemy | ≥2.0.25 | Database connectivity |
| pyodbc | ≥5.0.1 | SQL Server ODBC interface |
| streamlit | ≥1.20.0 | Validation dashboard |
| cvxpy[glpk] | ≥1.6.5 | Optimization solver |
| ortools | ≥9.14.6206 | Operations research tools |
| numba | ≥0.60.0 | JIT compilation for performance |

## Next Steps

✅ Installation complete? → [Configuration Reference](Configuration-Reference)  
✅ Ready to run? → [Running PopulationSim](Running-PopulationSim)  
❓ Need help? → [Troubleshooting](Troubleshooting)

---

**For detailed technical documentation:** See [SANDAG_PopulationSim_Documentation.md](../documentation/SANDAG_PopulationSim_Documentation.md) Section 4.1
