# Troubleshooting

Common issues and solutions for PopulationSim.

## Quick Diagnostic Checklist

Before deep troubleshooting, verify:

1. ✓ Python environment activated
2. ✓ All dependencies installed (`uv sync`)
3. ✓ `secrets.yml` created with correct credentials
4. ✓ Database connectivity working
5. ✓ Sufficient disk space (~10 GB per year)
6. ✓ ODBC Driver 17 installed

## Installation Issues

### uv not found

**Symptom:**
```powershell
uv : The term 'uv' is not recognized...
```

**Solution:**
```powershell
# Reinstall uv
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Add to PATH manually if needed
$env:Path += ";$env:USERPROFILE\.cargo\bin"

# Verify
uv --version
```

### Python Version Mismatch

**Symptom:**
```
uv sync fails: Python 3.13 not compatible
```

**Solution:**
```powershell
# Install compatible Python version
uv python install 3.11

# Or specify version explicitly
uv sync --python 3.11
```

### ODBC Driver Missing

**Symptom:**
```python
pyodbc.Error: [IM002] Data source name not found
```

**Solution:**
```powershell
# Check installed drivers
Get-OdbcDriver | Where-Object {$_.Name -like "*SQL Server*"}

# If not present, download and install:
# https://go.microsoft.com/fwlink/?linkid=2249006

# After installation, verify:
python -c "import pyodbc; print(pyodbc.drivers())"
```

### Permission Denied Creating .venv

**Symptom:**
```
PermissionError: [WinError 5] Access is denied: '.venv'
```

**Solution:**
```powershell
# Run PowerShell as Administrator
# Or change directory permissions
icacls . /grant:r "$env:USERNAME:(OI)(CI)F"

# Retry
uv sync
```

## Database Connection Issues

### SQL Server Timeout

**Symptom:**
```python
sqlalchemy.exc.OperationalError: Login timeout expired
```

**Solution:**
```powershell
# Test network connectivity
Test-NetConnection -ComputerName <SERVER> -Port 1433

# Check server name in secrets.yml
# Try with instance name if needed: "SERVER\INSTANCE"

# Increase timeout in connection string (requires code edit)
# engine = create_engine(..., connect_args={'timeout': 60})
```

### Schema Not Found

**Symptom:**
```sql
Invalid object name '[schema].[table]'
```

**Solution:**
```yaml
# Check secrets.yml format
sql:
  schema: "[database].[schema]"  # Must have square brackets
  
# Verify schema exists
# Run in SQL Server Management Studio:
SELECT * FROM sys.schemas WHERE name = 'your_schema'
```

### Authentication Failed

**Symptom:**
```
Login failed for user 'DOMAIN\username'
```

**Solution:**
```powershell
# Verify Windows Authentication
# Check SQL Server allows Windows auth
# Verify user has db_datareader role

# Test connection manually:
python -c "
import sqlalchemy as sql
engine = sql.create_engine('mssql+pyodbc://@SERVER/master?trusted_connection=yes&driver=ODBC Driver 17 for SQL Server')
with engine.connect() as conn:
    print(conn.execute(sql.text('SELECT @@VERSION')).fetchone())
"
```

## Execution Issues

### PopulationSim Convergence Failure

**Symptom:**
```
RuntimeError: Balancing did not converge after 5000 iterations
```

**Root Causes:**
1. Conflicting control totals
2. Insufficient seed diversity
3. Too restrictive max_expansion_factor

**Solutions:**

**Option 1: Increase iterations**
```yaml
# populationsim/configs/settings.yaml
max_iterations: 10000
```

**Option 2: Loosen convergence criteria**
```yaml
absolute_convergence: 0.001  # Was 0.0001
relative_convergence: 0.001  # Was 0.0001
```

**Option 3: Increase expansion factor**
```yaml
max_expansion_factor: 40  # Was 30
```

**Option 4: Check control totals**
```python
# Verify controls sum correctly
import pandas as pd
controls = pd.read_csv('populationsim/data/mgra_controls.csv')

# Check household size categories sum to Total_HH
controls['size_sum'] = controls[['HHSize_1', 'HHSize_2', 'HHSize_3', 'HHSize_4Plus']].sum(axis=1)
assert (controls['Total_HH'] == controls['size_sum']).all()
```

### Memory Error / Process Killed

**Symptom:**
```
MemoryError: Unable to allocate array
```
or process suddenly terminates

**Solutions:**

**Option 1: Reduce parallel processes**
```yaml
# populationsim/configs_mp/settings.yaml
num_processes: 11  # Was 22
```

**Option 2: Close other applications**
```powershell
# Monitor memory usage
Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 10
```

**Option 3: Increase virtual memory**
```
System Properties → Advanced → Performance Settings → Advanced → Virtual Memory
Set to 1.5x physical RAM
```

