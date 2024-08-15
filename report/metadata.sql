SELECT
    [run_id]
    , [year]
    , [user]
    , [date]
    , [version]
    , [staging_schema]
    , [comments]
    , [loaded]
FROM [metadata].[run]
WHERE run_id = {run_id}