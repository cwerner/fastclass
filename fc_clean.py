#!/usr/bin/env/ python 
#
# fc_clean.py
# 
# Christian Werner, 2018-10-23

import click
import glob
import os
from PIL import ImageTk, Image
import tkinter as tk
import shutil

EPILOG = """::: FastClass :::\r
...a fast way to cleanup/ sort your images when building a\r
dataset for conv nets.\r
\r
Note:\r
In the application use the following keys:\r
<1>, <2> for class assignments\r
<d> to mark a deletion\r
<x> to terminate the app/ write output\r
\r
Use the buttons to navigate back and forth without changing\r
the classification. The current classification of an image\r
is given in the title bar (X indicated a mark for deletion).\r
The counter in the titlebar gives number of classified images\r
vs the total number in the input folder.\r

In the output csv file 1,2 depcit class asignments, -1 indicates\r
files marked for deletion (if not excluded with -d)."""


class AppTk(tk.Frame):
    def __init__(self, *args, **kwargs):

        INFOLDER = kwargs['infolder']
        OUTFILE  = kwargs['outfile']
        COPY     = kwargs['copy']
        EXT      = kwargs['file_ext']
        DEL      = kwargs['delete']
        WIPE     = kwargs['wipe']
 
        for e in ['infolder', 'outfile', 'copy', 'file_ext', 'delete', 'wipe']:
            kwargs.pop(e)

        tk.Frame.__init__(self,*args,**kwargs)

        # bind keys
        args[0].bind('<Key>', self.callback)
        self.root = args[0]

        # store classification
        self.c1 = set()
        self.c2 = set()
        self.delete  = set()

        # config settings
        self.filelist = sorted(glob.glob(INFOLDER + '/*.' + EXT))
        self.outfile = OUTFILE
        self.infolder = INFOLDER
        self.exclude_del = DEL 
        self.copy = COPY        
        self.wipe = WIPE

        if len(self.filelist) == 0:
            print('No files in infolder.')
            exit(-1)

        self.index=-1
        
        self.size = (299, 299)

        # basic setup
        self.setup()

        # raise window to top
        self.root.lift()
        self.root.attributes("-topmost", True)
    
        # show first image
        self.display_next()
        
    def callback(self, event=None):
        #_key = '{k!r}'.format(k = event.char)
        if event.char == "1":
            print("Class 1")
            #self.ButtonA.config(bg='yellow')
            #self.root.after(100, lambda: self.ButtonA.config(bg='lightgrey'))
            self.c1.add(self.filelist[self.index])
            self.display_next()
        elif event.char == "2":
            print("Class 2")
            #self.ButtonB.config(bg='yellow')
            #self.root.after(100, lambda: self.ButtonB.config(bg='lightgrey'))
            self.c2.add(self.filelist[self.index])
            self.display_next()
        elif event.char == "d":
            print("DELETE!")
            self.delete.add(self.filelist[self.index])
            self.display_next()

        elif event.keysym == 'Left': #'<Left>':
            self.display_prev()

        elif event.keysym == 'Right': #'<Right>':
            self.display_next()


        elif event.char == "x":
            print("Results:")
            
            print("\nCLASS 1:")
            for i in sorted(list(self.c1)):
                print(i)

            print("\nCLASS 2:")
            for i in sorted(list(self.c2)):
                print(i)

            print("\nDELETE:")
            for i in sorted(list(self.delete)):
                print(i)

            # create output folders
            if self.copy:
                ds = ['class1_files', 'class2_files']

                if os.path.exists(ds[0]):
                    if self.wipe:
                        if os.path.exists(ds[0]):
                            print("Wiping existing output folder!")
                            for d in ds:
                                shutil.rmtree('/%s' % d)
                    else:
                        print("Output folders exist and wipe was not requested.")
                        print("Will not copy folders...")
                        self.copy = False

                for d in ds:
                    if not os.path.exists(d):
                        os.makedirs(d)


            if not self.outfile:
                self.outfile = open(os.path.basename(self.infolder) + '_classified.csv', 'w')
            for f in self.filelist:
                if f in self.c1:
                    x = '1'
                    if self.copy:
                        shutil.copy(f, ds[0])
                elif f in self.c2:
                    x = '2'
                    if self.copy:
                        shutil.copy(f, ds[1])                    
                elif f in self.delete:
                    if self.exclude_del:
                        continue
                    x = '-1'
                else:
                    # no decision ignore for output
                    x = '0'                    
                    continue
                out = f + ';' + x + '\n'
                self.outfile.write(out)

            self.outfile.close()

            self.root.destroy()  
        else:
            pass


    def printSomething(self):
        labeled = " - "
        if self.filelist[self.index] in self.c1:
            labeled += "[ 1 ] " 
        if self.filelist[self.index] in self.c2:
            labeled += "[ 2 ] "
        if self.filelist[self.index] in self.delete:
            labeled += "[ X ] "

        total = len(self.filelist) 
        classified = len(self.c1) + len(self.c2) + len(self.delete)

        labeled += " (%d/%d)" % (classified, total)

        self.root.title(os.path.basename( self.filelist[self.index]) + labeled )

    def setup(self):
        self.Label=tk.Label(self)
        self.Label.grid(row=0, column=0, columnspan=6, rowspan=6) #, sticky=tk.N+tk.S)

        self.Button=tk.Button(self, text="Prev", command=self.display_prev)
        self.Button.grid(row=5, column=7, sticky=tk.S)
        self.Button=tk.Button(self, text="Next", command=self.display_next)
        self.Button.grid(row=5, column=8, sticky=tk.S)
        

    def display_next(self):
        self.index+=1
        try:
            f=self.filelist[self.index]
        except IndexError:
            self.index=-1  #go back to the beginning of the list.
            self.display_next()
            return

        im = Image.open(f)
        im.thumbnail(self.size, Image.ANTIALIAS)

        bg = Image.new('RGBA', self.size, (255, 255, 255, 0))
        bg.paste(im, (int((self.size[0] - im.size[0]) / 2), int((self.size[1] - im.size[1]) / 2)))

        photoimage = ImageTk.PhotoImage(bg)
        self.Label.config(image=photoimage)
        self.Label.image=photoimage
        self.printSomething()


    def display_prev(self):
        self.index-=1
        try:
            f=self.filelist[self.index]
        except IndexError:
            self.index=-1  #go back to the beginning of the list.
            self.display_next()
            return

        im = Image.open(f)
        im.thumbnail(self.size, Image.ANTIALIAS)

        bg = Image.new('RGBA', self.size, (255, 255, 255, 0))
        bg.paste(im, (int((self.size[0] - im.size[0]) / 2), int((self.size[1] - im.size[1]) / 2)))

        photoimage = ImageTk.PhotoImage(bg)
        self.Label.config(image=photoimage)
        self.Label.image=photoimage
        self.printSomething()


