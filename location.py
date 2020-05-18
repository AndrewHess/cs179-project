class PointLocation:
    def __init__(self, _filename, _line, _col):
        self.filename = _filename       # Type string
        self.line = _line               # Type int
        self.col = _col                 # Type int


    def __less(self, other):
        '''
        Return true if this PointLocation is less than the 'other'
        PointLocation.
        '''

        assert(self.filename == other.filename)

        if self.line != other.line:
            return self.line < other.line

        return self.col < other.col


    def span(self, other):
        '''
        Return a Location spanning this PointLoation and the 'other'
        PointLocation.
        '''

        assert(self.__less(other))
        return Location(self.filename, self.line, other.line,
                        self.col, other.col)


    def to_string(self):
        return f'{self.filename}: line {self.line}: column {self.col}'


    def print(self):
        print(self.to_string())


class Location:
    def __init__(self, _filename, _start_line, _end_line, _start_col, _end_col):
        self.filename = _filename       # Type string
        self.start_line = _start_line   # Type int
        self.end_line = _end_line       # Type int
        self.start_col = _start_col     # Type int
        self.end_col = _end_col         # Type int

        assert(self.start_line <= self.end_line)
        if self.start_line == self.end_line:
            assert(self.start_col <= self.end_col)


    def to_string(self):
        file = self.filename
        sline = self.start_line
        eline = self.end_line
        scol = self.start_col
        ecol = self.end_col

        if sline == eline:
            return f'{file}: line {sline}: columns {sc}-{ec}'

        return f'{file}: lines {sline}-{eline}'


    def print(self):
        print(self.to_string())