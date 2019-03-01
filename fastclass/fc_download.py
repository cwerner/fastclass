#!/usr/bin/env python
#
# fastclass - fc_download.py
#
# Christian Werner, 2018-10-23
#
# TODO:
#  - print report (images per class etc)
#  - check if we need grace periods to avoid blocking

import click
import glob
from icrawler import ImageDownloader
from icrawler.builtin import GoogleImageCrawler, BingImageCrawler, BaiduImageCrawler
import logging
import os
import shutil
import tempfile
from typing import List, Dict

from . deduplicate import remove_dups
from . imageprocessing import resize
from . misc import sanitize_searchstring

EPILOG = """::: FastClass fcd :::\r
\r
...an easy way to crawl the net for images when building a\r
dataset for deep learning.\r
\r
Example: fcd -c GOOGLE -c BING -s 224 example/guitars.csv

"""

class ImageLog:
    """Dummy class to attach registry of source urls to ImageDownloader"""
    registry = {}

class CustomDownloader(ImageDownloader, ImageLog):
    def process_meta(self, task):
        ImageLog.registry[task['filename']] = task['file_url']

def crawl(folder: str, search: str, maxnum:int, crawlers: [List[str]] = ['GOOGLE', 'BING', 'BAIDU']) -> Dict[str, str]:
    """Crawl web sites for images"""
    print('(1) Crawling ...')
    # prepare folders
    os.makedirs(folder, exist_ok=True)

    sources = {}
    if maxnum > 1000:
        print("Max num limited to 1000")
        maxnum = 1000

    for c in crawlers:
        print(f'    -> {c}')
        if c == 'GOOGLE':
            google_crawler = GoogleImageCrawler(
                downloader_cls=CustomDownloader,
                log_level=logging.CRITICAL,
                feeder_threads=1,
                parser_threads=1,
                downloader_threads=4,
                storage={'root_dir': folder})

            google_crawler.crawl(keyword=search, offset=0, max_num=maxnum,
                                min_size=(200,200), max_size=None, file_idx_offset=0)

        if c == 'BING':
            bing_crawler = BingImageCrawler(downloader_cls=CustomDownloader,
                                            log_level=logging.CRITICAL,
                                            downloader_threads=4,
                                            storage={'root_dir': folder})
            bing_crawler.crawl(keyword=search, filters=None, offset=0, max_num=maxnum, file_idx_offset='auto')


        if c == 'BAIDU':
            baidu_crawler = BaiduImageCrawler(downloader_cls=CustomDownloader,
                                    log_level=logging.CRITICAL,
                                    storage={'root_dir': folder})
            baidu_crawler.crawl(keyword=search, offset=0, max_num=maxnum,
                                min_size=(200,200), max_size=None, file_idx_offset='auto')


    return {k: v for k, v in CustomDownloader.registry.items() if k is not None}

def main(infile: str, size: int, crawler: List[str], keep: bool, maxnum:int, outpath: str):
    SIZE=(size,size)
    classes = []

    if 'ALL' in crawler:
        crawler = ['GOOGLE', 'BING']

    if os.path.isdir(outpath):
        print(f'Directory "{outpath}" exists. Would you like to overwrite the directory? [y/n]')
        choice = input().lower()
        while (not (choice is 'y' or 'n')):
            print("Please reply with 'y' or 'n'")
            choice = input().lower()
        if (choice == 'y'):
            shutil.rmtree(outpath)
        else:
            exit(-1)

    os.makedirs(outpath)
    print(f'INFO: final dataset will be located in {outpath}')

    with tempfile.TemporaryDirectory() as tmp:
        for lcnt, line in enumerate(infile):
            if lcnt > 0:
                search_term, remove_terms = line[:-1].split(',')
                classes.append((search_term, remove_terms))

        for search_term, remove_terms in classes:
            print(f'Searching: >> {search_term} <<')
            out_name = sanitize_searchstring(search_term, rstring=remove_terms)
            raw_folder = os.path.join(tmp, out_name)

            source_urls = crawl(raw_folder, search_term, maxnum, crawlers=crawler)
            remove_dups(raw_folder)

            # resize
            out_resized = os.path.join(outpath, out_name)
            os.makedirs(out_resized, exist_ok=True)

            files = sorted(glob.glob(raw_folder+'/*'))

            source_urls = resize(files, outpath=out_resized, size=SIZE, urls=source_urls)

            # write report file
            with open(out_resized + '.log', 'w') as log:
                log.write('image,source\n')
                for item in source_urls:
                    log.write(','.join([item, source_urls[item]]) + '\n')

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

@click.option('-m', '--maxnum', default=1000, show_default=True, type=int,
                    help='maximum number of images per crawler (lower is faster, 1000 is max)')

@click.option('-s', '--size',  default=299, show_default=True, type=int,
                    help='image size for rescaling. Set to 0 to keep original size.')

@click.option('-o', '--outpath',  default='dataset', show_default=True,
                    help='name of output directory')

@click.argument('infile', type=click.File('r'), required=True)

def cli(infile, size, crawler, keep, maxnum, outpath):
    main(infile, size, crawler, keep, maxnum, outpath)

if __name__ == "__main__":
    cli()
