#!/usr/bin/env bash
# encode.sh FRAMES_DIR OUT_DIR: every 10 s turn finished PNG frames of each camera into mp4 chunks and delete them,
# so a long run doesn't fill the disk. touch FRAMES_DIR/STOP to flush, then one <camera>.mp4 per camera lands in OUT_DIR.
root=$(realpath "$1"); out=$2; mkdir -p "$out"
chunk() {  # chunk CAMDIR KEEP
  local cam=$1 keep=$2 fps=24
  [[ $(basename "$cam") == wide ]] && fps=12
  [[ $(basename "$cam") == onboard ]] && fps=30
  mapfile -t f < <(find "$cam" -maxdepth 1 -name '*.png' | sort -V | head -n -"$keep")
  (( ${#f[@]} < 24 )) && [[ $keep != 0 ]] && return
  (( ${#f[@]} == 0 )) && return
  local n list; n=$(find "$cam" -maxdepth 1 -name 'chunk_*.mp4' | wc -l); list=$(mktemp)
  for x in "${f[@]}"; do printf "file '%s'\nduration %s\n" "$x" "$(awk "BEGIN{print 1/$fps}")"; done > "$list"
  ffmpeg -v error -y -f concat -safe 0 -i "$list" -vf "fps=$fps,format=yuv420p" -c:v libx264 -preset veryfast -crf 15 \
    "$cam/chunk_$(printf %05d "$n").mp4" && rm -f "${f[@]}"
  rm -f "$list"
}
while :; do
  stop=0; [ -f "$root/STOP" ] && stop=1
  for cam in "$root"/*/; do chunk "${cam%/}" $(( stop ? 0 : 12 )); done
  (( stop )) && break
  sleep 10
done
for cam in "$root"/*/; do
  ls "$cam"chunk_*.mp4 >/dev/null 2>&1 || continue
  ls "$cam"chunk_*.mp4 | sort | sed "s/.*/file '&'/" > "$cam/all.txt"
  ffmpeg -v error -y -f concat -safe 0 -i "$cam/all.txt" -c copy "$out/$(basename "$cam").mp4"
done
