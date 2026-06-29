$ErrorActionPreference = "Stop"

$slideDuration = 120
$slideCount = 10
$outputDir = "out\linkedin"
$remotion = Join-Path (Get-Location) "node_modules\.bin\remotion.cmd"

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

# Export individual slides as PNGs
for ($index = 0; $index -lt $slideCount; $index++) {
  $frame = $index * $slideDuration
  $slideNumber = ($index + 1).ToString("00")
  $output = Join-Path $outputDir "slide-$slideNumber.png"

  & $remotion still ZillowIntelligenceCarousel --frame $frame --output $output
}

# Combine into PDF (PNGs stay in the same folder)
node -e "
const { PDFDocument } = require('pdf-lib');
const fs = require('fs');
const path = require('path');

async function createPDF() {
  const pdf = await PDFDocument.create();
  const outputDir = '$($outputDir -replace '\\', '/')';
  const outputFile = path.join(outputDir, 'LinkedIn-Carousel.pdf');

  for (let i = 1; i <= $slideCount; i++) {
    const num = String(i).padStart(2, '0');
    const imgPath = path.join(outputDir, 'slide-' + num + '.png');
    const imgBytes = fs.readFileSync(imgPath);
    const img = await pdf.embedPng(imgBytes);
    const page = pdf.addPage([img.width, img.height]);
    page.drawImage(img, { x: 0, y: 0, width: img.width, height: img.height });
  }

  const pdfBytes = await pdf.save();
  fs.writeFileSync(outputFile, pdfBytes);
  console.log('PDF saved to: ' + outputFile);
}

createPDF().catch(console.error);
"
