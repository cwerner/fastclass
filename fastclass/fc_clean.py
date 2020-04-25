#!/usr/bin/env python
#
# fastclass - fc_clean.py
#
# Christian Werner, 2018-10-23

import click
import glob
import itertools as it
import os
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


class AppTk(tk.Frame):
    def __init__(self, parent, **kwargs):

        INFOLDER = kwargs["infolder"]
        OUTFOLDER = kwargs["outfolder"]

        if OUTFOLDER is None:
            OUTFOLDER = INFOLDER + ".clean"
            os.makedirs(OUTFOLDER, exist_ok=True)

        NOCOPY = kwargs["nocopy"]

        # remove these kwargs before passing them into tk frame
        [kwargs.pop(e) for e in ["infolder", "outfolder", "nocopy"]]

        tk.Frame.__init__(self, parent, **kwargs)
        self.parent = parent

        # bind keys
        self.parent.bind("<Key>", self.callback)

        # store classification
        self._class = {f"c{d}": set() for d in digits}
        self._delete = set()

        files = list(it.chain(*[glob.glob(f"{INFOLDER}/*.{x}") for x in suffixes]))

        self.filelist = sorted(set(files))
        if len(self.filelist) == 0:
            print("No files in infolder.")
            exit(-1)

        self.outfolder = OUTFOLDER
        self.infolder = INFOLDER
        self.nocopy = NOCOPY

        self._classified = 0
        self._index = -1

        self.size = (299, 299)

        # basic setup
        self.setup()

        # raise window to top
        self.parent.lift()
        self.parent.attributes("-topmost", True)

        # show first image
        self.display_next()

    @property
    def cur_file(self):
        return self.filelist[self._index]

    @property
    def no_classified(self):
        cnt = 0
        for d in digits:
            if self.cur_file in self._class[f"c{d}"]:
                cnt += len(self._class[f"c{d}"])
        if self.cur_file in self._delete:
            cnt += len(self._delete)
        return cnt

    @property
    def no_total(self):
        return len(self.filelist)

    @property
    def title(self):
        def get_class():
            for d in digits:
                if self.cur_file in self._class[f"c{d}"]:
                    return f"[ {d} ] "
            if self.cur_file in self._delete:
                return "[ X ] "
            return "[   ] "

        return (
            os.path.basename(self.cur_file)
            + " - "
            + get_class()
            + f" ({self.no_classified}/{self.no_total})"
        )

    def print_titlebar(self):
        self.parent.title(self.title)

    def callback(self, event=None):
        def button_action(char):
            self._class[f"c{char}"].add(self.cur_file)
            self.display_next()

        if event.keysym in digits:
            button_action(event.keysym)
        elif event.keysym == "space":  #'<space>':
            button_action("1")
        elif event.keysym == "d":
            self._delete.add(self.cur_file)
            self.display_next()
        elif event.keysym == "Left":  #'<Left>':
            self.display_prev()
        elif event.keysym == "Right":  #'<Right>':
            self.display_next()
        elif event.keysym == "x":

            # write report file
            rows_all, rows_clean = [], []
            for f in self.filelist:
                row = (f, "?")
                for d in digits:
                    if f in self._class[f"c{d}"]:
                        row = (f, d)

                if f in self._delete:
                    row = (f, "D")
                else:
                    rows_clean.append(row)
                rows_all.append(row)

            for ftype, rows in zip(["all", "clean"], [rows_all, rows_clean]):
                with open(
                    os.path.join(
                        self.infolder.replace(" ", "_") + "_report_%s.csv" % ftype
                    ),
                    "w",
                ) as f:
                    f.write("file;rank\n")
                    for row in rows:
                        f.write(";".join(row) + "\n")

            if not self.nocopy:
                for r in rows_clean:
                    shutil.copy(r[0], self.outfolder)

            self.parent.destroy()
        else:
            pass

    def setup(self):
        self.Label = tk.Label(self)
        self.Label.grid(row=0, column=0, columnspan=6, rowspan=6)  # , sticky=tk.N+tk.S)
        self.Button1 = ttk.Button(self, text="Prev", command=self.display_prev)
        self.Button1.grid(row=5, column=7, sticky=tk.S)
        self.Button2 = ttk.Button(self, text="Next", command=self.display_next)
        self.Button2.grid(row=5, column=8, sticky=tk.S)

    def display_next(self):
        self.print_titlebar()
        self._index += 1
        try:
            f = self.cur_file
        except IndexError:
            self._index = -1  # go back to the beginning of the list.
            self.display_next()
            return

        padded_im = image_pad(f, self.size)

        photoimage = ImageTk.PhotoImage(padded_im)
        self.Label.config(image=photoimage)
        self.Label.image = photoimage
        self.print_titlebar()

    def display_prev(self):

        self._index -= 1
        try:
            f = self.cur_file
        except IndexError:
            self._index = -1  # go back to the beginning of the list.
            self.display_next()
            return

        padded_im = image_pad(f, self.size)

        photoimage = ImageTk.PhotoImage(padded_im)
        self.Label.config(image=photoimage)
        self.Label.image = photoimage
        self.print_titlebar()


def main(INFOLDER, OUTFOLDER, nocopy):
    root = tk.Tk()
    root.title("FastClass")

    app = AppTk(root, infolder=INFOLDER, outfolder=OUTFOLDER, nocopy=nocopy)

    app.grid(row=0, column=0)

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
