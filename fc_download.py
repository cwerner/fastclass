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
import glob
import hashlib
from icrawler.builtin import GoogleImageCrawler, BingImageCrawler, BaiduImageCrawler
import logging
import os
from PIL import Image
import sys
from tqdm import tqdm

EPILOG = """::: FastClass fc_download :::\r
\r
...an easy way to crawl the net for images when building a\r
dataset for deep learning.\r
\r
Example: fcd -c GOOGLE -c BING -s 224 example/guitars.csv

"""

def crawl(DIR, KW, crawlers=['GOOGLE', 'BING', 'BAIDU']):
    print('(1) Crawling ...')
    # prepare folders
    for c in crawlers:
        os.makedirs(DIR+'.'+c.lower(), exist_ok=True)

        if c == 'GOOGLE':
            print('    -> Google')
            google_crawler = GoogleImageCrawler(
                log_level=logging.CRITICAL,
                feeder_threads=1,
                parser_threads=1,
                downloader_threads=4,
                storage={'root_dir': DIR+'.google'})

            google_crawler.crawl(keyword=KW, offset=0, max_num=1000,
                                min_size=(200,200), max_size=None, file_idx_offset=0)
        if c == 'BING':
            print('    -> Bing')
            bing_crawler = BingImageCrawler(log_level=logging.CRITICAL,
                                            downloader_threads=4,
                                            storage={'root_dir': DIR+'.bing'})
            bing_crawler.crawl(keyword=KW, filters=None, offset=0, max_num=1000)

        if c == 'BAIDU':
            print('    -> Baidu')
            baidu_crawler = BaiduImageCrawler(log_level=logging.CRITICAL,
                                    storage={'root_dir': DIR+'.baidu'})
            baidu_crawler.crawl(keyword=KW, offset=0, max_num=1000,
                                min_size=(200,200), max_size=None)

def hashfile(path, blocksize = 65536):
    afile = open(path, 'rb')
    hasher = hashlib.md5()
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    afile.close()
    return hasher.hexdigest()

def findDup(parentFolder, match=None):
    # Dups in format {hash:[names]}
    dups = {}
    for dirName, subdirs, fileList in os.walk(parentFolder):
        print('Scanning %s...' % dirName)
        for filename in fileList:
            # Get the path to the file
            path = os.path.join(dirName, filename)
            # Calculate hash
            file_hash = hashfile(path)
            # Add or append the file path
            if file_hash in dups:
                dups[file_hash].append(path)
            else:
                dups[file_hash] = [path]
    return dups

def remove_dups(folder):
    print('Removing duplicates')

    dups = findDup(folder)
    print(f"Number of duplicate image files: {len(dups)}. Removing...")
    dup_files = [dups[hash] for hash in dups if len(dups[hash]) > 1]
    for d in dup_files:
        # keep first, delete all others
        for rfile in d[1:]:
            os.remove(rfile)


def resize(files, outpath=None, size=(299, 299)):
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
            out = fname + '.jpg'
            if outpath:
                out = os.path.join(outpath, fname + '.jpg')
            bg.save(out)
            t.update(1)
            

def main(infile, size, crawler, outpath):
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

    BASEDIR='tmp'; basedir_ok = False
    basedirs = [BASEDIR] + [f'{BASEDIR}.{i}' for i in range(10)]
    while basedir_ok == False and len(basedirs) > 0:
        try:
            bd = basedirs.pop(0)
            os.makedirs(bd)
            basedir_ok = True
        except OSError:
            print(f'Directory "{bd}" exists...')
    
    if basedir_ok == False:
        print('Please check your local directory')
        exit(-1)
    else:
        print(f'Download data into "{bd}"...')

    for lcnt, line in enumerate(infile):
        if lcnt > 0:
            search_term, remove_terms = line[:-1].split(';')
            classes.append((search_term, remove_terms))

    for search_term, remove_terms in classes:
        print(f'Searching: >> {search_term} <<')
        out_name = search_term

        if ',' in remove_terms:
            remove_items = remove_terms.split(',')
        else:
            remove_items = [remove_terms]

        for i in remove_items:
            out_name = out_name.replace(i, '')

        # the cleaned name of this classes folder
        out_name = out_name.strip().replace('"','').replace('&', 'and').replace(' ', '_')

        DIR= os.path.join(BASEDIR, out_name)

        crawl(DIR, search_term, crawlers=crawler)

        # resize
        out_resized = os.path.join(outpath, out_name)
        os.makedirs(out_resized, exist_ok=True)

        files = glob.glob(DIR+'.*/*')
        resize(files, outpath=out_resized, size=SIZE)
    
    # remove duplicates
    remove_dups(outpath)



CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
click.Context.get_usage = click.Context.get_help

@click.command(context_settings=CONTEXT_SETTINGS, epilog=EPILOG)

@click.option('-c', '--crawler', default=['ALL'], 
                    type=click.Choice(['ALL','GOOGLE', 'BING', 'BAIDU']),
                    show_default=True, multiple=True,
                    help='selection of crawler (multiple invocations supported)')

@click.option('-s', '--size',  default=299, show_default=True, type=int,
                    help='image size for rescaling')

@click.option('-o', '--outpath',  default='dataset', show_default=True,
                    help='name of output directory')

@click.argument('infile', type=click.File('r'), required=True)

def cli(infile, size, crawler, outpath):
    main(infile, size, crawler, outpath)

if __name__ == "__main__":
    cli()






