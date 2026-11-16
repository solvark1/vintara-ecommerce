$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$sshOptions = @('-i', 'azure/private/vintara', '-o', 'UserKnownHostsFile=azure/private/known_hosts', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15')
$server = 'azureuser@20.3.229.69'
& tar --exclude=analytics/private --exclude=analytics/__pycache__ --exclude=analytics/tests/__pycache__ -czf azure/terranostra-analytics.tar.gz analytics
if ($LASTEXITCODE -ne 0) { throw 'Could not package analytics source.' }
& scp @sshOptions azure/terranostra-analytics.tar.gz "${server}:/tmp/terranostra-analytics.tar.gz"
if ($LASTEXITCODE -ne 0) { throw 'Could not upload analytics source.' }
$remote = 'set -eu; tar -xzf /tmp/terranostra-analytics.tar.gz -C /opt/vintara; cd /opt/vintara/analytics; python3 -m unittest discover -s tests -v; python3 seed_reviews.py; python3 etl.py --trigger manual; python3 verify.py; install -m 644 terranostra-etl.service /etc/systemd/system/terranostra-etl.service; install -m 644 terranostra-etl.timer /etc/systemd/system/terranostra-etl.timer; systemd-analyze verify /etc/systemd/system/terranostra-etl.service /etc/systemd/system/terranostra-etl.timer; systemctl daemon-reload; systemctl enable --now terranostra-etl.timer'
& ssh @sshOptions $server "sudo sh -c '$remote'"
if ($LASTEXITCODE -ne 0) { throw 'Analytics deployment failed; inspect journal and latest manifest. The web store was not redeployed.' }
Write-Host 'Terra Nostra ETL deployed, verified and scheduled.'
