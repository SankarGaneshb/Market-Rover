SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'investcraft';
DROP DATABASE IF EXISTS "InvestBrand_DB";
DROP DATABASE IF EXISTS "InvestBrand";
ALTER DATABASE investcraft RENAME TO "InvestBrand";
DROP DATABASE IF EXISTS investcraft_test;
CREATE DATABASE "InvestBrand_test";
DROP DATABASE IF EXISTS investcraft_verify;
CREATE DATABASE "InvestBrand_verify";
