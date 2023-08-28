#!/usr/bin/env python3

import crossfiledialog
from crossfiledialog.win32 import open_file
from crossfiledialog.zenity import open_file


def test():
    # TODO: Windows Testing
    print(open_file(
        start_dir="c:\\Users\\sebas\\OneDrive\\Documents\\Python\\crossfiledialog",
        filter={"PDF-Files": "*.pdf", "Python Project": ["*.py", "*.md"]}
        # filter=[["*.py", "*.txt"], ["*.png", "*.jpg"]]
        # filter=["*.py", "*.md"]
        # filter="*.py"
    ))
    # print(crossfiledialog.open_multiple())
    # print(crossfiledialog.save_file())
    # print(crossfiledialog.choose_folder())


if __name__ == "__main__":
    test()
