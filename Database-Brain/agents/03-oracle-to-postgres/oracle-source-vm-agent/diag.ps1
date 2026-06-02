$ErrorActionPreference = "Continue"
$az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
Write-Host "=== Running diagnostic via Azure agent (no SSH needed) ===" -ForegroundColor Cyan
$script = @'
echo "=== UPTIME ==="
uptime
echo ""
echo "=== CLOUD-INIT STATUS ==="
sudo cloud-init status --long 2>&1 || echo "cloud-init unavailable"
echo ""
echo "=== ORACLE INSTALL LOG (last 80 lines) ==="
if [ -f /var/log/oracle-install.log ]; then
  sudo tail -80 /var/log/oracle-install.log
else
  echo "NO log at /var/log/oracle-install.log"
  echo "--- /var/log/cloud-init-output.log tail ---"
  sudo tail -100 /var/log/cloud-init-output.log 2>&1 | head -120
fi
echo ""
echo "=== ORACLE PROCESS / LISTENER ==="
ps -ef | grep -E "(ora_|tnslsnr|oracle)" | grep -v grep | head -20
echo ""
echo "=== PORT 1521 ==="
sudo ss -tln | grep 1521 || echo "1521 NOT listening"
echo ""
echo "=== /opt/oracle ==="
ls -la /opt/oracle 2>/dev/null || echo "no /opt/oracle"
echo ""
echo "=== systemd oracle-xe ==="
sudo systemctl status oracle-xe-21c --no-pager 2>&1 | head -20 || echo "no oracle-xe-21c service"
'@

& $az vm run-command invoke `
  -g rg-demo-ora2pg `
  -n vm-oracle-src `
  --command-id RunShellScript `
  --scripts $script `
  --query "value[0].message" -o tsv
