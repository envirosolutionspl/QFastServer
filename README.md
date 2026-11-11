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

The official image `qgis/qgis-server:3.44.15-noble` against the QFastServer image built from it with
`docker/build.sh 3.44.15`. Both are started the same way: the nginx front of the image, 4 FastCGI workers,
parallel rendering off, 4 CPUs and 4 GB of memory for the container, PostGIS 16 in another container on the
same host. Load generated with k6: median response time with one client, requests per second with 16 clients,
two runs of 8 s for each image and each cell, the images alternating. No failed responses in any run.

| Request | Median, 1 client | Requests/s, 16 clients |
| --- | --- | --- |
| Tile 256x256, 1 vector layer, PNG | 10.9 → 4.5 ms | 304 → 459 |
| Tile 256x256, 3 vector layers, PNG | 11.0 → 7.9 ms | 222 → 271 |
| Map 1024x768, 1 vector layer, PNG | 30.3 → 18.0 ms | 70 → 95 |
| Map 1024x768, 3 vector layers, PNG | 44.6 → 27.5 ms | 42 → 57 |
| Map 1024x768, raster in the layer CRS, JPEG | 17.8 → 10.1 ms | 198 → 301 |
| Map 1024x768, raster reprojected, JPEG | 37.5 → 18.9 ms | 86 → 162 |
| GetFeatureInfo, JSON | 11.0 → 3.7 ms | 374 → 871 |
| GetLegendGraphic, PNG | 10.9 → 4.5 ms | 377 → 724 |
| WMTS GetTile | 10.9 → 5.3 ms | 261 → 356 |
| WFS GetFeature, GML, up to 2000 polygons | 44.6 → 37.0 ms | 57 → 74 |
| Map 1024x768, 3 vector layers, 8 bits PNG | 37.2 → 35.9 ms | 45 → 47 |

Machine: Intel Core Ultra 7 165H (16 cores, 22 threads), 31 GB of memory, Windows 11, Docker Engine 29.9 on
WSL 2 (Linux 6.18), laptop on mains power. Data: an OpenStreetMap extract of one Polish region in PostGIS
(land use, buildings, roads), a Sentinel-2 true colour image of 10980x10980 pixels as a deflate compressed
GeoTIFF with overviews.

Measured with an unpatched and a patched build of the same source instead of the official image:

- project with 200 PostGIS layers: four workers starting together load it in 1.0 s instead of 2.4 s; the
  first GetCapabilities with `QGIS_SERVER_TRUST_LAYER_METADATA=true` takes 0.02 s instead of 3.2 s;
- map of a raster in the layer CRS as PNG: 22 ms instead of 89 ms;
- GetMap returning 2.9 MB of DXF, in-process: 40 ms instead of 52 ms.

Not faster: GetPrint.

What to keep in mind when reading these numbers:

- They come from one machine and short runs. Differences below about 10% are not resolved by this set-up:
  the 8 bits PNG row is within that noise (in-process, 24 different maps take 11% less time).
- The image is built with the options of the upstream Debian packaging, but not by the build system of the
  official packages; the compiler flags may differ.
- PNG files of vector maps are smaller than upstream (tiles 20.8 → 16.6 kB, maps of 3 layers 330 → 288 kB).
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
