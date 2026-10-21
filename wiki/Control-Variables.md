# Control Variables Reference

Complete list of all 56 control variables used in SANDAG PopulationSim.

## Overview

Control variables are demographic totals that PopulationSim matches during synthesis. Each control has:
- **Target:** Household (`household`) or Person (`person`)
- **Geography:** Where control is applied (`region`, `puma`, or `mgra`)
- **Importance:** Weight for balancing (higher = more precise matching)
- **Expression:** PUMS variable logic for classification
- **Description:** Human-readable explanation

## Importance Weights

| Range | Meaning | Example Use |
|-------|---------|-------------|
| 1,000,000,000 | **Critical** - Must match exactly | Total households |
| 1,000,000 | **Very High** - Top priority | Sex totals |
| 250,000 | **High** - Important demographics | Household size |
| 100,000 | **Medium** - Standard controls | Income, age, race |

Higher importance = tighter constraint during IPF optimization.

## Household Controls (18 total)

### Total Households (1 control)

| ID | Control Name | Geography | Importance | Expression | Description |
|----|-------------|-----------|------------|------------|-------------|
| 1 | `Total_HH` | mgra | 1,000,000,000 | `(WGTP > 0) & (WGTP < np.inf)` | Total households (highest priority) |

**Note:** This is the most important control - must match exactly. All other controls are secondary.

### Household Size (4 controls)

| ID | Control Name | Geography | Importance | Expression | Description |
|----|-------------|-----------|------------|------------|-------------|
| 2 | `HHSize_1` | mgra | 250,000 | `NP == 1` | Single-person households |
| 3 | `HHSize_2` | mgra | 250,000 | `NP == 2` | Two-person households |
| 4 | `HHSize_3` | mgra | 250,000 | `NP == 3` | Three-person households |
| 5 | `HHSize_4Plus` | mgra | 250,000 | `NP >= 4` | Households with 4+ persons |

**Sum constraint:** HHSize_1 + HHSize_2 + HHSize_3 + HHSize_4Plus = Total_HH

### Household Income (7 controls)

| ID | Control Name | Geography | Importance | Expression | Description |
|----|-------------|-----------|------------|------------|-------------|
| 6 | `HHInc_0to14999` | mgra | 100,000 | `(HHADJINC >= 0) & (HHADJINC <= 14999)` | Income: $0-$14,999 |
| 7 | `HHInc_15000to29999` | mgra | 100,000 | `(HHADJINC >= 15000) & (HHADJINC <= 29999)` | Income: $15,000-$29,999 |
| 8 | `HHInc_30000to59999` | mgra | 100,000 | `(HHADJINC >= 30000) & (HHADJINC <= 59999)` | Income: $30,000-$59,999 |
| 9 | `HHInc_60000to99999` | mgra | 100,000 | `(HHADJINC >= 60000) & (HHADJINC <= 99999)` | Income: $60,000-$99,999 |
| 10 | `HHInc_100000to149999` | mgra | 100,000 | `(HHADJINC >= 100000) & (HHADJINC <= 149999)` | Income: $100,000-$149,999 |
| 11 | `HHInc_150000to199999` | mgra | 100,000 | `(HHADJINC >= 150000) & (HHADJINC <= 199999)` | Income: $150,000-$199,999 |
| 12 | `HHInc_200000Plus` | mgra | 100,000 | `(HHADJINC >= 200000)` | Income: $200,000+ |

**Variable:** `HHADJINC` = Adjusted household income (inflation-adjusted to ACS year)

### Workers per Household (4 controls)

| ID | Control Name | Geography | Importance | Expression | Description |
|----|-------------|-----------|------------|------------|-------------|
| 13 | `HHWork_0` | mgra | 100,000 | `workers == 0` | Zero-worker households |
| 14 | `HHWork_1` | mgra | 100,000 | `workers == 1` | One-worker households |
| 15 | `HHWork_2` | mgra | 100,000 | `workers == 2` | Two-worker households |
| 16 | `HHWork_3Plus` | mgra | 100,000 | `workers >= 3` | Households with 3+ workers |

**Variable:** `workers` = Derived from person-level ESR (employment status) within household

### Children Presence (2 controls)

| ID | Control Name | Geography | Importance | Expression | Description |
|----|-------------|-----------|------------|------------|-------------|
| 17 | `HHChild_0` | mgra | 100,000 | `HUPAC == 4` | No children present |
| 18 | `HHChild_1Plus` | mgra | 100,000 | `(HUPAC == 1) \| (HUPAC == 2) \| (HUPAC == 3)` | One or more children present |

**Variable:** `HUPAC` = HH presence and age of children
- 1 = With children under 6 only
- 2 = With children 6-17 only
- 3 = With children under 6 and 6-17
- 4 = No children

## Person Controls (38 total)

### Sex (2 controls)

| ID | Control Name | Geography | Importance | Expression | Description |
|----|-------------|-----------|------------|------------|-------------|
| 19 | `Male` | mgra | 1,000,000 | `SEX == 1` | Male persons |
| 20 | `Female` | mgra | 1,000,000 | `SEX == 2` | Female persons |

