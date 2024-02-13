-- Create '[inputs]' schema if it does not exist
CREATE SCHEMA inputs;
GO

CREATE SCHEMA outputs;
GO

CREATE SCHEMA metadata;
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
    [target] NVARCHAR(255) NOT NULL,
    [geography] NVARCHAR(255) NOT NULL,
    [seed_table] NVARCHAR(255) NOT NULL,
    [importance] INT NOT NULL,
    [control_field] NVARCHAR(255) NOT NULL,
    [expression] NVARCHAR(255) NOT NULL,
    CONSTRAINT [pk_run_control] PRIMARY KEY ([run_id], [control_id]),
    FOREIGN KEY ([run_id]) REFERENCES [metadata].[run]([run_id])
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
    CONSTRAINT fk_control_totals_controls FOREIGN KEY ([run_id], [control_id]) 
    REFERENCES [inputs].[controls] ([run_id], [control_id])
);
GO


-- Create Table '[inputs].[seed_households]'
CREATE TABLE [inputs].[seed_households] (
    [run_id] INT NOT NULL,
    [SERIALNO] NVARCHAR(15) NOT NULL,
    [PUMA] INT NOT NULL,
    [NP] INT NOT NULL,
    [HINCP] INT NOT NULL,
    [HHADJINC] INT NOT NULL,
    [HHT] INT NOT NULL,
    [workers] INT NOT NULL,
    [HUPAC] INT NOT NULL,
    [VEH] INT NOT NULL,
    [BLD] INT NOT NULL,
    [TYPEHUGQ] INT NOT NULL,
    [gq_type] INT NOT NULL,
    [WGTP] INT NOT NULL,
    [hhid] INT NOT NULL,
    FOREIGN KEY ([run_id]) REFERENCES [metadata].[run]([run_id]),
    INDEX ccsi_inputs_seed_households CLUSTERED COLUMNSTORE
);
GO

-- Create Table '[inputs].[seed_persons_hh]'
CREATE TABLE [inputs].[seed_persons_hh] (
    [run_id] INT NOT NULL,
    [SERIALNO] NVARCHAR(15) NOT NULL,
    [SPORDER] INT NOT NULL,
    [PUMA] INT NOT NULL,
    [AGEP] INT NOT NULL,
    [SEX] NVARCHAR(1) NOT NULL,
    [ESR] NVARCHAR(1) NULL,
    [laborforce] INT NOT NULL,
    [worker] INT NOT NULL,
    [COW] INT NULL,
    [WKHP] INT NULL,
    [SCHG] INT NOT NULL,
    [HISP] INT NOT NULL,
    [RAC1P] INT NOT NULL,
    [race] NVARCHAR(255) NOT NULL,
    [MIL] NVARCHAR(1) NULL,
    [SCHL] NVARCHAR(2) NULL,
    [OCCP] NVARCHAR(4) NULL,
    [WKW] NVARCHAR(1) NULL,
    [NAICSP] NVARCHAR(255) NULL,
    [NAICS2] NVARCHAR(3) NULL,
    [SOCP] NVARCHAR(255) NULL,
    [SOC2] NVARCHAR(3) NULL,
    [TYPEHUGQ] INT NOT NULL,
    [gq_type] INT NOT NULL,
    [hhid] INT NOT NULL,
    [PINCP] INT NOT NULL
    FOREIGN KEY ([run_id]) REFERENCES [metadata].[run]([run_id]),
    INDEX ccsi_inputs_seed_persons CLUSTERED COLUMNSTORE
);
GO


-- Create Table '[outputs].[households]' 
CREATE TABLE [outputs].[households] (
    [run_id] INT NOT NULL,
    [household_id] INT NOT NULL,
    [mgra] INT NOT NULL,
    [SERIALNO] NVARCHAR(15) NOT NULL,
    [NP] INT NOT NULL,
    [HHADJINC] INT NOT NULL,
    [HHT] NVARCHAR(1) NOT NULL,
    [HUPAC] NVARCHAR(1) NOT NULL,
    [VEH] NVARCHAR(1) NOT NULL,
    [BLD] NVARCHAR(2) NOT NULL,
    [gq_type] INT NOT NULL,
    [workers] INT NOT NULL,
    FOREIGN KEY ([run_id]) REFERENCES [metadata].[run]([run_id]),
    INDEX ccsi_outputs_households CLUSTERED COLUMNSTORE
);
GO


-- Create Table '[outputs].[persons]'
CREATE TABLE [outputs].[persons] (
    [run_id] INT NOT NULL,
    [mgra] INT NOT NULL,
    [household_id] INT NOT NULL,
    [SERIALNO] NVARCHAR(15) NOT NULL,
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
    [NAICSP] NVARCHAR(15) NULL,
    [NAICS2] NVARCHAR(3) NULL,
    [SOCP] NVARCHAR(15) NULL,
    [SOC2] NVARCHAR(3) NULL,
    FOREIGN KEY ([run_id]) REFERENCES [metadata].[run]([run_id]),
    INDEX CCI_outputs_persons CLUSTERED COLUMNSTORE
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
    [parkactive] INT NOT NULL,
    [openspaceparkpreserve] INT NOT NULL,
    [beachactive] INT NOT NULL,
    [district27] INT NOT NULL,
    [milestocoast] FLOAT NOT NULL,
    [acre] FLOAT NOT NULL,
    [landacre] FLOAT NOT NULL,
    [effective_acres] FLOAT NOT NULL,
    [truckregiontype] INT NOT NULL,
    FOREIGN KEY ([run_id]) REFERENCES [metadata].[run]([run_id]),
    INDEX ccsi_mgra_based_input CLUSTERED COLUMNSTORE
);
GO