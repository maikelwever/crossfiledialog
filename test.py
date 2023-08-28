#!/usr/bin/env python3

import crossfiledialog
from crossfiledialog.zenity import open_file


def test():
    # TODO: Windows Testing
    print(open_file(
        start_dir="/home/sebastian/Programming/20_Python/21_Projects/PDFCat",
        # filter={"PDF-Files": "*.pdf", "Python Project": ["*.py", "*.md]}
        filter=[["*.py", "*.txt"], ["*.png", "*.jpg"]]
        # filter=["*.py", "*.txt"]
        # filter=".*py"
    ))
    # print(crossfiledialog.open_multiple())
    # print(crossfiledialog.save_file())
    # print(crossfiledialog.choose_folder())


if __name__ == "__main__":
    test()
