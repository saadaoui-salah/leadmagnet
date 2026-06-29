$ErrorActionPreference = "Stop"

$slideDuration = 90
$slideCount = 10
$outputDir = "out\instagram"
$remotion = Join-Path (Get-Location) "node_modules\.bin\remotion.cmd"

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

for ($index = 0; $index -lt $slideCount; $index++) {
  $frame = $index * $slideDuration
  $slideNumber = ($index + 1).ToString("00")
  $output = Join-Path $outputDir "instagram-$slideNumber.png"

  & $remotion still InstagramZillowCarousel --frame $frame --output $output
}
