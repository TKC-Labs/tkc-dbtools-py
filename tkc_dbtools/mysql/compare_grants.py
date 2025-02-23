"""
Functions to compare MySQL user grants between multiple MySQL servers.
"""

import logging
import pprint
import pymysql
import re
import yaml
from typing import Dict, List, Set, Any

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _compare_user_grants(
    user_grants: List[str], anchor_user_grants: List[str]
) -> Set[str]:
    """Compare the grants of two users."""
    # Strip the IP address from the grants so we can compare them
    stripped_user_grants = [_strip_ip_from_grant(grant) for grant in user_grants]
    stripped_anchor_user_grants = [
        _strip_ip_from_grant(grant) for grant in anchor_user_grants
    ]

    sorted_user_grants = sorted(stripped_user_grants)
    sorted_anchor_user_grants = sorted(stripped_anchor_user_grants)

    logger.debug(f"Anchor User grants: {sorted_anchor_user_grants}")
    logger.debug(f"User grants: {sorted_user_grants}")

    missing_from_anchor_user_grants = set(sorted_anchor_user_grants) - set(
        sorted_user_grants
    )
    missing_from_user_grants = set(sorted_user_grants) - set(sorted_anchor_user_grants)

    logger.debug(f"Missing from anchor user: {missing_from_anchor_user_grants}")
    logger.debug(f"Missing from user: {missing_from_user_grants}")

    grant_diffs = {
        "missing_from_user": missing_from_user_grants,
        "missing_from_anchor_user": missing_from_anchor_user_grants,
    }

    return grant_diffs


def _compare_workload_grants(workload: Dict[str, Dict[str, List[str]]]) -> bool:
    """Compare grants in a workload"""
    # dict to store the diffs for each user in the workload
    workload_grant_diffs = {}

    for env, users in workload.items():
        logger.debug(f"Comparing grants for environment: {env}")
        workload_grant_diffs[env] = {}

        # Get a list of users
        user_list = list(users.keys())
        # Select anchor user
        anchor_user = user_list[0]

        # Compare each user to th eothers
        for i in range(1, len(user_list)):
            user = user_list[i]
            logger.debug(f"Comparing grants between users: {anchor_user} and {user}")
            workload_grant_diffs[env][user] = {}
            workload_grant_diffs[env][user]["anchor_user"] = anchor_user
            workload_grant_diffs[env][user]["diffs"] = _compare_user_grants(
                users[anchor_user], users[user]
            )

    return workload_grant_diffs


def _extract_db_table(grant: str) -> tuple:
    """Extract the database and table name from a grant string."""
    match = re.search(r"`([^`]+)`\.`([^`]+)`", grant)
    if match:
        return match.group(1), match.group(2)
    return "", ""


def _gather_workload_grants(
    workload: Dict[str, List[Dict[str, Any]]],
    db_connections: Dict[str, pymysql.Connection],
) -> Dict[str, Dict[str, List[str]]]:
    """Collect and return grants for each environment in the workload"""
    # Build a dict of envs, users, and grants to use as data/lookup table
    workload_grants = {}
    for env, users in workload.items():
        # Add env to our data table
        workload_grants[env] = {}
        for user in users:
            user_name, hosts = user["user"], user["hosts"]
            for host in hosts:
                grants = _get_grants(db_connections[env], user_name, host)
                workload_grants[env][f"{user_name}@{host}"] = grants
    return workload_grants


def _get_grants(conn: pymysql.Connection, user: str, host: str) -> List[str]:
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


def _read_config(config_file: str = "compare-mysql-grants.yml") -> Dict[str, Any]:
    """Read the configuration file."""
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    if config is None:
        raise ValueError("Failed to parse configuration file.")
    return config


def _strip_ip_from_grant(grant: str) -> str:
    """Remove the IP address from a grant string."""
    return re.sub(r"@\`[^\`]+\`", "@`<IP>`", grant)


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

    # For each workload we need to gather the grants for each user in each env
    all_grants = {}
    for workload_name, workload in config.get("workloads").items():
        logger.info(f"Gathering MySQL user grants for workload: {workload_name}")
        all_grants[workload_name] = _gather_workload_grants(workload, db_connections)

    # Now we have all the grants and may compare
    for workload_name, workload in all_grants.items():
        logger.info(f"Comparing grants for workload: {workload_name}")

        workload_grants_status = _compare_workload_grants(workload)

        for env, status in workload_grants_status.items():
            workload_has_grant_diffs = False
            for user, comparison in status.items():
                if (
                    comparison.get("diffs")["missing_from_user"]
                    or comparison.get("diffs")["missing_from_anchor_user"]
                ):
                    anchor_user = comparison.get("anchor_user")
                    workload_has_grant_diffs = True

                    logger.info(
                        f"User {user} has grant differences compared to anchor user {anchor_user}. (Workload: {workload_name}, Environment: {env})"
                    )
                    if comparison.get("diffs")["missing_from_user"]:
                        logger.info(
                            f"Grants missing from {user} present for anchor user {anchor_user}:"
                        )
                        for grant in sorted(
                            comparison.get("diffs")["missing_from_user"],
                            key=_extract_db_table,
                        ):
                            logger.info(f"  {grant}")
                    if comparison.get("diffs")["missing_from_anchor_user"]:
                        logger.info(
                            f"Grants present for {user} missing from anchor user {anchor_user}:"
                        )
                        for grant in sorted(
                            comparison.get("diffs")["missing_from_anchor_user"],
                            key=_extract_db_table,
                        ):
                            logger.info(f"  {grant}")

            if workload_has_grant_diffs:
                logger.info(
                    f"Grants differences detected, Workload: {workload_name}, Environment: {env}"
                )
            else:
                logger.info(
                    f"Grants aligned, Workload: {workload_name}, Environment: {env}"
                )

        logger.info(f"Grants comparison completed, Workload: {workload_name}.")

    # Close the database connections
    for conn_name, conn in db_connections.items():
        logger.info(f"Closing connection to database: {conn_name}")
        conn.close()

    logger.info("Finished comparing MySQL user grants.")

    return 0
