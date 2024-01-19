with
    [ase_controls]
    AS
    (
        SELECT
            [mgra],
            SUM(CASE WHEN [sex_id] = 2 THEN [hhp] ELSE 0 END) AS 'Male',
            SUM(CASE WHEN [sex_id] = 1 THEN [hhp] ELSE 0 END) AS 'Female',
            SUM(CASE WHEN [age_group_id] = 1 THEN [hhp] ELSE 0 END) AS 'Age_LT5',
            SUM(CASE WHEN [age_group_id] = 2 THEN [hhp] ELSE 0 END) AS 'Age_5to9',
            SUM(CASE WHEN [age_group_id] = 3 THEN [hhp] ELSE 0 END) AS 'Age_10to14',
            SUM(CASE WHEN [age_group_id] = 4 THEN [hhp] ELSE 0 END) AS 'Age_15to17',
            SUM(CASE WHEN [age_group_id] BETWEEN 5 AND 6 THEN [hhp] ELSE 0 END) AS 'Age_18to24',
            SUM(CASE WHEN [age_group_id] BETWEEN 7 AND 8 THEN [hhp] ELSE 0 END) AS 'Age_25to34',
            SUM(CASE WHEN [age_group_id] BETWEEN 9 AND 10 THEN [hhp] ELSE 0 END) AS 'Age_35to44',
            SUM(CASE WHEN [age_group_id] BETWEEN 11 AND 12 THEN [hhp] ELSE 0 END) AS 'Age_45to54',
            SUM(CASE WHEN [age_group_id] BETWEEN 13 AND 15 THEN [hhp] ELSE 0 END) AS 'Age_55to64',
            SUM(CASE WHEN [age_group_id] BETWEEN 16 AND 17 THEN [hhp] ELSE 0 END) AS 'Age_65to74',
            SUM(CASE WHEN [age_group_id] BETWEEN 18 AND 19 THEN [hhp] ELSE 0 END) AS 'Age_75to84',
            SUM(CASE WHEN [age_group_id] BETWEEN 20 AND 21 THEN [hhp] ELSE 0 END) AS 'Age_85Plus',
            SUM(CASE WHEN [ethnicity_id] = 5 THEN [hhp] ELSE 0 END) AS 'Asian',
            SUM(CASE WHEN [ethnicity_id] = 3 THEN [hhp] ELSE 0 END) AS 'Black',
            SUM(CASE WHEN [ethnicity_id] = 1 THEN [hhp] ELSE 0 END) AS 'Hispanic',
            -- Other Control is AIAN, NHPI, and Other
            SUM(CASE WHEN [ethnicity_id] IN (4,6,7) THEN [hhp] ELSE 0 END) AS 'Other',
            SUM(CASE WHEN [ethnicity_id] = 8 THEN [hhp] ELSE 0 END) AS 'Two_or_more',
            SUM(CASE WHEN [ethnicity_id] = 2 THEN [hhp] ELSE 0 END) AS 'White'
        FROM
            [sr15_staging].{staging_schema}.[pop_ase_mgra]
	WHERE
		[increment] = {year}
	GROUP BY
		[mgra]
),
[hh_controls] AS
(
	SELECT
    [mgra],
    SUM([hhs1]) AS [HHSize_1],
    SUM([hhs2]) AS [HHSize_2],
    SUM([hhs3]) AS [HHSize_3],
    SUM([hhs4]) + SUM([hhs5]) + SUM([hhs6]) + SUM([hhs7]) AS [HHSize_4Plus],
    SUM([hhs1]) + SUM([hhs2]) + SUM([hhs3]) + SUM([hhs4]) + SUM([hhs5]) + SUM([hhs6]) + SUM([hhs7]) AS [Total_HH],
    SUM([hhworkers0]) AS [HHWork_0],
    SUM([hhworkers1]) AS [HHWork_1],
    SUM([hhworkers2]) AS [HHWork_2],
    SUM([hhworkers3]) AS [HHWork_3Plus],
    SUM([hhwoc]) AS [HHChild_0],
    SUM([hhwc]) AS [HHChild_1Plus]
FROM
    [sr15_staging].{staging_schema}.[hh_characteristics_mgra]
	WHERE
		[increment] = {year}
	GROUP BY
		[mgra]
),
[mgrabase_controls] AS
(
	SELECT
    [mgra],
    [i1] AS [HHInc_0to14999],
    [i2] AS [HHInc_15000to29999],
    [i3] + i4 AS [HHInc_30000to59999],
    [i5] + [i6] AS [HHInc_60000to99999],
    [i7] + [i8] AS [HHInc_100000to149999],
    [i9] AS [HHInc_150000to199999],
    [i10] AS [HHInc_200000Plus],
    [gq_civ_college] AS [gq_college_pop],
    [gq_mil] AS [gq_mil_pop],
    [gq_civ_other] AS [gq_other_pop]
FROM
    [sr15_staging].{staging_schema}.[mgrabase]
	WHERE
		[increment] = {year}
)
SELECT
    [ase_controls].[mgra],
    [Male],
    [Female],
    [Age_LT5],
    [Age_5to9],
    [Age_10to14],
    [Age_15to17],
    [Age_18to24],
    [Age_25to34],
    [Age_35to44],
    [Age_45to54],
    [Age_55to64],
    [Age_65to74],
    [Age_75to84],
    [Age_85Plus],
    [Asian],
    [Black],
    [Hispanic],
    [Other],
    [Two_or_more],
    [White],
    [HHSize_1],
    [HHSize_2],
    [HHSize_3],
    [HHSize_4Plus],
    [HHWork_0],
    [HHWork_1],
    [HHWork_2],
    [HHWork_3Plus],
    [HHChild_0],
    [HHChild_1Plus],
    [HHInc_0to14999],
    [HHInc_15000to29999],
    [HHInc_30000to59999],
    [HHInc_60000to99999],
    [HHInc_100000to149999],
    [HHInc_150000to199999],
    [HHInc_200000Plus],
    [Total_HH],
    [gq_college_pop],
    [gq_mil_pop],
    [gq_other_pop],
    [Total_HH] + [gq_college_pop] + [gq_mil_pop] + [gq_other_pop] AS [Total_HH_GQ]
FROM
    [ase_controls]
    INNER JOIN
    [hh_controls]
    ON
	[ase_controls].[mgra] = [hh_controls].[mgra]
    INNER JOIN
    [mgrabase_controls]
    ON
	[ase_controls].[mgra] = [mgrabase_controls].[mgra]
ORDER BY
	[mgra]