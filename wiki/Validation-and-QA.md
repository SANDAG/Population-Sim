# Validation & Quality Assurance

Complete guide to validating PopulationSim outputs and ensuring quality.

## Overview

Quality assurance ensures the synthetic population accurately reflects control totals and maintains demographic coherence. SANDAG's validation framework combines:

- **Automated summary files** - Compare controls vs. results
- **Interactive Streamlit dashboard** - Visual validation and drill-down
- **Quantitative quality metrics** - Statistical measures of fit

## Summary Files

PopulationSim generates summary files that compare control totals to synthesis results for each year.

### summary_mgra.csv

**Purpose:** MGRA-level control vs. result comparison

**Key Characteristics:**
- **Rows:** ~24,321 (one per MGRA)
- **Columns:** ~86 columns (id, geography, plus 42 control pairs)
- **Format:** Each control has `{name}_control` and `{name}_result` columns

**Acceptable Ranges:**
- **Total_HH:** Should match exactly or within ±1 household per MGRA
- **Demographic controls:** ±5% deviation acceptable for most MGRAs
- **Small MGRAs:** Higher percentage deviations expected due to rounding

**Quick Validation:**
```python
import pandas as pd

df = pd.read_csv("output/2022/summary_mgra.csv")

# Calculate differences for all controls
for col in df.columns:
    if col.endswith("_control"):
        base = col.replace("_control", "")
        result_col = f"{base}_result"
        df[f"{base}_diff"] = df[result_col] - df[col]

# Find MGRAs with largest household discrepancies
worst_hh = df.nlargest(10, "Total_HH_diff")[
    ["id", "Total_HH_control", "Total_HH_result", "Total_HH_diff"]
]
print(worst_hh)
```

### summary_mgra_PUMA.csv

**Purpose:** Aggregated PUMA-level validation (22 PUMAs)

**Key Characteristics:**
- **Rows:** 22 (one per PUMA)
- **Columns:** Same 86 columns as MGRA summary
- **Use Case:** Mid-level validation before drilling into MGRAs

**Acceptable Ranges:**
- **All controls:** Should match within ±0.5% at PUMA level
- **Larger deviations:** Indicate systematic issues with controls or balancing

### summary_region_1.csv

**Purpose:** Regional (county-wide) employment and labor force validation

**Key Characteristics:**
- **Rows:** 18 employment sectors + labor force controls
- **Columns:** control_name, control_value, mgra_integer_weight
- **Coverage:** job_1 through job_18, lfp_* controls

**Acceptable Ranges:**
- **Integer integerization:** Results within ±5 of control values
- **All controls:** Should match within ±10 workers or ±0.1%

**Quick Validation:**
```python
df_region = pd.read_csv("output/2022/summary_region_1.csv")

# Calculate differences
df_region["diff"] = df_region["mgra_integer_weight"] - df_region["control_value"]
df_region["diff_pct"] = 100 * df_region["diff"] / df_region["control_value"]

# Display all regional controls
print(df_region[["control_name", "control_value", "mgra_integer_weight", "diff", "diff_pct"]])
```

### final_summary_mgra_gq.csv

**Purpose:** Group quarters validation

**Key Characteristics:**
- **Rows:** ~24,321 (one per MGRA)
- **Columns:** 8 (id, geography, 3 GQ types × 2)
- **Expected Accuracy:** **100% exact match** (GQ sampling is deterministic)

**Acceptable Ranges:**
- **All GQ controls:** Must match exactly (0 difference)
- **Any deviation:** Indicates a bug in GQ sampling logic

**Quick Validation:**
```python
df_gq = pd.read_csv("output/2022/final_summary_mgra_gq.csv")

# Check for any mismatches
gq_types = ["gq_mil_pop", "gq_college_pop", "gq_other_pop"]

for gq in gq_types:
    control_col = f"{gq}_control"
    result_col = f"{gq}_result"
    mismatches = df_gq[df_gq[control_col] != df_gq[result_col]]
    
    if len(mismatches) > 0:
        print(f"❌ {gq}: {len(mismatches)} MGRAs with mismatches!")
    else:
        print(f"✓ {gq}: All MGRAs match exactly")
```

### timing_log.csv

**Purpose:** Performance metrics for pipeline steps

**Typical Durations:**

| Step | Typical Duration | Concern Threshold |
|------|------------------|-------------------|
| input_pre_processor | 30-60 sec | >120 sec |
| initial_seed_balancing | 200-400 sec | >600 sec |
| integerize_final_seed_weights | 100-200 sec | >400 sec |
| sub_balancing.geography=mgra | 2000-3000 sec | >4000 sec |
| expand_households | 150-250 sec | >400 sec |
| **Total** | **3500-4500 sec (60-75 min)** | **>5400 sec (90 min)** |

**Quick Check:**
```python
df_timing = pd.read_csv("output/2022/timing_log.csv")

# Calculate total runtime
total_seconds = df_timing["seconds"].sum()
print(f"Total runtime: {total_seconds:.0f} seconds ({total_seconds/60:.1f} minutes)")

# Identify bottlenecks
slowest = df_timing.nlargest(5, "seconds")
print("\nSlowest steps:")
print(slowest)
```

## Streamlit Validation Dashboard

Interactive web-based dashboard for visual validation and quality assurance.

### Launching the Dashboard

```powershell
# Navigate to repository root
cd C:\Projects\Population-Sim

# Activate environment
.venv\Scripts\Activate.ps1

# Launch Streamlit app
streamlit run report/report.py
```

