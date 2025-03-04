--
-- Apply with something like:
--
-- mysql -h localhost -P 3307 -u root -proot < ./examples/dev-api-grants-chaos-cross-env-example.sql
--
GRANT UPDATE ON example.api TO 'api-dev'@'192.168.122.10';
GRANT UPDATE ON example.api TO 'api-dev'@'192.168.122.11';
GRANT UPDATE ON example.api TO 'api-dev'@'192.168.122.12';

GRANT UPDATE ON example.syskvp TO 'api-dev'@'192.168.122.10';
GRANT UPDATE ON example.syskvp TO 'api-dev'@'192.168.122.11';
GRANT UPDATE ON example.syskvp TO 'api-dev'@'192.168.122.12';
