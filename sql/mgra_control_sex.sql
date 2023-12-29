SELECT
      [mgra]
      ,[sex].sex
      ,SUM([hhp]) AS pop
  FROM [sr15_staging].{staging_table}.[pop_ase_mgra]
  LEFT JOIN [demographic_warehouse].[dim].[sex]
  ON [pop_ase_mgra].sex_id = [sex].sex_id
  WHERE increment = {year}
  GROUP BY [mgra], [sex].sex