SELECT
	  mgra
      ,SUM([hhs1]) AS HHSize_1
      ,SUM([hhs2]) AS HHSize_2
	  , SUM([hhs3]) AS HHSize_3
	  ,SUM([hhs4]) + SUM([hhs5]) + SUM([hhs6]) + SUM([hhs7]) AS HHSize_4Plus
	  ,SUM([hhs1]) + SUM([hhs2]) + SUM([hhs3]) + SUM([hhs4]) + SUM([hhs5]) + SUM([hhs6]) + SUM([hhs7]) AS Total_HH
      ,SUM([hhworkers0]) AS HHWork_0
      ,SUM([hhworkers1]) AS HHWork_1
      ,SUM([hhworkers2]) AS HHWork_2
      ,SUM([hhworkers3]) AS HHWork_3Plus
	  ,SUM([hhwoc]) AS HHChild_0
	,SUM([hhwc]) AS HHChild_1Plus
  FROM [sr15_staging].{staging_table}.[hh_characteristics_mgra]
  WHERE increment = {year}
  GROUP BY mgra