def main(INFOLDER, OUTFILE, COPY, EXT, DEL, WIPE):
    root = tk.Tk()
    root.title('FastClass')
    
    app = AppTk(root, infolder=INFOLDER, outfile=OUTFILE, copy=COPY, file_ext=EXT, delete=DEL, wipe=WIPE) 
    app.grid(row=0,column=0)

    # start of nasty hack to give app focus on a mac -----------------------------
    from os import system
    from platform import system as platform
    if platform() == 'Darwin':  # How Mac OS X is identified by Python
        system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
    # end of nasty hack to give app focus on a mac -----------------------------

    # start event loop
    root.mainloop()

# Cli - command line arguments
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
click.Context.get_usage = click.Context.get_help

@click.command(context_settings=CONTEXT_SETTINGS, epilog=EPILOG)
@click.option('-c', '--copy',  is_flag=True, 
                    default=False, show_default=True,
                    help='Copy files into class folder after completion')

@click.option('-d', '--delete', is_flag=True, default=True, show_default=True,
                    help='Exclude deleted files from output csv file')

@click.option('-e', '--ext',  default='jpg', show_default=True,
                    help='Image file extention to look for')

@click.option('-w', '--wipe',  is_flag=True, default=False, show_default=True,
                    help='Wipe existing output folders if copy is requested')


@click.argument('infolder', type=click.Path(exists=True), required=True)
@click.argument('outfile', type=click.File('w'), required=False)

def cli(infolder, outfile, copy, ext, delete, wipe):
    """FastClass Image Classifier"""

    main(infolder, outfile, copy, ext, delete, wipe)

if __name__ == "__main__":
    cli()
