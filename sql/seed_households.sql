-- Get ACS PUMS seed households
SELECT
    [households].[SERIALNO],
    [PUMA],
    [NP],
    [HINCP],
    -- Adjust HINCP using ADJINC to account for survey month and year
    -- This brings HINCP to last year of survey (2021), then use SD CPI to adjust to 2022
    ROUND([HINCP] * [ADJINC] * .000001 * (1+(344.416 - 319.761)/344.416), 0) AS [HHADJINC],
    [HHT],
    [workers],
    [HUPAC],
    [VEH],
    [BLD],
    [TYPEHUGQ],
    CASE WHEN [TYPEHUGQ] = 1 THEN 0  -- housing unit
         WHEN [TYPEHUGQ] = 3 AND [MIL] = 1 THEN 1  -- military gq
         WHEN [TYPEHUGQ] = 3 AND [SCHG] IN (15,16) THEN 2  -- college gq
		 WHEN [TYPEHUGQ] IN (2,3) THEN 3  -- other gq
		 END AS [gq_type],
    CASE WHEN [TYPEHUGQ] = 1 THEN [WGTP]
         WHEN [TYPEHUGQ] IN (2,3) THEN [PWGTP]
         END AS [WGTP]
FROM
    [acs].[pums].[5y_2017_2021_households] AS [households]
    INNER JOIN (
	SELECT
        [SERIALNO],
        SUM(CASE WHEN [ESR] IN (1,2,4,5) THEN 1 ELSE 0 END) AS [workers],
        -- use only for GQs (1 person)
        MAX([MIL]) AS [MIL],
        MAX([SCHG]) AS [SCHG],
        MAX([PWGTP]) AS [PWGTP]
    FROM
        [acs].[pums].[5y_2017_2021_persons]
    GROUP BY
		[SERIALNO]
) AS [hh_workers]
    ON
	[households].[SERIALNO] = [hh_workers].[SERIALNO]
WHERE
	[NP] > 0 -- remove vacant households
    -- Note the 2017-2021 ACS PUMS uses 2010 PUMAS
    AND [households].[ST] = '06' AND [households].[PUMA] IN  (
	'07301', '07302','07303','07304', '07305','07306',
	'07307','07308','07309','07310','07311','07312',
	'07313','07314','07315','07316','07317','07318',
	'07319','07320','07321','07322')
ORDER BY
	[households].[SERIALNO]