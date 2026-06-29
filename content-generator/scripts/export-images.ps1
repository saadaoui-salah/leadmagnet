$ErrorActionPreference = "Stop"

$slideDuration = 120
$slideCount = 10
$outputDir = "out\linkedin"
$remotion = Join-Path (Get-Location) "node_modules\.bin\remotion.cmd"

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

for ($index = 0; $index -lt $slideCount; $index++) {
  $frame = $index * $slideDuration
  $slideNumber = ($index + 1).ToString("00")
  $output = Join-Path $outputDir "slide-$slideNumber.png"

  & $remotion still ZillowIntelligenceCarousel --frame $frame --output $output
}
