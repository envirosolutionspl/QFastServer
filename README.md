# QFastServer

[![QGIS Server 3.44 LTR](https://img.shields.io/badge/QGIS%20Server-3.44%20LTR-589632)](#compatibility)
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
| 3.44.15 (LTR) | [versions/3.44.15.env](versions/3.44.15.env) | [3.44](patches/3.44), 14 patches | released: [3.44.15-qfs.1](https://github.com/envirosolutionspl/QFastServer/releases/tag/3.44.15-qfs.1) |
| 4.x | — | — | not started; the code changed by the patches is still present in upstream `master` |
| any other version | — | — | not supported |

Notes for 3.44.15: the image is built from the upstream tag `final-3_44_15` with the patches applied; the
upstream test suites were run with the same patches on the branch `release-3_44` 28 commits after that tag
(see [SOURCE](patches/3.44/SOURCE)). What was verified for a release is in its notes.

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

Five of the 59 requests give different responses from one process to the next in upstream itself (8 bits PNG,
GetContext, DXF, PDF, a cascaded WMS layer as PNG), so they cannot be compared between builds. For 8 bits PNG
the equality is tested at the function level instead.

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
    # image: qgis/qgis-server:<QGIS Server version>-noble
    image: ghcr.io/envirosolutionspl/qfastserver:<QGIS Server version>
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

With the values of your QGIS Server version loaded from its file:

```bash
. versions/<QGIS Server version>.env
git clone --branch "$QGIS_TAG" --depth 1 https://github.com/qgis/QGIS
git -C QGIS apply "$PWD"/patches/"$SERIES"/*.patch
```

Then build QGIS Server as described in `INSTALL.md` of the QGIS source tree. The patched source tree is also
available in the development fork, <https://github.com/envirosolutionspl/QGIS>, on the branch named in
`patches/<series>/SOURCE`.

## What it changes

| Area | Change |
| --- | --- |
| Every request | The FastCGI socket monitoring thread no longer adds up to 10 ms to each request |
| PNG output | 32 bits PNG written directly with libpng, row filter chosen from the image content |
| 8 bits PNG | Faster search of the closest palette color, same result |
| Rasters | Faster cell loop of the raster projector, of the multiband renderer and of the GDAL provider |
| PostGIS | Connections are reused when the layers of a project are loaded in parallel |
| Trusted layer metadata | The extent stored in the project is kept, so the first GetCapabilities does not scan every layer |
| GetFeatureInfo (JSON) | One request to the data source for a layer instead of one for every feature |
| WFS GetFeature (GML) | The features are written without converting every character to check its encoding |
| DXF export | The group codes are formatted once |
| Fixes | The project cache size setting is applied; the opacity of vector tile layers is restored after a request |

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
- The styles were written by hand for every server; the images are not identical between the servers.
- The image is built with the options of the upstream Debian packaging, but not by the build system of the
  official packages; the compiler flags may differ.
- PNG files of vector maps are smaller than upstream (tiles 20.7 → 16.6 kB, maps of 3 layers 343 → 288 kB).
  PNG files of pure imagery (orthophotos) are about 20% larger, because rows are written without the
  expensive filter search.

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
