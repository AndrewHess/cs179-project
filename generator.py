import error
from expr import ExprEnum
from parser import Parser
from type import Type


class Generator:
    ''' A class to read parsed code and output C++ and CUDA code. '''
    def __init__(self, _in_filename, _out_filename):
        self.in_filename = _in_filename
        self.out_filename = _out_filename
        self._out_file = None    # The result from open(_out_filename)


    def __translate_expr(self, expr):
        ''' Get a single parsed expression and write the equivalent C++ and
            CUDA code to the output file.
        '''
        if expr.exprClass == ExprEnum.LITERAL:
            self.__translate_literal_expr(expr)
        elif expr.exprClass == ExprEnum.CREATE_VAR:
            self.__translate_create_var_expr(expr)
        elif expr.exprClass == ExprEnum.SET_VAR:
            self.__translate_set_var_expr(expr)
        elif expr.exprClass == ExprEnum.GET_VAR:
            self.__translate_get_var_expr(expr)
        elif expr.exprClass == ExprEnum.DEFINE:
            self.__translate_define_expr(expr)
        elif expr.exprClass == ExprEnum.CALL:
            self.__translate_call_expr(expr)


    def __translate_literal_expr(self, expr):
        ''' Get a single parsed LITERAL expression and write the equivalent
            C++ and CUDA code to the output file.
        '''

        code = ''
        if expr.type == Type.STRING:
            code = f'"{expr.val}" '
        else:
            code = f'{expr.val} '

        self._out_file.write(code)
        return


    def __translate_create_var_expr(self, expr):
        ''' Get a single parsed CREATE_VAR expression and write the equivalent
            C++ and CUDA code to the output file.
        '''

        code = ''
        if expr.type == Type.INT:
            code = f'int {expr.name} = {expr.val};\n'
        elif expr.type == Type.FLOAT:
            code = f'float {expr.name} = {expr.val};\n'
        elif expr.type == Type.STRING:
            size = len(expr.val) + 1  # Add 1 for the null terminator.
            code = f'\nchar *{expr.name} = malloc({size});\n' + \
                   f'if ({expr.name} == NULL) {"{"}\n' + \
                   f'    printf("failed to allocate {size} bytes\\n");\n' + \
                   f'    exit(1);\n' + \
                   f'{"}"}\n' + \
                   f'*{expr.name} = "{expr.val}";\n\n'

        self._out_file.write(code)
        return


    def __translate_set_var_expr(self, expr):
        ''' Get a single parsed SET_VAR expression and write the equivalent
            C++ and CUDA code to the output file.
        '''

        code = ''
        if expr.type == Type.STRING:
            size = len(expr.val) + 1  # Add 1 for the null terminator.
            code = f'if (realloc({expr.name}, size) == NULL) {"{"}\n' + \
                   f'    printf("failed to get space for {size} bytes\\n");\n' + \
                   f'    exit(1);\n' + \
                   f'{"}"}\n' + \
                   f'*{expr.name} = {expr.val};\n\n'
        else:
            code = f'{expr.name} = {expr.val};\n'

        self._out_file.write(code)
        return


    def __translate_get_var_expr(self, expr):
        ''' Get a single parsed GET_VAR expression and write the equivalent
            C++ and CUDA code to the output file.
        '''

        self._out_file.write(f'{expr.name} ')
        return


    def __translate_define_expr(self, expr):
        ''' Get a single parsed DEFINE expression and write the equivalent
            C++ and CUDA code to the output file.
        '''

        return_type = Type.enum_to_c_type(expr.loc, expr.return_type)
        code = f'{return_type} {expr.name} ('

        # Add the parameters.
        for (arg_type, arg_name) in expr.args[:-1]:
            code += f'{Type.enum_to_c_type(expr.loc, arg_type)} {arg_name}, '

        # The last parameter is a little different.
        if len(expr.args) > 0:
            (arg_type, arg_name) = expr.args[-1]
            code += f'{Type.enum_to_c_type(expr.loc, arg_type)} {arg_name}'
        code += ') {\n'

        self._out_file.write(code)

        # Add the body of the function.
        for e in expr.body[:-1]:
            self.__translate_expr(e)

        # The last expression should be returned.
        if len(expr.body) == 0:
            error_str = 'expected one or more body expressions'
            raise error.Syntax(expr.loc, error_str)

        e = expr.body[-1]
        if e.exprClass != ExprEnum.LITERAL and e.exprClass != ExprEnum.GET_VAR:
            error_str = 'expected literal or variable as last body expression'
            raise error.Syntax(expr.loc, error_str)

        self._out_file.write('return ')
        self.__translate_expr(e);
        self._out_file.write(';\n}\n\n')

        return


    def __translate_call_expr(self, expr):
        ''' Get a single parsed CALL expression and write the equivalent
            C++ and CUDA code to the output file.
        '''

        return




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

        # Convert each expression to C++ and CUDA code, writing the result to
        # the output file.
        self._out_file = open(self.out_filename, 'w')
        for expr in parsed_exprs:
            self.__translate_expr(expr)

        self._out_file.close()


def main():
    g = Generator('example.zb', 'example.cpp')
    g.generate()

main()