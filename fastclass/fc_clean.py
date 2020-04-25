#!/usr/bin/env python
#
# fastclass - fc_clean.py
#
# Christian Werner, 2018-10-23

import click
from collections import deque
from functools import partial
import itertools as it
import os
from pathlib import Path
from PIL import ImageTk, Image
import tkinter as tk
from tkinter import ttk
import shutil

from .imageprocessing import image_pad

EPILOG = """::: FastClass fcc :::\r
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

In the output csv file 1,2 indicate class assignments/ ratings, 
-1 indicates files marked for deletion (if not excluded with -d)."""

# supported suffixes
suffixes = ["jpg", "jpeg", "png", "tif", "tiff"]
suffixes += [x.upper() for x in suffixes]

digits = "123456789"


class Item(object):
    def __init__(self, image_path, size):
        self.image_path = image_path
        self.label = None
        self.size = size

    def __repr__(self):
        return f"Item <{self.image_path} [{self.label if self.label else None}]>"

    def show(self):
        return ImageTk.PhotoImage(image_pad(self.image_path, self.size))


class ItemList(object):
    def __init__(self, items=[], size=(299, 299)):
        self._data = deque([Item(i, size) for i in items])
        self._initial = True

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return ", ".join([str(x) for x in self._data])

    def forward(self):
        self._data.rotate(-1)

    def backward(self):
        self._data.rotate(1)

    @property
    def current(self):
        if len(self._data) > 0:
            return self._data[0]

    @property
    def labels(self):
        return [x.label for x in self._data]


class AppTk(tk.Frame):
    def __init__(self, parent, **kwargs):

        INFOLDER = Path(kwargs["infolder"])
        OUTFOLDER = kwargs["outfolder"]

        if OUTFOLDER is None:
            OUTFOLDER = INFOLDER.parent / (INFOLDER.name + ".clean")
            OUTFOLDER.mkdir(exist_ok=True)
        else:
            OUTFOLDER = Path(OUTFOLDER)

        NOCOPY = kwargs["nocopy"]

        # remove these kwargs before passing them into tk frame
        [kwargs.pop(e) for e in ["infolder", "outfolder", "nocopy"]]

        tk.Frame.__init__(self, parent, **kwargs)
        self.parent = parent

        # bind keys
        self.parent.bind("<Key>", self.callback)

        files = list(it.chain(*[INFOLDER.glob(f"*.{x}") for x in suffixes]))

        self.filelist = sorted(set(files))
        if len(self.filelist) == 0:
            print("No files in infolder.")
            exit(-1)

        self.images = ItemList(items=sorted(set(files)), size=(299, 299))

        self.outfolder = OUTFOLDER
        self.infolder = INFOLDER
        self.nocopy = NOCOPY

        # basic setup
        self.setup()

        # raise window to top
        self.parent.lift()
        self.parent.attributes("-topmost", True)

        # show first image
        self.display()

    @property
    def cur_file(self):
        return self.images.current

    @property
    def no_classified(self):
        return sum(1 for x in self.images.labels if x is not None)

    @property
    def no_total(self):
        return len(self.images)

    @property
    def title(self):
        def get_class():
            label = self.images.current.label
            if label is None:
                label = " "
            return f"[ {label} ] "

        stats = f"{self.no_classified}/{self.no_total}"
        label = (
            f"FastClass :: {self.cur_file.image_path.name} - {get_class()} ({stats})"
        )
        return label

    def print_titlebar(self):
        self.parent.title(self.title)

    def button_callback(self, button):
        self.images.current.label = button
        self.display_next()

    def callback(self, event=None):
        def button_action(char):
            self.images.current.label = char
            self.display_next()

        e = event.keysym
        if e in digits + "d":
            button_action(e)
        elif e == "space":  #'<space>':
            button_action("1")
        elif e == "Left":  #'<Left>':
            self.display_prev()
        elif e == "Right":  #'<Right>':
            self.display_next()
        elif e == "x":
            self.save_and_exit()
        else:
            pass

    def save_and_exit(self):
        # write report file
        rows_all, rows_clean = [], []
        for f in self.images:
            row = (f.image_path, f.label if f.label else "?")

            if f.label is not "d":
                rows_clean.append(row)
            rows_all.append(row)

        for ftype, rows in zip(["all", "clean"], [rows_all, rows_clean]):
            foutname = Path(
                str(self.infolder).replace(" ", "_") + f"_report_{ftype}.csv"
            )
            with open(foutname, "w") as f:
                f.write("file;rank\n")
                for row in sorted(rows, key=lambda x: x[0]):
                    f.write(";".join([str(x) for x in row]) + "\n")

        if not self.nocopy:
            for r in rows_clean:
                shutil.copy(r[0], self.outfolder)

        self.parent.destroy()

    def setup(self):
        self.Canvas = tk.Label(self)
        self.Canvas.grid(row=0, column=0, columnspan=6, rowspan=6)
        ttk.Button(self, text="Prev", command=self.display_prev).grid(row=4, column=6)
        ttk.Button(self, text="Next", command=self.display_next).grid(row=4, column=7)
        ttk.Button(self, text="Save & Exit", command=self.save_and_exit).grid(
            row=5, column=6, columnspan=2
        )

        self.lfdata = ttk.Labelframe(self, padding=(2, 2, 4, 4), text="Selection")
        self.lfdata.grid(row=0, column=6, columnspan=2, sticky="ne")
        for i, item in enumerate(digits + "d"):
            ttk.Button(
                self.lfdata, text=item, command=partial(self.button_callback, item)
            ).grid(in_=self.lfdata, column=6 + i % 2, row=i // 2, sticky="w")

    def display(self):
        photoimage = self.images.current.show()
        self.Canvas.config(image=photoimage)
        self.Canvas.image = photoimage
        self.print_titlebar()

    def display_next(self):
        self.images.forward()
        self.display()

    def display_prev(self):
        self.images.backward()
        self.display()


def main(INFOLDER, OUTFOLDER, nocopy):
    root = tk.Tk()
    root.title("FastClass")

    app = AppTk(root, infolder=INFOLDER, outfolder=OUTFOLDER, nocopy=nocopy)

    app.grid(row=0, column=0, columnspan=8, rowspan=6)
    app.configure(background="gray90")

    # start event loop
    root.lift()
    root.attributes("-topmost", True)
    root.after_idle(root.attributes, "-topmost", False)

    from os import system
    from platform import system as platform

    if platform() == "Darwin":  # How Mac OS X is identified by Python
        script = 'tell application "System Events" \
        to set frontmost of the first process whose unix id is {pid} to true'.format(
            pid=os.getpid()
        )
        os.system("/usr/bin/osascript -e '{script}'".format(script=script))

    root.mainloop()


# Cli - command line arguments
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
click.Context.get_usage = click.Context.get_help


@click.command(context_settings=CONTEXT_SETTINGS, epilog=EPILOG)
@click.option(
    "--nocopy",
    default=False,
    show_default=True,
    help="disable filecopy for cleaned image set",
)
@click.argument("infolder", type=click.Path(exists=True), required=True)
@click.argument("outfolder", type=click.Path(exists=False), required=False)
def cli(infolder, outfolder, nocopy):
    """FastClass fcc"""

    main(infolder, outfolder, nocopy)


if __name__ == "__main__":
    cli()