**Expected Output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.100:8501
```

**Open Browser:** Navigate to http://localhost:8501

### Dashboard Interface

**Sidebar:**
- **Data Source Toggle:** Choose "Database" or "Local Output"
- **Run Selection:** Table of available runs (click row to select)
- **Run Metadata:** Shows run_id, year, date, version, comments

**Main Panel (3 Tabs):**
1. **Region Tab** - Regional employment controls (18 controls)
2. **PUMA Tab** - PUMA-level validation (22 PUMAs × 42 controls)
3. **MGRA Tab** - MGRA-level validation (~24,321 MGRAs × 42 controls)

**Visual Elements:**
- **Scatter Plots:** Control value (x-axis) vs. Difference (y-axis)
  - Red dashed line at y=0 (perfect match)
  - Hover shows control name and geography ID
- **Summary Tables:** Aggregated statistics by control category

### Using Local Output Mode

**When to Use:**
- Runs completed but not loaded to database
- Quick validation without database connection
- Testing or debugging scenarios

**How It Works:**
1. Scans `output/` directory for year folders
2. Loads summary CSV files
3. Displays validation metrics

**Selecting a Local Run:**
- Choose "Local Output" from sidebar data source toggle
- Select run from table showing year, date, version
- Dashboard loads and displays validation tabs

### Using Database Mode

**When to Use:**
- Production validation of loaded runs
- Comparing multiple runs
- Accessing historical runs

**Prerequisites:**
- ETL completed (`load_to_database: True` in config.yml)
- Database credentials in secrets.yml

**Selecting a Database Run:**
- Choose "Database" from sidebar data source toggle
- Select run from table showing run_id, year, date, user, version
- Dashboard queries database and displays validation tabs

## Quality Assurance Checklist

### Level 1: Basic Validation (Required)

✓ **All years completed successfully**
- Check console output for "All years processed successfully"
- Verify output folders exist for each year

✓ **Output files present**
- Check each year folder has 14 files (see [Output Files](Output-Files))
- Verify file sizes are reasonable (not 0 bytes)

✓ **Regional controls match**
- Open `summary_region_1.csv`
- All differences within ±10 workers or ±0.1%

✓ **GQ controls exact match**
- Open `final_summary_mgra_gq.csv`
- All gq_*_control == gq_*_result (zero difference)

### Level 2: Statistical Validation (Recommended)

✓ **PUMA-level convergence**
- Open `summary_mgra_PUMA.csv`
- All control differences within ±0.5%

✓ **MGRA household totals**
- Open `summary_mgra.csv`
- 95% of MGRAs have Total_HH_diff within ±1
- No MGRA has Total_HH_diff > ±5

✓ **Demographic balance**
- Age/sex controls: Mean absolute % error < 5%
- Income controls: Mean absolute % error < 10%
- Household size: Mean absolute % error < 5%

### Level 3: Visual Inspection (As Needed)

✓ **Streamlit dashboard review**
- Launch dashboard with local output
- Review Region tab - all points near y=0 line
- Review PUMA tab - scatter plots show good fit
- Review MGRA tab - no systematic patterns in residuals

✓ **Geographic patterns**
- No clusters of high-error MGRAs in specific areas
- Errors evenly distributed across county

✓ **Time series consistency** (if comparing to previous runs)
- Growth rates reasonable across years
- No sudden jumps or drops in population

## Common Validation Issues

| Issue | Symptom | Resolution |
|-------|---------|------------|
| Regional controls mismatch | summary_region_1 shows large diffs | Check economic controls CSV, verify year column |
| GQ mismatch | final_summary_mgra_gq shows non-zero diffs | Bug in GQ sampling - contact development team |
| Large MGRA deviations | Many MGRAs with >10% error | Check max_expansion_factor, verify control totals |
| Systematic geographic bias | Errors cluster in specific area | Check geographic crosswalk, verify PUMA assignments |
| Convergence failure | Balancing never converges | Increase max_iterations, check for conflicting controls |

## Validation Report Template

Create a validation report for each run:

```markdown
# PopulationSim Validation Report

**Run ID:** [run_id]
**Date:** [date]
**Version:** [version]
**Years:** [2022, 2026, 2029, 2032, 2035, 2040, 2050]

## Summary Statistics

| Year | Households | Persons | GQ Pop | Runtime |
|------|------------|---------|--------|---------|
| 2022 | 1,276,883  | 3,283,519 | 116,411 | 72 min |
| ...  | ...        | ...       | ...     | ...    |

## Quality Metrics

### Regional Controls
- ✓ All job_* controls within ±0.1%
- ✓ All lfp_* controls match exactly

### PUMA-Level Validation
- ✓ 22/22 PUMAs within ±0.5% for all controls
- Mean absolute % error: 0.23%

### MGRA-Level Validation
- ✓ 98.5% of MGRAs within ±1 household
- ✓ No MGRA exceeds ±5 household difference
- Mean absolute household error: 0.12

### Group Quarters
- ✓ 100% exact match on all GQ controls

## Issues & Notes

[Document any anomalies, warnings, or special circumstances]

## Approval

Validated by: [name]
Date: [date]
Status: ✓ APPROVED / ❌ NEEDS REVIEW
```

## Next Steps

✅ Validation complete? → [Output Files](Output-Files) for delivery details  
❓ Found issues? → [Troubleshooting](Troubleshooting)  
🔧 Need to adjust? → [Configuration Reference](Configuration-Reference)

---

**For detailed technical documentation:** See [SANDAG_PopulationSim_Documentation.md](../documentation/SANDAG_PopulationSim_Documentation.md) Section 5
