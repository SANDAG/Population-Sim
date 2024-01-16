SELECT 1 AS [region], SUM([gq_mil]) AS [gq_mil]
FROM [sr15_staging].{staging_schema}.[mgrabase]
WHERE increment = {year}