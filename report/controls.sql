SELECT
    [controls].[control_id] AS [id],
    CASE WHEN [controls].[control_field] = 'Total_HH' THEN 'Households'
         WHEN [controls].[control_field] LIKE 'HHSize_%' THEN 'Household Size'
         WHEN [controls].[control_field] LIKE 'HHInc_%' THEN 'Household Income'
         WHEN [controls].[control_field] LIKE 'HHWork__%' THEN 'Household Workers'
         WHEN [controls].[control_field] LIKE 'HHChild__%' THEN 'Household Children'
         WHEN [controls].[control_field] IN ('Male', 'Female') THEN 'Sex'
         WHEN [controls].[control_field] LIKE 'Age_%' THEN 'Age'
         WHEN [controls].[control_field] IN ('Asian', 'Black', 'Hispanic', 'Other', 'Two_or_more', 'White') THEN 'Race/Ethnicity'
         WHEN [controls].[control_field] LIKE 'job_%' THEN 'Labor Force'
         WHEN [controls].[control_field] LIKE 'lfp_%' THEN 'Civilian Labor Force'
         WHEN [controls].[control_field] LIKE 'gq__%' THEN 'Group Quarters'
         ELSE NULL END AS [Category],
    [controls].[control_field] AS [Control Field],
    [control_totals].[geography],
    [control_totals].[geography_id],
    SUM([control_value]) AS [Control],
    SUM([result]) AS [Result],
    SUM([result]) - SUM([control_value]) AS [Diff],
    CASE WHEN SUM([result]) = SUM([control_value]) THEN 0
         WHEN SUM([control_value]) = 0 THEN NULL
         ELSE CONVERT(DECIMAL(6,2), ROUND(100.0 * (SUM([result]) - SUM([control_value])) / SUM([control_value]), 2))
         END AS [Diff %]
FROM [outputs].[control_totals]
    LEFT JOIN [inputs].[controls]
    ON [control_totals].[run_id] = [controls].[run_id] AND [control_totals].[control_id] = [controls].control_id
WHERE
    [control_totals].[run_id] = {run_id}
GROUP BY
    [controls].[control_id],
    [controls].[control_field],
    [control_totals].[geography],
    [control_totals].[geography_id]
ORDER BY
    [controls].[control_id],
    [controls].[control_field],
    [control_totals].[geography],
    [control_totals].[geography_id]