"""
Functions to compare MySQL user grants between multiple MySQL servers.
"""

import logging
import re
from typing import Dict, List, Set, Any

import pymysql
import yaml

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _compare_workload_user_grants(
    anchor_user_grants: List[str], user_grants: List[str]
) -> Set[str]:
    """Compare the grants of two users."""
    # Strip the Username and IP address from the grants so we can compare them
    # without those considerations.
    stripped_user_grants = [
        _strip_ip_and_username_from_grant(grant) for grant in user_grants
    ]
    stripped_anchor_user_grants = [
        _strip_ip_and_username_from_grant(grant) for grant in anchor_user_grants
    ]

    sorted_user_grants = sorted(stripped_user_grants)
    sorted_anchor_user_grants = sorted(stripped_anchor_user_grants)

    logger.debug("Anchor User grants: %s", sorted_anchor_user_grants)
    logger.debug("User grants: %s", sorted_user_grants)

    missing_from_anchor_user_grants = set(sorted_user_grants) - set(
        sorted_anchor_user_grants
    )
    missing_from_user_grants = set(sorted_anchor_user_grants) - set(sorted_user_grants)

    logger.debug("Missing from anchor user: %s", missing_from_anchor_user_grants)
    logger.debug("Missing from user: %s", missing_from_user_grants)

    grant_diffs = {
        "missing_from_user": missing_from_user_grants,
        "missing_from_anchor_user": missing_from_anchor_user_grants,
    }

    return grant_diffs


def _compare_cross_env_workload_grants(
    workload: Dict[str, Dict[str, List[str]]], anchor_env: str
) -> Dict[str, Dict[str, Dict[str, Set[str]]]]:
    """Compare cross-env grants in a workload"""
    workload_grant_diffs = {}

    # Get the first user in the anchor_env as our baseline
    anchor_env_user = next(iter(workload[anchor_env]))

    for env in workload.keys():
        # Skip the anchor_env because we use it as our baseline
        if env == anchor_env:
            continue

        workload_grant_diffs[env] = {}

        # Get the first user in the env as our comparison
        env_user = next(iter(workload[env]))

        logger.info(
            "Cross-environment comparison between environments: %s and %s",
            anchor_env,
            env,
        )
        workload_grant_diffs[env][env_user] = {}
        workload_grant_diffs[env][env_user]["anchor_env"] = anchor_env
        workload_grant_diffs[env][env_user]["anchor_env_user"] = anchor_env_user

        logger.debug(
            "Anchor Env User Grants: %s", workload[anchor_env][anchor_env_user]
        )
        logger.debug("Env User Grants: %s", workload[env][env_user])

        workload_grant_diffs[env][env_user]["diffs"] = _compare_workload_user_grants(
            workload[anchor_env][anchor_env_user], workload[env][env_user]
        )

    return workload_grant_diffs


