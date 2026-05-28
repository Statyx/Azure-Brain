#!/usr/bin/env bash
# install-ora2pg.sh — install Ora2Pg 25.0 + dependencies on a Linux jumpbox.
# Tested on Oracle Linux 8 / RHEL 8 / Ubuntu 22.04.
# Run as root (or with sudo).
set -euo pipefail

ORA2PG_VERSION="${ORA2PG_VERSION:-25.0}"
ORACLE_INSTANTCLIENT_VERSION="${OIC_VERSION:-21.13.0.0.0}"

# ---- Detect distro ----
if [ -f /etc/redhat-release ]; then
  DISTRO="rhel"
elif [ -f /etc/debian_version ]; then
  DISTRO="debian"
else
  echo "Unsupported distro" >&2; exit 1
fi

# ---- Install Perl + DBI + DBD::Pg + libaio ----
if [ "$DISTRO" = "rhel" ]; then
  dnf install -y perl perl-DBI perl-DBD-Pg libaio gcc make wget unzip
else
  apt-get update
  apt-get install -y perl libdbi-perl libdbd-pg-perl libaio1 build-essential wget unzip
fi

# ---- Oracle Instant Client (needed for DBD::Oracle) ----
if [ ! -d /opt/oracle/instantclient_${ORACLE_INSTANTCLIENT_VERSION//./_} ]; then
  mkdir -p /opt/oracle && cd /opt/oracle
  wget -q "https://download.oracle.com/otn_software/linux/instantclient/2113000/instantclient-basic-linux.x64-21.13.0.0.0dbru.zip"
  wget -q "https://download.oracle.com/otn_software/linux/instantclient/2113000/instantclient-sdk-linux.x64-21.13.0.0.0dbru.zip"
  wget -q "https://download.oracle.com/otn_software/linux/instantclient/2113000/instantclient-sqlplus-linux.x64-21.13.0.0.0dbru.zip"
  unzip -o "*.zip"
  rm -f *.zip
  ln -sf /opt/oracle/instantclient_21_13 /opt/oracle/instantclient
fi

cat > /etc/profile.d/oracle-instantclient.sh <<EOF
export ORACLE_HOME=/opt/oracle/instantclient
export LD_LIBRARY_PATH=\$ORACLE_HOME:\${LD_LIBRARY_PATH:-}
export PATH=\$ORACLE_HOME:\$PATH
EOF
source /etc/profile.d/oracle-instantclient.sh

# ---- DBD::Oracle (CPAN) ----
cpan -i DBD::Oracle || PERL_MM_USE_DEFAULT=1 cpan -fi DBD::Oracle

# ---- Ora2Pg ----
cd /tmp
wget -q "https://github.com/darold/ora2pg/archive/refs/tags/v${ORA2PG_VERSION}.tar.gz"
tar xzf "v${ORA2PG_VERSION}.tar.gz"
cd "ora2pg-${ORA2PG_VERSION}"
perl Makefile.PL
make && make install
cd /

# ---- Verify ----
ora2pg --version
echo "==> Ora2Pg ${ORA2PG_VERSION} installed."
