#!/usr/bin/env bash
# Checks that the patch series applied to its upstream base gives exactly the tree recorded in SOURCE.
# Works in a temporary index of the fork clone: no checkout, nothing is changed in the clone.
#
# Usage: tools/check-patches.sh <path to a clone of qgis/QGIS> <series name> [other base ref]
# With [other base ref] it only reports whether the series applies to that ref (e.g. a newer upstream tag).
set -euo pipefail
FORK=${1:?path to a QGIS clone}
SERIES=${2:?series name}
HERE=$(cd "$(dirname "$0")/.." && pwd)
DIR=$HERE/patches/$SERIES
BASE=${3:-$(awk '/^base:/{print $2}' "$DIR/SOURCE")}
EXPECTED=$(awk '/^tree:/{print $2}' "$DIR/SOURCE")

export GIT_INDEX_FILE
GIT_INDEX_FILE=$(mktemp)
trap 'rm -f "$GIT_INDEX_FILE"' EXIT
git -C "$FORK" read-tree "$BASE"
while read -r patch; do
  git -C "$FORK" apply --cached "$DIR/$patch" || { echo "FAILED on $BASE: $patch"; exit 1; }
done <"$DIR/series"
TREE=$(git -C "$FORK" write-tree)
if [ $# -ge 3 ]; then
  echo "series $SERIES applies to $BASE ($(wc -l <"$DIR/series") patches), tree $TREE"
elif [ "$TREE" = "$EXPECTED" ]; then
  echo "series $SERIES: $(wc -l <"$DIR/series") patches, tree matches the fork branch ($TREE)"
else
  echo "series $SERIES: tree $TREE differs from the fork branch ($EXPECTED)"; exit 1
fi
