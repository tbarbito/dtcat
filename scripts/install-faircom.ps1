# Assisted installer for FairCom DB Developer Edition (Windows).
#
# This script does NOT download FairCom for you (their site requires a form).
# It opens the sign-up form, asks where you saved the file, and configures
# environment variables.
#
# Usage:  .\scripts\install-faircom.ps1 [-Target <path>]
#         default Target: $env:USERPROFILE\faircom

[CmdletBinding()]
param(
    [string]$Target = "$env:USERPROFILE\faircom"
)

$ErrorActionPreference = 'Stop'
$FormUrl = "https://www.faircom.com/download-ctreeace"
$DownloadsUrl = "https://www.faircom.com/products/downloads"

Write-Host @"
================================================================
  FairCom DB Developer Edition — assisted installer for dtcat
================================================================

This script will help you install FairCom DB locally. It does NOT
redistribute any FairCom binaries — you download them yourself,
under FairCom's own license.

Steps:
  1. Open the sign-up form in your browser
  2. Fill in: name, email, company, country
  3. Open the email FairCom sends and download:
       Windows x64 (.msi recommended)
  4. Come back here and tell me where you saved the file

Form URL:      $FormUrl
All downloads: $DownloadsUrl

"@

$answer = Read-Host "Press [Enter] to open the form in your browser, or [s] to skip"
if ($answer.ToLower() -ne "s") {
    Start-Process $FormUrl
}

Write-Host ""
$archive = Read-Host "Full path to the downloaded archive (.msi or .zip)"
$archive = [Environment]::ExpandEnvironmentVariables($archive)

if (-not (Test-Path $archive)) {
    Write-Error "File not found: $archive"
    exit 1
}

if (-not (Test-Path $Target)) {
    New-Item -ItemType Directory -Path $Target | Out-Null
}

$ext = [IO.Path]::GetExtension($archive).ToLower()
switch ($ext) {
    ".msi" {
        Write-Host "Running MSI installer (you may see UAC prompts) ..."
        Start-Process msiexec.exe -ArgumentList "/i `"$archive`" INSTALLLOCATION=`"$Target`" /qb" -Wait
    }
    ".zip" {
        Write-Host "Extracting ZIP to $Target ..."
        Expand-Archive -Path $archive -DestinationPath $Target -Force
    }
    default {
        Write-Error "Unsupported archive format: $ext (expected .msi or .zip)"
        exit 1
    }
}

[Environment]::SetEnvironmentVariable("FAIRCOM_HOME", $Target, "User")
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$binPath = "$Target\bin"
if ($currentPath -notlike "*$binPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$binPath", "User")
}

Write-Host @"

================================================================
  Installation complete
================================================================

Next steps:
  1. Open a NEW PowerShell window (so env vars are picked up)
  2. Configure ctsrvr.cfg:   see docs\setup-windows.md
  3. Configure ODBC DSN:     ODBC Data Sources (64-bit)
  4. Validate:               dtcat doctor

"@
