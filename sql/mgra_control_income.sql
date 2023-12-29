SELECT
      [mgra]
      ,[i1] AS HHInc_0to14999
      ,[i2] AS HHInc_15000to29999
      ,[i3] + i4 AS HHInc_30000to59999
      ,[i5] + [i6] AS HHInc_60000to99999
      ,[i7] + [i8] AS HHInc_100000to149999
      ,[i9] AS HHInc_150000to199999
      ,[i10] AS HHInc_200000Plus
	  ,[gq_civ_college] AS gq_college_pop
	  ,[gq_mil] AS gq_mil_pop
	  ,[gq_civ_other] AS gq_other_pop
  FROM [sr15_staging].{staging_table}.[mgrabase]
  WHERE increment = {year}