**Sum constraint:** Male + Female = Total Population (household + GQ)

### Age (9 controls)

| ID | Control Name | Geography | Importance | Expression | Description |
|----|-------------|-----------|------------|------------|-------------|
| 21 | `Age_LT5` | mgra | 100,000 | `(AGEP >= 0) & (AGEP <= 4)` | Age 0-4 years |
| 22 | `Age_5to9` | mgra | 100,000 | `(AGEP >= 5) & (AGEP <= 9)` | Age 5-9 years |
| 23 | `Age_10to14` | mgra | 100,000 | `(AGEP >= 10) & (AGEP <= 14)` | Age 10-14 years |
| 24 | `Age_15to17` | mgra | 100,000 | `(AGEP >= 15) & (AGEP <= 17)` | Age 15-17 years |
| 25 | `Age_18to24` | mgra | 100,000 | `(AGEP >= 18) & (AGEP <= 24)` | Age 18-24 years |
| 26 | `Age_25to34` | mgra | 100,000 | `(AGEP >= 25) & (AGEP <= 34)` | Age 25-34 years |
| 27 | `Age_35to49` | mgra | 100,000 | `(AGEP >= 35) & (AGEP <= 49)` | Age 35-49 years |
| 28 | `Age_50to64` | mgra | 100,000 | `(AGEP >= 50) & (AGEP <= 64)` | Age 50-64 years |
| 29 | `Age_65Plus` | mgra | 100,000 | `(AGEP >= 65)` | Age 65+ years |

**Variable:** `AGEP` = Age in years at time of survey

### Race/Ethnicity (7 controls)

| ID | Control Name | Geography | Importance | Expression | Description |
|----|-------------|-----------|------------|------------|-------------|
| 30 | `race_White` | mgra | 100,000 | `race == 1` | White alone, non-Hispanic |
| 31 | `race_Black` | mgra | 100,000 | `race == 2` | Black/African American alone |
| 32 | `race_AmInd` | mgra | 100,000 | `race == 3` | American Indian/Alaska Native |
| 33 | `race_Asian` | mgra | 100,000 | `race == 4` | Asian alone |
| 34 | `race_PacIsl` | mgra | 100,000 | `race == 5` | Pacific Islander alone |
| 35 | `race_Other` | mgra | 100,000 | `race == 6` | Other race or two+ races |
| 36 | `race_Hispanic` | mgra | 100,000 | `race == 7` | Hispanic/Latino (any race) |

**Variable:** `race` = Derived from `RAC1P` (race) and `HISP` (Hispanic origin)
- If `HISP > 1`: race = 7 (Hispanic)
- Else: race = simplified RAC1P category

### Employment Status (17 controls - Region level only)

#### Total Employment & Unemployment

| ID | Control Name | Geography | Importance | Expression | Description |
|----|-------------|-----------|------------|------------|-------------|
| 37 | `employed_civilians` | region | 100,000 | `(ESR == 1) \| (ESR == 2) \| (ESR == 4) \| (ESR == 5)` | Civilian employed persons |
| 38 | `employed_military` | region | 100,000 | `ESR == 6` | Active duty military |
| 39 | `unemployed` | region | 100,000 | `ESR == 3` | Unemployed persons |

**Variable:** `ESR` = Employment status recode
- 1 = Civilian employed, at work
- 2 = Civilian employed, with job but not at work
- 3 = Unemployed
- 4 = Armed forces, at work
- 5 = Armed forces, with job but not at work
- 6 = Not in labor force

#### Workers by Age (7 controls)

| ID | Control Name | Geography | Importance | Expression | Description |
|----|-------------|-----------|------------|------------|-------------|
| 40 | `workers_age16to19` | region | 100,000 | `((ESR == 1) \| (ESR == 2)) & (AGEP >= 16) & (AGEP <= 19)` | Workers age 16-19 |
| 41 | `workers_age20to24` | region | 100,000 | `((ESR == 1) \| (ESR == 2)) & (AGEP >= 20) & (AGEP <= 24)` | Workers age 20-24 |
| 42 | `workers_age25to34` | region | 100,000 | `((ESR == 1) \| (ESR == 2)) & (AGEP >= 25) & (AGEP <= 34)` | Workers age 25-34 |
| 43 | `workers_age35to44` | region | 100,000 | `((ESR == 1) \| (ESR == 2)) & (AGEP >= 35) & (AGEP <= 44)` | Workers age 35-44 |
| 44 | `workers_age45to54` | region | 100,000 | `((ESR == 1) \| (ESR == 2)) & (AGEP >= 45) & (AGEP <= 54)` | Workers age 45-54 |
| 45 | `workers_age55to64` | region | 100,000 | `((ESR == 1) \| (ESR == 2)) & (AGEP >= 55) & (AGEP <= 64)` | Workers age 55-64 |
| 46 | `workers_age65Plus` | region | 100,000 | `((ESR == 1) \| (ESR == 2)) & (AGEP >= 65)` | Workers age 65+ |

