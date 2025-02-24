CREATE USER IF NOT EXISTS 'usermgr-stage'@'192.168.124.16' IDENTIFIED BY 'Super-Secure-Password';
CREATE USER IF NOT EXISTS 'usermgr-stage'@'192.168.124.17' IDENTIFIED BY 'Super-Secure-Password';
CREATE USER IF NOT EXISTS 'usermgr-stage'@'192.168.124.18' IDENTIFIED BY 'Super-Secure-Password';

GRANT SELECT, UPDATE ON example.api TO 'usermgr-stage'@'192.168.124.16';
GRANT SELECT, UPDATE ON example.api TO 'usermgr-stage'@'192.168.124.17';
GRANT SELECT, UPDATE ON example.api TO 'usermgr-stage'@'192.168.124.18';

GRANT SELECT ON example.syskvp TO 'usermgr-stage'@'192.168.124.16';
GRANT SELECT ON example.syskvp TO 'usermgr-stage'@'192.168.124.17';
GRANT SELECT ON example.syskvp TO 'usermgr-stage'@'192.168.124.18';

GRANT ALL PRIVILEGES ON example.users TO 'usermgr-stage'@'192.168.124.16';
GRANT ALL PRIVILEGES ON example.users TO 'usermgr-stage'@'192.168.124.17';
GRANT ALL PRIVILEGES ON example.users TO 'usermgr-stage'@'192.168.124.18';
