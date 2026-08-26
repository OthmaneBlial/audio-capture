#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tour_file="$project_dir/site/product-tour.html"
asset_dir="$project_dir/site/assets"

if [[ ! -f "$tour_file" ]]; then
  echo "Missing product tour source: $tour_file" >&2
  exit 1
fi

chrome_binary="${CHROME_BINARY:-}"
if [[ -z "$chrome_binary" ]]; then
  for candidate in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "$(command -v google-chrome || true)" \
    "$(command -v chromium || true)"; do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
      chrome_binary="$candidate"
      break
    fi
  done
fi

if [[ -z "$chrome_binary" || ! -x "$chrome_binary" ]]; then
  echo "Chrome or Chromium is required to render the product tour." >&2
  exit 1
fi
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is required to assemble the animated product tour." >&2
  exit 1
fi

mkdir -p "$asset_dir"
tour_url="file://$tour_file"

render_state() {
  local state="$1"
  local output="$2"
  "$chrome_binary" \
    --headless=new \
    --hide-scrollbars \
    --disable-gpu \
    --allow-file-access-from-files \
    --window-size=1200,750 \
    --screenshot="$output" \
    "$tour_url?state=$state" >/dev/null 2>&1
}

render_state ready "$asset_dir/demo-01-ready.png"
render_state active "$asset_dir/demo-02-active.png"
render_state complete "$asset_dir/demo-03-complete.png"

ffmpeg -loglevel error -y \
  -framerate 0.5 \
  -pattern_type glob \
  -i "$asset_dir/demo-*.png" \
  -vf "fps=12,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=96[p];[s1][p]paletteuse=dither=bayer" \
  -loop 0 \
  "$asset_dir/voice-transcriber-tour.gif"

echo "Rendered product-tour assets in $asset_dir"
