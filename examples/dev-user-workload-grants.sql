CREATE USER IF NOT EXISTS 'usermgr-dev'@'192.168.122.16' IDENTIFIED BY 'Super-Secure-Password';
CREATE USER IF NOT EXISTS 'usermgr-dev'@'192.168.122.17' IDENTIFIED BY 'Super-Secure-Password';
CREATE USER IF NOT EXISTS 'usermgr-dev'@'192.168.122.18' IDENTIFIED BY 'Super-Secure-Password';

GRANT SELECT, UPDATE ON example.api TO 'usermgr-dev'@'192.168.122.16';
GRANT SELECT, UPDATE ON example.api TO 'usermgr-dev'@'192.168.122.17';
GRANT SELECT, UPDATE ON example.api TO 'usermgr-dev'@'192.168.122.18';

GRANT SELECT ON example.syskvp TO 'usermgr-dev'@'192.168.122.16';
GRANT SELECT ON example.syskvp TO 'usermgr-dev'@'192.168.122.17';
GRANT SELECT ON example.syskvp TO 'usermgr-dev'@'192.168.122.18';

GRANT ALL PRIVILEGES ON example.users TO 'usermgr-dev'@'192.168.122.16';
GRANT ALL PRIVILEGES ON example.users TO 'usermgr-dev'@'192.168.122.17';
GRANT ALL PRIVILEGES ON example.users TO 'usermgr-dev'@'192.168.122.18';

FLUSH PRIVILEGES;
