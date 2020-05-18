import error
from exprs import *
from location import *
from type import Type


# Keywords cannot be used for function/variable names etc.
keywords = ['val', 'set', 'define', 'call']


class Parser:
    def __init__(self, _filename):
        self.filename = _filename   # Type string
        self._file = None           # Type of open file
        self._file_line = 0         # Type int; line of current point in file.
        self._file_col = 0          # Type int; column of current point in file.
        self._eof = False           # End of file was reached.
        self._parsed_exprs = []     # Type list of Expr's


    def __get_point_loc(self, prev_col=False):
        ''' Return PointLocation of the current location in the file. '''
        col = self._file_col - 1 if prev_col else self._file_col
        return PointLocation(self.filename, self._file_line, col)


    def __eat_whitespace(self):
        '''
        Advance the file until the next non-whitespace character is read.
        Return that first non-whitespace character.
        '''

        while True:
            # Reach a single character.
            c = self._file.read(1)
            self._file_col += 1

            if c == ' ' or c == '\t' or c == '\n':
                if c == '\n':
                    self._file_line += 1
                    self._file_col = 0

                continue

            # Check for end of file.
            if c == '':
                self._eof = True

            return c


    def __parse_word_with_loc(self):
        '''
        Parse a single word, stopping at a whitespace or ')'.

        Return (loc, word), where loc is the location in the file of the word
        that was read.
        '''

        word = self.__eat_whitespace()
        start_point_loc = self.__get_point_loc(True)
        end_point_loc = None

        while True:
            # Read a single character.
            c = self._file.read(1)

            # Check if the end of the word was reached.
            if not c or c == ' ' or c == '\t' or c == '\n' or c == ')':
                # The word ended.
                end_point_loc = self.__get_point_loc()

                if c == '':
                    self._eof = True
                elif c == '\n':
                    self._file_line += 1
                    self._file_col = 0

                break

            word += c
            self._file_col += 1

        assert(end_point_loc is not None)

        return (start_point_loc.span(end_point_loc), word)


    def __parse_word(self):
        ''' Parse and return a single word, stopping at a whitespace or ')'. '''
        (_, word) = self.__parse_word_with_loc()
        return word


    def __parse_type(self):
        ''' Private function to parse a single type. '''
        (loc, word) = self.__parse_word_with_loc()
        return Type.str_to_type(loc, word)


    def __parse_expr(self):
        ''' Private function to parse a single expression. '''
        c = self.__eat_whitespace()
        if c == '':
            # The end of file was reached
            return

        if c != '(':
            loc = self.__get_point_loc(True).span(self.__get_point_loc())
            raise error.InvalidExprStart(loc, '(', c)

        start_point_loc = self.__get_point_loc(prev_col=True)
        word = self.__parse_word()

        if word == 'val':
            return self.__parse_create_var(start_point_loc)
        else:
            print(f'unknown word: "{word}"')


    def __parse_create_var(self, start_point_loc):
        '''
        Private function to parse a single CREATE_VAR expression. The _file
        variable should be in a state starting with (without quotes):
        '<type> <name> <val>)'
        That is, the '(val ' section has alread been read.

        Returns an instance of CreateVar()
        '''

        var_type = self.__parse_type()
        var_name = self.__parse_word()
        var_val = self.__parse_word()
        end_point_loc = self.__get_point_loc()
        loc = start_point_loc.span(end_point_loc)

        # Convert the value to the given type.
        var_val = Type.convert_type(loc, var_type, var_val)

        return CreateVar(loc, var_type, var_name, var_val)


    def parse(self):
        '''
        Read a file of code and return the corresponding list of Expr's.
        '''

        self._file = open(self.filename)

        while not self._eof:
            e = self.__parse_expr()

            if e is not None:
                self._parsed_exprs.append(e)

        self._file.close()

        print('got these expressions:')
        for p in self._parsed_exprs:
            print(p)


def main():
    p = Parser('example.zb')
    p.parse()

main()