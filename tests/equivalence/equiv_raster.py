"""Renders reprojected rasters and prints a hash per case; run with two builds and diff the output."""
import hashlib, sys
from qgis.core import (QgsApplication, QgsRasterLayer, QgsMapSettings, QgsMapRendererCustomPainterJob,
                       QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsRectangle, QgsProject,
                       QgsRasterProjector)
from qgis.PyQt.QtGui import QImage, QPainter
from qgis.PyQt.QtCore import QSize
app = QgsApplication([], False); app.initQgis()
T = "/work/QGIS/tests/testdata/"
ctx = QgsProject.instance().transformContext()

def h(b):
    return hashlib.sha1(bytes(b)).hexdigest()[:16]

def render(name, path, crs, bbox, size):
    layer = QgsRasterLayer(path, "l")
    assert layer.isValid(), path
    ms = QgsMapSettings(); ms.setLayers([layer]); ms.setDestinationCrs(QgsCoordinateReferenceSystem(crs))
    ext = QgsRectangle(*bbox) if bbox else QgsCoordinateTransform(layer.crs(), QgsCoordinateReferenceSystem(crs), ctx).transformBoundingBox(layer.extent())
    ms.setExtent(ext); ms.setOutputSize(QSize(*size))
    img = QImage(size[0], size[1], QImage.Format_ARGB32_Premultiplied); img.fill(0)
    p = QPainter(img); QgsMapRendererCustomPainterJob(ms, p).renderSynchronously(); p.end()
    ptr = img.constBits(); ptr.setsize(img.sizeInBytes())
    print("render   %-34s %-10s %4dx%-4d %s" % (name, crs, size[0], size[1], h(ptr)))

def project(name, path, crs, size, precision):
    layer = QgsRasterLayer(path, "l")
    assert layer.isValid(), path
    prov = layer.dataProvider()
    dst = QgsCoordinateReferenceSystem(crs)
    ext = QgsCoordinateTransform(layer.crs(), dst, ctx).transformBoundingBox(layer.extent())
    ext.grow(ext.width() * 0.05)
    for band in range(1, prov.bandCount() + 1):
        proj = QgsRasterProjector(); proj.setInput(prov); proj.setCrs(layer.crs(), dst, ctx); proj.setPrecision(precision)
        blk = proj.block(band, ext, size[0], size[1])
        nod = sum(1 for i in range(0, size[0] * size[1], 7) if blk.isNoData(i))
        print("project  %-34s %-10s %4dx%-4d band %d prec %d %s nodata-sample %d" % (name, crs, size[0], size[1], band, int(precision), h(blk.data()), nod))

tci = "/raster/tci.tif"
render("tci dense", tci, "EPSG:3857", (2002542.05, 6609266.47, 2031214.05, 6630770.47), (1024, 768))
render("tci tile", tci, "EPSG:3857", (1996798.10, 6573878.47, 2001798.10, 6578878.47), (256, 256))
render("tci whole", tci, "EPSG:3857", None, (1024, 768))
render("tci whole", tci, "EPSG:2180", None, (1024, 768))
render("tci whole", tci, "EPSG:4326", None, (800, 600))
render("tci whole small", tci, "EPSG:4326", None, (97, 53))
# layer CRS (no reprojection): inside, partly outside and zoomed in
render("tci native", tci, "EPSG:32633", (709771.66, 5646883.70, 727818.34, 5660418.71), (1024, 768))
render("tci native edge", tci, "EPSG:32633", (690000.0, 5646883.70, 708046.68, 5660418.71), (1024, 768))
render("tci native zoom", tci, "EPSG:32633", (709771.66, 5646883.70, 710771.66, 5647633.70), (1024, 768))
render("tci native tile", tci, "EPSG:32633", (709771.66, 5646883.70, 712331.66, 5649443.70), (256, 256))
for f, crs in (("raster/band3_byte_noct_epsg4326.tif", "EPSG:4326"), ("landsat.tif", None), ("raster/rgb_with_mask.tif", None), ("raster/rotated_rgb.png", None)):
    try:
        layer = QgsRasterLayer(T + f, "l")
        render(f + " native", T + f, crs or layer.crs().authid(), None, (640, 480))
        e = layer.extent(); e.grow(e.width() * 0.2)
        render(f + " native grown", T + f, crs or layer.crs().authid(), (e.xMinimum(), e.yMinimum(), e.xMaximum(), e.yMaximum()), (333, 211))
    except AssertionError as e:
        print("skip", f, e)
for f in ("raster/band1_byte_ct_epsg4326.tif", "raster/band3_byte_noct_epsg4326.tif", "raster/dem.tif", "landsat.tif", "raster/with_color_table.tif", "raster/rgb_with_mask.tif"):
    try:
        for crs, size in (("EPSG:3857", (640, 480)), ("EPSG:32633", (333, 211))):
            render(f, T + f, crs, None, size)
        for prec in (QgsRasterProjector.Precision.Approximate, QgsRasterProjector.Precision.Exact):
            project(f, T + f, "EPSG:3857", (301, 207), prec)
    except AssertionError as e:
        print("skip", f, e)
