#!/usr/bin/env python 
#
# fastclass - imageprocessing.py
# 
# Christian Werner, 2018-10-27

import os
from PIL import Image
from tqdm import tqdm
from typing import List, Optional, Tuple

def resize(files: List[str], outpath: Optional[str] = None, size: Tuple[int, int] = (299, 299)):
    """Resize image to specified size"""
    print(f'(2) Resizing images to {size}')
    with tqdm(total=len(files)) as t:
        for fcnt, f in enumerate(files):
            im = Image.open(f)
            try:
                im.thumbnail(size, Image.ANTIALIAS)
            except OSError:
                # skip truncated files
                continue
            bg = Image.new('RGBA', size, (255, 255, 255, 0))
            bg.paste(im, (int((size[0] - im.size[0]) / 2), int((size[1] - im.size[1]) / 2)))
            bg = bg.convert('RGB')

            fname, _ = os.path.splitext(os.path.basename(f))
            out = os.path.join(outpath, fname + '.jpg') 
            bg.save(out)
            t.update(1)
