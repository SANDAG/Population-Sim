# Configuration Reference

Complete reference for all configuration files and settings.

## Configuration Files Overview

PopulationSim uses three main configuration files:

| File | Location | Version Controlled | Purpose |
|------|----------|-------------------|---------|
| config.yml | Repository root | ✓ Yes | Run configuration, SQL paths, years |
| secrets.yml | Repository root | ✗ NO (local only) | Database credentials |
| settings.yaml | populationsim/configs/ | ✓ Yes | PopulationSim algorithm settings |
| controls.csv | populationsim/configs/ | ✓ Yes | Control variable definitions |

## config.yml

**Location:** `config.yml` (repository root)

**Purpose:** Main run configuration (version-controlled)

### Complete Structure

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

synthesis_runs:
  - name: gq_mil
    configs: [configs_gq_mil, configs_common]
    data: data
    output: output_gq_mil
    num_processes: 1
  - name: gq_col
    configs: [configs_gq_col, configs_common]
    data: data
    output: output_gq_col
    num_processes: 1
  - name: gq_oth
    configs: [configs_gq_oth, configs_common]
    data: data
    output: output_gq_oth
    num_processes: 1
  - name: household
    configs: [configs_mp, configs, configs_common]
    data: data
    output: output
    num_processes: 22

years:
  - 2022
  - 2026
  - 2029
  - 2032
  - 2035
  - 2040
  - 2050
```

### Field Reference

**Metadata:**
- `version` - Run version identifier (for tracking)
- `seed_data` - Documentation of seed data vintage
- `comments` - Optional notes about this run

**SQL Queries:**
- `seed_households` - Path to household seed extraction query
- `seed_persons` - Path to person seed extraction query
- `mgra_controls` - Path to MGRA control generation query
- `region_controls` - Path to regional control query
- `mgrabase` - Path to ABM land use file query
- `load_to_database` - Boolean: Enable ETL to production database
  - `False` - Write CSV files only (default, faster)
  - `True` - Load to database (enables validation dashboard)

**Data Sources:**
- `economic_controls` - Path to Economics Team forecast CSV

**Synthesis Runs:**
- `synthesis_runs` - List of PopulationSim executions for each year
  - Each run is a separate PopulationSim invocation
  - Runs execute sequentially in listed order
  - **Run Fields:**
    - `name` - Identifier (gq_mil, gq_col, gq_oth, household)
    - `configs` - List of config directories (relative to `populationsim/`)
      - Layered in order (later overrides earlier)
      - `configs_common` should be last for shared settings
    - `data` - Data directory path (relative to `populationsim/`)
    - `output` - Output directory path (relative to `populationsim/`)
    - `num_processes` - Number of parallel processes
      - `1` for GQ runs (small populations)
      - `22` for household run (one per PUMA)
  - **Standard Setup:** 3 GQ runs + 1 household run

**Run Configuration:**
- `years` - List of forecast years to process sequentially

### Common Customizations

**Single Year Testing:**
```yaml
years:
  - 2026  # Test with just one year
```

**Run Households Only (Skip GQ for testing):**
```yaml
synthesis_runs:
  - name: household
    configs: [configs_mp, configs, configs_common]
    data: data
    output: output
    num_processes: 22
```

**Single-Process Household Run (Low-Memory System):**
```yaml
synthesis_runs:
  - name: gq_mil
    configs: [configs_gq_mil, configs_common]
    data: data
    output: output_gq_mil
    num_processes: 1
  - name: gq_col
    configs: [configs_gq_col, configs_common]
    data: data
    output: output_gq_col
    num_processes: 1
  - name: gq_oth
    configs: [configs_gq_oth, configs_common]
    data: data
    output: output_gq_oth
    num_processes: 1
  - name: household
    configs: [configs, configs_common]  # configs_mp removed
    data: data
    output: output
    num_processes: 1  # Single process
```

**Database Loading:**
```yaml
sql:
  load_to_database: True
```

**Alternative Seed Data:**
```yaml
seed_data: "ACS PUMS 5 year 2016-2020"
sql:
  seed_households: "sql/seed_households_2020.sql"
  seed_persons: "sql/seed_persons_2020.sql"
```

## secrets.yml

**Location:** `secrets.yml` (repository root)

**Purpose:** Database credentials (NOT version-controlled)

⚠️ **CRITICAL:** Create locally, NEVER commit to Git

### Template

```yaml
sql:
  server: "<SQLInstanceName>"
  schema: "<[database].[schema]>"
  output_database: "<SQLoutputDatabaseName>"
