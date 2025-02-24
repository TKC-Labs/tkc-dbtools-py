CREATE USER IF NOT EXISTS 'syskvp-stage'@'192.168.124.13' IDENTIFIED BY 'Super-Secure-Password';
CREATE USER IF NOT EXISTS 'syskvp-stage'@'192.168.124.14' IDENTIFIED BY 'Super-Secure-Password';
CREATE USER IF NOT EXISTS 'syskvp-stage'@'192.168.124.15' IDENTIFIED BY 'Super-Secure-Password';

GRANT SELECT, UPDATE, DELETE ON example.syskvp TO 'syskvp-stage'@'192.168.124.13';
GRANT SELECT, UPDATE, DELETE ON example.syskvp TO 'syskvp-stage'@'192.168.124.14';
GRANT SELECT, UPDATE, DELETE ON example.syskvp TO 'syskvp-stage'@'192.168.124.15';
