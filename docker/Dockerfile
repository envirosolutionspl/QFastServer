# QFastServer image: the official QGIS Server image of the same version, with the QGIS binaries
# replaced by a build of the same upstream release with the patch series applied.
#
# The build uses the upstream build image and the options of the upstream Debian packaging
# (debian/rules), so the result has the same features and the same file layout as the official packages.
#
# Build with docker/build.sh <QGIS Server version>, which passes the values of versions/<version>.env,
# or by hand from the root of this repository:
#   docker build -f docker/Dockerfile \
#     --build-arg QGIS_VERSION=3.44.15 --build-arg QGIS_TAG=final-3_44_15 --build-arg SERIES=3.44 \
#     --build-arg BUILD_IMAGE=qgis/qgis3-build-deps-24.04-qt5:release-3_44 \
#     --build-arg BASE_IMAGE=qgis/qgis-server:3.44.15-noble \
#     -t qfastserver:3.44.15 .

ARG BUILD_IMAGE
ARG BASE_IMAGE

FROM ${BUILD_IMAGE} AS build
ARG QGIS_TAG
ARG SERIES
# parallel compiler jobs; each one may need about 1.5 GB of memory
ARG JOBS=8

ADD https://github.com/qgis/QGIS/archive/refs/tags/${QGIS_TAG}.tar.gz /tmp/qgis.tar.gz
RUN mkdir /src && tar -xzf /tmp/qgis.tar.gz -C /src --strip-components=1 && rm /tmp/qgis.tar.gz

COPY patches/${SERIES}/ /patches/
# git apply refuses a patch which does not apply exactly
RUN cd /src && while read -r patch; do git apply "/patches/$patch" || exit 1; done </patches/series

# Options of debian/rules which decide the features and the layout of the installed files.
# Not built: the desktop application, the GRASS plugins, the documentation and the tests,
# which are not part of the server image.
RUN FLAGS="-O2 -fstack-protector-strong -fstack-clash-protection -Wformat -Werror=format-security -fcf-protection -D_FORTIFY_SOURCE=3" \
 && cmake -S /src -B /build -G Ninja \
      -DCMAKE_BUILD_TYPE=None \
      -DCMAKE_C_FLAGS="$FLAGS" -DCMAKE_CXX_FLAGS="$FLAGS" \
      -DCMAKE_SHARED_LINKER_FLAGS="-Wl,-Bsymbolic-functions -Wl,-z,relro" \
      -DCMAKE_MODULE_LINKER_FLAGS="-Wl,-Bsymbolic-functions -Wl,-z,relro" \
      -DCMAKE_INSTALL_PREFIX=/usr \
      -DBINDINGS_GLOBAL_INSTALL=TRUE \
      -DSIP_GLOBAL_INSTALL=TRUE \
      -DSERVER_SKIP_ECW=TRUE \
      -DQGIS_CGIBIN_SUBDIR=/usr/lib/cgi-bin \
      -DQT_PLUGINS_DIR=lib/x86_64-linux-gnu/qt5/plugins \
      -DWITH_CUSTOM_WIDGETS=TRUE \
      -DWITH_SERVER=TRUE \
      -DWITH_SERVER_PLUGINS=TRUE \
      -DWITH_QWTPOLAR=FALSE \
      -DWITH_QSPATIALITE=TRUE \
      -DWITH_3D=TRUE \
      -DWITH_HANA=TRUE \
      -DWITH_EPT=TRUE \
      -DWITH_PDAL=FALSE \
      -DWITH_DESKTOP=FALSE \
      -DWITH_GRASS7=FALSE -DWITH_GRASS8=FALSE \
      -DWITH_APIDOC=FALSE \
      -DENABLE_TESTS=FALSE \
 && ninja -C /build -j "$JOBS" \
 && DESTDIR=/out ninja -C /build install >/dev/null \
 && find /out -type f \( -name '*.so' -o -name '*.so.*' -o -name 'qgis_mapserv.fcgi' \) -exec strip --strip-unneeded {} + \
 && (cd /out && find usr/lib/qgis -name '*.so' | sort) >/out/qfastserver-plugins.txt

FROM ${BASE_IMAGE}
ARG BASE_IMAGE
ARG QGIS_VERSION
ARG SERIES

# the plugins and the server modules of the official packages, to check that all of them are replaced
RUN find /usr/lib/qgis -name '*.so' | sed 's,^/,,' | sort >/tmp/official-plugins.txt

COPY --from=build /out/ /

# Nothing of the official build may stay next to the new libraries, every library has to resolve
# and the Python bindings have to load
RUN ldconfig \
 && missing=$(comm -23 /tmp/official-plugins.txt /qfastserver-plugins.txt) \
 && if [ -n "$missing" ]; then echo "not replaced: $missing"; exit 1; fi \
 && if ldd /usr/lib/cgi-bin/qgis_mapserv.fcgi /usr/lib/libqgis_*.so.* $(find /usr/lib/qgis -name '*.so') | grep 'not found'; then exit 1; fi \
 && python3 -c "from qgis.core import Qgis; import qgis.server, qgis.analysis; print('QGIS', Qgis.QGIS_VERSION)" \
 && rm /tmp/official-plugins.txt

LABEL org.opencontainers.image.title="QFastServer" \
      org.opencontainers.image.description="QGIS Server ${QGIS_VERSION} with the QFastServer patch series ${SERIES}" \
      org.opencontainers.image.licenses="GPL-2.0-or-later" \
      org.opencontainers.image.source="https://github.com/envirosolutionspl/QFastServer" \
      org.opencontainers.image.base.name="${BASE_IMAGE}"
