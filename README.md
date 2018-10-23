# fastclass
A little set of tools to batch download images and weed through, delete and
classify them into groups for building deep learning image datasets.

## Installation

*pip install git+https://github.com/cwerner/fastclass.git*

The installer will also place the executables *fcc* (fc_clean.py) and *fcd* (fc_download.py)
in your PATH.  

The package currently contains the follwing tools:  

## Download images 

Use **fc_download.py** to crawl search engines (Google, Bing, Baidu) and pull all images for
a defined set of queries. In addition, files are renamed, scaled and checked
for duplicates.

You provide queries and terms that should be excluded when naming the category folders. There
is an example (guitars.csv) provided in the repository. 

### Usage
Call the script from the commandline. If you omit any input parameters it 
will show you the help page.

```
Usage: fcd [OPTIONS] INFILE

Options:
  -c, --crawler [ALL|GOOGLE|BING|BAIDU]
                                  selection of crawler (multiple invocations
                                  supported)  [default: ALL]
  -s, --size INTEGER              image size for rescaling  [default: 299]
  -o, --outpath TEXT              name of output directory  [default: dataset]
  -h, --help                      Show this message and exit.

  ::: FastClass fc_download :::

  ...an easy way to crawl the net for images when building a dataset for
  deep learning.

  Example: fcd -c GOOGLE -c BING -s 224 example/guitars.csv
```

## Clean image sets

Once downloaded use **fc_clean** to quickly inspect the loaded files and rate or
classify them. You can also mark them for deletion.

### Usage
Call the script from the commandline. If you omit any input parameters it
will show you the help page.

```
Usage: fcc [OPTIONS] INFOLDER [OUTFOLDER]

  FastClass fc_clean

Options:
  --nocopy TEXT  disable filecopy for cleaned image set  [default: False]
  -h, --help     Show this message and exit.

  ::: FastClass fc_clean ::: ...a fast way to cleanup/ sort your images when
  building a dataset for deep learning.

  Note: In the application use the following keys: <1>, <2>, ... <9> for
  class assignments or quality ratings <space> assigns <1> <d> to mark a
  deletion <x> to terminate the app/ write output

  Use the buttons to navigate back and forth without changing the
  classification. The current classification of an image is given in the
  title bar (X indicated a mark for deletion). The counter in the titlebar
  gives number of classified images vs the total number in the input folder.

  In the output csv file 1,2 depcit class assignments/ ratings,  -1
  indicates files marked for deletion (if not excluded with -d).
```



