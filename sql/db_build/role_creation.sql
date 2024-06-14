-- Create the populationsim_user role when running population sim
CREATE ROLE populationsim_user;

-- Grant INSERT, SELECT permission on a specific SCHEMA
GRANT INSERT, SELECT ON SCHEMA::[metadata] TO populationsim_user;
GRANT INSERT, SELECT ON SCHEMA::[inputs] TO populationsim_user;
GRANT INSERT, SELECT ON SCHEMA::[outputs] TO populationsim_user;

-- Grant UPDATE permission on a specific table
GRANT UPDATE ON [metadata].[run] TO populationsim_user;