```

### Field Reference

- `server` - SQL Server instance name
  - Format: `ServerName` or `ServerName\InstanceName`
  - Examples: `SANDAG-SQL01`, `localhost`
  
- `schema` - UDM staging schema
  - Format: `[database_name].[schema_name]`
  - Must use square brackets
  - Example: `[udm_staging].[sr15]`
  
- `output_database` - Database for PopulationSim outputs
  - Only used if `load_to_database: True`
  - Example: `PopulationSim_Production`

### Example

```yaml
sql:
  server: "SANDAG-SQL01"
  schema: "[udm_staging].[sr15]"
  output_database: "PopulationSim_Production"
```

### Security Best Practices

✓ **Never commit to Git** - Check with `git check-ignore secrets.yml`  
✓ **Use Windows Authentication** - Avoid hardcoded passwords  
✓ **Read-only permissions** - For source databases  
✓ **Separate output database** - For write operations  

## settings.yaml

**Location:** `populationsim/configs/settings.yaml`

**Purpose:** PopulationSim algorithm configuration

### Key Algorithm Settings

```yaml
# Integerization
INTEGERIZE_WITH_BACKSTOPPED_CONTROLS: True
USE_SIMUL_INTEGERIZER: True
SUB_BALANCE_WITH_FLOAT_SEED_WEIGHTS: False

# Expansion limits
max_expansion_factor: 30
min_expansion_factor: 0.01

# Convergence
max_iterations: 5000
absolute_convergence: 0.0001
relative_convergence: 0.0001

# Geography
geographies: [region, PUMA, mgra]
seed_geography: PUMA
```

### Setting Reference

**Integerization:**
- `INTEGERIZE_WITH_BACKSTOPPED_CONTROLS: True` - Ensure critical controls exactly met
- `USE_SIMUL_INTEGERIZER: True` - Simultaneous integerization (better quality)
- `SUB_BALANCE_WITH_FLOAT_SEED_WEIGHTS: False` - Use integer weights for sub-balancing

**Expansion Constraints:**
- `max_expansion_factor: 30` - Maximum weight multiplier (household can be replicated max 30 times)
- `min_expansion_factor: 0.01` - Minimum weight (effectively allow dropping households)

**Convergence:**
- `max_iterations: 5000` - Maximum IPF iterations before failure
- `absolute_convergence: 0.0001` - Stop when all controls within this absolute difference
- `relative_convergence: 0.0001` - Stop when all controls within this relative difference

**Geography:**
- `geographies: [region, PUMA, mgra]` - Three-level hierarchy
- `seed_geography: PUMA` - Seed data identified by PUMA

### When to Modify

**Convergence Issues:**
- Increase `max_iterations` to 10000
- Loosen `absolute_convergence` to 0.001

**Too Much Household Replication:**
- Decrease `max_expansion_factor` to 20 or 15

**Balance Quality Issues:**
- Increase `max_expansion_factor` to 40 or 50
- Review control importance weights

## configs_mp/settings.yaml

**Location:** `populationsim/configs_mp/settings.yaml`

**Purpose:** Multiprocessing configuration

### Key Settings

```yaml
inherit_settings: True  # Inherit from base settings.yaml

multiprocess: True
num_processes: 22  # One per PUMA

slice_geography: PUMA

multiprocess_steps:
  - name: mp_sub_balancing_mgra
    begin: sub_balancing.geography=mgra
    num_processes: 22
