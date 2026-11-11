# QFastServer

[![QGIS Server 3.44 LTR](https://img.shields.io/badge/QGIS%20Server-3.44%20LTR-589632)](#versions-and-compatibility)
[![Status: pre-release](https://img.shields.io/badge/status-pre--release-orange)](#versions-and-compatibility)
[![License: GPL v2 or later](https://img.shields.io/badge/license-GPL--2.0--or--later-blue)](LICENSE)

Performance patches for [QGIS Server](https://qgis.org): the same requests, the same responses, less time.

QFastServer is not another map server. It is a small series of patches on top of a specific QGIS Server
release. Configuration, projects, Python server plugins and client stacks (Lizmap, QWC2 and others) stay as
they are; the responses are the ones the unpatched server gives.

QFastServer is an independent project. It is not affiliated with or endorsed by QGIS.org. QGIS is a trademark
of QGIS.org.

**Status: pre-release.** The patch series for the 3.44 long term release line is published here. There is no
binary release yet, and the numbers below were measured against an unpatched build of the same source, not
yet against the official packages (see [Measurements](#measurements)).

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
| Fixes | The project cache size setting is applied; the opacity of vector tile layers is restored after a request |

Every patch is one commit with a test, written to the upstream coding standards. The list is in
[UPSTREAM.md](UPSTREAM.md), together with the reason why the patches are not proposed to QGIS: they were
written with the assistance of an AI coding agent, which the QGIS contribution policy does not allow.

## Measurements

Same source commit, with and without the patches, built in the same image and served the same way
(lighttpd, 4 FastCGI workers, 4 CPUs for the container, PostGIS on the same host). Load generated with k6:
median response time with one client, requests per second with 16 clients. No failed responses in any run.

| Request | Median, 1 client | Requests/s, 16 clients |
| --- | --- | --- |
| Tile 256x256, 1 vector layer, PNG | 10.9 → 4.6 ms | 323 → 495 |
| Tile 256x256, 3 vector layers, PNG | 11.0 → 7.0 ms | 250 → 304 |
| Map 1024x768, 1 vector layer, PNG | 27.7 → 14.4 ms | 84 → 111 |
| Map 1024x768, 3 vector layers, PNG | 41.2 → 24.6 ms | 50 → 64 |
| Raster, layer CRS, JPEG | 22.9 → 9.7 ms | 165 → 332 |
| Raster, layer CRS, PNG | 89.2 → 22.0 ms | 38 → 138 |
| Raster, reprojected, JPEG | 43.4 → 15.7 ms | 82 → 202 |
| GetFeatureInfo, JSON | 10.9 → 3.5 ms | 377 → 918 |
| GetLegendGraphic, PNG | 11.0 → 5.0 ms | 377 → 716 |
| WMTS GetTile | 11.0 → 5.3 ms | 281 → 377 |

Project with 200 PostGIS layers: four workers starting together load it in 1.0 s instead of 2.4 s; the first
GetCapabilities with `QGIS_SERVER_TRUST_LAYER_METADATA=true` takes 0.02 s instead of 3.2 s.

Not faster: GetPrint, WFS GetFeature.

What to keep in mind when reading these numbers:

- They come from one machine (a laptop on mains power) and short runs. Differences below about 10% are not
  resolved by this set-up.
- The reference is an unpatched build of the same commit, not the official packages or Docker image. A
  comparison with the official image of the same version will be published with the first release.
- PNG files of pure imagery (orthophotos) are about 20% larger than upstream, because rows are written
  without the expensive filter search. PNG files of vector maps are 13 to 20% smaller.

## Compatibility

A release of QFastServer is declared compatible with one QGIS Server release, the one in its version number.
The declaration is checked, not assumed:

- the upstream test suites for the server, rasters, projects and vector layers pass on the patched build;
- 59 kinds of requests (WMS GetMap in every output format, GetFeatureInfo, GetLegendGraphic, GetPrint, WFS,
  OGC API Features, WMTS, WCS, error responses) are sent to both builds and the responses compared: images
  pixel by pixel, XML after canonicalisation, everything else byte by byte
  ([tests/equivalence](tests/equivalence));
- 68 raster renderings (reprojected and not, inside and across the raster extent) give the same pixels.

Five of the 59 requests give different responses from one process to the next in upstream itself (8 bits PNG,
GetContext, DXF, PDF, a cascaded WMS layer as PNG), so they cannot be compared between builds. For 8 bits PNG
the equality is tested at the function level instead.

## Versions and compatibility

A QFastServer release is named `<QGIS Server version>-qfs.<n>`, for example `3.44.15-qfs.1`: the QGIS Server
release it is built from and compatible with, then the number of the QFastServer release for it. The notes of
every release state the upstream tag and commit, the number of patches and the results of the tests and of
the comparison with the unpatched server ([RELEASING.md](RELEASING.md)).

| QGIS Server | Patch series | State |
| --- | --- | --- |
| 3.44.15 (LTR) | [3.44](patches/3.44), 12 patches | patches apply to the tag `final-3_44_15`; built, tested and compared on `release-3_44` 28 commits after that tag (see [SOURCE](patches/3.44/SOURCE)); no release yet |
| 4.x | — | not started; the code paths changed by the patches are still present in upstream `master` |
| other versions | — | not supported: the patches are only checked against the versions listed here |

## Building

Until there is a binary release:

```bash
git clone --branch final-3_44_15 --depth 1 https://github.com/qgis/QGIS
```

```bash
git -C QGIS am ../QFastServer/patches/3.44/*.patch
```

Then build QGIS Server as described in the
[QGIS developer documentation](https://github.com/qgis/QGIS/blob/release-3_44/INSTALL.md). The patched source
tree is also available as the branch `fast-server-3_44` of the development fork,
<https://github.com/envirosolutionspl/QGIS>.

## How this repository is maintained

- The code is edited only in the development fork, one branch for each upstream line.
- The files under `patches/` are generated from that branch with `tools/export-patches.sh` and never edited by
  hand. `tools/check-patches.sh` verifies that the series applied to its base gives exactly the tree of the
  fork branch.
- For a new upstream release the branch is rebased on the upstream tag, built, tested and compared with the
  unpatched build; then the series is exported again and released under the new version.

## License

GNU General Public License, version 2 or later, the license of QGIS. See [LICENSE](LICENSE).
