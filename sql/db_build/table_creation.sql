CREATE SCHEMA [inputs];
GO

CREATE SCHEMA [outputs];
GO

CREATE SCHEMA [metadata];
GO

-- Create Table [metadata].[run]
CREATE TABLE [metadata].[run] (
    [run_id] INT NOT NULL,
    [year] INT NOT NULL,
    [user] NVARCHAR(100) NOT NULL, 
    [date] DATETIME NOT NULL,
    [version] NVARCHAR(50) NOT NULL,
    [staging_schema] NVARCHAR(50) NOT NULL,
    [comments] NVARCHAR(200) NULL,
    [loaded] BIT NOT NULL,
    CONSTRAINT [pk_metadata_run] PRIMARY KEY ([run_id]))
WITH (DATA_COMPRESSION = PAGE)
GO

-- Create Table '[inputs].[controls]'
CREATE TABLE [inputs].[controls] (
    [run_id] INT NOT NULL,
    [control_id] INT NOT NULL,
    [target] NVARCHAR(255) NOT NULL,
    [geography] NVARCHAR(255) NOT NULL,
    [seed_table] NVARCHAR(255) NOT NULL,
    [importance] INT NOT NULL,
    [control_field] NVARCHAR(255) NOT NULL,
    [expression] NVARCHAR(255) NOT NULL,
    CONSTRAINT [pk_inputs_controls] PRIMARY KEY ([run_id], [control_id]),
    CONSTRAINT fk_inputs_controls_run_id FOREIGN KEY ([run_id])
    REFERENCES [metadata].[run]([run_id])
) WITH (DATA_COMPRESSION = PAGE);
GO

-- Create Table '[outputs].[control_totals]'
CREATE TABLE [outputs].[control_totals] (
    [run_id] INT NOT NULL,
    [geography] NVARCHAR(15) NOT NULL,
    [geography_id] NVARCHAR(15) NOT NULL,
    [control_id] INT NOT NULL,
    [control_value] INT NOT NULL,
    [result] INT NOT NULL,
    INDEX ccsi_outputs_control_totals CLUSTERED COLUMNSTORE,
    CONSTRAINT fk_control_totals_run_id_control_id FOREIGN KEY ([run_id], [control_id]) 
    REFERENCES [inputs].[controls] ([run_id], [control_id]),
    CONSTRAINT fk_control_totals_run_id FOREIGN KEY ([run_id]) REFERENCES [metadata].[run]([run_id])
);
GO

-- Create Table '[inputs].[seed_households]' 
CREATE TABLE [inputs].[seed_households] (
    [run_id] INT NOT NULL,
    [SERIALNO] VARCHAR(13) NOT NULL,
    [PUMA] VARCHAR(5) NOT NULL,
    [NP] FLOAT NOT NULL,
    [HINCP] FLOAT NULL,
    [HHADJINC] INT NULL,
    [HHT] VARCHAR(1) NULL,
    [workers] INT NOT NULL,
    [HUPAC] VARCHAR(1) NULL,
    [VEH] VARCHAR(1) NULL,
    [BLD] VARCHAR(2) NULL,
    [TYPEHUGQ] INT NOT NULL,
    [gq_type] INT NOT NULL,
    [WGTP] FLOAT NOT NULL,
    [hhid] INT NOT NULL,
    CONSTRAINT fk_inputs_seed_households_run_id FOREIGN KEY ([run_id]) REFERENCES [metadata].[run]([run_id]),
    INDEX ccsi_inputs_seed_households CLUSTERED COLUMNSTORE
);
GO