```

### Hardware-Specific Adjustments

**11 cores available:**
```yaml
num_processes: 11
```
Runtime: ~2 hours (vs. 40 min with 22)

**Less than 64 GB RAM:**
```yaml
num_processes: 10  # or lower
```
Runtime: ~3 hours

**Debugging (disable parallelization):**
```yaml
multiprocess: False
```
Runtime: ~13 hours (sequential)

## controls.csv

**Location:** `populationsim/configs/controls.csv`

**Purpose:** Define all control variables

### Structure

```csv
target,geography,seed_table,importance,expression
Total_HH,mgra,households,1000000000,(households.WGTP > 0) & (households.WGTP < np.inf)
HHSize_1,mgra,households,250000,households.NP == 1
HHSize_2,mgra,households,250000,households.NP == 2
Male_0_4,mgra,persons,1000,((persons.SEX == 1) & (persons.AGEP >= 0) & (persons.AGEP <= 4))
```

### Field Reference

- `target` - Unique control name (e.g., HHSize_1)
- `geography` - Geographic level (region, PUMA, or mgra)
- `seed_table` - Which seed table to query (households or persons)
- `importance` - Weight for balancing (higher = more important)
- `expression` - Pandas boolean expression to identify matching records

### Control Categories

| Category | Count | Importance Range | Geography |
|----------|-------|------------------|-----------|
| Total Households | 1 | 1,000,000,000 | mgra |
| Household Size | 4 | 250,000 | mgra |
| Income | 10 | 10,000 | mgra |
| Workers | 4 | 5,000 | mgra |
| Children | 3 | 5,000 | mgra |
| Age/Sex | 42 | 1,000 | mgra |
| Race/Ethnicity | 6 | 1,000 | mgra |
| Employment | 18 | 100,000,000 | region |
| Labor Force | 4 | 1,000,000 | region |

### Importance Weight Guidelines

- **1,000,000,000** - Total_HH (must match exactly)
- **100,000,000** - Employment totals (critical regional controls)
- **1,000,000** - Labor force (important but allow some flex)
- **250,000** - Household size (high priority)
- **10,000** - Income (medium priority)
- **5,000** - Workers, children (medium priority)
- **1,000** - Age, sex, race (lower priority, more flexible)

### Adding a Custom Control

**Example: Households with seniors (65+)**

```csv
HHSenior,mgra,households,5000,(households.persons.AGEP >= 65).any()
```

**Requirements:**
1. Add row to `controls.csv`
2. Add corresponding column to `mgra_controls.csv`
3. Test expression with seed data
4. Verify control totals sum correctly

## Configuration Validation

### Pre-Run Validation Script

```python
import yaml
import os
import pandas as pd

# Load configurations
with open('config.yml') as f:
    config = yaml.safe_load(f)

assert os.path.exists('secrets.yml'), "secrets.yml not found!"

with open('secrets.yml') as f:
    secrets = yaml.safe_load(f)

# Validate config.yml
assert 'sql' in config
assert 'years' in config
assert len(config['years']) > 0

# Validate secrets.yml
assert 'sql' in secrets
assert 'server' in secrets['sql']
assert 'schema' in secrets['sql']

# Check SQL file paths exist
for key, path in config['sql'].items():
    if key != 'load_to_database':
        assert os.path.exists(path), f"SQL file not found: {path}"

# Check economic controls file
assert os.path.exists(config['economic_controls'])

# Validate PopulationSim configs
assert os.path.exists('populationsim/configs/settings.yaml')
assert os.path.exists('populationsim/configs/controls.csv')

# Load and validate controls.csv
controls = pd.read_csv('populationsim/configs/controls.csv')
required_cols = ['target', 'geography', 'seed_table', 'importance', 'expression']
assert all(col in controls.columns for col in required_cols)

print("✓ All configuration files validated!")
print(f"✓ Years: {config['years']}")
print(f"✓ SQL Server: {secrets['sql']['server']}")
print(f"✓ Database loading: {config['sql']['load_to_database']}")
print(f"✓ Controls: {len(controls)}")
```

## Configuration Checklist

Before running PopulationSim:

✓ **config.yml**
- [ ] `version` updated for this run
- [ ] `years` list correct
- [ ] SQL file paths valid
- [ ] `load_to_database` set appropriately

✓ **secrets.yml**
- [ ] File created (not in Git)
- [ ] `server` correct
- [ ] `schema` matches UDM staging
- [ ] `output_database` exists (if loading)

✓ **settings.yaml**
- [ ] `max_expansion_factor` appropriate (default: 30)
- [ ] `max_iterations` sufficient (default: 5000)
- [ ] `geographies` list correct

✓ **configs_mp/settings.yaml**
- [ ] `num_processes` matches available cores
- [ ] `multiprocess: True` (unless debugging)

✓ **controls.csv**
- [ ] 56 controls defined
- [ ] No duplicate `target` names
- [ ] Expressions valid pandas syntax
- [ ] Importance weights reasonable

## Next Steps

✅ Configuration complete? → [Running PopulationSim](Running-PopulationSim)  
✅ Need data info? → [Data Preparation](Data-Preparation)  
❓ Something not working? → [Troubleshooting](Troubleshooting)

---

**For detailed technical documentation:** See [SANDAG_PopulationSim_Documentation.md](../documentation/SANDAG_PopulationSim_Documentation.md) Section 4.2
