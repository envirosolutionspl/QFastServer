# Relation to upstream QGIS

The patches are kept in the form upstream expects: one change in one commit, with a test, following the
QGIS coding standards and formatted with the tools pinned in the upstream pre-commit configuration. They live
on a branch of a fork of `qgis/QGIS`, so each of them can be proposed upstream as it is.

Status of all patches: **not submitted**.

The patches were written with the assistance of an AI coding agent. QGIS does not accept code contributions
made with the help of AI tools ([QEP 408](https://github.com/qgis/QGIS-Enhancement-Proposals/blob/master/qep-408-ai-tool-policy.md),
stated in the pull request template of `qgis/QGIS` since October 2026), and the author of a pull request has
to certify that no such tool was used. For this reason none of these patches has been or will be proposed
upstream while that policy stands. Should the policy change, they are ready to be proposed, with the use of
AI disclosed.

## Series 3.44

Branch `fast-server-3_44` of <https://github.com/envirosolutionspl/QGIS>.

| # | Patch | Kind | Also in upstream `master` (2026-11-11) |
| --- | --- | --- | --- |
| 0001 | Apply the project cache size setting to the config cache instance | bug fix | bug present, applies cleanly |
| 0002 | Restore the opacity of vector tile layers after a WMS request | bug fix | bug present |
| 0003 | Do not delay short FCGI requests in the socket monitoring thread | performance | delay present, applies by hand |
| 0004 | Write 32 bits PNG images with libpng, without row filtering | performance | applies by hand |
| 0005 | Use the connection pool when a provider is created for a parallel loading | performance | applies cleanly |
| 0006 | Keep the extent read from the project when layers are read with the trust flag | bug fix | bug present, applies cleanly |
| 0007 | Choose the PNG row filter from the image content | performance | follows 0004 |
| 0008 | Speed up the cell loop of the raster projector | performance | applies by hand |
| 0009 | Speed up the no data test of 8-bit bands in the multiband color renderer | performance | not checked |
| 0010 | Copy the cells of 8-bit bands without a call to memcpy for every cell | performance | not checked |
| 0011 | Speed up the conversion of WMS images to 8 bits PNG | performance | not checked |
| 0012 | Get the features of a JSON GetFeatureInfo with a single request | performance | not checked |

"Applies cleanly" and "applies by hand" describe a trial application of the commit to upstream `master`
(`53943cb164`); nothing was built on `master`.

## Measured, not implemented

Candidates found by profiling every request type of the server, with the share of the request time they
account for. None of them is implemented.

| Candidate | Share of the request | Note |
| --- | --- | --- |
| WFS GetFeature, GML | 44% in the per-character encoding check of QtXml | Qt 5 only |
| Labels | 36% converting text to outlines | gain only for texts which repeat |
| GetPrint, PNG | 58% writing the PNG with Qt | the file metadata has to be kept |
| DXF export | about 60% formatting numbers | — |
| WMTS GetCapabilities | 58% transforming extents, no cache | small absolute gain |
