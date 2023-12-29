SELECT 
    mgra,
    CASE 
        WHEN [age_group_id] BETWEEN 1 AND 1 THEN 'Age_LT5'
        WHEN [age_group_id] BETWEEN 2 AND 2 THEN 'Age_5to9'
        WHEN [age_group_id] BETWEEN 3 AND 3 THEN 'Age_10to14'
        WHEN [age_group_id] BETWEEN 4 AND 4 THEN 'Age_15to17'
        WHEN [age_group_id] BETWEEN 5 AND 6 THEN 'Age_18to24'
        WHEN [age_group_id] BETWEEN 7 AND 8 THEN 'Age_25to34'
        WHEN [age_group_id] BETWEEN 9 AND 10 THEN 'Age_35to44'
        WHEN [age_group_id] BETWEEN 11 AND 12 THEN 'Age_45to54'
        WHEN [age_group_id] BETWEEN 13 AND 15 THEN 'Age_55to64'
        WHEN [age_group_id] BETWEEN 16 AND 17 THEN 'Age_65to74'
        WHEN [age_group_id] BETWEEN 18 AND 19 THEN 'Age_75to84'
        WHEN [age_group_id] BETWEEN 20 AND 21 THEN 'Age_85Plus'
        ELSE NULL 
    END AS age_group,
    SUM([hhp]) AS 'pop'
FROM [sr15_staging].{staging_table}.[pop_ase_mgra]
WHERE increment = {year}
GROUP BY [increment], 
    mgra,
    CASE 
        WHEN [age_group_id] BETWEEN 1 AND 1 THEN 'Age_LT5'
        WHEN [age_group_id] BETWEEN 2 AND 2 THEN 'Age_5to9'
        WHEN [age_group_id] BETWEEN 3 AND 3 THEN 'Age_10to14'
        WHEN [age_group_id] BETWEEN 4 AND 4 THEN 'Age_15to17'
        WHEN [age_group_id] BETWEEN 5 AND 6 THEN 'Age_18to24'
        WHEN [age_group_id] BETWEEN 7 AND 8 THEN 'Age_25to34'
        WHEN [age_group_id] BETWEEN 9 AND 10 THEN 'Age_35to44'
        WHEN [age_group_id] BETWEEN 11 AND 12 THEN 'Age_45to54'
        WHEN [age_group_id] BETWEEN 13 AND 15 THEN 'Age_55to64'
        WHEN [age_group_id] BETWEEN 16 AND 17 THEN 'Age_65to74'
        WHEN [age_group_id] BETWEEN 18 AND 19 THEN 'Age_75to84'
        WHEN [age_group_id] BETWEEN 20 AND 21 THEN 'Age_85Plus'
        ELSE NULL
    END;