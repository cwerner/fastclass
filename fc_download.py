#!/usr/bin/env python 
#
# fc_download.py
# 
# Christian Werner, 2018-10-23
#
# TODO: 
#  - print report (images per class etc) 
#  - check if we need grace periods to avoid blocking
 
import click
import collections
import glob
import hashlib
from icrawler.builtin import GoogleImageCrawler, BingImageCrawler, BaiduImageCrawler
import itertools
import logging
import os
from PIL import Image
import shutil
import sys
import tempfile
from tqdm import tqdm
from typing import Any, Iterable, List, Optional, Tuple

EPILOG = """::: FastClass fc_download :::\r
\r
...an easy way to crawl the net for images when building a\r
dataset for deep learning.\r
\r
Example: fcd -c GOOGLE -c BING -s 224 example/guitars.csv

"""

def flatten(iterable: Iterable, ltypes=collections.abc.Iterable) -> Any:
    remainder = iter(iterable)
    while True:
        first = next(remainder)
        if isinstance(first, ltypes) and not isinstance(first, (str,bytes)):
            remainder = itertools.chain(first, remainder)
        else:
            yield first

def crawl(folder: str, search: str, crawlers: [List[str]] = ['GOOGLE', 'BING', 'BAIDU']):
    print('(1) Crawling ...')
    # prepare folders
    os.makedirs(folder, exist_ok=True)

    for c in crawlers:
        print(f'    -> {c}')
        if c == 'GOOGLE':
            google_crawler = GoogleImageCrawler(
                log_level=logging.CRITICAL,
                feeder_threads=1,
                parser_threads=1,
                downloader_threads=4,
                storage={'root_dir': folder})

            google_crawler.crawl(keyword=search, offset=0, max_num=1000,
                                min_size=(200,200), max_size=None, file_idx_offset=0)

        if c == 'BING':
            bing_crawler = BingImageCrawler(log_level=logging.CRITICAL,
                                            downloader_threads=4,
                                            storage={'root_dir': folder})
            bing_crawler.crawl(keyword=search, filters=None, offset=0, max_num=1000, file_idx_offset='auto')

        if c == 'BAIDU':
            baidu_crawler = BaiduImageCrawler(log_level=logging.CRITICAL,
                                    storage={'root_dir': folder})
            baidu_crawler.crawl(keyword=search, offset=0, max_num=1000,
                                min_size=(200,200), max_size=None, file_idx_offset='auto')

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
            

def main(infile: str, size: int, crawler: List[str], keep: bool, outpath: str):

    SIZE=(size,size)
    classes = []

    if 'ALL' in crawler:
        crawler = ['GOOGLE', 'BING', 'BAIDU']

    if os.path.isdir(outpath):
        print(f'Directory "{outpath}" exists. Please specify another one using -o')
        exit(-1)
    else:
        os.makedirs(outpath)
        print(f'INFO: final dataset will be located in {outpath}')

    with tempfile.TemporaryDirectory() as tmp:
        for lcnt, line in enumerate(infile):
            if lcnt > 0:
                search_term, remove_terms = line[:-1].split(';')
                classes.append((search_term, remove_terms))

        for search_term, remove_terms in classes:
            print(f'Searching: >> {search_term} <<')
            out_name = search_term

            # preprocessing
            remove_items = remove_terms.split(',') if ',' in remove_terms else [remove_terms]

            for i in remove_items:
                out_name = out_name.replace(i.strip(), '')

            out_name = (out_name.strip()
                                .replace('"','')
                                .replace('&', 'and')
                                .replace(' ', '_'))

            raw_folder = os.path.join(tmp, out_name)

            crawl(raw_folder, search_term, crawlers=crawler)

            remove_dups(raw_folder)

            # resize
            out_resized = os.path.join(outpath, out_name)
            os.makedirs(out_resized, exist_ok=True)

            files = glob.glob(raw_folder+'/*')
            resize(files, outpath=out_resized, size=SIZE)

        if keep:
            shutil.copytree(tmp, outpath+'.raw')


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
click.Context.get_usage = click.Context.get_help

@click.command(context_settings=CONTEXT_SETTINGS, epilog=EPILOG)

@click.option('-c', '--crawler', default=['ALL'], 
                    type=click.Choice(['ALL','GOOGLE', 'BING', 'BAIDU']),
                    show_default=True, multiple=True,
                    help='selection of crawler (multiple invocations supported)')

@click.option('-k', '--keep',  default=False, is_flag=True, show_default=True,
                    help='keep original results of crawlers')

@click.option('-s', '--size',  default=299, show_default=True, type=int,
                    help='image size for rescaling')

@click.option('-o', '--outpath',  default='dataset', show_default=True,
                    help='name of output directory')

@click.argument('infile', type=click.File('r'), required=True)

def cli(infile, size, crawler, keep, outpath):
    main(infile, size, crawler, keep, outpath)

if __name__ == "__main__":
    cli()






