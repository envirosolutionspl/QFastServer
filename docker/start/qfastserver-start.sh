#!/bin/bash
# Start of the QFastServer image.
#
# Without the variables below it does nothing but run the start script of the official image,
# which is left unchanged: the container then starts exactly as the official one.
#
#   QFASTSERVER_WORKERS  number of QGIS Server processes answering on the FastCGI socket.
#                        Default 1, as the official image. Each process serves one request at a
#                        time and keeps its own copy of the loaded projects.
#   QFASTSERVER_GZIP     "true" or "1": nginx compresses the XML, JSON and text responses for the
#                        clients which accept gzip. Default: not compressed, as the official image.

OFFICIAL=/usr/local/bin/start-xvfb-nginx.sh
LIB=/usr/local/lib/qfastserver

typeset -l gzip=${QFASTSERVER_GZIP:-}
# qgis.d is included in the server block of the nginx configuration of the official image
rm -f /etc/nginx/qgis.d/qfastserver-gzip.conf
if [ "$gzip" = true ] || [ "$gzip" = 1 ]; then
    cp "$LIB/gzip.conf" /etc/nginx/qgis.d/qfastserver-gzip.conf
fi

workers=${QFASTSERVER_WORKERS:-1}
if ! [[ $workers =~ ^[1-9][0-9]*$ ]]; then
    echo "WARNING: Invalid QFASTSERVER_WORKERS '$workers'. Must be a number, 1 or more. One process is started."
    workers=1
fi
if [ "$workers" -gt 1 ]; then
    # The official script starts QGIS Server with spawn-fcgi and looks for its process with pidof.
    # With the two commands of $LIB in front of the system ones, it starts and waits for
    # the supervisor of the workers instead, and everything else it does stays the same.
    export QFASTSERVER_WORKERS=$workers
    export PATH=$LIB:$PATH
fi
exec "$OFFICIAL"
