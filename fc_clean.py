#!/usr/bin/env python 
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

EPILOG = """::: FastClass fc_clean :::\r
...a fast way to cleanup/ sort your images when building a\r
dataset for deep learning.\r
\r
Note:\r
In the application use the following keys:\r
<1>, <2>, ... <9> for class assignments or quality ratings\r
<space> assigns <1>\r
<d> to mark a deletion\r
<x> to terminate the app/ write output\r
\r
Use the buttons to navigate back and forth without changing\r
the classification. The current classification of an image\r
is given in the title bar (X indicated a mark for deletion).\r
The counter in the titlebar gives number of classified images\r
vs the total number in the input folder.\r

In the output csv file 1,2 depcit class assignments/ ratings, 
-1 indicates files marked for deletion (if not excluded with -d)."""


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
        self._class = {f'c{c}': set() for c in range(1,10)}
        self._delete = set()

        # config settings
        self.filelist = sorted(glob.glob(INFOLDER + '/*.' + EXT))
        self.outfile = OUTFILE
        self.infolder = INFOLDER
        self.exclude_del = DEL 
        self.copy = COPY        
        self.wipe = WIPE

        self._classified = 0

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
    
    @property
    def total(self):
        return len(self.filelist)
        
    @property
    def classified(self):
        cnt = 0
        for c in '123456789':
            if self.filelist[self.index] in self._class[f'c{c}']:
                cnt += len(self._class[f'c{c}'])            
        if self.filelist[self.index] in self._delete: 
            cnt += len(self._delete)
        return cnt 

    @property
    def title(self):

        def get_class():
            for c in '123456789':
                if self.filelist[self.index] in self._class[f'c{c}']:
                    return f'[ {c} ] '
            if self.filelist[self.index] in self._delete: 
                return '[ X ] '
            return '[   ] '

        return (os.path.basename( self.filelist[self.index]) + 
                " - " +
                get_class() + 
                f" ({self.classified}/{self.total})")

    def print_titlebar(self):
        self.root.title(self.title)

    def callback(self, event=None):

        def button_action(char):
            self._class[f'c{char}'].add(self.filelist[self.index]) 
            self.display_next()

        if event.char in '123456789':
            button_action(event.char)
        elif event.keysym == 'space': #'<space>':
            button_action('1')
        elif event.char == 'd':
            self._delete.add(self.filelist[self.index])
            self.display_next()
        elif event.keysym == 'Left': #'<Left>':
            self.display_prev()
        elif event.keysym == 'Right': #'<Right>':
            self.display_next()
        elif event.char == "x":
            print("Results:")
            for c in range(1,10):
                print("\nCLASS {c}:")
                for i in sorted(list(self._class[f'c{c}'])): print(i)
            print("\nDELETE:")
            for i in sorted(list(self._delete)): 
                print(i)
            self.root.destroy()  
        else:
            pass


        # #_key = '{k!r}'.format(k = event.char)
        # if event.char == "1":
        #     print("Class 1")
        #     #self.ButtonA.config(bg='yellow')
        #     #self.root.after(100, lambda: self.ButtonA.config(bg='lightgrey'))
        #     self.c1.add(self.filelist[self.index])
        #     self.display_next()
        # elif event.char == "2":
        #     print("Class 2")
        #     #self.ButtonB.config(bg='yellow')
        #     #self.root.after(100, lambda: self.ButtonB.config(bg='lightgrey'))
        #     self.c2.add(self.filelist[self.index])
        #     self.display_next()
        # elif event.char == "d":
        #     print("DELETE!")
        #     self.delete.add(self.filelist[self.index])
        #     self.display_next()

        # elif event.keysym == 'Left': #'<Left>':
        #     self.display_prev()

        # elif event.keysym == 'Right': #'<Right>':
        #     self.display_next()


        # elif event.char == "x":
        #     print("Results:")
            
        #     print("\nCLASS 1:")
        #     for i in sorted(list(self.c1)):
        #         print(i)

        #     print("\nCLASS 2:")
        #     for i in sorted(list(self.c2)):
        #         print(i)

        #     print("\nDELETE:")
        #     for i in sorted(list(self.delete)):
        #         print(i)

        #     # create output folders
        #     if self.copy:
        #         ds = ['class1_files', 'class2_files']

        #         if os.path.exists(ds[0]):
        #             if self.wipe:
        #                 if os.path.exists(ds[0]):
        #                     print("Wiping existing output folder!")
        #                     for d in ds:
        #                         shutil.rmtree('/%s' % d)
        #             else:
        #                 print("Output folders exist and wipe was not requested.")
        #                 print("Will not copy folders...")
        #                 self.copy = False

        #         for d in ds:
        #             if not os.path.exists(d):
        #                 os.makedirs(d)


        #     if not self.outfile:
        #         self.outfile = open(os.path.basename(self.infolder) + '_classified.csv', 'w')
        #     for f in self.filelist:
        #         if f in self.c1:
        #             x = '1'
        #             if self.copy:
        #                 shutil.copy(f, ds[0])
        #         elif f in self.c2:
        #             x = '2'
        #             if self.copy:
        #                 shutil.copy(f, ds[1])                    
        #         elif f in self.delete:
        #             if self.exclude_del:
        #                 continue
        #             x = '-1'
        #         else:
        #             # no decision ignore for output
        #             x = '0'                    
        #             continue
        #         out = f + ';' + x + '\n'
        #         self.outfile.write(out)

        #     self.outfile.close()

        #     self.root.destroy()  
        # else:
        #     pass




    def setup(self):
        self.Label=tk.Label(self)
        self.Label.grid(row=0, column=0, columnspan=6, rowspan=6) #, sticky=tk.N+tk.S)

        self.Button=tk.Button(self, text="Prev", command=self.display_prev)
        self.Button.grid(row=5, column=7, sticky=tk.S)
        self.Button=tk.Button(self, text="Next", command=self.display_next)
        self.Button.grid(row=5, column=8, sticky=tk.S)
        

    def display_next(self):
        self.print_titlebar()
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
        self.print_titlebar()


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
        self.print_titlebar()


def main(INFOLDER, OUTFILE, COPY, EXT, DEL, WIPE):
    root = tk.Tk()
    root.title('FastClass')
    
    app = AppTk(root, infolder=INFOLDER, outfile=OUTFILE, copy=COPY, file_ext=EXT, delete=DEL, wipe=WIPE) 
    app.grid(row=0,column=0)


    # start event loop
    root.lift()
    root.attributes('-topmost',True)
    root.after_idle(root.attributes,'-topmost',False)

    from os import system
    from platform import system as platform

    if platform() == 'Darwin':  # How Mac OS X is identified by Python
        script = 'tell application "System Events" \
        to set frontmost of the first process whose unix id is {pid} to true'.format(pid=os.getpid())
        os.system("/usr/bin/osascript -e '{script}'".format(script=script))

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
    """FastClass fc_clean"""

    main(infolder, outfile, copy, ext, delete, wipe)

if __name__ == "__main__":
    cli()
