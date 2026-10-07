# Plan: SANDAG PopulationSim Comprehensive Documentation

Create detailed technical documentation for SANDAG's PopulationSim implementation in Markdown format, structured after the MWCOG example with sections on Population Synthesizer methodology and Data Preparation & Application. Target audience: technical staff running the system and ABM team consuming outputs.

## Steps

1. **Create documentation structure** - Create main documentation file `documentation/SANDAG_PopulationSim_Documentation.md` with complete section outline
   
2. **Section 1: Introduction & Overview** - Write executive summary, system purpose, key features, and software dependencies (*parallel with step 3*)
   
3. **Section 2: SANDAG Population Synthesizer** (*parallel with step 2*) - Document methodology including:
   - PopulationSim conceptual framework and algorithm overview
   - Three-level geographic hierarchy (Region → PUMA → MGRA)
   - Control specifications (56+ controls defined in controls.csv)
   - Seed data structure from ACS PUMS
   - Balancing algorithm details (IPF, integerization, backstopping)
   - Group quarters handling (separate sampling approach)
   - Multiprocessing architecture (22 parallel processes)
   - Model pipeline steps with flowcharts

4. **Section 3: Data Preparation** (*depends on step 3*) - Document data sources and preparation:
   - ACS PUMS seed data extraction and processing
   - UDM forecast data (control totals at MGRA/Region levels)
   - Economic team controls integration
   - SQL query documentation for each data source
   - Geographic crosswalk creation
   - Data transformations (CPI adjustments, variable derivations)
   - Control file generation process

5. **Section 4: Application & Execution** (*depends on step 4*) - Document system operation:
   - Installation and environment setup (uv, dependencies)
   - Configuration files walkthrough (config.yml, secrets.yml, settings.yaml)
   - Step-by-step execution guide from main.py
   - Year iteration processing
   - Output file descriptions and schemas
   - ABM team deliverables format

6. **Section 5: Validation & Quality Assurance** (*depends on step 5*) - Document validation procedures:
   - Summary file interpretation
   - Streamlit reporting app usage
   - Control vs result comparison metrics
   - Common issues and troubleshooting

7. **Section 6: Database Integration (Optional)** (*depends on step 6*) - Document production database:
   - Database schema and table descriptions
   - ETL process documentation
   - Metadata and versioning system
   - Query examples for accessing results

8. **Create supporting materials** (*parallel with steps 2-7*) - Generate:
   - System architecture diagram (showing data flow)
   - Algorithm flowcharts for balancing process
   - Entity-relationship diagram for database schema
   - Example configuration files with annotations
   - Sample output file structures

9. **Add appendices** (*depends on steps 2-8*) - Create reference sections:
   - Appendix A: Complete control variable definitions
   - Appendix B: File format specifications
   - Appendix C: SQL query reference
   - Appendix D: Glossary of terms (PUMA, MGRA, IPF, etc.)
   - Appendix E: References and resources

10. **Review and finalize** - Verify completeness, accuracy, and clarity against MWCOG example structure

## Relevant Files

### Core documentation sources:
- `main.py` — Entry point and orchestration logic, documents end-to-end workflow
- `README.md` — Existing documentation to incorporate and expand
- `populationsim/configs/settings.yaml` — Algorithm configuration details
- `populationsim/configs/controls.csv` — Control variable specifications
- `populationsim/run_populationsim.py` — Main simulation runner
- `populationsim/generate_gq.py` — Group quarters synthesis approach

### Data preparation modules:
- `python/build_controls.py` — Control data generation, reference get_mgra_controls() and get_region_controls()
- `python/build_seed_data.py` — Seed data preparation, reference get_seed_households() and get_seed_persons()
- `python/outputs.py` — Output processing, reference create_abm_outputs() and organize_outputs()
- `python/etl.py` — Database ETL, reference run_etl() function

### SQL queries:
- `sql/seed_households.sql` — ACS PUMS household extraction with CPI adjustments
- `sql/seed_persons.sql` — ACS PUMS person extraction with labor force calculations  
- `sql/mgra_controls.sql` — MGRA-level control totals from UDM
- `sql/region_controls.sql` — Regional control totals
- `sql/mgrabase.sql` — ABM spatial reference file generation

### Database schema:
- `sql/db_build/table_creation.sql` — Production database schema

### Validation:
- `report/report.py` — Streamlit validation dashboard
- `report/controls.sql` — Query for validation data

### Existing diagrams:
- `documentation/Database Diagram.png` — Database schema visualization

## Verification

1. **Completeness checks**:
   - Verify all 56+ control variables are documented with formulas from controls.csv
   - Confirm all SQL queries are explained with sample output
   - Ensure all configuration parameters from settings.yaml are described
   - Validate all output files have schema documentation

2. **Technical accuracy**:
   - Test configuration examples provided in documentation
   - Verify algorithm descriptions match actual implementation in run_populationsim.py
   - Confirm file paths and command examples are correct for Windows environment

3. **Audience appropriateness**:
   - Include sufficient detail for technical staff to run system independently
   - Provide ABM team with clear output file specifications and schemas
   - Balance algorithm theory with practical implementation details

4. **MWCOG alignment**:
   - Verify Section 2 (Population Synthesizer) mirrors MWCOG methodology section structure
   - Confirm Section 3 (Data Preparation & Application) follows MWCOG practical implementation format

## Decisions

- **Format**: Markdown (.md) for version control compatibility and easy editing
- **Target audience**: Technical staff (operations) and ABM team (consumers)
- **Detail level**: Very detailed/comprehensive - include algorithm details, code references, complete configuration documentation
- **Structure**: Based on MWCOG sections 2.0 (synthesizer) and 3.0 (data prep/application)
- **Scope includes**: 
  - Full methodology documentation
  - Complete data pipeline description
  - Step-by-step execution guides
  - Validation procedures
  - Optional database integration
  - Supporting diagrams and appendices
- **Scope excludes**:
  - ActivitySim PopulationSim package internals (reference external docs)
  - Advanced troubleshooting beyond common issues
  - Modification guides for algorithm changes

## Further Considerations

1. **Diagram creation tools** - Recommendation: Use Mermaid for flowcharts (renders in Markdown). Should I create these inline or as separate image files?

2. **Code snippet inclusion** - Should the documentation include actual code snippets from Python files, or just describe functionality? Recommendation: Include key snippets for clarity, especially configuration examples.

3. **Version tracking** - Should the documentation include version history section tracking changes? Current config shows "v1.0.3-prerelease".
