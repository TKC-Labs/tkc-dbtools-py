"""
Functions to compare MySQL user grants between multiple MySQL servers.
"""

import logging
import pymysql
import yaml
from typing import Dict, List, Any

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _compare_grants(
    workload: Dict[str, List[Dict[str, List[str]]]],
    db_connections: Dict[str, pymysql.Connection],
) -> None:
    """Compare MySQL user grants for a specific workload."""
    logger.info(f"Comparing grants for workload: {workload}")
    for env, users in workload.items():
        for user in users:
            user_name, hosts = user["user"], user["hosts"]
            for host in hosts:
                grants = _get_grants(db_connections[env], user_name, host)
                logger.info(f"Grants for {user_name}@{host} in {env}: {grants}")


def _get_grants(conn, user, host):
    """Get the grants for a specific user and host."""
    with conn.cursor() as cursor:
        query = "SHOW GRANTS FOR %s@%s"
        cursor.execute(query, (user, host))
        grants = [row[0] for row in cursor.fetchall()]
    return sorted(grants)


def _connect_to_db(database: Dict[str, Any]) -> pymysql.Connection:
    """Connect to the MySQL database."""
    return pymysql.connect(
        host=database["host"],
        port=database["port"],
        user=database["user"],
        password=database["password"],
        database="mysql",
    )


def _read_config(config_file="compare-mysql-grants.yml") -> Dict[str, Any]:
    """Read the configuration file."""
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    if config is None:
        raise ValueError("Failed to parse configuration file.")
    return config


def _validate_config(config: Dict[str, Any]) -> None:
    """Validate the configuration values read from configuration file."""

    # First make sure we have all of the top level sections we expect
    if not config.get("databases"):
        raise AttributeError("Databases not found in configuration file.")
    if not config.get("workloads"):
        raise AttributeError("Workloads not found in configuration file.")

    # Next, we need to validate the databases configuration
    databases_config = config.get("databases")

    # We need at exactly one database set as the "leader" which is considered
    # the source of truth We'll add any databases that have leader: true set
    # to this list and if the list is > 1, we raise an error
    leaders = []

    # We need to validate that each workload has a user and host set for each
    # environment so we create a list of envs
    envs = []

    for database, config_values in databases_config.items():
        logger.info(f"Validating database configuration for {database}")
        required_keys = ["host", "port", "user", "password"]
        missing_keys = [key for key in required_keys if key not in config_values.keys()]
        if missing_keys:
            raise AttributeError(
                f"Database configuration for {database} is incomplete. Missing keys: {', '.join(missing_keys)}"
            )

        # We have all our required keys, so we can add the env to the list of
        # envs for further validation
        envs.append(database)

        if config_values.get("leader", False):
            logger.info(f"Database {database} is set as leader.")
            leaders.append(database)

    if len(leaders) != 1:
        raise AttributeError(
            f"Exactly one database must be set as the leader. Found {len(leaders)} databases set as leader."
        )

    # Then we need to validate the workloads configuration
    workloads_config = config.get("workloads")
    logger.info(
        f"Validating workload configurations for workloads: {', '.join(workloads_config.keys())}"
    )

    for workload, workload_envs in workloads_config.items():
        logger.info(f"Validating workload configuration for {workload}")

        # Check workload for required envs
        missing_envs = [env for env in envs if env not in workload_envs.keys()]
        if missing_envs:
            raise AttributeError(
                f"Workload configuration for {workload} is incomplete. Missing environments: {', '.join(missing_envs)}"
            )

        # Check workload environments for required user keys
        for env, users in workload_envs.items():
            required_keys = ["user", "hosts"]
            for user in users:
                missing_keys = [key for key in required_keys if key not in user.keys()]
                if missing_keys:
                    raise AttributeError(
                        f"User configuration for {workload} in {env} is incomplete. Missing keys: {', '.join(missing_keys)}"
                    )
                # We have our required keys, are they the expected types?
                if not isinstance(user["user"], str):
                    raise AttributeError(
                        f"User key 'user' for {workload} in {env} must be a string."
                    )
                if not isinstance(user["hosts"], list):
                    raise AttributeError(
                        f"User key 'hosts' for {workload} in {env} must be a list."
                    )


