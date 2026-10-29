<#
.SYNOPSIS
    Automated SSH Configuration Script for Windows (PowerShell)
    Configures ~/.ssh/config for Bastion Host & ProxyJump access.
#>

param (
    [Parameter(Mandatory=$true, HelpMessage="Enter the Public IP of your Bastion host")]
    [string]$BastionPublicIP,

    [Parameter(Mandatory=$false)]
    [string]$KeyPath = "$HOME\.ssh\ewb-lab.pem"
)

$sshDir = "$HOME\.ssh"
if (-not (Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    Write-Host "[+] Created directory: $sshDir" -ForegroundColor Green
}

$configFile = "$sshDir\config"

$sshBlock = @"

# ==========================================
# EWB AWS VPC Peering Lab Configuration
# ==========================================
Host ewb-bastion
    HostName $BastionPublicIP
    User ec2-user
    IdentityFile $KeyPath
    IdentitiesOnly yes

Host ewb-app-a
    HostName 10.10.2.10
    User ec2-user
    IdentityFile $KeyPath
    IdentitiesOnly yes
    ProxyJump ewb-bastion

Host ewb-app-b
    HostName 10.20.1.10
    User ec2-user
    IdentityFile $KeyPath
    IdentitiesOnly yes
    ProxyJump ewb-bastion
# ==========================================
"@

Add-Content -Path $configFile -Value $sshBlock
Write-Host "[✓] Successfully appended SSH configuration to $configFile" -ForegroundColor Green
Write-Host ""
Write-Host "You can now connect to your instances using:" -ForegroundColor Cyan
Write-Host "  ssh ewb-bastion" -ForegroundColor Yellow
Write-Host "  ssh ewb-app-a" -ForegroundColor Yellow
Write-Host "  ssh ewb-app-b" -ForegroundColor Yellow
