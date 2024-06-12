-- Create the populationsim_user role when running the popualtion 
USE [PopulationSim_v1]
GO

CREATE ROLE populationsim_user;

GRANT ALL TO populationsim_user;
GO