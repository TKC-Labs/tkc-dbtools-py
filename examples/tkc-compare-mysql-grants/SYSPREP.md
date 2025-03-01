# System Preparation Instructions

This is how to prepare a bare system for running this example in podman.

One should be able to remove the `podman` package and perform the Docker installtion of choice to use Docker for the containers.

These stpes are tested against the distribution provided cloud images for the versions mentioned.

## Ubuntu 22.04 (Python 3.10)

```bash
# Update apt, update the system, and install necessary packages
apt-get update
apt-get upgrade
apt-get install python3-pip python3-venv podman mysql-client-8.0
```

## Debian 12 (Pytho3.11)

```bash
# Update apt, update the system, and install necessary packages
apt-get update
apt-get upgrade
apt-get install python3-pip python3-venv podman mariadb-client git
```

## Fedora 41 (Python 3.13)

```bash
# Update the system and install necessary packages
dnf update -y
dnf install mysql git
```
