#!/bin/sh
set -eu
nginx -t
nginx
trap 'nginx -s quit; exit 0' TERM INT
while sleep 3600 & wait $!; do
    nginx -t && nginx -s reload
done
