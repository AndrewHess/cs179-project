from generator import Generator

import sys


def usage(filename):
    print(f'usage: {filename} code_file parallelize')
    print("`parallelize' should be 0 or 1")
    exit(-1)


def main():
    if len(sys.argv) != 3:
        usage(sys.argv[0])

    # The first command line argument should be the script to convert to C++
    # and CUDA. The second command line arguments should be a boolean: True to
    # parallelize the code, and false to just convert it to C++.
    g = Generator(sys.argv[1])
    g.generate(int(sys.argv[2]))


if __name__ == '__main__':
    main()
