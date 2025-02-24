CREATE USER IF NOT EXISTS 'syskvp-dev'@'192.168.122.13' IDENTIFIED BY 'Super-Secure-Password';
CREATE USER IF NOT EXISTS 'syskvp-dev'@'192.168.122.14' IDENTIFIED BY 'Super-Secure-Password';
CREATE USER IF NOT EXISTS 'syskvp-dev'@'192.168.122.15' IDENTIFIED BY 'Super-Secure-Password';

GRANT SELECT, UPDATE, DELETE ON example.syskvp TO 'syskvp-dev'@'192.168.122.13';
GRANT SELECT, UPDATE, DELETE ON example.syskvp TO 'syskvp-dev'@'192.168.122.14';
GRANT SELECT, UPDATE, DELETE ON example.syskvp TO 'syskvp-dev'@'192.168.122.15';

FLUSH PRIVILEGES;