def _compare_per_env_workload_grants(workload: Dict[str, Dict[str, List[str]]]) -> bool:
    """Compare per-env grants in a workload"""
    workload_grant_diffs = {}

    for env, users in workload.items():
        logger.debug("Comparing grants for environment: %s", env)
        workload_grant_diffs[env] = {}

        # Get a list of users
        user_list = list(users.keys())

        # Select first user in list as anchor user
        anchor_user = user_list[0]

        # Compare each user to the others
        for i in range(1, len(user_list)):
            user = user_list[i]
            logger.debug("Comparing grants between users: %s and %s", anchor_user, user)
            workload_grant_diffs[env][user] = {}
            workload_grant_diffs[env][user]["anchor_user"] = anchor_user
            workload_grant_diffs[env][user]["diffs"] = _compare_workload_user_grants(
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


def _process_cross_env_workload_grants_status(
    workload_name: str,
    cross_env_workload_grants_status: Dict[str, Dict[str, Dict[str, Set[str]]]],
) -> None:
    """Process the grants status and log the results."""

    # Process the grants for users across each environment per-workload
    # to ensure each user across environments has the same grants.
    for env, status in cross_env_workload_grants_status.items():
        workload_has_grant_diffs = False

        for user, comparison in status.items():
            if (
                comparison.get("diffs")["missing_from_user"]
                or comparison.get("diffs")["missing_from_anchor_user"]
            ):
                anchor_user = comparison.get("anchor_env_user")
                workload_has_grant_diffs = True

                logger.info(
                    (
                        "Cross-environment %s has grant differences compared to"
                        "anchor user %s for workload %s in environment %s."
                    ),
                    user,
                    anchor_user,
                    workload_name,
                    env,
                )
                if comparison.get("diffs")["missing_from_user"]:
                    logger.info(
                        "Grants missing from %s present for anchor user %s:",
                        user,
                        anchor_user,
                    )
                    for grant in sorted(
                        comparison.get("diffs")["missing_from_user"],
                        key=_extract_db_table,
                    ):
                        logger.info("  %s", grant)
                if comparison.get("diffs")["missing_from_anchor_user"]:
                    logger.info(
                        "Grants present for %s missing from anchor user %s:",
                        user,
                        anchor_user,
                    )
                    for grant in sorted(
                        comparison.get("diffs")["missing_from_anchor_user"],
                        key=_extract_db_table,
                    ):
                        logger.info("  %s", grant)

            if workload_has_grant_diffs:
                logger.info(
                    (
                        "Cross-environment grants differences detected for workload %s "
                        "between environments %s and %s."
                    ),
                    workload_name,
                    comparison.get("anchor_env"),
                    env,
                )
            else:
                logger.info(
                    "Cross-environment grants are aligned for %s between environments %s and %s.",
                    workload_name,
                    comparison.get("anchor_env"),
                    env,
                )


def _process_per_env_workload_grants_status(
    workload_name: str,
    workload_grants_status: Dict[str, Any],
) -> None:
    """Process the grants status and log the results."""

    # Process the grants for users within each environment per-workload
    # to ensure each user across an environment has the same grants.
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
                    (
                        "User %s has grant differences compared to anchor user %s. "
                        "(Workload: %s, Environment: %s)"
                    ),
                    user,
                    anchor_user,
                    workload_name,
                    env,
                )
                if comparison.get("diffs")["missing_from_user"]:
                    logger.info(
                        "Grants missing from %s present for anchor user %s:",
                        user,
                        anchor_user,
                    )
                    for grant in sorted(
                        comparison.get("diffs")["missing_from_user"],
                        key=_extract_db_table,
                    ):
                        logger.info("  %s", grant)
                if comparison.get("diffs")["missing_from_anchor_user"]:
                    logger.info(
                        "Grants present for %s missing from anchor user %s:",
                        user,
                        anchor_user,
                    )
                    for grant in sorted(
                        comparison.get("diffs")["missing_from_anchor_user"],
                        key=_extract_db_table,
                    ):
                        logger.info("  %s", grant)

        if workload_has_grant_diffs:
            # The environment for the workload had grant differences so we
            # cannot complete the cross-environment comparison for this
            # workload.
            logger.info(
                (
                    "Environment grants differences detected for workload %s in environment %s, "
                    "use caution with cross-environment comparisons."
                ),
                workload_name,
                env,
            )

        else:
            # The environment for the workload had no grant differences so we
            # can proceed with the cross-environment comparison for this
            # workload.
            logger.info(
                "Environment grants are aligned for workload %s in environment %s",
                workload_name,
                env,
            )


def _read_config(config_file: str = "compare-mysql-grants.yml") -> Dict[str, Any]:
    """Read the configuration file."""
    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if config is None:
        raise ValueError("Failed to parse configuration file.")
    return config


def _strip_ip_from_grant(grant: str) -> str:
    """Remove the IP address from a grant string."""
    return re.sub(r"@\`[^\`]+\`", "@`<IP>`", grant)


def _strip_ip_and_username_from_grant(grant: str) -> str:
    """Remove the IP address and username from a grant string."""
    # Remove the IP address
    grant = re.sub(r"@\`[^\`]+\`", "@`<IP>`", grant)
    # Remove the username
    grant = re.sub(r"TO \`[^\`]+\`@", "TO `user`@", grant)
    return grant


def _validate_config(config: Dict[str, Any]) -> None:
    """Validate the configuration values read from configuration file."""

    # First make sure we have all of the top level sections we expect
    if not config.get("databases"):
        raise AttributeError("Databases not found in configuration file.")
    if not config.get("workloads"):
        raise AttributeError("Workloads not found in configuration file.")

    # Validate the databases configuration
    databases_config = config.get("databases")
    envs = _validate_database_config(databases_config)

    # Validate the workloads configuration
    workloads_config = config.get("workloads")
    _validate_workload_config(workloads_config, envs)


