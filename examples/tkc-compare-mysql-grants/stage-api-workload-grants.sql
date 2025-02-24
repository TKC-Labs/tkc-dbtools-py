CREATE USER IF NOT EXISTS 'api-stage'@'192.168.124.10' IDENTIFIED BY 'Super-Secure-Password';
CREATE USER IF NOT EXISTS  'api-stage'@'192.168.124.11' IDENTIFIED BY 'Super-Secure-Password';
CREATE USER IF NOT EXISTS  'api-stage'@'192.168.124.12' IDENTIFIED BY 'Super-Secure-Password';

GRANT SELECT, INSERT ON example.api TO 'api-stage'@'192.168.124.10';
GRANT SELECT, INSERT ON example.api TO 'api-stage'@'192.168.124.11';
GRANT SELECT, INSERT ON example.api TO 'api-stage'@'192.168.124.12';

GRANT SELECT ON example.syskvp TO 'api-stage'@'192.168.124.10';
GRANT SELECT ON example.syskvp TO 'api-stage'@'192.168.124.11';
GRANT SELECT ON example.syskvp TO 'api-stage'@'192.168.124.12';
