from generator import Generator


def main():
    g = Generator('examples/add_lists.zb')
    g.generate(False)


if __name__ == '__main__':
    main()