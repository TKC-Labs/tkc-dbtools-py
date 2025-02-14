"""
Functions to compare MySQL user grants between multiple MySQL servers.
"""
import logging
import pymysql
import yaml

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def get_grants(conn, user, host):
    with conn.cursor() as cursor:
        cursor.execute("SHOW GRANTS FOR %s@%s;", (user, host))
        grants = [row[0] for row in cursor.fetchall()]
    return sorted(grants)  # Sort for consistent comparison

def connect_to_db(config):
    return pymysql.connect(
        host=config["host"],
        user=config["user"],
        password=config["password"],
        database="mysql"  # Grants exist in the MySQL system database
    )


def compare_grants(dev_grants, prod_grants, workload):
    if dev_grants == prod_grants:
        print(f"✅ Grants match for workload: {workload}")
    else:
        print(f"❌ Mismatch in grants for workload: {workload}")
        print(f"Dev Grants:\n" + "\n".join(dev_grants))
        print(f"Prod Grants:\n" + "\n".join(prod_grants))


def run():
    """
    Compare MySQL user grants between multiple MySQL servers.
    """
    logger.info("Comparing MySQL user grants...")

    with open("compare-mysql-grants.yml", "r") as f:
        config = yaml.safe_load(f)

    print(f"Database Configs:\n{config.get("databases")}")

    # dev_conn = connect_to_db(db_config["dev"])
    # prod_conn = connect_to_db(db_config["prod"])
    
    for workload, users in config.get("workloads").items():
        print(f"Workload: {workload} has users: {users}")
        # dev_user, dev_host = users["dev"]["user"], users["dev"]["host"]
        # prod_user, prod_host = users["prod"]["user"], users["prod"]["host"]

        # dev_grants = get_grants(dev_conn, dev_user, dev_host)
        # prod_grants = get_grants(prod_conn, prod_user, prod_host)

        # compare_grants(dev_grants, prod_grants, workload)

    # dev_conn.close()
    # prod_conn.close()
