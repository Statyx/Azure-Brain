#!/bin/bash
set -e
echo "==INSTALL-DOCKER=="
if ! command -v docker >/dev/null 2>&1; then
  sudo dnf install -y dnf-plugins-core 2>&1 | tail -5
  sudo dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo
  sudo dnf install -y docker-ce docker-ce-cli containerd.io 2>&1 | tail -5
  sudo systemctl enable --now docker
  sudo usermod -aG docker oracleadmin
fi
docker --version

echo "==PULL-ORACLE-XE=="
sudo docker pull gvenzl/oracle-xe:21-slim-faststart 2>&1 | tail -3

echo "==RUN-CONTAINER=="
sudo docker rm -f oracle-xe 2>/dev/null || true
sudo docker run -d --name oracle-xe --restart=always \
  -p 1521:1521 \
  -e ORACLE_PASSWORD=Demo_Ora2Pg_2026! \
  -e APP_USER=hr \
  -e APP_USER_PASSWORD=hr \
  -v oradata:/opt/oracle/oradata \
  gvenzl/oracle-xe:21-slim-faststart

echo "==WAIT-READY=="
for i in $(seq 1 90); do
  if sudo docker logs oracle-xe 2>&1 | grep -q "DATABASE IS READY TO USE"; then
    echo "Ready after ${i}*5s"
    break
  fi
  sleep 5
done

echo "==STATUS=="
sudo docker ps --format '{{.Names}} {{.Status}}'
sudo ss -tln | grep 1521 || echo "1521 not listening"
echo "==DONE=="
