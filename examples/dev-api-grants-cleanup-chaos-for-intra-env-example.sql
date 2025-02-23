--
-- Apply with something like:
--
-- mysql -h localhost -P 3307 -u root -proot < ./examples/dev-api-grants-cleanup-chaos-for-intra-env-example.sql
--
REVOKE UPDATE ON example.api FROM 'api-dev'@'192.168.122.11';

REVOKE UPDATE ON example.syskvp FROM 'api-dev'@'192.168.122.11';
