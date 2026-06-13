$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

if (-not $env:NEXT_PUBLIC_API_URL) {
  $env:NEXT_PUBLIC_API_URL = "http://localhost:8000"
}

if (-not $env:INTERNAL_API_URL) {
  $env:INTERNAL_API_URL = "http://localhost:8000"
}

& "C:\Program Files\nodejs\node.exe" "$PSScriptRoot\node_modules\next\dist\bin\next" dev --hostname 0.0.0.0

