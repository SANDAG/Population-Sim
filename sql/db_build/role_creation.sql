-- Create the populationsim_user role when running population sim
CREATE ROLE populationsim_user;

GRANT INSERT, SELECT TO populationsim_user;
GO