**Option 4: Process MGRAs sequentially**
```yaml
# populationsim/configs_mp/settings.yaml
multiprocess: False
# Warning: Very slow (~13 hours)
```

### Disk Full Error

**Symptom:**
```
OSError: [Errno 28] No space left on device
```

**Solution:**
```powershell
# Check free space
Get-PSDrive C

# Clean up old outputs
Remove-Item -Recurse -Force output\old_runs\*

# Clean up temp files
Remove-Item -Recurse -Force $env:TEMP\*

# Move output to larger drive
# Edit main.py to change output directory
```

### Permission Denied Writing Outputs

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: 'output/2022/'
```

**Solution:**
```powershell
# Run as Administrator
# Or fix permissions
icacls output /grant:r "$env:USERNAME:(OI)(CI)F" /T

# Check no other process has files open
Get-Process | Where-Object {$_.Path -like "*output*"}
```

### Control Mismatch Warnings

**Symptom:**
```
WARNING: MGRA 12345 control 'HHSize_1' differs by 15%
```

**Solutions:**

**Option 1: Check control data quality**
```python
import pandas as pd
mgra_controls = pd.read_csv('populationsim/data/mgra_controls.csv')

# Find MGRAs with suspicious values
weird = mgra_controls[mgra_controls['Total_HH'] == 0]
print(f"MGRAs with zero households: {len(weird)}")

# Check for negative values
negatives = mgra_controls[mgra_controls < 0].dropna(how='all')
print(f"Negative values found: {len(negatives)}")
```

**Option 2: Adjust importance weights**
```csv
# populationsim/configs/controls.csv
# Lower importance for problematic controls
HHSize_1,mgra,households,10000,households.NP == 1  # Was 250000
```

**Option 3: Verify geographic crosswalk**
```python
crosswalk = pd.read_csv('populationsim/data/geo_cross_walk.csv')

# Check for missing MGRAs
control_mgras = set(mgra_controls['mgra'])
crosswalk_mgras = set(crosswalk['mgra'])
missing = control_mgras - crosswalk_mgras
print(f"MGRAs in controls but not crosswalk: {missing}")
```

## Group Quarters Issues

### GQ Mismatch

**Symptom:**
```
ERROR: final_summary_mgra_gq shows non-zero differences
```

**This indicates a bug** - GQ sampling should produce exact matches

**Solution:**
```powershell
# Check GQ control totals
python -c "
import pandas as pd
gq_sum = pd.read_csv('output/2022/final_summary_mgra_gq.csv')
for gq_type in ['gq_mil_pop', 'gq_college_pop', 'gq_other_pop']:
    diff = (gq_sum[f'{gq_type}_result'] - gq_sum[f'{gq_type}_control']).sum()
    print(f'{gq_type}: {diff}')
"

# If non-zero, contact development team
# Possible causes:
# - Bug in generate_gq.py
# - Seed GQ data mismatch
# - Control file corruption
```

## Validation Dashboard Issues

### Streamlit Won't Start

**Symptom:**
```
streamlit: command not found
```

**Solution:**
```powershell
# Verify streamlit installed
.venv\Scripts\Activate.ps1
python -c "import streamlit; print(streamlit.__version__)"

# Reinstall if needed
uv pip install streamlit>=1.20.0

# Launch with full path
python -m streamlit run report/report.py
```

### Dashboard Shows No Runs

**Symptom:**
Dashboard loads but "No runs found" message appears

**Solutions:**

**For Local Output mode:**
```powershell
# Verify output folders exist
Get-ChildItem output\

# Check required files present
Get-ChildItem output\2022\

# Verify timing_log.csv exists (required)
```

**For Database mode:**
```sql
# Check database has runs
SELECT * FROM populationsim.runs WHERE loaded = 1

# Verify secrets.yml matches database
```

### Dashboard Displays Wrong Data

**Symptom:**
Selected run shows data from different year

**Solution:**
```powershell
# Clear Streamlit cache
Remove-Item -Recurse -Force $env:USERPROFILE\.streamlit\cache\

# Restart dashboard
streamlit run report/report.py
```

## Output File Issues

### Missing Output Files

**Symptom:**
Some expected files not created in `output/{year}/`

**Checklist:**
```powershell
# Expected files per year (14 total):
# - synthetic_households_2022.csv
# - synthetic_persons_2022.csv
# - mgra15_based_input_2022.csv
# - synthetic_households.csv
# - synthetic_persons.csv
# - synthetic_households_gq.csv
# - synthetic_persons_gq.csv
# - summary_mgra.csv
# - summary_mgra_PUMA.csv
# - summary_region_1.csv
# - final_summary_mgra_gq.csv
# - mgra_controls.csv
# - region_controls.csv
# - timing_log.csv

