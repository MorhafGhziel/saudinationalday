#!/usr/bin/env bash
# Renders every opening-world output. CYCLES_CONCURRENT_STATES_FACTOR keeps GPU working buffers small:
# this PC has no page file, so large reservations fail even with free VRAM.
export CYCLES_CONCURRENT_STATES_FACTOR=0.2
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
cd "$(dirname "$0")/../.."
for a in land port; do
  "$B" --factory-startup --background --python tools/blender/opening.py -- mode=all aspect=$a 2>&1 | grep -E "RENDERED|RuntimeError|Error:"
done
echo ALL-DONE
