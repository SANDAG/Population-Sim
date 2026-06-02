# Running PopulationSim

Complete guide to executing population synthesis runs.

## Pre-Execution Checklist

Before running `main.py`, verify:

1. ✓ Python environment activated (`.venv\Scripts\Activate.ps1`)
2. ✓ All configuration files present and valid
   - `config.yml` exists
   - `secrets.yml` created with correct credentials
   - `populationsim/configs/settings.yaml` exists
   - `populationsim/configs/controls.csv` exists
3. ✓ Database connectivity tested
4. ✓ Sufficient disk space (~10 GB per year)
5. ✓ No conflicting processes using data directories
6. ✓ Expected runtime: ~7-8 hours for all 7 years

## Basic Execution

```powershell
# Navigate to repository root
cd C:\Projects\Population-Sim

# Activate environment
.venv\Scripts\Activate.ps1

# Run main script
python main.py
```

### Expected Console Output

```
2026-06-02 09:00:15 - INFO - Building controls for 2022
[SQL queries executing...]
2026-06-02 09:02:30 - INFO - Running populationsim for 2022
[PopulationSim detailed logging...]
2026-06-02 10:05:45 - INFO - Simulation run successful
2026-06-02 10:06:00 - INFO - PopSim outputs organized for 2022
2026-06-02 10:08:15 - INFO - ABM outputs created for 2022

2026-06-02 10:08:20 - INFO - Building controls for 2026
[Process repeats for each year...]

2026-06-02 16:45:30 - INFO - All years processed successfully.
```

### Alternative: Capture Output to Log File

```powershell
# Capture all output to log file
python main.py > run_log_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt 2>&1

# Or use Tee to see output AND save to file
python main.py 2>&1 | Tee-Object -FilePath "run_log.txt"
```

## Execution Workflow

```mermaid
flowchart TD
    A[Start: python main.py] --> B[Load config.yml & secrets.yml]
    B --> C[Create SQL Engine]
    C --> D[Extract Seed Data]
    D --> E{For Each Year}
    
    E -->|Year N| F[Build MGRA Controls]
    F --> G[Build Region Controls]
    G --> H[Run PopulationSim]
    H --> I[Organize Outputs]
    I --> J[Create ABM Outputs]
    J --> K{Database Loading?}
    K -->|True| L[Run ETL]
    K -->|False| M[Next Year]
    L --> M
    M --> E
    
    E -->|All Years Done| N[Complete]
    
    style D fill:#e1f5ff
    style H fill:#ffe1e1
    style L fill:#e1ffe1
```

## Execution Steps Breakdown

### Step 1: Initialization (~1 second)
- Load `config.yml` and `secrets.yml`
- Create database connection
- Verify configuration

### Step 2: Seed Data Extraction (~2-3 minutes)
- Extract ACS PUMS households and persons
- Split into regular households (HH) and group quarters (GQ)
- Write 4 seed files to `populationsim/data/`:
  - `seed_households_gq.csv` (~50K rows)
  - `seed_households_hh.csv` (~350K rows)
  - `seed_persons_gq.csv` (~50K rows)
  - `seed_persons_hh.csv` (~950K rows)

### Step 3: For Each Year

#### 3a. Build Controls (~10-15 seconds per year)
- Generate MGRA-level control totals (42 controls × ~24,321 MGRAs)
- Generate regional control totals (18 employment sectors)
- Write to `populationsim/data/`:
  - `mgra_controls.csv`
  - `region_controls.csv`

#### 3b. Run PopulationSim (~60-70 minutes per year)
- Execute IPF (Iterative Proportional Fitting) algorithm
- Parallel processing across 22 PUMAs
- Integerize weights
- Sub-balance at MGRA level
- Generate synthetic population

**Output files** in `populationsim/output/` and `populationsim/output_gq/`:
- `synthetic_households.csv`
- `synthetic_persons.csv`
- `synthetic_households_gq.csv`
- `synthetic_persons_gq.csv`
- `summary_mgra.csv`
- `summary_mgra_PUMA.csv`
- `summary_region_1.csv`
- `final_summary_mgra_gq.csv`
- `timing_log.csv`

#### 3c. Organize Outputs (~5 seconds)
- Move files from `populationsim/output/` to `output/{year}/`
- Copy control files for archival

#### 3d. Create ABM Outputs (~2-3 minutes)
- Combine HH and GQ files
- Renumber GQ household IDs
- Clean NULL values
- Query and write land use file (`mgra15_based_input_{year}.csv`)

**Final output files** in `output/{year}/`:
- `synthetic_households_{year}.csv` (~1.3M households, 77 MB)
- `synthetic_persons_{year}.csv` (~3.3M persons, 292 MB)
- `mgra15_based_input_{year}.csv` (~24K MGRAs, 5 MB)

