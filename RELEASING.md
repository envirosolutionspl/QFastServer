# Releasing

A release is declared compatible with exactly one QGIS Server release. Nothing is released without the
checks below, and their results go into the release notes.

## Steps

1. In the development fork, rebase the branch of the series on the upstream release tag
   (for example `final-3_44_15`), build, and run the upstream test suites.
2. Compare the patched build with the unpatched build of the same tag
   ([tests/equivalence](tests/equivalence)) and measure both.
3. Export the patches: `tools/export-patches.sh <fork> <upstream tag> <branch> <series>`.
   `tools/check-patches.sh` has to report that the tree matches the fork branch.
4. Tag the fork branch and this repository with the version, `<QGIS Server version>-qfs.<n>`.
5. Publish the release with notes written from the template below.

## Release notes template

```markdown
## Compatibility

| | |
| --- | --- |
| QGIS Server | 3.44.15 |
| Upstream tag and commit | `final-3_44_15`, `<commit>` |
| Patch series | 3.44, `<n>` patches, fork commit `<commit>` |
| Qt | 5.15 |

## Verification

- Upstream tests (server, rasters, projects, vector layers): `<passed>` of `<run>`; failures: `<list or none>`
- Responses compared with the unpatched build: `<identical>` of `<compared>` request types;
  not comparable (different from run to run in upstream): `<list>`
- Raster renderings compared: `<identical>` of `<compared>`

## Performance

Table of the measured requests, unpatched against patched, with the set-up used.

## Changes since the previous release

## Known differences from upstream

- PNG files of pure imagery are larger (rows are written without the filter search).
```
