-- Get ACS PUMS seed households
SELECT
    [households].[SERIALNO],
    [PUMA],
    [NP],
    [HINCP],
    -- Adjust HINCP using the San Diego Region CPI based on survey year to 2022 dollars
    -- https://fred.stlouisfed.org/series/CUUSA424SA0
    ROUND(
        CASE 
            WHEN [TYPEHUGQ] IN (2,3) THEN
                CASE WHEN LEFT([households].[SERIALNO], 4) = '2017' THEN [PINCP] * 344.416/283.012
                     WHEN LEFT([households].[SERIALNO], 4) = '2018' THEN [PINCP] * 344.416/292.547
                     WHEN LEFT([households].[SERIALNO], 4) = '2019' THEN [PINCP] * 344.416/299.433
                     WHEN LEFT([households].[SERIALNO], 4) = '2020' THEN [PINCP] * 344.416/303.932
                     WHEN LEFT([households].[SERIALNO], 4) = '2021' THEN [PINCP] * 344.416/319.761
                     ELSE 'error' 
                END
            ELSE
                CASE WHEN LEFT([households].[SERIALNO], 4) = '2017' THEN [HINCP] * 344.416/283.012
                     WHEN LEFT([households].[SERIALNO], 4) = '2018' THEN [HINCP] * 344.416/292.547
                     WHEN LEFT([households].[SERIALNO], 4) = '2019' THEN [HINCP] * 344.416/299.433
                     WHEN LEFT([households].[SERIALNO], 4) = '2020' THEN [HINCP] * 344.416/303.932
                     WHEN LEFT([households].[SERIALNO], 4) = '2021' THEN [HINCP] * 344.416/319.761
                     ELSE 'error'
                END
        END, 0) AS [HHADJINC],
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
        MAX([PWGTP]) AS [PWGTP],
		MAX([PINCP]) AS [PINCP]
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
	SELECT DISTINCT(PUMA) FROM [acs].[pums].[vi_5y_2017_2021_households_sd])
ORDER BY
	[households].[SERIALNO]
