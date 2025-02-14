CREATE USER 'api'@'192.168.123.10' IDENTIFIED BY 'Super-Secure-Password';
CREATE USER 'api'@'192.168.123.11' IDENTIFIED BY 'Super-Secure-Password';
CREATE USER 'api'@'192.168.123.12' IDENTIFIED BY 'Super-Secure-Password';

GRANT SELECT, INSERT ON example.api TO 'api'@'192.168.123.10';
GRANT SELECT, INSERT ON example.api TO 'api'@'192.168.123.11';
GRANT SELECT, INSERT ON example.api TO 'api'@'192.168.123.12';

GRANT SELECT ON example.syskvp TO 'api'@'192.168.123.10';
GRANT SELECT ON example.syskvp TO 'api'@'192.168.123.11';
GRANT SELECT ON example.syskvp TO 'api'@'192.168.123.12';

FLUSH PRIVILEGES;