-- Create Table '[inputs].[seed_persons]'
CREATE TABLE [inputs].[seed_persons] (
    [run_id] INT NOT NULL,
    [SERIALNO] VARCHAR(13) NOT NULL, 
    [SPORDER] FLOAT NOT NULL,
    [PUMA] VARCHAR(5) NOT NULL,
    [AGEP] FLOAT NOT NULL,
    [SEX] VARCHAR(1) NOT NULL,
    [ESR] VARCHAR(1) NULL, 
    [laborforce] INT NOT NULL,
    [worker] INT NOT NULL,
    [COW] VARCHAR(1) NULL, 
    [WKHP] FLOAT NULL,
    [SCHG] VARCHAR(2) NOT NULL, 
    [HISP] INT NOT NULL,
    [RAC1P] VARCHAR(1) NOT NULL, 
    [race] VARCHAR(255) NOT NULL,
    [MIL] VARCHAR(1) NULL, 
    [SCHL] VARCHAR(2) NULL, 
    [OCCP] VARCHAR(4) NULL, 
    [WKW] VARCHAR(1) NULL,
    [NAICSP] VARCHAR(8) NULL, 
    [NAICS2] VARCHAR(3) NULL, 
    [SOCP] VARCHAR(6) NULL, 
    [SOC2] VARCHAR(2) NULL, 
    [TYPEHUGQ] INT NOT NULL,
    [gq_type] INT NOT NULL,
    [hhid] INT NOT NULL,
    [PINCP] FLOAT NULL
    CONSTRAINT fk_inputs_seed_persons_run_id FOREIGN KEY ([run_id]) REFERENCES [metadata].[run]([run_id]),
    INDEX ccsi_inputs_seed_persons CLUSTERED COLUMNSTORE
);
GO


-- Create Table '[outputs].[households]'
CREATE TABLE [outputs].[households] (
    [run_id] INT NOT NULL,
    [household_id] INT NOT NULL,
    [mgra] INT NOT NULL,
    [SERIALNO] VARCHAR(13) NOT NULL,
    [NP] FLOAT NOT NULL,
    [HHADJINC] INT NULL,
    [HHT] VARCHAR(1) NULL,
    [HUPAC] VARCHAR(1) NULL,
    [VEH] VARCHAR(1) NULL,
    [BLD] VARCHAR(2) NULL,
    [gq_type] INT NOT NULL,
    [workers] INT NOT NULL,
    CONSTRAINT fk_outputs_households_run_id FOREIGN KEY ([run_id]) REFERENCES [metadata].[run]([run_id]),
    INDEX ccsi_outputs_households CLUSTERED COLUMNSTORE
);
GO


-- Create Table '[outputs].[persons]'
CREATE TABLE [outputs].[persons] (
    [run_id] INT NOT NULL,
    [mgra] INT NOT NULL,
    [household_id] INT NOT NULL,
    [SERIALNO] VARCHAR(13) NOT NULL,
    [SPORDER] FLOAT NULL,
    [AGEP] FLOAT NULL,
    [SEX] VARCHAR(1) NOT NULL,
    [ESR] VARCHAR(1) NULL,
    [COW] VARCHAR(1) NULL,
    [WKHP] FLOAT NULL,
    [SCHG] VARCHAR(2) NOT NULL,
    [RAC1P] VARCHAR(1) NOT NULL,
    [HISP] INT NOT NULL,
    [MIL] VARCHAR(1) NULL,
    [SCHL] VARCHAR(2) NULL,
    [OCCP] VARCHAR(4) NULL,
    [WKW] VARCHAR(1) NULL,
    [NAICSP] VARCHAR(8) NULL,
    [NAICS2] VARCHAR(3) NULL,
    [SOCP] VARCHAR(6) NULL,
    [SOC2] VARCHAR(2) NULL,
    CONSTRAINT fk_outputs_persons_run_id FOREIGN KEY ([run_id]) REFERENCES [metadata].[run]([run_id]),
    INDEX ccsi_outputs_persons CLUSTERED COLUMNSTORE
);
GO

-- Create Table '[outputs].[mgra_based_input]' (This is for the ABM Team) 
CREATE TABLE [outputs].[mgra_based_input] (
    [run_id] INT NOT NULL,
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
    [hhs] FLOAT NOT NULL,
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
    [parkactive] FLOAT NOT NULL,
    [openspaceparkpreserve] FLOAT NOT NULL,
    [beachactive] FLOAT NOT NULL,
    [district27] INT NOT NULL,
    [milestocoast] FLOAT NOT NULL,
    [acre] FLOAT NOT NULL,
    [landacre] FLOAT NOT NULL,
    [effective_acres] FLOAT NOT NULL,
    [truckregiontype] INT NOT NULL,
    CONSTRAINT fk_outputs_mgra_based_input_run_id FOREIGN KEY ([run_id]) REFERENCES [metadata].[run]([run_id]),
    INDEX ccsi_mgra_based_input CLUSTERED COLUMNSTORE
);
GO