Get-ChildItem output\2022\ | Measure-Object
# Should show 14 files
```

**Solution:**
```powershell
# Check console output for errors
# Check populationsim.log for failures
Get-Content populationsim.log | Select-String "ERROR"

# Rerun if partial failure
Remove-Item -Recurse -Force output\2022\
python main.py
```

### Empty or Corrupt Output Files

**Symptom:**
Files created but 0 bytes or unreadable

**Solution:**
```powershell
# Check disk space during run
while ($true) {
    Get-PSDrive C
    Start-Sleep -Seconds 60
}

# Check for permission issues
# Check for antivirus interference (exclude .venv\ and output\)

# Verify file contents
python -c "
import pandas as pd
try:
    df = pd.read_csv('output/2022/synthetic_households_2022.csv')
    print(f'Rows: {len(df)}, Columns: {len(df.columns)}')
except Exception as e:
    print(f'Error reading file: {e}')
"
```

## Performance Issues

### Run Takes Too Long

**Expected times:**
- Per year: ~70 minutes
- All 7 years: ~8 hours

**If much longer:**

**Check database performance:**
```powershell
# Monitor query execution time
# Look for "Building controls for {year}" to "Running populationsim" time
# Should be < 30 seconds

# If slow, check:
# - Network latency to SQL Server
# - SQL Server load
# - Database query plans
```

**Check CPU utilization:**
```powershell
# During sub_balancing phase, should see 22 python processes
Get-Process python

# If not, check num_processes setting
```

**Check disk I/O:**
```powershell
# Use Resource Monitor (resmon.exe)
# Check for disk queue length
# SSD strongly recommended
```

### Sudden Performance Drop

**Symptom:**
First year runs fast, subsequent years slow

**Solutions:**

**Option 1: Check disk fragmentation**
```powershell
Optimize-Volume -DriveLetter C -Analyze
```

**Option 2: Check memory pressure**
```powershell
# Monitor available RAM
while ($true) {
    $mem = Get-WmiObject -Class Win32_OperatingSystem
    $freeGB = [math]::Round($mem.FreePhysicalMemory / 1MB, 2)
    Write-Host "Free RAM: $freeGB GB"
    Start-Sleep -Seconds 60
}
```

**Option 3: Restart between years**
```yaml
# Edit config.yml to run years one at a time
years:
  - 2022  # Run this
  
# After completion:
years:
  - 2026  # Run next
```

## Getting Help

If issues persist after trying these solutions:

1. **Check logs:**
   - Console output
   - `populationsim.log`
   - `populationsim_PUMA*.log` (if multiprocessing)

2. **Gather diagnostics:**
   ```powershell
   # System info
   systeminfo > diagnostics.txt
   
   # Python environment
   .venv\Scripts\Activate.ps1
   pip list >> diagnostics.txt
   
   # Configuration
   Get-Content config.yml >> diagnostics.txt
   Get-Content populationsim\configs\settings.yaml >> diagnostics.txt
   ```

3. **Document the issue:**
   - What command was run?
   - What was the expected behavior?
   - What actually happened?
   - Full error message
   - Relevant log excerpts

4. **Contact support:**
   - SANDAG Modeling team
   - Include diagnostics file
   - Reference this troubleshooting guide

## Common Error Messages

| Error Message | Likely Cause | Quick Fix |
|--------------|--------------|-----------|
| `Login timeout expired` | Database connectivity | Check network, verify server name |
| `Balancing did not converge` | Control conflicts | Increase max_iterations or max_expansion_factor |
| `MemoryError` | Insufficient RAM | Reduce num_processes |
| `No space left on device` | Disk full | Free disk space, check ~10 GB available |
| `Permission denied` | File access | Run as admin or fix permissions |
| `ODBC Driver not found` | Missing driver | Install ODBC Driver 17 |
| `secrets.yml not found` | Missing config | Create secrets.yml from template |
| `Invalid object name` | Wrong schema | Check schema in secrets.yml |

## Preventive Measures

**Before each run:**

✓ Verify free disk space (10 GB per year)  
✓ Close unnecessary applications  
✓ Check database server availability  
✓ Test database connection  
✓ Verify configuration files valid  
✓ Check no files locked in output folders  

**During runs:**

✓ Monitor console output for warnings  
✓ Check memory usage periodically  
✓ Watch for convergence failures  
✓ Verify intermediate files created  

**After runs:**

✓ Validate all output files present  
✓ Run validation dashboard  
✓ Check summary files for anomalies  
✓ Archive successful runs  

## Next Steps

✅ Issue resolved? → [Running PopulationSim](Running-PopulationSim)  
✅ Need validation help? → [Validation & QA](Validation-and-QA)  
❓ Still stuck? → Contact SANDAG Modeling team

---

**For detailed technical documentation:** See [SANDAG_PopulationSim_Documentation.md](../documentation/SANDAG_PopulationSim_Documentation.md) Sections 4.3.7 and Appendices
