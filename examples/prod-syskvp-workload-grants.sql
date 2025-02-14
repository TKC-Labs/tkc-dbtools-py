CREATE USER 'syskvp'@'192.168.123.13' IDENTIFIED BY 'Super-Secure-Password';
CREATE USER 'syskvp'@'192.168.123.14' IDENTIFIED BY 'Super-Secure-Password';
CREATE USER 'syskvp'@'192.168.123.15' IDENTIFIED BY 'Super-Secure-Password';

GRANT SELECT, UPDATE, DELETE ON example.syskvp TO 'syskvp'@'192.168.123.13';
GRANT SELECT, UPDATE, DELETE ON example.syskvp TO 'syskvp'@'192.168.123.14';
GRANT SELECT, UPDATE, DELETE ON example.syskvp TO 'syskvp'@'192.168.123.15';

FLUSH PRIVILEGES;
