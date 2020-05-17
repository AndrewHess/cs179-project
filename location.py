class Location:
    def __init__(self, _filename, _line, _start_col, _end_col):
        self.filename = _filename       # Type string
        self.line = _line               # Type int
        self.start_col = _start_col     # Type int
        self.end_col = _end_col         # Type int


    def to_string(self):
        file = self.filename
        line = self.line
        sc = self.start_col
        ec = self.end_col

        return f'{file}: line {line}: columns {sc}-{ec}'


    def print(self):
        print(to_string(self))