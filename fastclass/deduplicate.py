#!/usr/bin/env python 
#
# fastclass - deduplicate.py
# 
# Christian Werner, 2018-10-27

import hashlib
import os
from . misc import flatten 

def hashfile(path: str, blocksize: int = 65536) -> str:
    """Create hash for file"""
    with open(path, 'rb') as f:
        hasher = hashlib.md5()
        buf = f.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(blocksize)
    return hasher.hexdigest()

def remove_dups(parent_folder: str, match: str = None):
    """Remove duplicate files"""
    dups = {}
    for dirName, subdirs, files in os.walk(parent_folder):
        for f in files:
            path = os.path.join(dirName, f)
            dups.setdefault(hashfile(path), []).append(path)
    dups = flatten([v[1:] for k,v in dups.items() if len(v) > 1])

    print(f"Number of duplicate image files: {len(list(dups))}. Removing...")
    for dup in dups:
        os.remove(dup)