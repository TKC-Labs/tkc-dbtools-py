# Example: tkc-compare-mysql-grants

This example demonstrates usage of the *tkc-compare-mysql-grants* DB utility.

The *tkc-compare-mysql-grants* utility is a configurable grants comparison script for MySQL compatible databases.  It accepts a configuration map of workloads, users, and databases to produce a comparison of grants across environments.

This example deploys 3 Percona database servers in containers to mimic the following environments.

 - `proddb` is for the prod environment database container
 - `devdb` is the dev environment database container
 - `stagedb` is the stage environment database container

Each environment has the same "workloads" but the username and IP for the workload users differ making direct comparison rather difficult.

SQL scripts exist that can be applied creating drift and differences in an expected way to demonstrate the utilities function and output.

## A workload defined

A *workload* in this utility is a defined set of grants that should be the same for any user that is created for that workload.

A specific user *(user_id@ip_or_host)* should not participate in more than a single workload to prevent grant comparisons from becoming unmanageably complex.

As an alternative I suggest creating a new workload to match the exact grants this user needs to allow managable grants comparison.

## Requirements to run the example

To run this example you'll need a few things installed on the container host machine.

  - Podman or Docker
  - `mysql` CLI client
  - `mysqladmin` CLI client

*See the [system prep guide](examples/tkc-compare-mysql-grants/SYSPREP.md) for OS specific setup information.*

The deployment scripts check for these binaries before attempting to run.

- [deploy_example_in_podman.sh](examples/tkc-compare-mysql-grants/deploy_example_in_podman.sh)
  - Deploys containers using podman

- [deploy_example_in_docker.sh](examples/tkc-compare-mysql-grants/deploy_example_in_docker.sh)
  - Deploys containers using docker
  - Requires user to have permissions to start socker containers

## Usage

