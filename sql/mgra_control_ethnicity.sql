SELECT
      [mgra]
      ,[ethnicity].long_name
      ,SUM([hhp]) AS hhp
  FROM [sr15_staging].{staging_table}.[pop_ase_mgra]
  LEFT JOIN [demographic_warehouse].[dim].[ethnicity]
  ON [pop_ase_mgra].ethnicity_id = [ethnicity].ethnicity_id
  WHERE increment = {year}
  GROUP BY mgra, [ethnicity].long_name