-- Create '[inputs]' schema if it does not exist
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '[inputs]')
BEGIN
    EXEC('CREATE SCHEMA [inputs]')
END
GO

-- Create 'outputs' schema if it does not exist
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'outputs')
BEGIN
    EXEC('CREATE SCHEMA outputs')
END
GO

-- Create 'outputs' schema if it does not exist
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'metadata')
BEGIN
    EXEC('CREATE SCHEMA metadata')
END
GO

-- Create Table [metadata].[run]
CREATE TABLE [metadata].[run] (
    [run_id] INT NOT NULL,
    [year] INT NOT NULL,
    [user] NVARCHAR(100) NOT NULL, 
    [date] DATETIME NOT NULL,
    [version] NVARCHAR(50) NOT NULL,
    [comments] NVARCHAR(200) NULL,
    [loaded] BIT NOT NULL,
    CONSTRAINT [pk_run] PRIMARY KEY ([run_id]))
WITH (DATA_COMPRESSION = PAGE)
GO

-- Create Table '[inputs].[controls]'
CREATE TABLE [inputs].[controls] (
    [run_id] INT NOT NULL,
    [control_id] INT NOT NULL,
    [control_name] NVARCHAR(255) NOT NULL,
    [geography_name] NVARCHAR(255) NOT NULL,
    [output_name] NVARCHAR(255) NOT NULL,
    [importance] INT NOT NULL,
    [expression] NVARCHAR(MAX) NOT NULL,
    FOREIGN KEY ([run_id]) REFERENCES [metadata].[run]([run_id])
) WITH (DATA_COMPRESSION = PAGE);
GO


-- Create Table '[inputs].[region_controls]'
CREATE TABLE [inputs].[region_controls] (
    [run_id] INT NOT NULL,
    [year] INT NOT NULL,
    [region] INT NOT NULL,
    [job_1] INT NOT NULL,
    [job_2] INT NOT NULL,
    [job_3] INT NOT NULL,
    [job_4] INT NOT NULL,
    [job_5] INT NOT NULL,
    [job_6] INT NOT NULL,
    [job_7] INT NOT NULL,
    [job_8] INT NOT NULL,
    [job_9] INT NOT NULL,
    [job_10] INT NOT NULL,
    [job_11] INT NOT NULL,
    [job_12] INT NOT NULL,
    [job_13] INT NOT NULL,
    [job_14] INT NOT NULL,
    [lfp_black] INT NOT NULL,
    [lfp_hispanic] INT NOT NULL,
    [lfp_other] INT NOT NULL,
    [lfp_white] INT NOT NULL,
    FOREIGN KEY ([run_id]) REFERENCES [metadata].[run]([run_id])
) WITH (DATA_COMPRESSION = PAGE);
GO


-- Create Table '[inputs].[mgra_controls]'
CREATE TABLE [inputs].[mgra_controls] (
    [run_id] INT NOT NULL,
    [year] INT NOT NULL,
    [mgra] INT NOT NULL,
    [Male] INT NOT NULL,
    [Female] INT NOT NULL,
    [Age_LT5] INT NOT NULL,
    [Age_5to9] INT NOT NULL,
    [Age_10to14] INT NOT NULL,
    [Age_15to17] INT NOT NULL,
    [Age_18to24] INT NOT NULL,
    [Age_25to34] INT NOT NULL,
    [Age_35to44] INT NOT NULL,
    [Age_45to54] INT NOT NULL,
    [Age_55to64] INT NOT NULL,
    [Age_65to74] INT NOT NULL,
    [Age_75to84] INT NOT NULL,
    [Age_85Plus] INT NOT NULL,
    [Asian] INT NOT NULL,
    [Black] INT NOT NULL,
    [Hispanic] INT NOT NULL,
    [Other_v2] INT NOT NULL,
    [TwoorMore] INT NOT NULL,
    [White] INT NOT NULL,
    [HHSize_1] INT NOT NULL,
    [HHSize_2] INT NOT NULL,
    [HHSize_3] INT NOT NULL,
    [HHSize_4Plus] INT NOT NULL,
    [Total_HH] INT NOT NULL,
    [HHWork_0] INT NOT NULL,
    [HHWork_1] INT NOT NULL,
    [HHWork_2] INT NOT NULL,
    [HHWork_3Plus] INT NOT NULL,
    [HHChild_0] INT NOT NULL,
    [HHChild_1Plus] INT NOT NULL,
    [HHInc_0to14999] INT NOT NULL,
    [HHInc_15000to29999] INT NOT NULL,
    [HHInc_30000to59999] INT NOT NULL,
    [HHInc_60000to99999] INT NOT NULL,
    [HHInc_100000to149999] INT NOT NULL,
    [HHInc_150000to199999] INT NOT NULL,
    [HHInc_200000Plus] INT NOT NULL,
    [gq_college_pop] INT NOT NULL,
    [gq_mil_pop] INT NOT NULL,
    [gq_other_pop] INT NOT NULL,
    [Total_HH_GQ] INT NOT NULL,
    FOREIGN KEY ([run_id]) REFERENCES [metadata].[run]([run_id])
) WITH (DATA_COMPRESSION = PAGE);
GO


