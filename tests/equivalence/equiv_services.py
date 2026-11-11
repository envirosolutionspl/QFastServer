"""Compare the responses of two QGIS Server builds for the request types not covered by the GetMap load tests.

Run inside a container with PyQt5 on the compose network (project svc.qgs on both services):
  python3 equiv_services.py http://qgis_base/ http://qgis_fast/ [requests.json]
Images are compared pixel by pixel, XML after canonicalisation (Qt randomises the attribute order per process),
PDF after removing the creation date, everything else byte by byte. Exit code 1 on any difference.
"""

import json
import re
import sys
import urllib.request
from xml.etree.ElementTree import canonicalize

from PyQt5.QtGui import QImage

A, B = sys.argv[1], sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 else None

W = "SERVICE=WMS&VERSION=1.3.0&"
BB = "1996798.10,6473878.47,1997156.50,6474236.87"  # scale 5000 tile with buildings and roads
BIG = "1990000,6520000,2000000,6529000"
MAP = f"{W}REQUEST=GetMap&STYLES=&CRS=EPSG:3857&WIDTH=512&HEIGHT=512&BBOX="
GFI = (
    f"{W}REQUEST=GetFeatureInfo&CRS=EPSG:3857&WIDTH=256&HEIGHT=256&BBOX={BB}&I=128&J=128"
    "&FI_POINT_TOLERANCE=40&FI_LINE_TOLERANCE=40&FI_POLYGON_TOLERANCE=40&FEATURE_COUNT=10"
)
F = "SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&"
REQUESTS = {
    "wms_capabilities": f"{W}REQUEST=GetCapabilities",
    "wms_capabilities_111": "SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities",
    "wms_project_settings": f"{W}REQUEST=GetProjectSettings",
    "wms_context": f"{W}REQUEST=GetContext",
    "wms_describe_layer": f"{W}REQUEST=DescribeLayer&LAYERS=buildings,roads&SLD_VERSION=1.1.0",
    "wms_get_styles": f"{W}REQUEST=GetStyles&LAYERS=buildings,roads",
    "map_labels_png": f"{MAP}{BIG}&LAYERS=landuse,buildings,roads,places&FORMAT=image/png",
    "map_transparent": f"{MAP}{BB}&LAYERS=buildings,roads&FORMAT=image/png&TRANSPARENT=TRUE",
    "map_png8": f"{MAP}{BB}&LAYERS=landuse,buildings,roads&FORMAT=image/png;%20mode%3D8bit",
    "map_png1": f"{MAP}{BB}&LAYERS=buildings&FORMAT=image/png;%20mode%3D1bit",
    "map_png16": f"{MAP}{BB}&LAYERS=landuse,buildings,roads&FORMAT=image/png;%20mode%3D16bit",
    "map_jpeg": f"{MAP}{BB}&LAYERS=landuse,buildings,roads&FORMAT=image/jpeg",
    "map_webp": f"{MAP}{BB}&LAYERS=landuse,buildings,roads&FORMAT=image/webp",
    "map_dpi": f"{MAP}{BB}&LAYERS=landuse,buildings,roads&FORMAT=image/png&DPI=192",
    "map_opacity": f"{MAP}{BB}&LAYERS=landuse,buildings,roads&FORMAT=image/png&OPACITIES=255,120,60",
    "map_filter": f"{MAP}{BIG}&LAYERS=roads&FORMAT=image/png&FILTER=roads:%22class%22%20%3D%20%27primary%27",
    "map_selection": f"{MAP}{BB}&LAYERS=buildings&FORMAT=image/png&SELECTION=buildings:1,2,3,4,5",
    "map_2180": f"{W}REQUEST=GetMap&STYLES=&CRS=EPSG:2180&WIDTH=512&HEIGHT=512&BBOX=350000,400000,360000,410000"
    "&LAYERS=tci,landuse,buildings,roads&FORMAT=image/png",
    "map_raster_native": f"{MAP}{BIG}&LAYERS=tci&FORMAT=image/png",
    "map_raster_bilinear": f"{MAP}{BIG}&LAYERS=tci_bilinear&FORMAT=image/jpeg",
    "map_cascade": f"{MAP}{BIG}&LAYERS=cascade&FORMAT=image/png",
    "map_cascade_over": f"{MAP}{BIG}&LAYERS=cascade,roads&FORMAT=image/jpeg",
    "map_dxf": f"{MAP}{BB}&LAYERS=buildings,roads&FORMAT=application/dxf",
    "gfi_text": f"{GFI}&LAYERS=buildings,roads&QUERY_LAYERS=buildings,roads&INFO_FORMAT=text/plain",
    "gfi_xml": f"{GFI}&LAYERS=buildings,roads&QUERY_LAYERS=buildings,roads&INFO_FORMAT=text/xml",
    "gfi_xml_geometry": f"{GFI}&LAYERS=buildings&QUERY_LAYERS=buildings&INFO_FORMAT=text/xml&WITH_GEOMETRY=true",
    "gfi_html": f"{GFI}&LAYERS=buildings,roads&QUERY_LAYERS=buildings,roads&INFO_FORMAT=text/html",
    "gfi_json": f"{GFI}&LAYERS=buildings,roads&QUERY_LAYERS=buildings,roads&INFO_FORMAT=application/json",
    "gfi_gml": f"{GFI}&LAYERS=buildings&QUERY_LAYERS=buildings&INFO_FORMAT=application/vnd.ogc.gml",
    "gfi_raster": f"{W}REQUEST=GetFeatureInfo&CRS=EPSG:3857&WIDTH=256&HEIGHT=256&BBOX={BIG}&I=128&J=128"
    "&LAYERS=tci&QUERY_LAYERS=tci&INFO_FORMAT=text/xml",
    "gfi_filter": f"{W}REQUEST=GetFeatureInfo&LAYERS=roads&QUERY_LAYERS=roads&INFO_FORMAT=text/xml&FEATURE_COUNT=5"
    "&FILTER=roads:%22class%22%20%3D%20%27major%27",
    "legend_png": f"{W}REQUEST=GetLegendGraphic&LAYERS=landuse,buildings,roads,places&FORMAT=image/png",
    "legend_json": f"{W}REQUEST=GetLegendGraphic&LAYERS=landuse,roads&FORMAT=application/json",
    "legend_rule": f"{W}REQUEST=GetLegendGraphic&LAYER=roads&RULE=primary&WIDTH=30&HEIGHT=20&FORMAT=image/png",
    "print_png": f"{W}REQUEST=GetPrint&TEMPLATE=a4&FORMAT=png&DPI=100&CRS=EPSG:3857&map0:EXTENT={BIG}"
    "&map0:LAYERS=landuse,buildings,roads,places",
    "print_pdf": f"{W}REQUEST=GetPrint&TEMPLATE=a4&FORMAT=pdf&DPI=100&CRS=EPSG:3857&map0:EXTENT={BIG}"
    "&map0:LAYERS=landuse,buildings,roads",
    "print_svg": f"{W}REQUEST=GetPrint&TEMPLATE=a4&FORMAT=svg&DPI=100&CRS=EPSG:3857&map0:EXTENT={BIG}&map0:LAYERS=roads",
    "wfs_capabilities": "SERVICE=WFS&VERSION=1.1.0&REQUEST=GetCapabilities",
    "wfs_capabilities_100": "SERVICE=WFS&VERSION=1.0.0&REQUEST=GetCapabilities",
    "wfs_describe": "SERVICE=WFS&VERSION=1.1.0&REQUEST=DescribeFeatureType&TYPENAME=buildings,roads",
    "wfs_gml3": f"{F}TYPENAME=buildings&BBOX={BB},EPSG:3857&MAXFEATURES=500",
    "wfs_gml2": f"SERVICE=WFS&VERSION=1.0.0&REQUEST=GetFeature&TYPENAME=roads&BBOX={BB}&MAXFEATURES=500",
    "wfs_geojson": f"{F}TYPENAME=buildings&BBOX={BB},EPSG:3857&MAXFEATURES=500&OUTPUTFORMAT=application/json",
    "wfs_geojson_4326": f"{F}TYPENAME=roads&MAXFEATURES=300&OUTPUTFORMAT=application/json&SRSNAME=EPSG:4326",
    "wfs_hits": f"{F}TYPENAME=buildings&BBOX={BB},EPSG:3857&RESULTTYPE=hits",
    "wfs_featureid": f"{F}FEATUREID=buildings.1,buildings.2,roads.7",
    "wfs_exp_filter": f"{F}TYPENAME=roads&EXP_FILTER=%22class%22%20%3D%20%27major%27&MAXFEATURES=50",
    "wfs_ogc_filter": f"{F}TYPENAME=roads&MAXFEATURES=50&FILTER=%3CFilter%3E%3CPropertyIsEqualTo%3E"
    "%3CPropertyName%3Eclass%3C/PropertyName%3E%3CLiteral%3Eprimary%3C/Literal%3E%3C/PropertyIsEqualTo%3E%3C/Filter%3E",
    "wfs_property": f"{F}TYPENAME=buildings&MAXFEATURES=100&PROPERTYNAME=id&GEOMETRYNAME=none",
    "wfs_paging": f"{F}TYPENAME=buildings&MAXFEATURES=100&STARTINDEX=1000&OUTPUTFORMAT=application/json",
    "wfs3_collections": "wfs3/collections.json",
    "wfs3_items": "wfs3/collections/buildings/items.json?limit=100",
    "wfs3_items_bbox": "wfs3/collections/roads/items.json?limit=100&bbox=17.9,50.6,18.0,50.7",
    "wmts_capabilities": "SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetCapabilities",
    "wmts_tile": "SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetTile&LAYER=buildings&STYLE=default&TILEMATRIXSET=EPSG:3857"
    "&TILEMATRIX=14&TILEROW=5545&TILECOL=9008&FORMAT=image/png",
    "wcs_capabilities": "SERVICE=WCS&VERSION=1.0.0&REQUEST=GetCapabilities",
    "wcs_describe": "SERVICE=WCS&VERSION=1.0.0&REQUEST=DescribeCoverage&COVERAGE=tci",
    "error_layer": f"{MAP}{BB}&LAYERS=nope&FORMAT=image/png",
    "error_service": "SERVICE=NOPE&REQUEST=GetCapabilities",
}


