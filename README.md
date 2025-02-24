# Database Tools and Utilities

This started with a need to compare user grants across databases.

## Tools

### tkc-compare-mysql-grants

A configurable grants comparison script for MySQL compatible databases.

This utility accepts a configuration map of workload users and environments to produce a comparison of grants across environments.

Config File Example:

  - [compare-mysql-grants.yml](examples/tkc-compare-mysql-grants/compare-mysql-grants.yml)
