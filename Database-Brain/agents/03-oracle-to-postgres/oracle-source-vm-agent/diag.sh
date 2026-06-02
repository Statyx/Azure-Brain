#!/bin/bash
echo "==UPTIME=="
uptime
echo "==CLOUD-INIT=="
sudo cloud-init status --long 2>&1 || echo "no cloud-init"
echo "==INSTALL-LOG=="
if [ -f /var/log/oracle-install.log ]; then
  sudo tail -100 /var/log/oracle-install.log
else
  echo "MISSING /var/log/oracle-install.log"
fi
echo "==CLOUD-INIT-OUTPUT=="
sudo tail -50 /var/log/cloud-init-output.log 2>&1
echo "==PROCS=="
ps -ef | grep -E "ora_|tnslsnr" | grep -v grep | head -10
echo "==PORTS=="
sudo ss -tln 2>&1 | grep -E "1521|22|:80"
echo "==OPT-ORACLE=="
ls -la /opt/oracle 2>/dev/null || echo "missing /opt/oracle"
echo "==SVC=="
sudo systemctl list-units --type=service --no-pager 2>&1 | grep -i oracle || echo "no oracle service"
echo "==DONE=="
