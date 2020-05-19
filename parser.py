import error
from expr import *
from location import *
from type import Type


# Keywords cannot be used for function/variable names etc.
keywords = ['lit', 'val', 'set', 'get', 'define', 'call', 'if', 'then', 'else']


class Parser:
    def __init__(self, _filename):
        self.filename = _filename   # Type string
        self._file = None           # Type of open file
        self._file_line = 1         # Type int; line of current point in file.
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
        Parse a single word, stopping at a whitespace or ')'. If a string is
        encountered, then parse until the end instead of immediately stopping
        at whitespace or ')'

        Return (loc, word), where loc is the location in the file of the word
        that was read.
        '''

        word = self.__eat_whitespace()
        is_string = (word == '\'')
        string_done = False  # Only used if is_string is True
        start_point_loc = self.__get_point_loc(True)
        end_point_loc = None

        while True:
            # Read a single character.
            c = self._file.read(1)

            # Check if the end of the word was reached.
            if not c or string_done or \
               (not is_string and (c in [' ', '\t', '\n', ')'])):
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

            if c == '\'' and is_string:
                string_done = True

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


    def __parse_expr_or_keyword(self):
        '''
        Private function to parse and return a single expression or a keyword.
        Returns either a parsed expression or a string keyword.
        '''

        c = self.__eat_whitespace()
        if c == '':
            # The end of file was reached
            return

        if c == '(':
            # Get the rest of the expression.
            return self.__parse_expr(got_paren=True)
        else:
            # All expressions start with '(', so this must be a keyword.
            (loc, word) = self.__parse_word_with_loc()
            word = c + word

            if word in keywords:
                return word
            else:
                error_str = f'expected expression or keyword but found "{word}"'
                raise error.Syntax(loc, error_str)


    def __parse_expr(self, parsing_exprs_list=False, got_paren=False):
        '''
        Private function to parse and return a single expression.

        If parsing_exprs_list is true, then reading the next non-whitespace
        character as ')' causes this function to return None, indicating that
        there are no more expressions in the list. If parsing_exprs_list is
        false and a ')' is read, an error occurs indicating invalid syntax.

        If got_paren is false, then the expression must start with '('. If
        got_paren is true, then the opening parenthesis was already read so
        the expression should begin with a keyword like lit, val, call, ....
        '''

        if not got_paren:
            # Make sure the expression starts with an open paranthesis.
            c = self.__eat_whitespace()
            if c == '':
                # The end of file was reached
                return

            if parsing_exprs_list and c == ')':
                # The end of the expression list has been reached.
                return None

            if c != '(':
                loc = self.__get_point_loc(True).span(self.__get_point_loc())
                raise error.Syntax(loc, f'expected "(" but found "{c}"')

        start_point_loc = self.__get_point_loc(prev_col=True)
        word = self.__parse_word()

        if word == 'lit':
            return self.__parse_literal(start_point_loc)
        elif word == 'get':
            return self.__parse_get_var(start_point_loc)
        elif word == 'val':
            return self.__parse_create_var(start_point_loc)
        elif word == 'set':
            return self.__parse_set_var(start_point_loc)
        elif word == 'define':
            return self.__parse_define(start_point_loc)
        elif word == 'call':
            return self.__parse_call(start_point_loc)
        elif word == 'if':
            return self.__parse_if(start_point_loc)
        else:
            print(f'unknown word: "{word}"')


    def __parse_literal(self, start_point_loc):
        '''
        Private function to parse a single LITERAL expression. The _file
        variable should be in a state starting with (without quotes):
        '<val>)'
        That is, the '(lit ' section has alread been read.

        Returns an instance of Literal()
        '''

        lit_val = self.__parse_word()
        loc = start_point_loc.span(self.__get_point_loc())

        # Convert the value to the correct type.
        lit_type = Type.get_type_from_string_val(loc, lit_val)
        lit_val = Type.convert_type(loc, lit_type, lit_val)

        return Literal(loc, lit_type, lit_val)


    def __parse_get_var(self, start_point_loc):
        '''
        Private function to parse a single GET_VAR expression. The _file
        variable should be in a state starting with (without quotes):
        '<name>)'
        That is, the '(get ' section has alread been read.

        Returns an instance of GetVar()
        '''

        get_name = self.__parse_word()
        loc = start_point_loc.span(self.__get_point_loc())

        return GetVar(loc, get_name)


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
        var_val = self.__parse_expr()

        # Read the final ')'.
        var_end = self._file.read(1)
        self._file_col += 1

        loc = start_point_loc.span(self.__get_point_loc())

        if var_end != ')':
            raise error.Syntax(loc, f'expected ")" but got "{var_end}"')

        # # Convert the value to the given type.
        # var_val = Type.convert_type(loc, var_type, var_val)

        return CreateVar(loc, var_type, var_name, var_val)


    def __parse_set_var(self, start_point_loc):
        '''
        Private function to parse a single SET_VAR expression. The _file
        variable should be in a state starting with (without quotes):
        '<name> <val>)'
        That is, the '(set ' section has alread been read.

        Returns an instance of SetVar()
        '''

        set_name = self.__parse_word()
        set_val = self.__parse_expr()

        # Read the final ')'.
        set_end = self._file.read(1)
        self._file_col += 1

        loc = start_point_loc.span(self.__get_point_loc())

        if set_end != ')':
            raise error.Syntax(loc, f'expected ")" but got "{set_end}"')

        # # Convert the value to the correct type.
        # set_type = Type.get_type_from_string_val(loc, set_val)
        # set_val = Type.convert_type(loc, set_type, set_val)
        set_type = None

        return SetVar(loc, set_type, set_name, set_val)


    def __parse_define(self, start_point_loc):
        '''
        Private function to parse a single DEFINE expression. The _file
        variable should be in a state starting with (without quotes):
        '<name> (<arg1> <arg2> ...) <body1> <body2> ...)'
        That is, the '(define ' section has alread been read.

        Returns an instance of Define()
        '''

        # Get the return type and function name.
        def_return_type = self.__parse_type()
        def_name = self.__parse_word()

        # Parse the ':' between function name and start of arguments.
        c = self.__eat_whitespace()
        if c == '':
            # The end of file was reached.
            loc = self.__get_point_loc(True).span(self.__get_point_loc())
            raise error.Syntax(loc, f'unexpected end of file')

        if c != ':':
            loc = self.__get_point_loc(True).span(self.__get_point_loc())
            raise error.Syntax(loc, f'expected ":" but found "{c}"')

        # Parse the arguments.
        def_args = []

        while True:
            (l, maybe_type) = self.__parse_word_with_loc()

            # Check if the end of the arguments has been reached.
            if maybe_type == ':':
                break

            # There is another argument to parse.
            arg_type = Type.str_to_type(l, maybe_type)
            arg_name = self.__parse_word()

            def_args.append((arg_type, arg_name))

        # Parse the body expressions.
        def_body = []

        while True:
            e = self.__parse_expr(parsing_exprs_list=True)

            if e is None:
                break

            def_body.append(e)

        # Now the entire function has been parsed.
        loc = start_point_loc.span(self.__get_point_loc())
        return Define(loc, def_return_type, def_name, def_args, def_body)


    def __parse_call(self, start_point_loc):
        '''
        Private function to parse a single CALL expression. The _file
        variable should be in a state starting with (without quotes):
        '<name> <arg1_expr> <arg2_expr> ...)'
        That is, the '(call ' section has alread been read.

        Returns an instance of Call()
        '''

        call_name = self.__parse_word()
        call_params = []

        # Parse the ':' between function name and start of arguments.
        c = self.__eat_whitespace()
        if c == '':
            # The end of file was reached.
            loc = self.__get_point_loc(True).span(self.__get_point_loc())
            raise error.Syntax(loc, f'unexpected end of file')

        if c != ':':
            loc = self.__get_point_loc(True).span(self.__get_point_loc())
            raise error.Syntax(loc, f'expected ":" but found "{c}"')

        # Parse the argumnts, if any.
        while True:
            e = self.__parse_expr(parsing_exprs_list=True)

            if e is None:
                break

            call_params.append(e)

        # Now the entire call has been parsed.
        loc = start_point_loc.span(self.__get_point_loc())
        return Call(loc, call_name, call_params)


    def __parse_if(self, start_point_loc):
        '''
        Private function to parse a single IF expression. The _file
        variable should be in a state starting with (without quotes):
        '<cond> then <e1> <e2> ... else <e1> <e2> ...)'
        That is, the '(if ' section has alread been read.

        Returns an instance of If()
        '''

        # Parse the condition expression.
        if_cond = self.__parse_expr()

        # After the condition there should be the 'then' keyword
        (l, then_word) = self.__parse_word_with_loc()
        if then_word != 'then':
            raise error.Syntax(l, f'expected "then" but got {then_word}')

        # Parse the list of 'then' expressions.
        if_then = []
        while True:
            e = self.__parse_expr_or_keyword()

            # Check if a keyword was read.
            if e in keywords:
                if e == 'else':
                    break
                else:
                    point_l = self.__get_point_loc()
                    point_l.col -= len(e)
                    loc = point_l.span(self.__get_point_loc())

                    raise error.Syntax(loc, f'expected "else" but got {e}')

            # An expression was parsed.
            if_then.append(e)

        # Parse the list of 'else' expressions.
        if_else = []
        while True:
            e = self.__parse_expr(parsing_exprs_list=True)

            if e is None:
                break

            if_else.append(e)

        # Now the entire function has been parsed.
        loc = start_point_loc.span(self.__get_point_loc())
        return If(loc, if_cond, if_then, if_else)


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

        return self._parsed_exprs
