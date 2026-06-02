# Frequently Asked Questions (FAQ)

Quick answers to common questions about SANDAG PopulationSim.

## General Questions

### What is PopulationSim?

PopulationSim is a demographic simulation tool that creates synthetic households and persons matching aggregate demographic forecasts. It takes aggregate totals (e.g., "1,000 households in area X") and generates individual-level microdata with detailed attributes while maintaining statistical consistency with the input controls.

### Why do we need synthetic populations?

Activity-Based Models (ABM) require individual-level data to simulate travel behavior, but we only have aggregate forecasts. PopulationSim bridges this gap by creating realistic synthetic individuals that match the aggregate constraints.

### What version of PopulationSim do we use?

SANDAG uses PopulationSim v0.10.0 from the ActivitySim framework, customized for the San Diego region with specific control variables and geographic structure.

### How long does a full run take?

- **First time:** ~8-10 hours (includes seed data creation ~15 minutes + all 7 years)
- **Subsequent runs:** ~6-8 hours (seed data reused)
- **Single year:** ~70 minutes after seed data exists

### Can I run just one forecast year?

Yes! Edit `config.yml` and comment out years you don't need:

```yaml
years:
  - 2022  # Keep only this one
  # - 2026
  # - 2029
  # ... etc
```

## Technical Questions

### What Python versions are supported?

Python 3.9, 3.10, 3.11, and 3.12 are supported. Python 3.13+ is not yet supported by PopulationSim dependencies.

### Do I need SQL Server access?

It depends:
- **To generate controls:** Yes, you need read access to UDM staging database
- **To load outputs:** Optional (only if using legacy database integration)
- **To run synthesis:** No SQL Server required after controls are generated

### Can I run PopulationSim offline?

After seed data and controls are prepared, yes. But control generation requires database access to UDM staging.

### Why use uv instead of pip?

`uv` is a fast Rust-based package manager that:
- Resolves dependencies 10-100x faster than pip
- Automatically creates and manages virtual environments
- Provides better error messages
- Is the recommended tool for modern Python projects

You can still use pip if you prefer: `pip install -e .`

### How much memory do I need?

Recommended: 16GB RAM minimum, 32GB preferred. PopulationSim uses 22 parallel processes (one per PUMA) which can consume significant memory during synthesis.

### How much disk space do I need?

- **Minimum:** 5GB free for outputs
- **Recommended:** 10GB free
- **With database:** Additional 5GB for SQL Server data files

Breakdown:
- Seed data: ~500MB
- Output per year: ~1.2GB
- All 7 years: ~8.4GB

## Data Questions

### What is the seed data?

Seed data is drawn from ACS PUMS (American Community Survey Public Use Microdata Sample) 2017-2021 5-year estimates. This provides actual households and persons from surveys that are weighted and resampled to match our control totals.

### What are control variables?

Control variables are demographic totals we want the synthetic population to match. SANDAG uses 56 controls including:
- Household size (1, 2, 3, 4+ persons)
- Income brackets (7 categories)
- Workers per household (0, 1, 2, 3+)
- Age groups (9 categories)
- Sex (Male/Female)
- Race/ethnicity (7 categories)
- Employment status (workers, unemployed, not in labor force)

### Where do controls come from?

- **Demographic controls:** UDM (Urban Data Models) staging database - SANDAG's forecast system
- **Economic controls:** Economic Team CSV file with employment and labor force

### What is the geographic structure?

Three levels:
- **Region:** 1 (San Diego County)
- **PUMA:** 22 (Public Use Microdata Areas)
- **MGRA:** ~23,000 (Master Geographic Reference Areas)

Controls are specified at PUMA and MGRA levels, and PopulationSim balances hierarchically.

### Why are there ~23,000 MGRAs but some have no households?

Not all MGRAs are residential. Some are:
- Commercial/industrial zones
- Parks and open space
- Transportation infrastructure
- Water bodies

These MGRAs will have zero households but may still have employment data.

## Algorithm Questions

### What algorithm does PopulationSim use?

Iterative Proportional Fitting (IPF) with simultaneous integerization. It's an optimization problem that:
1. Starts with seed households/persons
2. Assigns fractional weights to match control totals
3. Integerizes weights (converts to whole numbers)
4. Balances across geographic levels

### What is "integerization"?

Converting fractional household weights to whole numbers. You can't have 2.7 households - you need exactly 2 or 3. PopulationSim solves this while maintaining control totals.

### What is "backstopping"?

When an MGRA has a control target (e.g., 50 households) but no suitable seed households can match, PopulationSim "backstops" by:
1. Relaxing constraints
2. Looking for near-matches from broader geography
3. Accepting larger deviation to avoid zero households

### What is max_expansion_factor and why is it 30?

This limits how many times a single seed household can be replicated. Setting it to 30 means one PUMS household can represent up to 30 synthetic households. This prevents over-reliance on single observations while allowing sufficient flexibility.

### How does multiprocessing work?

PopulationSim runs 22 parallel processes, one per PUMA:
- Each process handles only its assigned PUMA's MGRAs
- After PUMA-level balancing, results combine
- Then MGRA sub-balancing happens (also parallelized)
- Final expansion creates actual household records

## Output Questions

### What's the difference between final_*.csv and abm/*.csv?

