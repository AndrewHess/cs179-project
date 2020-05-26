from generator import Generator

import sys


def main():
    # The first command line argument should be the script to convert to C++
    # and CUDA. The second command line arguments should be a boolean: True to
    # parallelize the code, and false to just convert it to C++.
    g = Generator(sys.argv[1])
    g.generate(sys.argv[2])


if __name__ == '__main__':
    main()
