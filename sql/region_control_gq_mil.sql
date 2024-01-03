SELECT sum(gq_mil) 
FROM [sr15_staging].{staging_table}.[mgrabase]
WHERE increment = {year}