#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tour_file="$project_dir/site/product-tour.html"
site_file="$project_dir/site/index.html"
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

chrome_profile_dir="$(mktemp -d "${TMPDIR:-/tmp}/voice-transcriber-render.XXXXXX")"
cleanup_profile() {
  case "$chrome_profile_dir" in
    */voice-transcriber-render.*) rm -rf -- "$chrome_profile_dir" ;;
  esac
}
trap cleanup_profile EXIT

mkdir -p "$asset_dir"
tour_url="file://$tour_file"

capture_page() {
  local url="$1"
  local output="$2"
  local width="$3"
  local height="$4"
  local temp_output="$chrome_profile_dir/$(basename "$output")"
  local capture_pid
  local current_size=0
  local previous_size=0
  local stable_rounds=0

  "$chrome_binary" \
    --headless=new \
    --hide-scrollbars \
    --disable-gpu \
    --disable-extensions \
    --disable-component-update \
    --disable-background-networking \
    --no-first-run \
    --no-default-browser-check \
    --user-data-dir="$chrome_profile_dir" \
    --allow-file-access-from-files \
    --force-device-scale-factor=1 \
    --window-size="$width,$height" \
    --screenshot="$temp_output" \
    "$url" >/dev/null 2>&1 &
  capture_pid=$!

  for _ in {1..300}; do
    if [[ -s "$temp_output" ]]; then
      current_size="$(wc -c < "$temp_output")"
      if [[ "$current_size" == "$previous_size" ]]; then
        ((stable_rounds += 1))
      else
        stable_rounds=0
        previous_size="$current_size"
      fi
      if ((stable_rounds >= 3)); then
        kill -9 "$capture_pid" 2>/dev/null || true
        wait "$capture_pid" 2>/dev/null || true
        mv -f "$temp_output" "$output"
        return 0
      fi
    fi
    sleep 0.1
  done

  kill -9 "$capture_pid" 2>/dev/null || true
  wait "$capture_pid" 2>/dev/null || true
  echo "Timed out while rendering $url" >&2
  return 1
}

render_state() {
  local state="$1"
  local output="$2"
  capture_page "$tour_url?state=$state" "$output" 1200 750
}

render_state ready "$asset_dir/demo-01-ready.png"
render_state active "$asset_dir/demo-02-active.png"
render_state complete "$asset_dir/demo-03-complete.png"

capture_page "file://$site_file" "$asset_dir/social-preview.png" 1280 640

ffmpeg -loglevel error -y \
  -framerate 0.5 \
  -pattern_type glob \
  -i "$asset_dir/demo-*.png" \
  -vf "fps=12,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=96[p];[s1][p]paletteuse=dither=bayer" \
  -loop 0 \
  "$asset_dir/voice-transcriber-tour.gif"

echo "Rendered product-tour assets in $asset_dir"