```bash
# Clone the repository to the local machine
git clone https://github.com/TKC-Labs/tkc-dbtools-py.git

# Change directory into the local repo clone
# Checkout the branch you want to work with if it's different than main
cd tkc-dbtools-py

# Create a new venv for testing and install the tkc_dbtools module
python3 -m venv venv

# Activate the venv and update pip
source venv/bin/activate
pip install --upgrade pip

# pip install tkc_dbtools from the local clone
pip install .

# From the example directory
cd examples/tkc-compare-mysql-grants/

# Run the deployment script to bring up the containers
./deploy_example_in_podman.sh

# Check that there are no grants issues at initial deployment
tkc-compare-mysql-grants

# Introduce the planned differences
#
# This removes grants from the user api-dev@192.168.122.11 in the dev
# environment for the api workload. The utility should report that grants
# are missing from this user compared to the anchor user.
#
# User api-dev@192.168.122.11 has grant differences compared to anchor user api-dev@192.168.122.10. (Workload: api, Environment: dev)
# Grants missing from api-dev@192.168.122.11 present for anchor user api-dev@192.168.122.10:
#   GRANT SELECT, INSERT ON `example`.`api` TO `user`@`<IP>`
#   GRANT SELECT ON `example`.`syskvp` TO `user`@`<IP>`
#
mysql -h 127.0.0.1 -P 3307 -u root -proot < ./dev-api-grants-revoke-for-intra-env-example.sql

# Check that the issue is reported
tkc-compare-mysql-grants

# Return to the original state
mysql -h 127.0.0.1 -P 3307 -u root -proot < ./dev-api-workload-grants.sql

# Check that there are no grants issues
tkc-compare-mysql-grants

# This removes grants from ALL of the users in the dev environment for the api
# workload. The utility should show the intra-environment grants aligned but
# will report Cross-environment differences.
#
# Cross-environment comparison between environments: prod and dev
# Cross-environment api-dev@192.168.122.10 has grant differences compared to anchor user api@192.168.123.10 for workload api in environment dev.
# Grants missing from api-dev@192.168.122.10 present for anchor user api@192.168.123.10:
#   GRANT SELECT, INSERT ON `example`.`api` TO `user`@`<IP>`
#   GRANT SELECT ON `example`.`syskvp` TO `user`@`<IP>`

mysql -h 127.0.0.1 -P 3307 -u root -proot < ./dev-api-grants-revoke-for-cross-env-example.sql

# Check that the issue is reported
tkc-compare-mysql-grants

# Return to the original state
mysql -h 127.0.0.1 -P 3307 -u root -proot < ./dev-api-workload-grants.sql

# Check that there are no grants issues
tkc-compare-mysql-grants

# This creates differences beteween grants by adding an UPDATE to a specific
# user in a single environment for the api workload.
#
# The utility will show this type of difference from both directions due to
# our simple comparison approach. No drift is detected across environments
# with this because we only compare a single user per-workload across
# environments and those users happen to align.
#
# Grants missing from api-dev@192.168.122.11 present for anchor user api-dev@192.168.122.10:
#   GRANT SELECT, INSERT ON `example`.`api` TO `user`@`<IP>`
#   GRANT SELECT ON `example`.`syskvp` TO `user`@`<IP>`
# Grants present for api-dev@192.168.122.11 missing from anchor user api-dev@192.168.122.10:
#   GRANT SELECT, INSERT, UPDATE ON `example`.`api` TO `user`@`<IP>`
#   GRANT SELECT, UPDATE ON `example`.`syskvp` TO `user`@`<IP>`
#
mysql -h 127.0.0.1 -P 3307 -u root -proot < ./dev-api-grants-chaos-for-intra-env-example.sql

# Check that the issue is reported
tkc-compare-mysql-grants

# Return to the original state
mysql -h 127.0.0.1 -P 3307 -u root -proot < ./dev-api-grants-cleanup-chaos-for-intra-env-example.sql

# Check that there are no grants issues
tkc-compare-mysql-grants

# This creates differences beteween grants by adding an UPDATE to ALL users
# in a single environment for the api workload.
#
# The utility will show this type of difference from both directions due to
# our simple comparison approach. No drift is detected inside the environment
# with this because the grants for the users within the environments still
# match.
#
# Cross-environment comparison between environments: prod and dev
# Cross-environment api-dev@192.168.122.10 has grant differences compared to anchor user api@192.168.123.10 for workload api in environment dev.
# Grants missing from api-dev@192.168.122.10 present for anchor user api@192.168.123.10:
#   GRANT SELECT, INSERT ON `example`.`api` TO `user`@`<IP>`
#   GRANT SELECT ON `example`.`syskvp` TO `user`@`<IP>`
# Grants present for api-dev@192.168.122.10 missing from anchor user api@192.168.123.10:
#   GRANT SELECT, INSERT, UPDATE ON `example`.`api` TO `user`@`<IP>`
#   GRANT SELECT, UPDATE ON `example`.`syskvp` TO `user`@`<IP>`
#
mysql -h 127.0.0.1 -P 3307 -u root -proot < ./dev-api-grants-chaos-for-cross-env-example.sql

# Check that the issue is reported
tkc-compare-mysql-grants

# Return to the original state
mysql -h 127.0.0.1 -P 3307 -u root -proot < ./dev-api-grants-cleanup-chaos-for-cross-env-example.sql

# Check that there are no grants issues
tkc-compare-mysql-grants


# This creates differences beteween grants by adding an new additional grant
# for all users on the pod environment api workload.
#
# The utility will show this type of difference as missing grants found in
# a cross-environment comprison for any envrionment where the grant is missing.
#
# Cross-environment comparison between environments: prod and dev
# Cross-environment comparison between environments: prod and stage
# Cross-environment api-dev@192.168.122.10 has grant differences compared to anchor user api@192.168.123.10 for workload api in environment dev.
# Grants missing from api-dev@192.168.122.10 present for anchor user api@192.168.123.10:
#   GRANT SELECT ON `example`.`users` TO `user`@`<IP>`
# Cross-environment api-stage@192.168.124.10 has grant differences compared to anchor user api@192.168.123.10 for workload api in environment stage.
# Grants missing from api-stage@192.168.124.10 present for anchor user api@192.168.123.10:
#   GRANT SELECT ON `example`.`users` TO `user`@`<IP>`
#
mysql -h 127.0.0.1 -P 3306 -u root -proot < ./prod-api-add-extra-grants-example.sql

# Check that the issue is reported
tkc-compare-mysql-grants

# Return to the original state
mysql -h 127.0.0.1 -P 3306 -u root -proot < ./prod-api-remove-extra-grants-example.sql

# Check that there are no grants issues
tkc-compare-mysql-grants

# Cleanup the lab; destroys and removes the DB containers
./deploy_example_in_podman.sh cleanup
```