def run() -> int:
    """
    Compare MySQL user grants between multiple MySQL servers.
    """
    logger.info("Comparing MySQL user grants")

    # Reading configuration file
    try:
        config = _read_config()
    except FileNotFoundError as e:
        logger.error(f"No configuration file found. ({e})")
        return 1
    except ValueError as e:
        logger.error(f"Failed to parse configuration file. ({e})")
        return 1

    # Configuration data Validation
    try:
        _validate_config(config)
        logger.info("Configuration file appears valid.")
    except AttributeError as e:
        logger.error(f"Configuration file validation failed: {e}")
        return 1

    # Connect to the databases
    db_connections = {}
    for database in config.get("databases"):
        try:
            db_connections[database] = _connect_to_db(config.get("databases")[database])
        except pymysql.err.OperationalError as e:
            logger.error(f"Failed to connect to database: {database} ({e})")
            return 1

        try:
            db_connections[database].ping()
        except pymysql.MySQLError as e:
            logger.error(f"Database: {database} not responding: ({e})")
            return 1

    if len(db_connections.keys()) == len(config.get("databases").keys()):
        logger.info("All databases connected successfully.")

    # For each workload we need to compare the grants within each environment
    # first. If the grants across users in the same environment match, we can
    # use any user for cross environment comparison. If the grants do not match
    # we need to report that so it can be resolved before comparing across
    # environments.
    for workload_name, workload in config.get("workloads").items():
        logger.info(f"Comparing MySQL user grants for workload: {workload_name}")
        print(f"{workload}")
        _compare_grants(workload, db_connections)

    # try:
    #     for workload, users in config.get("workloads").items():

    #         # INFO:tkc_dbtools.mysql.compare_grants:Comparing MySQL user grants...
    #         # Workload: api has users: {'dev': [{'user': 'api-dev', 'hosts': ['192.168.122.10', '192.168.122.11', '192.168.122.12']}], 'prod': [{'user': 'api', 'hosts': ['192.168.123.10', '192.168.123.11', '192.168.123.12']}]}
    #         # Workload: syskvp has users: {'dev': [{'user': 'syskvp-dev', 'hosts': ['192.168.122.13', '192.168.122.14', '192.168.122.15']}], 'prod': [{'user': 'syskvp', 'hosts': ['192.168.123.13', '192.168.123.14', '192.168.123.15']}]}
    #         # Workload: users has users: {'dev': [{'user': 'usermgr-dev', 'hosts': ['192.168.122.16', '192.168.122.17', '192.168.122.18']}], 'prod': [{'user': 'usermgr', 'hosts': ['192.168.123.16', '192.168.123.17', '192.168.123.18']}]}
    #         # INFO:tkc_dbtools.mysql.compare_grants:Finished comparing MySQL user grants.

    #         print(f"Workload: {workload} has users: {users}")
    #         # dev_user, dev_host = users["dev"]["user"], users["dev"]["host"]
    #         # prod_user, prod_host = users["prod"]["user"], users["prod"]["host"]

    #         # dev_grants = get_grants(dev_conn, dev_user, dev_host)
    #         # prod_grants = get_grants(prod_conn, prod_user, prod_host)

    #         # compare_grants(dev_grants, prod_grants, workload)
    # except AttributeError as e:
    #     logger.error(
    #         f"Invalid configuration file, check workload and user configuration. ({e})"
    #     )
    #     return 1
    # finally:

    # Close the database connections
    for conn_name, conn in db_connections.items():
        logger.info(f"Closing connection to database: {conn_name}")
        conn.close()

    logger.info("Finished comparing MySQL user grants.")

    return 0
