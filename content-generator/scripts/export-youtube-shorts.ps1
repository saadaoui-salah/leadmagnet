# export-youtube-shorts.ps1
# Renders both YouTube Shorts compositions to MP4.

param()

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$OutputDir = Join-Path $Root "out" "youtube-shorts"

if (!(Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$Compositions = @(
    @{
        Id    = "YouTubeShortsWinnerVsRunnerUp"
        Out   = Join-Path $OutputDir "short-winner-vs-runner-up.mp4"
    },
    @{
        Id    = "YouTubeShortsWinnerVsLoser"
        Out   = Join-Path $OutputDir "short-winner-vs-loser.mp4"
    }
)

foreach ($comp in $Compositions) {
    Write-Host "`n=== Rendering: $($comp.Id) ==="
    Write-Host "  Output: $($comp.Out)"

    npx remotion render $comp.Id --output=$($comp.Out) --codec=h264 --crf=18 --preset=medium

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [DONE] $($comp.Id)"
    } else {
        Write-Error "  [FAIL] $($comp.Id)"
        exit 1
    }
}

Write-Host "`n[Done] All Shorts rendered."
