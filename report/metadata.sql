SELECT
    [run_id]
    , [staging_schema]
    , [year]
    , [date]
    , [user]
    , [version]
    , [comments]
FROM [metadata].[run]
WHERE [loaded] = 1