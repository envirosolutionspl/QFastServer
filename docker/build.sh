#!/usr/bin/env bash
# Builds the QFastServer image for one QGIS Server version of the compatibility table.
#
# Usage: docker/build.sh <QGIS Server version> [options passed to docker build]
#   e.g. docker/build.sh 3.44.15 --build-arg JOBS=8
# The values which depend on the version (upstream tag, patch series, build and base images)
# are read from versions/<QGIS Server version>.env.
set -euo pipefail
HERE=$(cd "$(dirname "$0")/.." && pwd)
available=$(cd "$HERE/versions" && ls -- *.env | sed 's/\.env$//' | tr '\n' ' ')
VERSION=${1:?QGIS Server version, one of: $available}
shift
[ -f "$HERE/versions/$VERSION.env" ] || { echo "No QFastServer for QGIS Server $VERSION. Available: $available"; exit 1; }

args=()
while IFS='=' read -r key value; do
  [[ $key =~ ^[A-Z_]+$ ]] && args+=(--build-arg "$key=$value")
done <"$HERE/versions/$VERSION.env"

docker build -f "$HERE/docker/Dockerfile" "${args[@]}" -t "qfastserver:$VERSION" "$@" "$HERE"
