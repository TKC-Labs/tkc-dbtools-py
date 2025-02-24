--
-- Apply with something like:
--
-- mysql -h localhost -P 3306 -u root -proot < ./examples/prod-api-add-extra-grants-example.sql
--
GRANT SELECT ON example.users TO 'api'@'192.168.123.10';
GRANT SELECT ON example.users TO 'api'@'192.168.123.11';
GRANT SELECT ON example.users TO 'api'@'192.168.123.12';
