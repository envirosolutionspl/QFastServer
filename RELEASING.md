# Releasing

A release is declared compatible with exactly one QGIS Server release. Nothing is released without the
checks below, and their results go into the release notes.

## Steps

1. In the development fork, rebase the branch of the series on the upstream release branch, build, and run
   the upstream test suites.
2. Export the patches: `tools/export-patches.sh <fork> <base> <branch> <series>`, then check that the series
   applies to the upstream release tag: `tools/check-patches.sh <fork> <series> <upstream tag>`.
3. Add `versions/<QGIS Server version>.env` and build the image: `docker/build.sh <QGIS Server version>`.
4. Compare the image with the official image of the same version ([tests/equivalence](tests/equivalence))
   and measure both.
5. Write the release notes from the template below to `releases/<QGIS Server version>-qfs.<n>.md`.
6. Push the tag `<QGIS Server version>-qfs.<n>`. The workflow `.github/workflows/release.yml` builds the
   image again from the upstream tag and the patches, starts it, publishes it as
   `ghcr.io/envirosolutionspl/qfastserver:<tag>` and creates the release with the notes. It refuses a tag
   whose notes have no Compatibility section.

The source of a release is the upstream tag plus the patch series of this repository at the release tag:
the image is built from exactly that.

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