-- Create Table '[inputs].[seed_households_hh]'
CREATE TABLE [inputs].[seed_households_hh] (
    [run_id] INT NOT NULL,
    [SERIALNO] NVARCHAR(15) NOT NULL,
    [hhid] INT NOT NULL,
    [PUMA] INT NOT NULL,
    [NP] INT NOT NULL,
    [HHADJINC] NVARCHAR(15) NOT NULL,
    [ADJINC] NVARCHAR(15) NOT NULL,
    [WGTP] INT NOT NULL,
    [HHT] INT NOT NULL,
    [child_present] INT NOT NULL,
    [WIF] INT NOT NULL,
    [HUPAC] INT NOT NULL,
    [VEH] INT NOT NULL,
    [numWorkers] INT NOT NULL,
    [BLD] INT NOT NULL,
    FOREIGN KEY ([run_id]) REFERENCES [metadata].[run]([run_id])
) WITH (DATA_COMPRESSION = PAGE);
GO

-- Create Table '[inputs].[seed_households_gq]'
CREATE TABLE [inputs].[seed_households_gq] (
    [run_id] INT NOT NULL,
    [SERIALNO] NVARCHAR(15) NOT NULL,
    [hhid] INT NOT NULL,
    [PUMA] INT NOT NULL,
    [NP] INT NOT NULL,
    [HHADJINC] NVARCHAR(15) NOT NULL,
    [ADJINC] NVARCHAR(15) NOT NULL,
    [WGTP] INT NOT NULL,
    [HHT] INT NULL,
    [GQ_type] INT NOT NULL,
    [child_present] INT NOT NULL,
    [WIF] INT NULL,
    [HUPAC] INT NULL,
    [VEH] INT NULL,
    [numWorkers] INT NOT NULL,
    [BLD] INT NULL,
    FOREIGN KEY ([run_id]) REFERENCES [metadata].[run]([run_id])
) WITH (DATA_COMPRESSION = PAGE);
GO




-- Create Table '[inputs].[seed_persons_hh]'
CREATE TABLE [inputs].[seed_persons_hh] (
    [run_id] INT NOT NULL,
    [HHID] INT NOT NULL,
    [SPORDER] INT NOT NULL,
    [PUMA] INT NOT NULL,
    [AGEP] INT NOT NULL,
    [SCHG] INT NOT NULL,
    [COW] INT NULL,
    [SEX] NVARCHAR(1) NOT NULL,
    [ESR] NVARCHAR(1) NULL,
    [MIL] NVARCHAR(1) NULL,
    [WKHP] INT NULL,
    [RAC1P] INT NOT NULL,
    [HISP] INT NOT NULL,
    [isWorker] INT NOT NULL,
    [pop_race] NVARCHAR(255) NOT NULL,
    [NAICS2] NVARCHAR(3) NOT NULL,
    [WKW] NVARCHAR(1) NULL,
    [OCCP] NVARCHAR(4) NULL,
    [SCHL] NVARCHAR(2) NULL,
    [isinlaborforce] INT NOT NULL,
    [SOCP] NVARCHAR(255) NOT NULL,
    [SOC2] NVARCHAR(3) NOT NULL,
    FOREIGN KEY ([run_id]) REFERENCES [metadata].[run]([run_id])
) WITH (DATA_COMPRESSION = PAGE);
GO


-- Create Table '[inputs].[seed_persons_gq]'
CREATE TABLE [inputs].[seed_persons_gq] (
    [run_id] INT NOT NULL,
    [SPORDER] INT NOT NULL,
    [PUMA] INT NOT NULL,
    [AGEP] INT NOT NULL,
    [SCHG] INT NOT NULL,
    [COW] INT NULL,
    [SEX] NVARCHAR(1) NOT NULL,
    [ESR] NVARCHAR(1) NULL,
    [MIL] NVARCHAR(1) NULL,
    [WKHP] INT NULL,
    [RAC1P] INT NOT NULL,
    [HISP] INT NOT NULL,
    [isWorker] INT NOT NULL,
    [pop_race] NVARCHAR(255) NOT NULL,
    [NAICS2] NVARCHAR(3) NOT NULL,
    [WKW] NVARCHAR(1) NULL,
    [OCCP] NVARCHAR(4) NULL,
    [SCHL] NVARCHAR(2) NULL,
    [isinlaborforce] INT NOT NULL,
    [SOCP] NVARCHAR(255) NOT NULL,
    [SOC2] NVARCHAR(3) NOT NULL,
    FOREIGN KEY ([run_id]) REFERENCES [metadata].[run]([run_id])
) WITH (DATA_COMPRESSION = PAGE);
GO



