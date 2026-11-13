#!/usr/bin/env bash
# Take off, hover and land on the running simulator, then say PASS or FAIL.
#
#   docker compose -f docker-compose.dev.yml up -d
#   tools/hover_test.sh
#
# Checks: PX4 passes preflight, the drone climbs to PX4's takeoff height (2.5 m), PX4's own height agrees with
# Gazebo's, and it lands and disarms.
set -uo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
drone="${DRONE:-$(grep -s '^DRONE=' "$here/.env" | cut -d= -f2)}"
drone="${drone:-huntsman}"

px4() { docker exec -w /px4/build/px4_sitl_default drone_px4 timeout 10 ./bin/px4-"$1" "${@:2}" 2>&1; }
px4_height() { px4 listener vehicle_local_position -n 1 | awk '$1=="z:"{printf "%.2f", -$2}'; }
gz_height() { docker exec drone_sim_dev timeout 10 gz model -m "${drone}_0" -p 2>/dev/null \
  | grep -A1 XYZ | tail -1 | tr -d '[]' | awk '{printf "%.2f", $3}'; }
near() { awk -v a="$1" -v b="$2" -v tol="$3" 'BEGIN{d=a-b; if(d<0)d=-d; exit !(d<=tol)}'; }
fail() { echo "FAIL: $1"; exit 1; }

echo "drone: $drone. Waiting for PX4 (up to 2 minutes)..."
for _ in $(seq 24); do
  px4 commander check | grep -q "Preflight check: OK" && ready=1 && break
  sleep 5
done
[ "${ready:-}" ] || fail "PX4 never passed preflight. Look at: docker logs drone_px4"

rest="$(gz_height)"
[ "$rest" ] || fail "Gazebo has no model called ${drone}_0. Is DRONE the same as in .env?"
px4_rest="$(px4_height)"
px4 commander takeoff | grep -v '^$'
# Without a GPU the simulator runs slower than real time, so wait for the climb, not for the clock.
for _ in $(seq 24); do
  sleep 5
  climbed="$(awk -v a="$(gz_height)" -v b="$rest" 'BEGIN{printf "%.2f", a-b}')"
  near "$climbed" 2.5 0.6 && break
done
sleep 5
climbed="$(awk -v a="$(gz_height)" -v b="$rest" 'BEGIN{printf "%.2f", a-b}')"
px4_climbed="$(awk -v a="$(px4_height)" -v b="$px4_rest" 'BEGIN{printf "%.2f", a-b}')"
echo "hover: Gazebo says ${climbed} m up, PX4 says ${px4_climbed} m"
px4 listener actuator_motors -n 1 | grep "control:" | sed 's/, nan.*/]/; s/^ */motors: /'
px4 commander land | grep -v '^$'

near "$climbed" 2.5 1.0 || fail "expected about 2.5 m, Gazebo has it at ${climbed} m"
near "$climbed" "$px4_climbed" 1.0 || fail "PX4 and Gazebo disagree on height by more than 1 m"

for _ in $(seq 12); do
  sleep 5
  px4 listener vehicle_status -n 1 | grep -q "arming_state: 1" && { echo "landed and disarmed"; echo PASS; exit 0; }
done
fail "still armed a minute after the land command"
