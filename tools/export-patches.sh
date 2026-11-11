#!/usr/bin/env bash
# Regenerates the patch series of one upstream line from the development fork.
#
# The fork (a clone of qgis/QGIS with our branch) is the only place where the code is edited:
# the files under patches/ are generated and must not be changed by hand.
#
# Usage: tools/export-patches.sh <path to the fork clone> <base ref> <branch> <series name>
#   e.g. tools/export-patches.sh ../QGIS final-3_44_15 fast-server-3_44 3.44
# <base ref> is the upstream commit or tag the branch is based on (the branch has to contain it).
set -euo pipefail
FORK=${1:?path to the fork clone}
BASE=${2:?upstream base ref}
BRANCH=${3:?branch of the fork}
SERIES=${4:?series name, e.g. 3.44}
HERE=$(cd "$(dirname "$0")/.." && pwd)
OUT=$HERE/patches/$SERIES

git -C "$FORK" merge-base --is-ancestor "$BASE" "$BRANCH" || { echo "$BRANCH is not based on $BASE"; exit 1; }

rm -rf "$OUT" && mkdir -p "$OUT"
git -C "$FORK" format-patch --quiet --no-signature --no-stat -o "$OUT" "$BASE..$BRANCH"
(cd "$OUT" && ls -- *.patch >series)
{
  echo "upstream: https://github.com/qgis/QGIS"
  echo "base: $(git -C "$FORK" rev-parse "$BASE^{commit}") ($(git -C "$FORK" describe --tags "$BASE"))"
  echo "branch: $BRANCH"
  echo "head: $(git -C "$FORK" rev-parse "$BRANCH^{commit}")"
  echo "tree: $(git -C "$FORK" rev-parse "$BRANCH^{tree}")"
} >"$OUT/SOURCE"

"$HERE/tools/check-patches.sh" "$FORK" "$SERIES"
