#!/usr/bin/env bash
# Renders the walk frames (resumable) and encodes them to H.264 MP4, which every phone decodes in hardware.
export CYCLES_CONCURRENT_STATES_FACTOR=0.2
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
cd "$(dirname "$0")/../.."
mkdir -p public/worlds/opening
for a in land port; do
  "$B" --factory-startup --background --python tools/blender/opening.py -- mode=walk aspect=$a 2>&1 | grep -E "RuntimeError|Error:" | head -3
  ffmpeg -y -loglevel error -framerate 30 -i renders/opening/walk/$a-%03d.png -c:v libx264 -profile:v high -pix_fmt yuv420p -crf 21 -preset slow -movflags +faststart -an public/worlds/opening/walk-$a.mp4
  ls -la public/worlds/opening/walk-$a.mp4
done
echo WALK-DONE
