-- Get ACS PUMS seed persons
SELECT
    [persons].[SERIALNO],
    [SPORDER],
    [persons].[PUMA],
    [AGEP],
    [SEX],
    [ESR],
    CASE WHEN [ESR] IN (1,2,3,4,5) THEN 1 ELSE 0 END AS [laborforce],
    CASE WHEN [ESR] IN (1,2,4,5) THEN 1 ELSE 0 END AS [worker],
    [COW],
    [WKHP],
    CASE WHEN [SCHG] IS NULL THEN 0 ELSE [SCHG] END AS [SCHG],
    [HISP],
    [RAC1P],
    CASE WHEN [HISP] != '01' THEN 'Hispanic' -- Hispanic takes precendence over Race
         WHEN [RAC1P] = '1' THEN 'White alone'
         WHEN [RAC1P] = '2' THEN 'Black or African American alone'
         WHEN [RAC1P] = '6' THEN 'Asian alone'
         WHEN [RAC1P] = '9' THEN 'Two or More Races'
         -- Other Control is AIAN, NHPI, and Other
         WHEN [RAC1P] IN ('3','4','5', '7', '8') THEN 'Other'
         ELSE NULL END AS [race],
    [MIL],
    [SCHL],
    [OCCP],
    [WKW],
    [NAICSP],
    CASE WHEN LEFT([NAICSP], 4) = '9281' THEN 'MIL'
         WHEN LEFT([NAICSP], 2) = '72' THEN LEFT([NAICSP], 3)
         ELSE LEFT([NAICSP], 2) END AS [NAICS2],
    [SOCP],
    LEFT([SOCP], 2) AS [SOC2],
    [TYPEHUGQ],
    CASE WHEN [TYPEHUGQ] = 1 THEN 0  -- housing unit
         WHEN [TYPEHUGQ] = 3 AND [MIL] = 1 THEN 1  -- military gq
         WHEN [TYPEHUGQ] = 3 AND [SCHG] IN (15,16) THEN 2  -- college gq
		 WHEN [TYPEHUGQ] IN (2,3) THEN 3  -- other gq
		 END AS [gq_type],
    [PINCP]
FROM
    [acs].[pums].[5y_2017_2021_persons] AS [persons]
    INNER JOIN
    [acs].[pums].[5y_2017_2021_households] AS [households]
    ON
	[persons].[SERIALNO] = [households].[SERIALNO]
WHERE
	[NP] > 0 -- remove vacant households (not necessary for persons but here for documentation)
    -- Note the 2017-2021 ACS PUMS uses 2010 PUMAS
    AND [persons].[ST] = '06' AND [persons].[PUMA] IN  (
	SELECT DISTINCT(PUMA) FROM [acs].[pums].[vi_5y_2017_2021_persons_sd])
ORDER BY
    [persons].[SERIALNO],
    [SPORDER]