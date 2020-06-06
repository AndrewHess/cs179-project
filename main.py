from generator import Generator

import os.path
import subprocess
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
    parallelized = g.generate(int(sys.argv[2]))

    # The generator outputs cpp, cuda, and Makefile files, but does not run
    # `make', so do that now.
    (dir_path, file) = os.path.split(sys.argv[1])
    process = subprocess.Popen('make', cwd=dir_path, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    (output, error) = process.communicate()

    # The `make' program only has a non-zero return code if an error occured.
    # Warnings do not yield a non-zero return code.
    if process.returncode != 0:
        # Print the errors for the user.
        print(f'{error.decode("utf-8")}')
        return process.returncode

    # Run the executable created by `make'.
    dir_path = '.' if dir_path == '' else dir_path
    executable = file[:file.rfind('.')]
    process = subprocess.Popen(f'{dir_path}/{executable}',
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    (output, error) = process.communicate()
    print(f'{output.decode("utf-8")}', end='')
    print(f'{error.decode("utf-8")}', end='')


if __name__ == '__main__':
    main()
