$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$logPath = Join-Path $PSScriptRoot 'azure/vintara-deploy.log'
Start-Transcript -LiteralPath $logPath -Force | Out-Null
try {
$sshArgs = @('-i', 'azure/private/vintara', '-o', 'UserKnownHostsFile=azure/private/known_hosts', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15')
$target = 'azureuser@20.3.229.69'
Write-Host 'Checking Azure SSH access...'
& ssh @sshArgs $target 'test -f /opt/vintara/azure/cloud.env && command -v docker'
if ($LASTEXITCODE -ne 0) { throw 'Cannot connect to Azure. Check the VM is running and the SSH rule allows your current public IP. No remote changes were made.' }
& tar -czf azure/vintara-release.tar.gz Dockerfile docker branding
if ($LASTEXITCODE -ne 0) { throw 'Cannot package release.' }
$releaseHash = (Get-FileHash -LiteralPath 'azure/vintara-release.tar.gz' -Algorithm SHA256).Hash.ToLowerInvariant()
& scp @sshArgs azure/vintara-release.tar.gz "${target}:/tmp/vintara-release.tar.gz"
if ($LASTEXITCODE -ne 0) { throw 'Cannot upload release.' }
& scp @sshArgs azure/update-vintara.sh "${target}:/tmp/update-vintara.sh"
if ($LASTEXITCODE -ne 0) { throw 'Cannot upload deployment script.' }
& ssh @sshArgs $target "sudo bash /tmp/update-vintara.sh $releaseHash"
if ($LASTEXITCODE -ne 0) { throw 'Deployment did not complete. Review the output; the server script attempts rollback automatically.' }
$url = 'https://vintara-if6201-508832.westus2.cloudapp.azure.com/'
$response = Invoke-WebRequest -Uri $url -UseBasicParsing
if ($response.StatusCode -ne 200 -or $response.Content -notmatch 'VINTARA') { throw 'Public HTTPS verification failed.' }
Write-Host "Vintara is published: $url" -ForegroundColor Green
} finally {
    Stop-Transcript | Out-Null
}
