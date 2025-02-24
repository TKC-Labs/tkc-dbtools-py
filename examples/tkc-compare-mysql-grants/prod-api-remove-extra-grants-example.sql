--
-- Apply with something like:
--
-- mysql -h localhost -P 3306 -u root -proot < ./examples/prod-api-remove-extra-grants-example.sql
--
REVOKE SELECT ON example.users FROM 'api'@'192.168.123.10';
REVOKE SELECT ON example.users FROM 'api'@'192.168.123.11';
REVOKE SELECT ON example.users FROM 'api'@'192.168.123.12';
