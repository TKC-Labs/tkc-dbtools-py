#!/usr/bin/env bash
#
# This script deploys the example databases to the local machine using Podman
#
set -euo pipefail


# Function to cleanup the containers and volumes
cleanup() {
    echo "Stopping containers..."
    podman stop devdb proddb stagedb
    echo
    echo "Removing containers..."
    podman rm devdb proddb stagedb
    echo
    echo "Removing volumes..."
    podman volume rm example_devdb example_proddb example_stagedb
    echo
    echo "Cleanup completed."
}

# Function to check if a database is ready
check_db_ready() {
    local DB_NAME=$1
    local PORT=$2
    until  mysqladmin ping --silent -h 127.0.0.1 -P $PORT -u root -proot > /dev/null; do
        echo "Waiting for $DB_NAME database connection..."
        sleep 2
    done
}

# Check if the script is called with 'cleanup' argument
if [ "${1:-}" == "cleanup" ]; then
    cleanup
    exit 0
fi

# Check if Podman, MySQL, and MySQL Admin are installed
missing_commands=()

for cmd in podman mysql mysqladmin; do
    case $cmd in
        podman)
            command -v podman &> /dev/null || missing_commands+=("podman")
            ;;
        mysql)
            command -v mysql &> /dev/null || missing_commands+=("mysql")
            ;;
        mysqladmin)
            command -v mysqladmin &> /dev/null || missing_commands+=("mysqladmin")
            ;;
    esac
done

if [ ${#missing_commands[@]} -ne 0 ]; then
    echo "The following commands could not be found: ${missing_commands[*]}. Please install them to use this script."
    exit 1
fi

# Launch the database containers
# Check if the containers or volumes already exist
for resource in container:devdb container:proddb volume:example_devdb volume:example_proddb; do
    type=${resource%%:*}
    name=${resource##*:}
    if podman $type exists $name; then
        echo "$type '$name' already exists, cleanup and try again. Exiting."
        exit 1
    fi
done

# Create data volumes for test persistance
echo "Creating data volumes for test persistence..."
podman volume create example_devdb
podman volume create example_proddb
podman volume create example_stagedb
echo

# Dev environment
echo "Creating devdb container..."
podman run -d --name devdb --hostname devdb \
    -e MYSQL_ROOT_PASSWORD=root \
    -v "example_devdb:/var/lib/mysql" \
    -p 3307:3306 \
    docker.io/percona/percona-server:8.0
echo

# Prod environment
echo "Creating proddb container..."
podman run -d --name proddb --hostname proddb \
    -e MYSQL_ROOT_PASSWORD=root \
    -v "example_proddb:/var/lib/mysql" \
    -p 3306:3306 \
    docker.io/percona/percona-server:8.0
echo


# Stage environment
echo "Creating stagedb container..."
podman run -d --name stagedb --hostname stagedb \
    -e MYSQL_ROOT_PASSWORD=root \
    -v "example_stagedb:/var/lib/mysql" \
    -p 3308:3306 \
    docker.io/percona/percona-server:8.0
echo

# Check if the databases are ready
check_db_ready devdb 3307
check_db_ready proddb 3306
check_db_ready stagedb 3308
echo
echo "Databases are ready."
echo

# Deploy the example database schema
echo "Deploying example database schema..."

# devdb is on 3307
if ! mysql -h localhost -P 3307 -u root -proot -e 'use example;' 2> /dev/null; then
mysql -h localhost -P 3307 -u root -proot < $(dirname "$0")/schema.sql
echo "  Example database schema deployed to devdb."
fi

# proddb is on 3306
if ! mysql -h localhost -P 3306 -u root -proot -e 'use example;' 2> /dev/null; then
mysql -h localhost -P 3306 -u root -proot < $(dirname "$0")/schema.sql
echo "  Example database schema deployed to proddb."
fi

# stagedb is on 3308
if ! mysql -h localhost -P 3308 -u root -proot -e 'use example;' 2> /dev/null; then
mysql -h localhost -P 3308 -u root -proot < $(dirname "$0")/schema.sql
echo "  Example database schema deployed to stagedb."
fi

# Create Users and Apply Grants
echo
echo "Creating users and applying grants..."

# devdb is on 3307
mysql -h localhost -P 3307 -u root -proot < $(dirname "$0")/dev-api-workload-grants.sql
mysql -h localhost -P 3307 -u root -proot < $(dirname "$0")/dev-syskvp-workload-grants.sql
mysql -h localhost -P 3307 -u root -proot < $(dirname "$0")/dev-user-workload-grants.sql

# proddb is on 3306
mysql -h localhost -P 3306 -u root -proot < $(dirname "$0")/prod-api-workload-grants.sql
mysql -h localhost -P 3306 -u root -proot < $(dirname "$0")/prod-syskvp-workload-grants.sql
mysql -h localhost -P 3306 -u root -proot < $(dirname "$0")/prod-user-workload-grants.sql

# stagedb is on 3306
mysql -h localhost -P 3308 -u root -proot < $(dirname "$0")/stage-api-workload-grants.sql
mysql -h localhost -P 3308 -u root -proot < $(dirname "$0")/stage-syskvp-workload-grants.sql
mysql -h localhost -P 3308 -u root -proot < $(dirname "$0")/stage-user-workload-grants.sql

# Show the users created
echo
echo "Users deployed to devdb:"
mysql -h localhost -P 3307 -u root -proot -e "SELECT User,Host FROM mysql.user WHERE Host NOT IN ('%', 'localhost')"

echo
echo "Users deployed to proddb:"
mysql -h localhost -P 3306 -u root -proot -e "SELECT User,Host FROM mysql.user WHERE Host NOT IN ('%', 'localhost')"

echo
echo "Users deployed to stagedb:"
mysql -h localhost -P 3308 -u root -proot -e "SELECT User,Host FROM mysql.user WHERE Host NOT IN ('%', 'localhost')"

echo
echo "Ready for testing"