#### Labor Force Participation by Age (7 controls)

| ID | Control Name | Geography | Importance | Expression | Description |
|----|-------------|-----------|------------|------------|-------------|
| 47 | `labor_force_age16to19` | region | 100,000 | `(ESR <= 5) & (AGEP >= 16) & (AGEP <= 19)` | Labor force age 16-19 |
| 48 | `labor_force_age20to24` | region | 100,000 | `(ESR <= 5) & (AGEP >= 20) & (AGEP <= 24)` | Labor force age 20-24 |
| 49 | `labor_force_age25to34` | region | 100,000 | `(ESR <= 5) & (AGEP >= 25) & (AGEP <= 34)` | Labor force age 25-34 |
| 50 | `labor_force_age35to44` | region | 100,000 | `(ESR <= 5) & (AGEP >= 35) & (AGEP <= 44)` | Labor force age 35-44 |
| 51 | `labor_force_age45to54` | region | 100,000 | `(ESR <= 5) & (AGEP >= 45) & (AGEP <= 54)` | Labor force age 45-54 |
| 52 | `labor_force_age55to64` | region | 100,000 | `(ESR <= 5) & (AGEP >= 55) & (AGEP <= 64)` | Labor force age 55-64 |
| 53 | `labor_force_age65Plus` | region | 100,000 | `(ESR <= 5) & (AGEP >= 65)` | Labor force age 65+ |

**Note:** Employment controls are **region-level only** (not MGRA-level) because:
- Employment data less reliable at fine geography
- Labor force participation is regional economic characteristic
- Reduces computational complexity

## Group Quarters Controls (3 total)

Group quarters controls use **exact sampling** (not IPF importance weights):

| ID | Control Name | Geography | Importance | Expression | Description |
|----|-------------|-----------|------------|------------|-------------|
| 57 | `gq_mil_pop` | mgra | None | `gq_type == 1` | Military group quarters population |
| 58 | `gq_college_pop` | mgra | None | `gq_type == 2` | College dormitory population |
| 59 | `gq_other_pop` | mgra | None | `gq_type == 3` | Other group quarters population |

**Process:** After IPF synthesis, GQ persons are sampled from seed data to exactly match these totals (no balancing needed).

## Control Data Sources

| Controls | Data Source | Query/File |
|----------|-------------|------------|
| 1-36 (HH & Person) | UDM Staging Database | `sql/mgra_controls.sql` |
| 37-53 (Employment) | Economic Team CSV | `data/Economic Team Region Controls.csv` |
| 57-59 (Group Quarters) | UDM Staging Database | `sql/mgra_controls.sql` (separate section) |

## Control Validation

Before running PopulationSim, verify controls pass these checks:

### 1. Completeness
```python
# All MGRAs should have controls (even if zero)
df_controls = pd.read_csv('populationsim/data/controls.csv')
unique_mgras = df_controls['mgra'].nunique()
assert unique_mgras == 23002, f"Missing MGRAs: {23002 - unique_mgras}"
```

### 2. Summation Logic
```python
# Household size should sum to total households
for mgra in df_controls['mgra'].unique():
    total_hh = df_controls.loc[(df_controls['mgra'] == mgra) & 
                                (df_controls['target'] == 'Total_HH'), 'value'].sum()
    size_sum = df_controls.loc[(df_controls['mgra'] == mgra) & 
                                (df_controls['target'].isin(['HHSize_1', 'HHSize_2', 
                                                              'HHSize_3', 'HHSize_4Plus'])), 
                                'value'].sum()
    assert abs(total_hh - size_sum) < 1, f"MGRA {mgra}: Size sum mismatch"
```

### 3. Non-Negative Values
```python
# All controls must be >= 0
assert (df_controls['value'] >= 0).all(), "Negative control values found!"
```

### 4. Reasonable Ranges
```python
# Total HH should be in expected range
region_hh = df_controls.loc[df_controls['target'] == 'Total_HH', 'value'].sum()
assert 1_000_000 < region_hh < 2_000_000, f"Unreasonable HH total: {region_hh:,}"
```

## Adding Custom Controls

To add a new control variable:

**1. Define in `populationsim/configs/controls.csv`:**
```csv
target,control_name,seed_table,geography,importance
household,HHType_Family,households,mgra,100000
```

**2. Add expression to seed data creation:**
```python
# In python/build_seed_data.py
df_households['HHType_Family'] = (df_households['HHT'].isin([1, 2, 3, 4, 5, 6])).astype(int)
```

**3. Add to control generation query:**
```sql
-- In sql/mgra_controls.sql
SELECT 
    mgra,
    'HHType_Family' as target,
    SUM(CASE WHEN household_type IN ('Family') THEN households ELSE 0 END) as value
FROM staging_table
GROUP BY mgra
```

**4. Test with small geography first:**
```yaml
# In config.yml, test with one year and verify
years:
  - 2022
```

---

**Next:** [Algorithm Details](Algorithm-Details) - How PopulationSim balances these 56 controls
