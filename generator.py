import error
from expr import ExprEnum
from parser import Parser
from type import Type

# Map from primitive binary function name to the cpp equivalent function name.
prim_binary_funcs = {'+': '+',
                     '-': '-',
                     '*': '*',
                     '/': '/',
                     '%': '%',
                     '>': '>',
                     '>=': '>=',
                     '<': '<',
                     '<=': '<=',
                     '==': '==',
                     '!=': '!=',
                     'or': '||',
                     'and': '&&'}

# Map from other primitive functions to the cpp equivalent.
prim_other_funcs = {'print': 'printf',
                    'not': '!'}


class Generator:
    ''' A class to read parsed code and output C++ and CUDA code. '''
    def __init__(self, _in_filename, _out_filename):
        self.in_filename = _in_filename
        self.out_filename = _out_filename
        self._out_file = None    # The result from open(_out_filename)
        self._indent_jump = 4    # The number of spaces a single indent uses
        self._indent = ''        # String of spaces for indenting output code


    def _increase_indent(self):
        self._indent += ' ' * self._indent_jump


    def _decrease_indent(self):
        new_indent_len = len(self._indent) - self._indent_jump
        self._indent = self._indent[:new_indent_len]


    def _make_indented(self, code):
        '''
        Takes a string and returns a new string where 'self._indent' is added
        to the beginning of every non-emtpy line.
        '''

        indented = self._indent
        for (i, c) in enumerate(code[:-1]):
            indented += c

            if c == '\n' and code[i + 1] != '\n':
                indented += self._indent

        if len(code) > 0:
            indented += code[-1]

        return indented


    def __translate_expr(self, expr, end=True):
        ''' Get a single parsed expression and return the equivalent C++ and
            CUDA code to the output file.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''
        if expr.exprClass == ExprEnum.LITERAL:
            return self.__translate_literal_expr(expr, end)
        elif expr.exprClass == ExprEnum.CREATE_VAR:
            return self.__translate_create_var_expr(expr, end)
        elif expr.exprClass == ExprEnum.SET_VAR:
            return self.__translate_set_var_expr(expr, end)
        elif expr.exprClass == ExprEnum.GET_VAR:
            return self.__translate_get_var_expr(expr, end)
        elif expr.exprClass == ExprEnum.DEFINE:
            return self.__translate_define_expr(expr, end)
        elif expr.exprClass == ExprEnum.CALL:
            return self.__translate_call_expr(expr, end)


    def __translate_literal_expr(self, expr, end=True):
        ''' Get a single parsed LITERAL expression and return the equivalent
            C++ and CUDA code to the output file.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        cpp = ''
        cuda = ''
        if expr.type == Type.STRING:
            cpp = f'"{expr.val}"'
        else:
            cpp = f'{expr.val}'

        cpp = self._make_indented(cpp)
        return (cpp, cuda)


    def __translate_create_var_expr(self, expr, end=True):
        ''' Get a single parsed CREATE_VAR expression and return the equivalent
            C++ and CUDA code to the output file.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        cpp = ''
        cuda = ''
        if expr.type == Type.INT:
            (c, _) = self.__translate_expr(expr.val, False)
            cpp = f'int {expr.name} = {c};\n'
        elif expr.type == Type.FLOAT:
            (c, _) = self.__translate_expr(expr.val, False)
            cpp = f'float {expr.name} = {c};\n'
        elif expr.type == Type.STRING:
            if expr.val.exprClass == ExprEnum.LITERAL:
                size = len(expr.val.val) + 1  # Add 1 for the null terminator.
                cpp = f'\nchar *{expr.name} = malloc({size});\n' + \
                      f'if ({expr.name} == NULL) {"{"}\n' + \
                      f'    printf("failed to allocate {size} bytes\\n");\n' + \
                      f'    exit(1);\n' + \
                      f'{"}"}\n' + \
                      f'*{expr.name} = "{expr.val.val}";\n\n'
            elif expr.val.exprClass == ExprEnum.GET_VAR or \
                 expr.val.exprClass == ExprEnum.CALL:
                (c, _) = self.__translate_expr(expr.val, False)
                cpp = f'char *{expr.name} = {c};\n'
            else:
                raise error.Syntax(expr.loc, 'invalid string initialization')

        cpp = self._make_indented(cpp)
        return (cpp, cuda)


    def __translate_set_var_expr(self, expr, end=True):
        ''' Get a single parsed SET_VAR expression and return the equivalent
            C++ and CUDA code to the output file.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        cpp = ''
        cuda = ''

        if expr.type == None:
            print('bad type in __translate_set_var_expr!!!')

        if expr.type == Type.STRING:
            # TODO: use pointer from realloc if not null.
            size = len(expr.val.val) + 1  # Add 1 for the null terminator.
            cpp = f'if (realloc({expr.name}, size) == NULL) {"{"}\n' + \
                  f'    printf("failed to get space for {size} bytes\\n");\n' + \
                  f'    exit(1);\n' + \
                  f'{"}"}\n' + \
                  f'*{expr.name} = {expr.val}'
            cpp += ';\n\n' if end else ''
        else:
            (c, _) = self.__translate_expr(expr.val, False)
            cpp = f'{expr.name} = {c}'
            cpp += ';\n' if end else ''

        cpp = self._make_indented(cpp)
        return (cpp, cuda)


    def __translate_get_var_expr(self, expr, end=True):
        ''' Get a single parsed GET_VAR expression and return the equivalent
            C++ and CUDA code to the output file.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        cpp = f'{expr.name}'
        cuda = ''

        cpp = self._make_indented(cpp)
        return (cpp, cuda)


    def __translate_define_expr(self, expr, end=True):
        ''' Get a single parsed DEFINE expression and return the equivalent
            C++ and CUDA code to the output file.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        cpp = ''
        cuda = ''

        return_type = Type.enum_to_c_type(expr.loc, expr.return_type)
        cpp = f'{return_type} {expr.name}('

        # Add the parameters.
        for (arg_type, arg_name) in expr.args[:-1]:
            cpp += f'{Type.enum_to_c_type(expr.loc, arg_type)} {arg_name}, '

        # The last parameter is a little different.
        if len(expr.args) > 0:
            (arg_type, arg_name) = expr.args[-1]
            cpp += f'{Type.enum_to_c_type(expr.loc, arg_type)} {arg_name}'
        cpp += ') {\n'

        # Add the body of the function.
        body_cpp = ''
        for e in expr.body[:-1]:
            (c, _) = self.__translate_expr(e, True)
            body_cpp += c

        # The last expression should be returned.
        if len(expr.body) == 0:
            error_str = 'expected one or more body expressions'
            raise error.Syntax(expr.loc, error_str)

        e = expr.body[-1]
        if e.exprClass != ExprEnum.LITERAL and \
           e.exprClass != ExprEnum.GET_VAR and \
           e.exprClass != ExprEnum.CALL:
            error_str = 'expected literal, get, or call as last body expression'
            raise error.Syntax(expr.loc, error_str)

        (c, _) = self.__translate_expr(e, False)
        body_cpp += f'return {c};\n'

        self._increase_indent()
        body_cpp = self._make_indented(body_cpp)
        self._decrease_indent()

        cpp = self._make_indented(cpp)
        cpp = cpp + body_cpp + self._make_indented('}\n\n')

        return (cpp, cuda)


    def __translate_call_expr(self, expr, end=True):
        ''' Get a single parsed CALL expression and return the equivalent
            C++ and CUDA code to the output file.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        if expr.name in prim_binary_funcs:
            return self.__translate_call_prim_binary_expr(expr, end)
        elif expr.name in prim_other_funcs:
            return self.__translate_call_prim_other_expr(expr, end)
        else:
            return self.__translate_call_user_expr(expr, end)


    def __translate_call_prim_binary_expr(self, expr, end=True):
        ''' Get a single parsed CALL expression for a primitive binary function
            and return the equivalent C++ and CUDA code to the output file.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        cpp = ''
        cuda = ''

        if len(expr.params) != 2:
            error_str = f'expected 2 arguments but got {len(expr.params)}'
            raise error.Syntax(expr.loc, error_str)

        cpp += '('
        cpp += f'{self.__translate_expr(expr.params[0], False)[0]}'
        cpp += f' {prim_binary_funcs[expr.name]} '
        cpp += f'{self.__translate_expr(expr.params[1], False)[0]}'
        cpp += ')'

        cpp += ';\n' if end else ''
        cpp = self._make_indented(cpp)

        return (cpp, cuda)


    def __translate_call_prim_other_expr(self, expr, end=True):
        ''' Get a single parsed CALL expression for a primitive (but not
            primitive binary) function and return the equivalent C++ and CUDA
            code to the output file.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        expr.name = prim_other_funcs[expr.name]
        return self.__translate_call_user_expr(expr, end)


    def __translate_call_user_expr(self, expr, end=True):
        ''' Get a single parsed CALL expression for a user defined function
            and return the equivalent C++ and CUDA code to the output file.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        cpp = f'{expr.name}('
        cuda = ''

        # Add the arguments.
        for e in expr.params[:-1]:
            (c, _) = self.__translate_expr(e, False)
            cpp += f'{c}, '

        # The last argument should not have a following comma.
        if len(expr.params) > 0:
            (c, _) = self.__translate_expr(expr.params[-1], False)
            cpp += f'{c}'

        cpp += ')'
        cpp += ';\n' if end else ''

        cpp = self._make_indented(cpp)
        return (cpp, cuda)


    def generate(self):
        '''
        Get the parsed code from the input file and write equivalent C++ and
        CUDA code to the output file.
        '''

        # Get the parsed versino of the code.
        p = Parser(self.in_filename)  # Type list of Expr's
        try:
            parsed_exprs = p.parse()
        except error.Error as e:
            e.print()
            exit(1)

        # Include some useful libraries.
        self._out_file = open(self.out_filename, 'w')
        self._out_file.write('#include <stdio.h>\n')
        self._out_file.write('#include <stdlib.h>\n')
        self._out_file.write('\n')

        # Convert each expression to C++ and CUDA code, writing the result to
        # the output file.
        for expr in parsed_exprs:
            (cpp, cuda) = self.__translate_expr(expr)
            self._out_file.write(cpp)

        self._out_file.close()


def main():
    g = Generator('examples/example4.zb', 'examples/example4.cpp')
    g.generate()

main()
