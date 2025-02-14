CREATE USER 'usermgr'@'192.168.123.16' IDENTIFIED BY 'Super-Secure-Password';
CREATE USER 'usermgr'@'192.168.123.17' IDENTIFIED BY 'Super-Secure-Password';
CREATE USER 'usermgr'@'192.168.123.18' IDENTIFIED BY 'Super-Secure-Password';

GRANT SELECT, UPDATE ON example.api TO 'usermgr'@'192.168.123.16';
GRANT SELECT, UPDATE ON example.api TO 'usermgr'@'192.168.123.17';
GRANT SELECT, UPDATE ON example.api TO 'usermgr'@'192.168.123.18';

GRANT SELECT ON example.syskvp TO 'usermgr'@'192.168.123.16';
GRANT SELECT ON example.syskvp TO 'usermgr'@'192.168.123.17';
GRANT SELECT ON example.syskvp TO 'usermgr'@'192.168.123.18';

GRANT ALL PRIVILEGES ON example.users TO 'usermgr'@'192.168.123.16';
GRANT ALL PRIVILEGES ON example.users TO 'usermgr'@'192.168.123.17';
GRANT ALL PRIVILEGES ON example.users TO 'usermgr'@'192.168.123.18';

FLUSH PRIVILEGES;
