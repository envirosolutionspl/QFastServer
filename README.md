# QFastServer

[![QGIS Server 3.44 LTR](https://img.shields.io/badge/QGIS%20Server-3.44%20LTR-589632)](#compatibility)
[![QGIS Server 4.4](https://img.shields.io/badge/QGIS%20Server-4.4-589632)](#compatibility)
[![Release](https://img.shields.io/github/v/release/envirosolutionspl/QFastServer)](https://github.com/envirosolutionspl/QFastServer/releases)
[![License: GPL v2 or later](https://img.shields.io/badge/license-GPL--2.0--or--later-blue)](LICENSE)

Performance patches for [QGIS Server](https://qgis.org): the same requests, the same responses, less time.

QFastServer is not another map server. It is a small series of patches on top of a specific QGIS Server
release. Configuration, projects, Python server plugins and client stacks (Lizmap, QWC2 and others) stay as
they are; the responses are the ones the unpatched server gives.

QFastServer is an independent project. It is not affiliated with or endorsed by QGIS.org. QGIS is a trademark
of QGIS.org.

## Compatibility

Every version of QFastServer is made for exactly one QGIS Server release and is only checked against it.
Use the row of the QGIS Server version you run today.

| QGIS Server | Values for the build | Patch series | State |
| --- | --- | --- | --- |
| 3.44.16 (LTR) | [versions/3.44.16.env](versions/3.44.16.env) | [3.44](patches/3.44), 15 patches | released: [3.44.16-qfs.1](https://github.com/envirosolutionspl/QFastServer/releases/tag/3.44.16-qfs.1) |
| 3.44.15 | [versions/3.44.15.env](versions/3.44.15.env) | [3.44](patches/3.44), 15 patches | released: [3.44.15-qfs.2](https://github.com/envirosolutionspl/QFastServer/releases/tag/3.44.15-qfs.2) |
| 4.4.0 | [versions/4.4.0.env](versions/4.4.0.env) | [4.4](patches/4.4), 16 patches | released: [4.4.0-qfs.2](https://github.com/envirosolutionspl/QFastServer/releases/tag/4.4.0-qfs.2) |
| any other version | — | — | not supported |

Each image is built from the upstream tag of its version with the patches applied. The upstream tests were
run on the patched tags `final-3_44_16` and `final-4_4_0` ([SOURCE](patches/3.44/SOURCE),
[SOURCE](patches/4.4/SOURCE)); for 3.44.15 they were run on the branch `release-3_44` 28 commits after its tag.
4.4 is built with Qt 6. What was verified for a release is in its notes.

A release is named `<QGIS Server version>-qfs.<n>`, for example `3.44.15-qfs.1`: the QGIS Server release it
is built from and compatible with, then the number of the QFastServer release for it. The notes of every
release state the upstream tag and commit, the number of patches and the results of the tests and of the
comparison with the unpatched server ([RELEASING.md](RELEASING.md)).

How the compatibility is checked:

- the upstream test suites for the server, rasters, projects and vector layers pass on the patched build;
- 59 kinds of requests (WMS GetMap in every output format, GetFeatureInfo, GetLegendGraphic, GetPrint, WFS,
  OGC API Features, WMTS, WCS, error responses) are sent to both builds and the responses compared: images
  pixel by pixel, XML after canonicalisation, everything else byte by byte
  ([tests/equivalence](tests/equivalence));
- 68 raster renderings (reprojected and not, inside and across the raster extent) give the same pixels.

Some of the 59 requests give different responses from one process to the next in upstream itself (8 bits PNG,
GetContext, DXF, PDF, DescribeFeatureType, a cascaded WMS layer as PNG and as JPEG), so they cannot be
compared between builds. For 8 bits PNG the equality is tested at the function level instead.

## Installation

### Docker

The QFastServer image is the official `qgis/qgis-server` image of the same version with the QGIS binaries
replaced by a build of the same upstream release with the patches applied. The build uses the options of the
upstream Debian packaging, so the features and the file layout are the ones of the official packages.

Pull the image of your QGIS Server version (one of the [compatibility table](#compatibility)):

```bash
docker pull ghcr.io/envirosolutionspl/qfastserver:<QGIS Server version>
```

`<QGIS Server version>` is the latest QFastServer release for that version; a tag of the form
`<QGIS Server version>-qfs.<n>` pins one release.

Use the image exactly as the official image of that version: same entry point, ports, volumes and environment
variables ([QGIS Server documentation](https://docs.qgis.org/latest/en/docs/server_manual/containerized_deployment.html)).
In an existing deployment only the image name changes:

```yaml
services:
  qgis-server:
    # image: qgis/qgis-server:<QGIS Server version>-noble   (4.4: -resolute)
    image: ghcr.io/envirosolutionspl/qfastserver:<QGIS Server version>
```

#### Options of the image

Two settings exist only in this image. Both are off by default, and without them the container is started
by the unchanged start script of the official image.

| Variable | Effect | Default |
| --- | --- | --- |
| `QFASTSERVER_WORKERS` | Number of QGIS Server processes answering on the FastCGI socket of the container | 1, as the official image |
| `QFASTSERVER_GZIP` | `true`: nginx compresses the XML, JSON and text responses for the clients which accept gzip; images are sent as they are | not compressed, as the official image |

A QGIS Server process answers one request at a time, so with the default of one process the requests of a
container are answered one after the other, in the official image as well. `QFASTSERVER_WORKERS` starts
several processes in the container; the other way is to run several containers behind a load balancer. Every
process keeps its own copy of the loaded projects: plan the memory for that, and expect the first request for
a project to be slow once for each process. When one of the processes ends, the container stops, as it does
with a single process. `QGIS_SERVER_MAX_THREADS` is the number of rendering threads of each process.

In a container with 4 CPUs, 16 maps of 1920x1080 pixels requested at once were all answered after 0.79 s with
one process and after 0.28 s with `QFASTSERVER_WORKERS=4`.

With QGIS 4.4 (Qt 6) one more setting helps when several processes or containers share the CPUs: the variable
`QT_NO_GUI_THREADPOOL` of Qt. Qt 6 splits large fills of the map and print rendering into tasks for a pool of
threads in every process; with several processes that is mostly switching between threads. Set to any value,
even `0`, it turns the pool off (do not set it to keep the pool); the images are the same. The official image
does not pass it to QGIS Server, this one does (patch 0016 of the 4.4 series), and it is not set by default.
With 4 processes and 16 clients it gave 40% more GetPrint PNG per second, and GetPrint PNG with one client
took 74 ms instead of 90 ms; GetLegendGraphic PNG was 5 to 15% slower (under 0.5 ms), the other requests did
not change measurably ([4.4.0-qfs.2](releases/4.4.0-qfs.2.md)). A single large print on a machine with idle
CPUs can be slower without the pool (not measured).

Like the official image, this one declares no health check. A request to `/ows/` without parameters is
answered by QGIS Server itself with HTTP 200, so it can be used to check that the server answers and not only
nginx. With one process the check waits behind the request being rendered: allow for that in the timeout.

```yaml
    healthcheck:
      test: ["CMD", "wget", "-q", "-O", "/dev/null", "http://127.0.0.1/ows/"]
      interval: 30s
      timeout: 20s
```

To build the image yourself instead:

```bash
git clone https://github.com/envirosolutionspl/QFastServer
cd QFastServer
docker/build.sh <QGIS Server version>
```

The build compiles QGIS, which takes about an hour and about 1.5 GB of memory for each parallel compiler job
(8 by default, `--build-arg JOBS=<n>` to change it). The result is the image
`qfastserver:<QGIS Server version>`.

### From source

With the values of your QGIS Server version read from its file:

```bash
QGIS_TAG=$(sed -n 's/^QGIS_TAG=//p' versions/<QGIS Server version>.env)
SERIES=$(sed -n 's/^SERIES=//p' versions/<QGIS Server version>.env)
git clone --branch "$QGIS_TAG" --depth 1 https://github.com/qgis/QGIS
git -C QGIS apply "$PWD"/patches/"$SERIES"/*.patch
```

Then build QGIS Server as described in `INSTALL.md` of the QGIS source tree. The patched source tree is also
available in the development fork, <https://github.com/envirosolutionspl/QGIS>, on the branch named in
`patches/<series>/SOURCE`.

## What it changes

| Area | Change |
| --- | --- |
| Every request (FastCGI) | The FastCGI socket monitoring thread no longer adds up to 10 ms to each request |
| PNG output | 32 bits PNG written directly with libpng, row filter chosen from the image content; empty and nearly empty images are written compactly |
| 8 bits PNG | Faster search of the closest palette color, same result |
| Rasters | Faster cell loop of the raster projector, of the multiband renderer and of the GDAL provider |
| PostGIS | Connections are reused when the layers of a project are loaded in parallel |
| Trusted layer metadata | The extent stored in the project is kept, so the first GetCapabilities does not scan every layer |
| GetFeatureInfo (JSON) | One request to the data source for a layer instead of one for every feature |
| WFS GetFeature (GML) | The features are written without converting every character to check its encoding |
| DXF export | The group codes are formatted once |
| Fixes | The project cache size setting is applied; the opacity of vector tile layers is restored after a request |
| Qt 6 thread pool (optional, 4.4) | `QT_NO_GUI_THREADPOOL` takes effect in the FastCGI server: see [Options of the image](#options-of-the-image) |
| Image (optional) | Several QGIS Server processes in one container, gzip for the text responses: see [Options of the image](#options-of-the-image) |

Every patch is one commit with a test, written to the upstream coding standards. The list is in
[UPSTREAM.md](UPSTREAM.md), together with the reason why the patches are not proposed to QGIS: they were
written with the assistance of an AI coding agent, which the QGIS contribution policy does not allow.

## Measurements

The published image of QFastServer 3.44.15-qfs.1 against the official image `qgis/qgis-server:3.44.15-noble`,
MapServer 8.6 and GeoServer 3.0.2. Each server runs alone in a container with 4 CPUs and 4 GB of memory;
QGIS Server, QFastServer and MapServer with 4 FastCGI workers, GeoServer with 2 GB of heap; PostGIS 16 in
another container on the same host. QGIS Server and QFastServer are started the same way (the nginx front of
the image, parallel rendering off) with the same projects. Load generated with k6, 20 s for each cell after
a warm-up.

Both images start one QGIS Server process by default. For this comparison each was started with 4 processes
by a start script written for the benchmark; in the QFastServer image the same is done with
`QFASTSERVER_WORKERS=4` since the release 3.44.15-qfs.2. With one process the requests per second with 16
clients are lower than in the table.

Cells: **median response time with one client in ms / requests per second with 16 clients**.

| Request | QGIS Server | QFastServer | MapServer | GeoServer |
| --- | --- | --- | --- | --- |
| Tile 256x256, buildings, PNG | 10.9 / 317 | 4.1 / 463 | 6.0 / 322 | 5.8 / 340 |
| Tile 256x256, 3 vector layers, PNG | 10.9 / 226 | 6.9 / 278 | 8.6 / 227 | 6.7 / 208 |
| Map 1024x768, buildings, PNG | 28.5 / 73 | 16.6 / 99 | 26.7 / 93 | 16.0 / 51 |
| Map 1024x768, 3 vector layers, PNG | 44.6 / 44 | 26.4 / 60 | 37.2 / 54 | 24.6 / 35 |
| Map 1024x768, 4 vector layers with labels, PNG | 45.8 / 43 | 27.1 / 54 | 37.4 / 52 | 24.6 / 33 |
| Map 1024x768, 3 vector layers reprojected to EPSG:2180, PNG | 50.0 / 36 | 28.6 / 46 | 41.6 / 45 | 59.1 / 6.6 |
| Map 1024x768, 10 layers of a project with 200 layers, PNG | 52.5 / 36 | 33.7 / 45 | 50.3 / 33 | 27.3 / 36 |
| Tile 256x256, raster in its CRS, JPEG | 10.8 / 377 | 2.5 / 1082 | 3.9 / 767 | 19.8 / 105 |
| Map 1024x768, raster in its CRS, JPEG | 14.3 / 204 | 10.7 / 258 | 18.5 / 179 | 60.6 / 29 |
| Map 1024x768, raster reprojected, JPEG | 38.1 / 81 | 20.7 / 143 | 17.5 / 166 | 206 / 8.1 |
| Map 1024x768, raster reprojected under 3 vector layers, PNG | 100 / 21 | 51.2 / 45 | 59.4 / 37 | 279 / 4.6 |
| Map 1024x768, cascaded WMS layer, PNG | 85.9 / 28 | 69.6 / 34 | 70.4 / 34 | 58.2 / 51 |
| Map 1024x768, 3 vector layers, 8 bits PNG (1 client only) | 35.9 | 33.2 | 34.7 | 51.7 |
| GetFeatureInfo, JSON | 10.8 / 378 | 3.3 / 916 | n/a | 4.7 / 629 |
| GetLegendGraphic, PNG | 10.8 / 378 | 2.3 / 1375 | 2.9 / 986 | 0.9 / 2868 |
| WFS GetFeature, GML, up to 2000 polygons | 41.8 / 60 | 34.0 / 77 | 20.4 / 160 | 28.6 / 79 |
| WFS GetFeature, GeoJSON, up to 2000 polygons | 16.7 / 161 | 18.0 / 159 | 23.7 / 125 | 11.8 / 215 |
| WMS GetCapabilities | 10.8 / 379 | 0.9 / 3169 | 3.6 / 803 | 27.6 / 104 |
| WMTS GetTile | 10.9 / 288 | 5.0 / 370 | n/a | n/a |

Machine: Intel Core Ultra 7 165H (16 cores, 22 threads), 31 GB of memory, Windows 11, Docker Engine 29.9 on
WSL 2 (Linux 6.18), laptop on mains power. Data: an OpenStreetMap extract of one Polish region in PostGIS
(land use, buildings, roads, places), a Sentinel-2 true colour image of 10980x10980 pixels as a deflate
compressed GeoTIFF with overviews.

All 52 kinds of requests, the set-up of every server, the start times, the memory use and the limits of the
comparison: [benchmarks/3.44.15-qfs.1.md](benchmarks/3.44.15-qfs.1.md).

Against the official image, QFastServer has the lower median for 49 of the 52 kinds of requests and the
higher throughput for 36 of 38. The few cells where it came out behind in this run were not confirmed as a regression by a
second run with the two images alternating. It is not the fastest server everywhere: MapServer writes WFS
responses as GML faster, GeoServer is faster with one client for vector maps of 1024x768 pixels and for WFS.

Also measured:

- project with 200 PostGIS layers and `QGIS_SERVER_TRUST_LAYER_METADATA=true`: the first GetCapabilities
  takes 0.02 s instead of 3.3 s; four requests arriving at once right after the start are answered in 1.2 s
  instead of 2.3 s;
- GetMap returning 2.9 MB of DXF, in-process, with an unpatched and a patched build of the same source: 40 ms
  instead of 52 ms.

Not faster: GetPrint.

What to keep in mind when reading these numbers:

- They come from one machine and one run. Differences below about 10% are not resolved by this set-up.
- MapServer and GeoServer were not tuned beyond the set-up described in the benchmark document. Their
  columns show the images as they come with the same resources, not the best these servers can do.
- The styles were written by hand for every server; the images are not identical between the servers. The
  legend of GeoServer is an image of 199 bytes (a style without rule titles), so that row does not compare the
  same work.
- The image is built with the options of the upstream Debian packaging, but not by the build system of the
  official packages; the compiler flags may differ.
- PNG files of vector maps are smaller than upstream (tiles 20.7 → 16.6 kB, maps of 3 layers 343 → 288 kB);
  empty maps have the size they have upstream.
  PNG files of pure imagery (orthophotos) are about 20% larger, because rows are written without the
  expensive filter search.

### With QJazz

[QJazz](https://github.com/3liz/qjazz), the server of the Lizmap stack, replaces the FastCGI front with its
own, so it does not have the floor of about 11 ms either. The rendering is done by the same QGIS libraries, and
the QGIS libraries of QFastServer work under QJazz unchanged. Same machine and limits, measured in one session
for each family of requests, so not comparable with the table above:

| Request | QGIS Server | QJazz | QFastServer | QJazz with QFastServer libraries |
| --- | --- | --- | --- | --- |
| Tile 256x256, buildings, PNG | 11.1 / 280 | 9.8 / 250 | 4.6 / 420 | 7.3 / 317 |
| Map 1024x768, 3 vector layers, PNG | 50.6 / 40 | 55.1 / 35 | 25.5 / 58 | 27.9 / 58 |
| Map 1024x768, raster in its CRS, PNG (1 client only) | 84.3 | 89.8 | 23.2 | 27.2 |
| Map 1024x768, raster reprojected, JPEG | 34.6 / 83 | 40.2 / 76 | 18.3 / 166 | 21.8 / 140 |
| GetFeatureInfo, JSON | 11.1 / 369 | 5.1 / 574 | 4.6 / 637 | 4.8 / 698 |
| WMS GetCapabilities | 11.2 / 373 | 1.8 / 1784 | 1.1 / 2361 | 1.6 / 1852 |
| WFS GetFeature, GML, up to 2000 polygons | 49.0 / 49 | 158 / 18 | 40.8 / 61 | 112 / 39 |

Over 62 kinds of requests, QJazz with the libraries of QFastServer has a median 1.44 times lower and a
throughput 1.31 times higher than QJazz (geometric means). QJazz was run with the defaults of its image, front
and pool in one container; other settings may give other results. All rows and the set-up:
[benchmarks/3.44.15-qfs.1-qjazz.md](benchmarks/3.44.15-qfs.1-qjazz.md).

## How this repository is maintained

- The code is edited only in the development fork, one branch for each upstream line.
- The files under `patches/` are generated from that branch with `tools/export-patches.sh` and never edited by
  hand. `tools/check-patches.sh` verifies that the series applied to its base gives exactly the tree of the
  fork branch.
- For a new upstream release the branch is rebased on the upstream tag, built, tested and compared with the
  unpatched build; then the series is exported again, a file is added under `versions/` and the release is
  published under the new version.

## License

GNU General Public License, version 2 or later, the license of QGIS. See [LICENSE](LICENSE).