-- Create Table '[outputs].[households]' 
CREATE TABLE [outputs].[households] (
    [run_id] INT NOT NULL,
    [year] INT NOT NULL, 
    [household_id] INT NOT NULL,
    [mgra] INT NOT NULL,
    [NP] FLOAT NOT NULL,
    [HHADJINC] FLOAT NOT NULL,
    [HHT] NVARCHAR(1) NOT NULL,
    [WIF] INT NULL,
    [HUPAC] NVARCHAR(1) NOT NULL,
    [VEH] NVARCHAR(1),
    [BLD] NVARCHAR(2),
    [GQ_type] INT NOT NULL,
    INDEX ccsi_outputs_households CLUSTERED COLUMNSTORE
);
GO


-- Create Table '[outputs].[persons]'
CREATE TABLE [outputs].[persons] (
    [run_id] INT NOT NULL,
    [year] INT NOT NULL,
    [mgra] INT NOT NULL,
    [household_id] INT NOT NULL,
    [SPORDER] FLOAT NULL,
    [AGEP] FLOAT NULL,
    [SEX] NVARCHAR(1) NOT NULL,
    [ESR] NVARCHAR(1) NOT NULL,
    [COW] NVARCHAR(1) NOT NULL,
    [WKHP] FLOAT NOT NULL,
    [SCHG] NVARCHAR(2) NOT NULL,
    [RAC1P] NVARCHAR(1) NOT NULL,
    [HISP] NVARCHAR(2) NOT NULL,
    [MIL] NVARCHAR(1) NOT NULL,
    [SCHL] NVARCHAR(2) NOT NULL,
    [OCCP] NVARCHAR(4) NOT NULL,
    [WKW] NVARCHAR(1) NOT NULL,
    [NAICS2] NVARCHAR(3) NOT NULL,
    [SOC2] NVARCHAR(3) NOT NULL,
    INDEX CCI_outputs_persons CLUSTERED COLUMNSTORE
);
GO



-- Create Table '[outputs].[mgra_based_input]' (This is for the ABM Team) 
CREATE TABLE [outputs].[mgra_based_input] (
    [run_id] INT NOT NULL,
    [year] INT NOT NULL,
    [mgra] INT NOT NULL,
    [taz] INT NOT NULL,
    [LUZ] INT NOT NULL,
    [pop] INT NOT NULL,
    [hhp] INT NOT NULL,
    [hs] INT NOT NULL,
    [hs_sf] INT NOT NULL,
    [hs_mf] INT NOT NULL,
    [hs_mh] INT NOT NULL,
    [hh] INT NOT NULL,
    [hh_sf] INT NOT NULL,
    [hh_mf] INT NOT NULL,
    [hh_mh] INT NOT NULL,
    [hhs] INT NOT NULL,
    [gq_civ] INT NOT NULL,
    [gq_mil] INT NOT NULL,
    [i1] INT NOT NULL,
    [i2] INT NOT NULL,
    [i3] INT NOT NULL,
    [i4] INT NOT NULL,
    [i5] INT NOT NULL,
    [i6] INT NOT NULL,
    [i7] INT NOT NULL,
    [i8] INT NOT NULL,
    [i9] INT NOT NULL,
    [i10] INT NOT NULL,
    [emp_gov] INT NOT NULL,
    [emp_mil] INT NOT NULL,
    [emp_ag_min] INT NOT NULL,
    [emp_bus_svcs] INT NOT NULL,
    [emp_fin_res_mgm] INT NOT NULL,
    [emp_educ] INT NOT NULL,
    [emp_hlth] INT NOT NULL,
    [emp_ret] INT NOT NULL,
    [emp_trn_wrh] INT NOT NULL,
    [emp_con] INT NOT NULL,
    [emp_utl] INT NOT NULL,
    [emp_mnf] INT NOT NULL,
    [emp_whl] INT NOT NULL,
    [emp_ent] INT NOT NULL,
    [emp_accm] INT NOT NULL,
    [emp_food] INT NOT NULL,
    [emp_oth] INT NOT NULL,
    [emp_non_ws_wfh] INT NOT NULL,
    [emp_non_ws_oth] INT NOT NULL,
    [emp_total] INT NOT NULL,
    [pseudomsa] INT NOT NULL,
    [zip] INT NOT NULL,
    [enrollgradekto8] INT NOT NULL,
    [enrollgrade9to12] INT NOT NULL,
    [majorcollegeenroll_total] INT NOT NULL,
    [othercollegeenroll_total] INT NOT NULL,
    [hotelroomtotal] INT NOT NULL,
    [parkactive] INT NOT NULL,
    [openspaceparkpreserve] INT NOT NULL,
    [beachactive] INT NOT NULL,
    [district27] INT NOT NULL,
    [milestocoast] FLOAT NOT NULL,
    [acre] FLOAT NOT NULL,
    [landacre] FLOAT NOT NULL,
    [effective_acres] FLOAT NOT NULL,
    [truckregiontype] INT NOT NULL
) WITH (DATA_COMPRESSION = PAGE);
GO