def fetch(base, query):
    url = base + (query if query.startswith("wfs3/") else "?" + query)
    try:
        with urllib.request.urlopen(url, timeout=300) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", ""), e.read()


def normalise(ctype, body, base):
    body = body.replace(base.encode(), b"http://HOST/")
    if ctype.startswith("image/") and b"svg" not in ctype.encode():
        img = QImage.fromData(body)
        if img.isNull():
            return "undecodable image", body
        img = img.convertToFormat(QImage.Format_ARGB32)
        ptr = img.constBits()
        ptr.setsize(img.sizeInBytes())
        return f"image {img.width()}x{img.height()}", bytes(ptr)
    if "pdf" in ctype:
        return "pdf", re.sub(rb"/CreationDate \([^)]*\)|/ID \[[^\]]*\]", b"", body)
    if "xml" in ctype or "gml" in ctype:
        try:
            return "xml", canonicalize(body.decode("utf-8")).encode()
        except Exception:  # not well formed: compare as is
            return "xml?", body
    return "bytes", body


failed = 0
rows = {}
for name, query in REQUESTS.items():
    sa, ca, ba = fetch(A, query)
    sb, cb, bb = fetch(B, query)
    ka, na = normalise(ca, ba, A)
    kb, nb = normalise(cb, bb, B)
    same = sa == sb and ca == cb and na == nb
    failed += not same
    rows[name] = {"status": [sa, sb], "type": [ca, cb], "bytes": [len(ba), len(bb)], "same": same}
    print(f"{'ok  ' if same else 'DIFF'} {name:24s} {sa}/{sb} {ka:18s} {len(ba):>8d} {len(bb):>8d}  {ca}")
if OUT:
    json.dump(rows, open(OUT, "w"), indent=1)
print(f"{len(REQUESTS) - failed} of {len(REQUESTS)} identical")
sys.exit(1 if failed else 0)
