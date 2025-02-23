--
-- Apply with something like:
--
-- mysql -h localhost -P 3307 -u root -proot < ./examples/dev-api-grants-revoke-for-intra-env-example.sql
--
-- Ensure the grants exist before attempting to revoke them
REVOKE SELECT, INSERT, UPDATE ON `example`.`api` FROM `api-dev`@`192.168.122.11`;

REVOKE SELECT, UPDATE ON `example`.`syskvp` FROM `api-dev`@`192.168.122.11`;