def _validate_database_config(databases_config: Dict[str, Any]) -> List[str]:
    """Validate the databases configuration."""
    leaders = []
    envs = []

    for database, config_values in databases_config.items():
        logger.info("Validating database configuration for %s", database)
        required_keys = ["host", "port", "user", "password"]
        missing_keys = [key for key in required_keys if key not in config_values.keys()]
        if missing_keys:
            raise AttributeError(
                (
                    f"Database configuration for {database} is incomplete."
                    f"Missing keys: {', '.join(missing_keys)}"
                )
            )

        # We have all our required keys, so we can add the env to the list of
        # envs for further validation
        envs.append(database)

        if config_values.get("leader", False):
            leaders.append(database)

    if len(leaders) != 1:
        raise AttributeError(
            (
                f"Exactly one database must be set as the leader."
                f"Found {len(leaders)} databases set as leader."
            )
        )

    return envs


def _validate_workload_config(
    workloads_config: Dict[str, Any], envs: List[str]
) -> None:
    """Validate the workloads configuration."""
    logger.debug(
        "Validating workload configurations for workloads: %s",
        ", ".join(workloads_config.keys()),
    )

    for workload, workload_envs in workloads_config.items():
        logger.info("Validating workload configuration for %s", workload)

        # Check workload for required envs
        missing_envs = [env for env in envs if env not in workload_envs.keys()]
        if missing_envs:
            raise AttributeError(
                (
                    f"Workload configuration for {workload} is incomplete."
                    f"Missing environments: {', '.join(missing_envs)}"
                )
            )

        # Check workload environments for required user keys
        for env, users in workload_envs.items():
            required_keys = ["user", "hosts"]
            for user in users:
                missing_keys = [key for key in required_keys if key not in user.keys()]
                if missing_keys:
                    raise AttributeError(
                        (
                            f"User configuration for {workload} in {env} is incomplete."
                            f"Missing keys: {', '.join(missing_keys)}"
                        )
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
        logger.error("No configuration file found. (%s)", e)
        return 1
    except ValueError as e:
        logger.error("Failed to parse configuration file. (%s)", e)
        return 1

    # Configuration data Validation
    try:
        _validate_config(config)
        logger.info("Configuration file appears valid.")
    except AttributeError as e:
        logger.error("Configuration file validation failed: %s", e)
        return 1

    # Get the leader environment for cross-environment comparison
    anchor_env = [
        db for db, values in config.get("databases").items() if values.get("leader")
    ][0]

    logger.info("Leader database: %s", anchor_env)

    # Connect to the databases
    db_connections = {}
    for database in config.get("databases"):
        try:
            db_connections[database] = _connect_to_db(config.get("databases")[database])
        except pymysql.err.OperationalError as e:
            logger.error("Failed to connect to database: %s (%s)", database, e)
            return 1

        try:
            db_connections[database].ping()
        except pymysql.MySQLError as e:
            logger.error("Database: %s not responding: (%s)", database, e)
            return 1

    if len(db_connections.keys()) == len(config.get("databases").keys()):
        logger.info("All databases connected successfully.")

    # For each workload we need to gather the grants for each user in each env
    all_grants = {}
    for workload_name, workload in config.get("workloads").items():
        logger.info("Gathering MySQL user grants for workload: %s", workload_name)
        all_grants[workload_name] = _gather_workload_grants(workload, db_connections)

    # Now we have all the grants and may compare
    for workload_name, workload in all_grants.items():
        logger.info("Comparing grants for workload: %s", workload_name)

        # Compare the per-env grants for the workload
        per_env_workload_grants_status = _compare_per_env_workload_grants(workload)
        _process_per_env_workload_grants_status(
            workload_name, per_env_workload_grants_status
        )

        # Compare the cross-env grants for the workload
        cross_env_workload_grants_status = _compare_cross_env_workload_grants(
            workload, anchor_env
        )
        _process_cross_env_workload_grants_status(
            workload_name, cross_env_workload_grants_status
        )

    # Close the database connections
    for conn_name, conn in db_connections.items():
        logger.info("Closing connection to database: %s", conn_name)
        conn.close()

    logger.info("Finished comparing MySQL user grants.")

    return 0
