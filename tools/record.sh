#!/usr/bin/env bash
# Fly scenarios and record them as videos with a minimap (obstacle map, path, start A, goal B, state).
#
#   tools/record.sh DRONE VIEWS SCENARIO [SCENARIO ...]
#   tools/record.sh huntsman chase,onboard,depth,lidar-chase avoid
#   tools/record.sh widow chase,pad,tree takeover a_to_b      (both in one sim, one after the other)
#
# DRONE     huntsman or widow
# VIEWS     comma list of:
#             chase    camera following the drone          onboard  what the drone's camera sees
#             pad, tree, crate, wide                       fixed cameras at those spots in the field
#             depth    the camera's depth image, coloured by distance
#             lidar-chase, lidar-top, lidar-pad, lidar-tree, lidar-crate, lidar-wide
#                      the LiDAR point cloud from that angle (Huntsman only)
# SCENARIO  any name from Autonomous-Systems/scripts/sim_scenarios.sh (a_to_b, avoid, abort, hold, takeover,
#           bad_landing, timeout, battery, perception_crash, autonomy_crash, popup)
#
# Out: recordings/<date>-<drone>-<scenarios>/ with one .mp4 per view, log.txt (PASS/FAIL) and data/ (raw).
# Needs Docker and ffmpeg; the views are drawn with uv (https://docs.astral.sh/uv), here or on another machine. Linux with an NVIDIA GPU runs in real time; anything
# else works but slowly, since the camera, depth and LiDAR are rendered in software.
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd); sim=$(dirname "$here")
autonomy=${AUTONOMY_ROOT:-$(cd "$sim/../Autonomous-Systems" 2>/dev/null && pwd)}
[ $# -ge 3 ] || { sed -n 2,20p "$0"; exit 1; }
[ -d "$autonomy" ] || { echo "Autonomous-Systems not found next to Simulation; set AUTONOMY_ROOT"; exit 1; }
drone=$1 views=$2; shift 2
for tool in docker ffmpeg; do command -v $tool >/dev/null || { echo "needs $tool"; exit 1; }; done

work=$sim/.record
out=$sim/recordings/$(date +%Y-%m-%d-%H%M)-$drone-$(IFS=+; echo "$*")
mkdir -p "$out" "$work"
cams=$(tr ',' '\n' <<<"$views" | grep -xE 'chase|onboard|pad|tree|crate|wide' | paste -sd, -)
python3 "$here/record/scene.py" "$work/sim" "${cams:-none}" || exit 1
rm -rf "$work/frames" "$work/videos"; mkdir -p "$work/frames" "$work/videos"
for c in ${cams//,/ }; do mkdir -p "$work/frames/$c"; done
chmod -R 777 "$work/frames"
printf 'services:\n  drone-dev:\n    volumes:\n      - %s:/film\n' "$work/frames" > "$work/frames.yml"
"$here/record/encode.sh" "$work/frames" "$work/videos" > "$work/encode.log" 2>&1 &
enc=$!

export AUTONOMY_ROOT=$autonomy SIMULATION_ROOT=$work/sim DRONE=$drone HEADLESS=1
C=(docker compose --project-directory "$work/sim" -f "$work/sim/docker-compose.dev.yml"
   -f "$autonomy/integration/compose.autonomy.yml" -f "$work/frames.yml")
docker info 2>/dev/null | grep -q "Runtimes:.*nvidia" && C+=(-f "$work/sim/docker-compose.gpu.yml")
"${C[@]}" down >/dev/null 2>&1; "${C[@]}" up -d 2>&1 | tail -1
for _ in $(seq 100); do docker exec lidron_autonomy test -f /autonomy/install/setup.bash 2>/dev/null && break; sleep 3; done
docker cp "$here/record/rec.py" lidron_autonomy:/tmp/rec.py
docker exec -d lidron_autonomy bash -c "source /autonomy/install/setup.bash && exec python3 /tmp/rec.py /tmp/rec"

"$autonomy/scripts/sim_scenarios.sh" "$@" 2>&1 | tee "$out/log.txt"
rc=${PIPESTATUS[0]}

docker exec lidron_autonomy pkill -TERM -f "[r]ec.py"; sleep 2
docker cp lidron_autonomy:/tmp/rec "$out/data"
"${C[@]}" down >/dev/null 2>&1
touch "$work/frames/STOP"; wait $enc
mv "$work"/videos/*.mp4 "$out/data/" 2>/dev/null
render=(python "$here/record/render.py" "$out/data" "$out/data" "$out" "$drone" "$views")
if command -v uv >/dev/null; then uv run -q --with numpy --with matplotlib "${render[@]}"; echo "videos in $out"
else echo "no uv here: copy $out to a machine with uv and run: uv run --with numpy --with matplotlib ${render[*]}"; fi
exit $rc
