# fastclass
A little tool to weed through images, delete and classify them into groups for building NN image datasets (based on tkinter).

## Usage
Simply install the requirements (if you are using Python2 you need to install Tkinter, not tkinter). Then call the scrpt from the commandline. If you omit any input parameters it will show you the help page.

```
Usage: fastclass.py [OPTIONS] INFOLDER [OUTFILE]

  FastClass image classifier

Options:
  -c, --copy         Copy files into class folder after completion  [default:
                     False]
  -d, --delete TEXT  Exclude deleted files from output csv file  [default:
                     True]
  -e, --ext TEXT     Image file extention to look for  [default: jpg]
  -w, --wipe TEXT    Wipe exiting output folders if copy is requested
                     [default: False]
  -h, --help         Show this message and exit.

  ::: FastClass ::: ...a fast way to cleanup/ sort your images when building
  a dataset for conv nets.

  Note: In the application use the following keys: <1>, <2> for class
  assignments <d> to mark a deletion <x> to terminate the app/ write output

  Use the buttons to navigate back and forth without changing the
  classification. The current classification of an image is given in the
  title bar (X indicated a mark for deletion). The counter in the titlebar
  gives number of classified images vs the total number in the input folder.
```


