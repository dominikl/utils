# requires Zarr v2 and ome-types
# pip install ome-types zarr==2.18.7

from zarr.storage import FSStore
import json
import dask.array as da
import sys
from ome_types import to_xml
from ome_types.model import OME, Image, Pixels
from ome_types.model.simple_types import ImageID, PixelsID, PixelType


if len(sys.argv) < 2:
    print("Error: Please provide the Zarr URI as a command line argument")
    print("Usage: python zarr_ome_xml.py <zarr_uri>")
    sys.exit(1)

zarr_uri = sys.argv[1]
zattrs = json.load(open(f"{zarr_uri}/.zattrs"))
if "bioformats2raw.layout" in zattrs and zattrs["bioformats2raw.layout"] == 3:
    store = FSStore(f"{zarr_uri}/0")
else:
    store = FSStore(zarr_uri)

zattrs = json.loads(store.get(".zattrs"))
array_path = zattrs["multiscales"][0]["datasets"][0]["path"]

array_data = da.from_zarr(store, array_path)

sizes = {}
shape = array_data.shape
axes = zattrs["multiscales"][0]["axes"]
for dim, size in zip(axes, shape):
    sizes[dim["name"]] = size

ome = OME()

pixels_type = array_data.dtype.name
pixels_id = 1
image_id = 1
image_name = zarr_uri.rstrip("/").split("/")[-1].split(".")[0]

ptype = PixelType(pixels_type)
pixels = Pixels(
    id=PixelsID("Pixels:%s" % pixels_id),
    dimension_order="XYZCT",
    size_c=sizes.get("c", 1),
    size_t=sizes.get("t", 1),
    size_z=sizes.get("z", 1),
    size_x=sizes.get("x", 1),
    size_y=sizes.get("y", 1),
    type=ptype,
    metadata_only=True,
)
img = Image(id=ImageID("Image:%s" % image_id), pixels=pixels, name=image_name)
ome.images.append(img)

xml_text = to_xml(ome)

with open(f'{image_name}.ome.xml', 'w') as f:
    f.write(xml_text)