#### 3e. Optional Database ETL (~5-10 minutes, if enabled)
- Load all outputs to production database
- Track run metadata
- Enable validation dashboard

## Runtime Expectations

### Per-Year Breakdown

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Controls generation | 15 sec | 0:00:15 |
| PopulationSim execution | 65 min | 1:05:15 |
| Output organization | 5 sec | 1:05:20 |
| ABM output creation | 3 min | 1:08:20 |
| Database ETL (optional) | 8 min | 1:16:20 |

**Total Per Year:** ~70-75 minutes (without ETL), ~80-85 minutes (with ETL)

### Total for All Years
- **7 years without ETL:** ~8 hours
- **7 years with ETL:** ~10 hours

### Factors Affecting Runtime
- Database query performance (network latency, server load)
- Number of parallel processes (fewer → slower)
- Disk I/O speed (SSD vs. HDD)
- CPU performance (core speed, not just core count)
- Convergence speed (varies by year's controls)

## Monitoring Progress

### Real-Time Log Monitoring

```powershell
# Open PowerShell window and tail the log
Get-Content populationsim.log -Wait -Tail 20

# Or monitor output directory size
while ($true) {
    Get-ChildItem output\ -Recurse | Measure-Object -Property Length -Sum
    Start-Sleep -Seconds 60
}
```

### Progress Indicators

**Console Messages:**
```
Building controls for {year}       → Controls phase started
Running populationsim for {year}   → PopSim executing (longest phase)
Simulation run successful          → PopSim completed
PopSim outputs organized for {year} → Files moved to output folder
ABM outputs created for {year}     → Year complete
```

**File System Indicators:**
- `populationsim/output/` populated → PopSim running
- `output/{year}/` created → Year processing
- `synthetic_households_{year}.csv` appears → Year complete

**PopulationSim Log Messages:**
```
INFO - step_01_input_pre_processor starting
INFO - step_03_initial_seed_balancing starting iteration 1
INFO - step_03_initial_seed_balancing iteration 50 converged
INFO - step_07_sub_balancing.geography=mgra starting parallel processing
INFO - step_07_sub_balancing.geography=mgra completed (22 processes)
```

## Handling Interruptions

### Safe Interruption Points

1. **Between years** (safest)
   - Can resume by removing completed years from `config.yml`
   - No data loss

2. **During PopulationSim execution** (moderate risk)
   - Can use `resume_after` in `configs_mp/settings.yaml`
   - May need to delete partial outputs

### Resume After Interruption

**Scenario 1: Completed 2022, 2026; stopped during 2029**

Edit `config.yml`:
```yaml
years:
  # - 2022  # Already done
  # - 2026  # Already done
  - 2029    # Resume here
  - 2032
  - 2035
  - 2040
  - 2050
```

**Scenario 2: PopulationSim crashed mid-run**

Edit `populationsim/configs_mp/settings.yaml`:
```yaml
# Uncomment to resume from specific step
resume_after: integerize_final_seed_weights
# Options: step name from models list
```

**Data Cleanup:**
```powershell
# Remove partial year outputs
Remove-Item -Recurse -Force output\2029\
Remove-Item -Recurse -Force populationsim\output\*
Remove-Item -Recurse -Force populationsim\output_gq\*
```

## Common Execution Issues

| Issue | Symptom | Resolution |
|-------|---------|------------|
| Database timeout | SQL query hangs | Check network, increase timeout in connection string |
| PopulationSim convergence failure | Balancing never converges | Increase max_iterations, check control totals |
| Memory error | Process killed or crashes | Reduce num_processes, close other applications |
| Disk full | I/O error writing files | Free disk space, check ~10 GB per year available |
| Permission denied | Cannot write to output/ | Run as administrator or check folder permissions |
| ODBC driver error | Connection fails | Reinstall ODBC Driver 17, verify in pyodbc.drivers() |
| Controls mismatch | Synthesis produces warnings | Verify control totals sum correctly, check MGRA/PUMA alignment |

## Debug Mode

```powershell
# Run with verbose logging (if main.py supports it)
python main.py --verbose

# Or modify logging level in main.py:
# logging.basicConfig(level=logging.DEBUG, ...)
```

## Running a Single Year (Testing)

To test with just one year, edit `config.yml`:

```yaml
years:
  - 2026  # Test with just one year
```

Expected runtime: ~70 minutes

## Next Steps

✅ Run complete? → [Validation & QA](Validation-and-QA)  
✅ Understand outputs? → [Output Files](Output-Files)  
❓ Something went wrong? → [Troubleshooting](Troubleshooting)

---

**For detailed technical documentation:** See [SANDAG_PopulationSim_Documentation.md](../documentation/SANDAG_PopulationSim_Documentation.md) Section 4.3
