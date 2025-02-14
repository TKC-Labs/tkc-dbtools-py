CREATE USER 'api-dev'@'192.168.122.10' IDENTIFIED BY 'Super-Secure-Password';
CREATE USER 'api-dev'@'192.168.122.11' IDENTIFIED BY 'Super-Secure-Password';
CREATE USER 'api-dev'@'192.168.122.12' IDENTIFIED BY 'Super-Secure-Password';

GRANT SELECT, INSERT ON example.api TO 'api-dev'@'192.168.122.10';
GRANT SELECT, INSERT ON example.api TO 'api-dev'@'192.168.122.11';
GRANT SELECT, INSERT ON example.api TO 'api-dev'@'192.168.122.12';

GRANT SELECT ON example.syskvp TO 'api-dev'@'192.168.122.10';
GRANT SELECT ON example.syskvp TO 'api-dev'@'192.168.122.11';
GRANT SELECT ON example.syskvp TO 'api-dev'@'192.168.122.12';

FLUSH PRIVILEGES;
