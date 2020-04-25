#!/usr/bin/env python
#
# fastclass - imageprocessing.py
#
# Christian Werner, 2018-10-27

import os
from PIL import Image
import piexif
import piexif.helper

from tqdm import tqdm
from typing import Any, Dict, List, Optional, Tuple


def resize(
    files: List[str],
    outpath: Optional[str] = None,
    size: Tuple[int, int] = (299, 299),
    urls: Optional[Dict[str, str]] = None,
) -> Optional[Dict[str, str]]:
    """Resize image to specified size"""
    should_resize = size[0] > 0 and size[1] > 0
    if should_resize:
        print(f"(2) Resizing images to {size}")
    else:
        print("Not resizing images")

    sources = None
    if urls:
        sources = {}

    with tqdm(total=len(files)) as t:
        for fcnt, f in enumerate(files):
            im = Image.open(f)
            if should_resize:
                try:
                    im.thumbnail(size, Image.ANTIALIAS)
                except OSError:
                    # skip truncated files
                    continue

                bg = Image.new("RGBA", size, (255, 255, 255, 0))
                bg.paste(
                    im,
                    (int((size[0] - im.size[0]) / 2), int((size[1] - im.size[1]) / 2)),
                )

            else:
                bg = im

            try:
                bg = bg.convert("RGB")
            except OSError:
                t.update(1)
                continue

            fname, _ = os.path.splitext(os.path.basename(f))
            out = os.path.join(outpath, fname + ".jpg")
            bg.save(out)

            if urls:
                # embed source in image
                tag_data = piexif.helper.UserComment.dump(
                    "source: " + urls[os.path.basename(f)]
                )
                exif_dict = piexif.load(out)
                exif_dict["Exif"][piexif.ExifIFD.UserComment] = tag_data
                exif_bytes = piexif.dump(exif_dict)
                bg.save(out, exif=exif_bytes)

                sources[os.path.basename(out)] = urls[os.path.basename(f)]

            t.update(1)

    return sources


def image_pad(file_name: str, size: Tuple[int, int]) -> Any:
    """Read image and pad"""
    im = Image.open(file_name)
    im.thumbnail(size, Image.ANTIALIAS)

    bg = Image.new("RGBA", size, (255, 255, 255, 0))
    bg.paste(im, (int((size[0] - im.size[0]) / 2), int((size[1] - im.size[1]) / 2)))
    return bg
