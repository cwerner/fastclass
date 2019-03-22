#!/usr/bin/env python 
#
# fastclass - misc.py
# 
# Christian Werner, 2018-10-27

import collections
import itertools
from typing import Any, Iterable
import re

# some helper functions

def flatten(iterable: Iterable, ltypes=collections.abc.Iterable) -> Any:
    """Convert nested into a flat list"""
    remainder = iter(iterable)
    while True:
        try:
            first = next(remainder)
        except StopIteration:
            return
        if isinstance(first, ltypes) and not isinstance(first, (str,bytes)):
            remainder = itertools.chain(first, remainder)
        else:
            yield first

def sanitize_searchstring(s: str, rstring: str = None) -> str:
    """Convert search term to clean folder string"""
    if rstring:
        ritems = rstring.strip().split(' ') if ' ' in rstring else [rstring]
        for rs in ritems:
            s = s.replace(rs.strip(), '')
    
    s = str(s).strip().replace(' ', '_').replace('&', 'and')
    return re.sub(r'(?u)[^-\w.]', '', s)