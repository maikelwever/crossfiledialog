#!/usr/bin/env python3

import filedialog


def test():
    result = filedialog.open_file(title='choose file')
    if result:
        print(result)


if __name__ == "__main__":
    test()
