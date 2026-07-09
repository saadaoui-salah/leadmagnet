# generate-shorts-audio.ps1
# Generates TTS audio for YouTube Shorts scenes using Piper-TTS.
#
# Prerequisites:
#   1. Piper binary on PATH or set $env:PIPER_PATH
#   2. Voice model at voices/en_US-lessac-medium.onnx or set $env:PIPER_VOICE_PATH
#
# Usage:
#   .\scripts\generate-shorts-audio.ps1 [-Mode "all"|"winner-vs-runner-up"|"winner-vs-loser"]

param(
    [ValidateSet("all", "winner-vs-runner-up", "winner-vs-loser")]
    [string]$Mode = "all"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$SrcData = Join-Path $Root "src" "data"
$AudioDir = Join-Path $Root "public" "audio" "shorts"

$PiperPath = if ($env:PIPER_PATH) { $env:PIPER_PATH } else { "piper" }
$VoicePath = if ($env:PIPER_VOICE_PATH) { $env:PIPER_VOICE_PATH } else { Join-Path $Root "voices" "en_US-lessac-medium.onnx" }

if (!(Test-Path $AudioDir)) {
    New-Item -ItemType Directory -Path $AudioDir -Force | Out-Null
}

$CopyFile = Join-Path $SrcData "generatedShortsCopy.json"
if (!(Test-Path $CopyFile)) {
    Write-Error "[ERROR] Narration file not found: $CopyFile"
    Write-Error "        Run: python scripts/generate_market_copy.py first"
    exit 1
}

$CopyData = Get-Content $CopyFile -Raw | ConvertFrom-Json

$Modes = @("winner-vs-runner-up", "winner-vs-loser")
if ($Mode -ne "all") { $Modes = @($Mode) }

foreach ($m in $Modes) {
    $key = if ($m -eq "winner-vs-runner-up") { "runnerUp" } else { "winnerVsLoser" }
    $scenes = $CopyData.shortsCopy.$key.scenes
    if (-not $scenes -or $scenes.Count -eq 0) {
        Write-Warning "[SKIP] No narration scenes for mode: $m"
        continue
    }

    Write-Host "`n=== Generating audio for: $m ==="

    # Check if Piper is available
    $piperAvailable = $false
    try {
        $null = Get-Command $PiperPath -ErrorAction Stop
        if (Test-Path $VoicePath) {
            $piperAvailable = $true
        } else {
            Write-Host "  [WARN] Voice model not found: $VoicePath"
        }
    } catch {
        Write-Host "  [INFO] Piper not found. Generating silent WAVs as fallback."
    }

    $narration = @()
    for ($i = 0; $i -lt 7; $i++) {
        $scene = if ($scenes[$i]) { $scenes[$i] } else { @{ text = "" } }
        $outFile = Join-Path $AudioDir ("scene-{0:D2}.wav" -f ($i + 1))
        $label = @("hook", "zip-a", "zip-b", "head-to-head", "key-difference", "takeaway", "cta")[$i]

        Write-Host "  [$($i + 1)/7] $label"

        if ($piperAvailable -and $scene.text) {
            try {
                $scene.text | & $PiperPath --model $VoicePath --output-raw -q --output-raw-file $outFile 2>$null
                if (-not (Test-Path $outFile)) {
                    throw "piper output missing"
                }
            } catch {
                Write-Host "  [FALLBACK] Piper failed. Using silent WAV."
                $piperAvailable = $false
            }
        }

        if (-not $piperAvailable) {
            # Generate 3-second silent WAV
            $bytes = [byte[]]::new(44)
            [System.Text.Encoding]::ASCII.GetBytes("RIFF").CopyTo($bytes, 0)
            $bytes[36..39] = [System.Text.Encoding]::ASCII.GetBytes("data")
            [System.IO.File]::WriteAllBytes($outFile, $bytes)
        }

        $narration += @{
            text = if ($scene.text) { $scene.text } else { "" }
            audioFile = "scene-{0:D2}.wav" -f ($i + 1)
        }
    }

    # Save narration JSON
    $narrationFile = Join-Path $SrcData "generatedShortsNarration.json"
    if (Test-Path $narrationFile) {
        $existing = Get-Content $narrationFile -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json
    } else {
        $existing = @{}
    }
    $existing | Add-Member -NotePropertyName $key -NotePropertyValue $narration -Force
    $existing | ConvertTo-Json -Depth 5 | Set-Content $narrationFile
    Write-Host "  [SAVED] Narration JSON: $narrationFile"
}

Write-Host "`n[Done] Audio generation complete."
