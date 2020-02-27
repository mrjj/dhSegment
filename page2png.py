#!/usr/bin/env python3

"""
Based on following code:
https://github.com/benetech/PagexmlToRgbConverter/blob/07ef2e6312a806e9c446efe26f47c5f3ce53b4f8/converter.py
"""
import os
import sys

from glob import glob
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw
import math

"""
Usage:
$ python page2png.py /jpeg_png_tif_images/ /page_xml/ /output_jpeg_images_and_png_masks/ 1280
"""
images_dir = sys.argv[1]
xml_dir = sys.argv[2]
masked_images_dir = sys.argv[3]
max_dim = sys.argv[4] if len(sys.argv) > 4 else 2048

# change this to an RGB tuple ie (0,0,0) to add an outline to the drawn polygons
region_outline = None

resize_method = 'NEAREST'
RESIZE_METHODS = {
    'NEAREST': Image.NEAREST_NEIGHBOR,
    'BICUBIC': Image.BICUBIC,
    'BILINEAR': Image.BILINEAR
}

# change this if you'd like to map specific region types to different colors
region_type_to_color = {
    # Black (Neutral)
    "Background": (0, 0, 0),
    "NoiseRegion": (0, 0, 0),
    "UnknownRegion": (0, 0, 0),

    # Grey
    "TextRegion": (128, 128, 128),

    # Red
    "TableRegion": (255, 0, 0),

    # Pink
    "GraphicRegion": (255, 0, 255),
    "ImageRegion": (255, 0, 255),
    "AdvertRegion": (255, 0, 255),

    # Green
    "SeparatorRegion": (0, 255, 0),

    # Blue
    "MusicRegion": (0, 0, 255),
    "ChemRegion": (0, 0, 255),
    "MathsRegion": (0, 0, 255),
    "ChartRegion": (0, 0, 255),
    "LineDrawingRegion": (0, 0, 255),
}

image_count = 1

# iterate over each original image file
for imagef in os.listdir(images_dir):
    basename = imagef.split(".")[0]

    print("%d) processing base name %s" % (image_count, basename))

    with Image.open("%s/%s" % (images_dir, imagef)) as image:
        # create a new image with the same dimensions as the original and a white background
        original_size = image.size
        ratio = float(max_dim) / max(original_size)
        desired_size = (
            max_dim if original_size[0] >= original_size[1] else math.ceil(original_size[0] * ratio),
            max_dim if original_size[1] >= original_size[0] else math.ceil(original_size[1] * ratio),
        )
        image.thumbnail(desired_size, RESIZE_METHODS[resize_method])
        new_image = Image.new('RGB', image.size, color=region_type_to_color['Background'])
        draw = ImageDraw.Draw(new_image)

        # find the XML file associated with this image
        for xmlf in glob("%s/*%s*" % (xml_dir, basename)):
            print('xmlf', xmlf)
            # os.path.copy(imagef, imagef + '.fine')
            # open associated PAGE XML file for parsing
            with open(xmlf, encoding="utf8") as file:
                soup = BeautifulSoup(file, 'lxml')

                # search XML for each region type
                for region_type in region_type_to_color.keys():
                    # iterate over region tags for the specified type
                    # bs4 likes to deal with lower case tag names
                    for region_tag in soup.find_all(region_type.lower()):
                        points = region_tag.findChildren("point", recursive=True)
                        coordinate_array = []

                        # iterate over each point in the polygon
                        for point in points:
                            coordinate_array.append((int(point["x"]) * ratio, int(point["y"]) * ratio))

                        # if we have coordinates draw our polygon
                        if len(coordinate_array) > 1:
                            draw.polygon(
                                coordinate_array,
                                fill=region_type_to_color[region_type],
                                outline=region_outline
                            )

                # write out the image
                image.save("%s/%s.jpg" % (masked_images_dir, basename), format="JPEG", quality=99, subsampling=0)
                new_image.save("%s/%s.png" % (masked_images_dir, basename), "PNG")

        image_count += 1