- **final_*.csv:** Raw PopulationSim output with all PUMS attributes
- **abm/*.csv:** Cleaned, formatted specifically for ABM team with selected columns

Both contain the same households/persons, just different columns and formatting.

### What is mgra_based_input_YYYY.csv?

MGRA-level summary file with demographic totals (households, population, group quarters, employment). The ABM reads this file for zonal data.

### How do I know if my run was successful?

Check for:
1. ✅ All output files exist
2. ✅ Household and person counts are reasonable (~1.2M households, ~3.5M persons)
3. ✅ No error messages in logs
4. ✅ Summary files show small percent differences (<1% for most controls)
5. ✅ Streamlit dashboard shows good control fits

### Can I modify the synthetic population after generation?

Yes, but carefully:
- Ensure household-person linkage remains valid
- Maintain consistent mgra assignments
- Don't break demographic totals if precision is important
- Document any changes for reproducibility

## Validation Questions

### What is an acceptable fit?

**Good fit:**
- Regional controls: <0.1% difference
- PUMA controls: <1% difference  
- MGRA controls: <5% difference (more tolerance at fine geography)

**Warning signs:**
- Any geography >10% difference
- Systematic bias (all controls too high or too low)
- Large number of zero-household MGRAs that should have households

### What is the Streamlit dashboard?

An interactive web application for validating PopulationSim results. Launch with:

```powershell
cd report
streamlit run report.py
```

Features:
- Control vs. result comparisons
- Geographic distribution maps
- Demographic breakdowns
- Interactive filtering and drill-down

### How do I validate group quarters?

Check:
1. GQ population totals match controls
2. GQ types distributed correctly (military, college, other)
3. No GQ persons in regular households
4. GQ persons have consistent attributes (age appropriate for college dorms, etc.)

## Troubleshooting Questions

### PopulationSim failed with "No feasible solution"

**Causes:**
- Impossible control combinations (e.g., more workers than persons)
- Seed data doesn't cover needed demographic profile
- Too-tight importance weights

**Solutions:**
1. Check control data for errors
2. Review `settings.yaml` importance weights
3. Lower importance for problematic controls
4. Check logs for specific MGRA failures

### Seed data creation takes forever

**Normal:** ~15 minutes is expected for first run

**Too slow (>1 hour):**
- Database connection is slow
- Query performance issues
- Insufficient memory causing swapping

**Solution:** Check network speed to database, optimize SQL queries

### Results don't match last year's run

**Expected reasons:**
- Control data changed (UDM updated)
- Different seed data (ACS vintage changed)
- Algorithm parameters modified
- Random seed different

**Solution:** Check `config.yml` and `settings.yaml` for changes

### How do I reproduce a previous run?

Ensure same:
1. Seed data (same ACS vintage)
2. Control data (same UDM query results)
3. Config settings (`config.yml` and `settings.yaml`)
4. PopulationSim version
5. Random seed

Version control your config files!

## Database Questions

### Do I have to use the database?

No, database integration is optional. You can:
- Run PopulationSim without database
- Work with CSV files directly
- Skip ETL process

Database is useful for:
- Historical versioning
- Streamlit dashboard queries
- Production audit trail

### What database do we use?

Legacy: Microsoft SQL Server (being phased out)  
Future: Azure Data Lake (in development on feature/datalake-exporter branch)

### Can I use PostgreSQL or MySQL instead?

Not without code modifications. The ETL code (`python/etl.py`) is specific to SQL Server. You'd need to adapt:
- Connection strings
- SQL dialects
- Schema definitions

## ABM Integration Questions

### What format does ABM expect?

ABM reads:
- `abm/households.csv` - household attributes
- `abm/persons.csv` - person attributes  
- `abm/mgra_based_input_YYYY.csv` - zonal summaries

These are created automatically by `python/outputs.py` after synthesis.

### Can I customize ABM output format?

Yes, modify `python/outputs.py` function `create_abm_outputs()`. Add/remove columns as needed, but coordinate with ABM team on schema changes.

### How do group quarters work with ABM?

Group quarters persons are included in `persons.csv` with:
- `household_id` still assigned (for technical reasons)
- `mgra` indicates location
- Specific `gq_type` attribute

ABM handles GQ persons differently than household residents.

## Customization Questions

### Can I add new control variables?

Yes! Edit:
1. `populationsim/configs/controls.csv` - add control definition
2. `sql/mgra_controls.sql` - query to fetch control values
3. Rerun with new configuration

Note: Control must be expressible using PUMS variables.

### Can I change importance weights?

Yes, edit `populationsim/configs/settings.yaml`:

```yaml
importance_weights:
  Total_HH: 1000000000  # Highest (exact match)
  HHSize_1: 250000      # High
  Age_25to34: 100000    # Medium
  # ... etc
```

Higher importance = tighter constraint.

### Can I run for different forecast years?

Yes, edit `config.yml`:

```yaml
years:
  - 2018
  - 2023
  - 2030
  # Any years where UDM has forecasts
```

Make sure UDM staging database has data for those years.

---

**Still have questions?** 

- Check the [comprehensive technical documentation](../documentation/SANDAG_PopulationSim_Documentation.md)
- Review [Troubleshooting](Troubleshooting) guide
- Contact the SANDAG Modeling team
