import { execFileSync } from "node:child_process";
import { mkdirSync } from "node:fs";
import { join } from "node:path";

const slideDuration = 120;
const slideCount = 10;
const outputDir = "out/linkedin";

mkdirSync(outputDir, { recursive: true });

for (let index = 0; index < slideCount; index += 1) {
  const frame = index * slideDuration;
  const output = join(outputDir, `slide-${String(index + 1).padStart(2, "0")}.png`);

  const remotionBinary = join(process.cwd(), "node_modules", ".bin", process.platform === "win32" ? "remotion.cmd" : "remotion");
  const args = ["still", "ZillowIntelligenceCarousel", "--frame", String(frame), "--output", output];

  if (process.platform === "win32") {
    execFileSync("cmd.exe", ["/d", "/s", "/c", `call "${remotionBinary}" ${args.map((arg) => `"${arg}"`).join(" ")}`], {
      stdio: "inherit"
    });
  } else {
    execFileSync(remotionBinary, args, {
      stdio: "inherit"
    });
  }
}
