from analyzer import Analyzer
import error
from expr import ExprEnum
from parser import Parser
from type import Type
from type_checker import TypeChecker

import math


# Map from primitive binary function name to the cpp equivalent function name.
# Note: If this is updated, Parser.parse() must also be updated for the new
# primitive functions to pass type checking and be used.
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
                     'and': '&&',
                     'xor': '^'}

# Map from other primitive functions to the cpp equivalent.
# Note: If this is updated, Parser.parse() must also be updated for the new
# primitive functions to pass type checking and be used.
prim_other_funcs = {'print': 'printf',
                    'not': '!',
                    'rand': '(int) random',
                    'srand': 'srandom',
                    'time': 'time'}


class Generator:
    ''' A class to read parsed code and output C++ and CUDA code. '''
    def __init__(self, _filename):
        # THe filename should be something like /path/to/file.code, so we can
        # extract the extensionless filename: /path/to/code and add extensions
        # for the other required file types. We also extract the base file name
        # without extension: "file". Finally, we extract the path: /path/to
        dot_pos = -1
        for i in range(len(_filename) - 1, -1, -1):
            if _filename[i] == '.':
                dot_pos = i
                break

        if dot_pos == -1:
            raise NameError(f'file {_filename} has no file extension')

        self._filename_no_ext = _filename[:dot_pos]

        last_slash_pos = -1
        for i in range(dot_pos - 1, -1, -1):
            if _filename[i] == '/':
                last_slash_pos = i
                break

        self._base_filename_no_ext = _filename[last_slash_pos + 1: dot_pos]
        self._path = _filename[:last_slash_pos]

        self.in_filename = _filename
        self.cpp_prototypes = []    # List of strings (function prototypes)
        self.cuda_prototypes = []   # List of strings (function prototypes)
        self._indent_jump = 4       # The number of spaces a single indent uses
        self._indent = ''           # String of spaces for indenting output code
        self._para_loop_ind = 0     # The number of parallelized loops so far


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
            CUDA code.

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
        elif expr.exprClass == ExprEnum.IF:
            return self.__translate_if_expr(expr, end)
        elif expr.exprClass == ExprEnum.LOOP:
            return self.__translate_loop_expr(expr, end)
        elif expr.exprClass == ExprEnum.LIST:
            return self.__translate_list_expr(expr, end)
        elif expr.exprClass == ExprEnum.LIST_AT:
            return self.__translate_list_at_expr(expr, end)
        elif expr.exprClass == ExprEnum.LIST_SET:
            return self.__translate_list_set_expr(expr, end)
        elif expr.exprClass == ExprEnum.PRIM_FUNC:
            # There is no need to translate primitive functions into C++/CUDA.
            return ('', '')
        elif expr.exprClass == ExprEnum.PARA_LOOP:
            return self.__translate_parallel_loop_expr(expr, end)
        else:
            error_str = f'unknown expression type: {expr.exprClass}'
            raise error.InternalError(expr.loc, error_str)


    def __translate_literal_expr(self, expr, end=True):
        ''' Get a single parsed LITERAL expression and return the equivalent
            C++ and CUDA code.

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
            C++ and CUDA code.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        cpp = ''
        cuda = ''
        if expr.type == Type.INT:
            (c, cu) = self.__translate_expr(expr.val, False)
            cpp = f'int {expr.name} = {c}'
            cpp += ';\n' if end else ''
            cuda += cu
        elif expr.type == Type.FLOAT:
            (c, cu) = self.__translate_expr(expr.val, False)
            cpp = f'float {expr.name} = {c}'
            cpp += ';\n' if end else ''
            cuda += cu
        elif expr.type == Type.STRING:
            if expr.val.exprClass == ExprEnum.LITERAL:
                size = len(expr.val.val) + 1  # Add 1 for the null terminator.
                cpp = f'\nchar *{expr.name} = malloc({size});\n' + \
                      f'if ({expr.name} == NULL) {"{"}\n' + \
                      f'    printf("failed to allocate {size} bytes\\n");\n' + \
                      f'    exit(1);\n' + \
                      f'{"}"}\n' + \
                      f'*{expr.name} = "{expr.val.val}"'
                cpp += ';\n' if end else ''
            elif expr.val.exprClass == ExprEnum.GET_VAR or \
                 expr.val.exprClass == ExprEnum.CALL:
                (c, cu) = self.__translate_expr(expr.val, False)
                cpp = f'char *{expr.name} = {c}'
                cpp += ';\n' if end else ''
                cuda += cu
            else:
                raise error.Syntax(expr.loc, 'invalid string initialization')

        cpp = self._make_indented(cpp)
        return (cpp, cuda)


    def __translate_set_var_expr(self, expr, end=True):
        ''' Get a single parsed SET_VAR expression and return the equivalent
            C++ and CUDA code.

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
            cpp += ';\n' if end else ''
        else:
            (c, cu) = self.__translate_expr(expr.val, False)
            cpp = f'{expr.name} = {c}'
            cpp += ';\n' if end else ''
            cuda += cu

        cpp = self._make_indented(cpp)
        return (cpp, cuda)


    def __translate_get_var_expr(self, expr, end=True):
        ''' Get a single parsed GET_VAR expression and return the equivalent
            C++ and CUDA code.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        cpp = f'{expr.name}'
        cuda = ''

        cpp = self._make_indented(cpp)
        return (cpp, cuda)


    def __translate_define_expr(self, expr, end=True):
        ''' Get a single parsed DEFINE expression and return the equivalent
            C++ and CUDA code.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        cpp = ''
        cuda = ''

        return_type = Type.enum_to_c_type(expr.loc, expr.type)
        cpp = f'{return_type} {expr.name}('

        # Add the parameters.
        for (arg_type, arg_name) in expr.args[:-1]:
            cpp += f'{Type.enum_to_c_type(expr.loc, arg_type)} {arg_name}, '

        # The last parameter is a little different.
        if len(expr.args) > 0:
            (arg_type, arg_name) = expr.args[-1]
            cpp += f'{Type.enum_to_c_type(expr.loc, arg_type)} {arg_name}'
        cpp += ')'

        # Add this prototype for use in a header file.
        self.cpp_prototypes.append(cpp + ';\n')

        cpp += ' {\n'

        # Add the body of the function.
        body_cpp = ''
        for e in expr.body[:-1]:
            (c, cu) = self.__translate_expr(e, True)
            body_cpp += c
            cuda += cu

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

        (c, cu) = self.__translate_expr(e, False)
        body_cpp += f'return {c};\n'
        cuda += cu

        self._increase_indent()
        body_cpp = self._make_indented(body_cpp)
        self._decrease_indent()

        cpp = self._make_indented(cpp)
        cpp = cpp + body_cpp + self._make_indented('}\n\n')

        return (cpp, cuda)


    def __translate_call_expr(self, expr, end=True):
        ''' Get a single parsed CALL expression and return the equivalent
            C++ and CUDA code.

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
            and return the equivalent C++ and CUDA code.

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
            code.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        expr.name = prim_other_funcs[expr.name]
        return self.__translate_call_user_expr(expr, end)


    def __translate_call_user_expr(self, expr, end=True):
        ''' Get a single parsed CALL expression for a user defined function
            and return the equivalent C++ and CUDA code.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        cpp = f'{expr.name}('
        cuda = ''

        # Add the arguments.
        for e in expr.params[:-1]:
            (c, cu) = self.__translate_expr(e, False)
            cpp += f'{c}, '
            cuda += cu

        # The last argument should not have a following comma.
        if len(expr.params) > 0:
            (c, cu) = self.__translate_expr(expr.params[-1], False)
            cpp += f'{c}'
            cuda += cu

        cpp += ')'
        cpp += ';\n' if end else ''

        cpp = self._make_indented(cpp)
        return (cpp, cuda)


    def __translate_if_expr(self, expr, end=True):
        ''' Get a single parsed IF expression and return the equivalent
            C++ and CUDA code.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        cpp = f'if '
        cuda = ''

        # Add the condition.
        cpp += f'({self.__translate_expr(expr.cond, end=False)[0]}) {"{"}\n'

        # Add the 'then' statements.
        for e in expr.then:
            (c, cu) = self.__translate_expr(e, end=False)
            cpp += (' ' * self._indent_jump) + f'{c};\n'
            cuda += cu

        # Close the 'if' section and start the 'else' section.
        cpp += '} else {\n'

        # Add the 'else' statements.
        for e in expr.otherwise:
            (c, cu) = self.__translate_expr(e, end=False)
            cpp += (' ' * self._indent_jump) + f'{c};\n'
            cuda += cu

        # Close the 'else' block.
        cpp += '}\n'

        cpp = self._make_indented(cpp)
        return (cpp, cuda)


    def __translate_loop_expr(self, expr, end=True):
        ''' Get a single parsed LOOP expression and return the equivalent
            C++ and CUDA code.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        cpp = 'for '
        cuda = ''

        # Add the beginning expressions for the loop.
        cpp += '('
        cpp += f'{self.__translate_expr(expr.init, end=False)[0]}; '
        cpp += f'{self.__translate_expr(expr.test, end=False)[0]}; '
        cpp += f'{self.__translate_expr(expr.update, end=False)[0]}'
        cpp += ') {\n'

        # Add the body expressions.
        for e in expr.body:
            (c, cu) = self.__translate_expr(e, end=False)
            cpp += (' ' * self._indent_jump) + f'{c};\n'
            cuda += cu

        # Close the loop.
        cpp += '}\n'

        cpp = self._make_indented(cpp)
        return (cpp, cuda)


    def __translate_list_expr(self, expr, end=True):
        ''' Get a single parsed LIST expression and return the equivalent
            C++ and CUDA code.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        cpp = ''
        cuda = ''

        cpp += f'{Type.enum_to_c_type(expr.loc, expr.elem_type)} '
        cpp += f'{expr.name}[{self.__translate_expr(expr.size, end=False)[0]}]'
        cpp += ';\n' if end else ''

        cpp = self._make_indented(cpp)
        return (cpp, cuda)


    def __translate_list_at_expr(self, expr, end=True):
        ''' Get a single parsed LIST_AT expression and return the equivalent
            C++ and CUDA code.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        cpp = ''
        cuda = ''

        cpp += f'{expr.name}[{self.__translate_expr(expr.index, end=False)[0]}]'
        cpp += ';\n' if end else ''

        cpp = self._make_indented(cpp)
        return (cpp, cuda)


    def __translate_list_set_expr(self, expr, end=True):
        ''' Get a single parsed LIST_SET expression and return the equivalent
            C++ and CUDA code.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        cpp = ''
        cuda = ''

        cpp += f'{expr.name}[{self.__translate_expr(expr.index, end=False)[0]}]'
        cpp += f' = {self.__translate_expr(expr.val, end=False)[0]}'
        cpp += ';\n' if end else ''

        cpp = self._make_indented(cpp)
        return (cpp, cuda)


    def __translate_parallel_loop_expr(self, expr, end=True):
        ''' Get a single parsed PARA_LOOP expression and return the equivalent
            C++ and CUDA code.

            If 'end' is false, then the final characters of the expression,
            like semi-colons and newlines, are not added.
        '''

        cpp = ''
        cuda = ''

        # Get a unique name for the cuda kernel.
        self._para_loop_ind += 1
        cuda_kernel_name = f'cuda_loop{self._para_loop_ind}_kernel'

        # Determine the number of blocks and threads to use.
        threads_per_block = min(512, expr.iterations)
        blocks = min(32, math.ceil(expr.iterations / threads_per_block))

        # Make device variables if necessary.
        dev_vars = []
        for var_name in expr.used_vars:
            dev_name = f'dev_{var_name}'
            dev_vars.append(dev_name)
            var_type = expr.env.lookup_variable(expr.loc, var_name)


            print(f'setting up device variable for {var_name} with type {var_type}')

            if var_type == Type.INT or var_type == Type.FLOAT:
                pass
            elif var_type == Type.LIST_INT:
                # TODO: use the actual size of the list. This can be a little
                #       difficult becuase the list could be passed through a
                #       function.
                size = expr.start_index + expr.iterations
                size_str = f'{size} * sizeof(int)'

                # Allocate memory.
                cpp += f'int *{dev_name};\n'
                cpp += f'cudaMalloc((void **) &{dev_name}, {size_str});\n'

                # Copy the data from host to device.
                cpp += f'cudaMemcpy({dev_name}, {var_name}, {size_str}, '
                cpp += f'cudaMemcpyHostToDevice);\n'
            elif var_type == Type.LIST_FLOAT:
                # TODO: use the actual size of the list. This can be a little
                #       difficult becuase the list could be passed through a
                #       function.
                size = expr.start_index + expr.iterations
                size_str = f'{size} * sizeof(float)'

                # Allocate memory.
                cpp += f'float *{dev_name};\n'
                cpp += f'cudaMalloc((void **) &{dev_name}, {size_str});\n'

                # Copy the data from host to device.
                cpp += f'cudaMemcpy({dev_name}, {var_name}, {size_str}, '
                cpp += f'cudaMemcpyHostToDevice);\n'
            elif var_type == Type.STRING or var_type == Type.LIST_STRING:
                error_str = 'strings not yet allowed in parallelization'
                raise error.InternalError(expr.loc, error_str)

        # Call the kernel.
        cpp += f'{cuda_kernel_name}<<<{blocks}, {threads_per_block}>>>'
        cpp += f'({", ".join(dev_vars)});\n'

        # Copy the data back from device to host.
        for var_name in expr.used_vars:
            dev_name = f'dev_{var_name}'
            var_type = expr.env.lookup_variable(expr.loc, var_name)

            if var_type == Type.INT or var_type == Type.FLOAT:
                # There is no need to copy the variable back, because C++
                # passes it by value and so the value did not change.
                pass
            elif var_type == Type.LIST_INT:
                # TODO: use the actual size of the list. This can be a little
                #       difficult becuase the list could be passed through a
                #       function.
                size = expr.start_index + expr.iterations
                size_str = f'{size} * sizeof(int)'

                # Copy the data from host to device.
                cpp += f'cudaMemcpy({var_name}, {dev_name}, {size_str}, '
                cpp += f'cudaMemcpyDeviceToHost);\n'
            elif var_type == Type.LIST_FLOAT:
                # TODO: use the actual size of the list. This can be a little
                #       difficult becuase the list could be passed through a
                #       function.
                size = expr.start_index + expr.iterations
                size_str = f'{size} * sizeof(float)'

                # Copy the data from host to device.
                cpp += f'cudaMemcpy({var_name}, {dev_name}, {size_str}, '
                cpp += f'cudaMemcpyDeviceToHost);\n'
            elif var_type == Type.STRING or var_type == Type.LIST_STRING:
                error_str = 'strings not yet allowed in parallelization'
                raise error.InternalError(expr.loc, error_str)

        # Put the code in a new scope because we create variables that are not
        # named by the user, so they may cause name conflicts if they were not
        # in a new scope.
        self._increase_indent()
        cpp = self._make_indented(cpp)
        self._decrease_indent()

        cpp = self._make_indented('{\n') + cpp + self._make_indented('}\n')

        # Setup the cuda code.
        # No return value is needed because results are returned via the input
        # lists.
        cuda += f'__global__ void {cuda_kernel_name}'

        # Add the arguments.
        args = []
        for var_name in expr.used_vars:
            var_type = expr.env.lookup_variable(expr.loc, var_name)
            c_type = Type.enum_to_c_type(expr.loc, var_type)

            if var_type == Type.INT or var_type == Type.FLOAT:
                c_type += ' *'

            if var_name in dev_vars:
                var_name = f'dev_{var_name}'

            args.append(f'{c_type} {var_name}')

        cuda += f'({", ".join(args)})'

        # Add this function prototype for use in a header file.
        self.cuda_prototypes.append(cuda + ';\n')

        cuda += ' {\n'

        # Determine the index in the loop.
        index = expr.index_name
        cuda += f'    int {index} = blockIdx.x * blockDim.x + threadIdx.x;\n\n'

        # Loop over all indices that this thread is responsible for.
        cuda += f'    while ({index} < {expr.iterations}) {"{"}\n'

        for e in expr.body:
            (c, _) = self.__translate_expr(e);
            cuda += c

        cuda += f'        {index} += gridDim.x * blockDim.x;\n'
        cuda += f'    {"}"}\n'
        cuda += f'{"}"}\n\n'

        return (cpp, cuda)


    def generate(self, try_parallelize=True):
        '''
        Get the parsed code from the input file and write equivalent C++ and
        CUDA code to the output file.

        If the try_parallelize parameter is false, the code is just converted
        to C++ without any CUDA code to parallelize it.
        '''

        # Get the parsed versino of the code.
        p = Parser(self.in_filename)  # Type list of Expr's
        try:
            # Parse the code.
            parsed_exprs = p.parse()

            # Typecheck the code. This also updates the type of some of the
            # parsed expressions (updates from unknown type to known type) and
            # addes environment data to the expressions.
            type_checker = TypeChecker(parsed_exprs)
            type_checker.validate_exprs()

            if try_parallelize:
                # Analyze the code to see if some parts can be marked to run in
                # parallel.
                analyzer = Analyzer(parsed_exprs)
                analyzer.analyze()
        except error.Error as e:
            e.print()
            exit(1)

        # Include some useful libraries.
        cpp_file = open(self._filename_no_ext + '.cpp', 'w')
        cpp_file.write('#include <cuda_runtime.h>\n')
        cpp_file.write('#include <stdio.h>\n')
        cpp_file.write('#include <stdlib.h>\n')
        cpp_file.write('#include <time.h>\n')
        cpp_file.write('\n')
        cpp_file.write(f'#include "{self._base_filename_no_ext + ".hpp"}"\n')
        cpp_file.write('\n')

        cuda_file = open(self._filename_no_ext + '.cu', 'w')
        cuda_file.write('#include <cuda_runtime.h>\n')
        cuda_file.write('\n')
        cuda_file.write(f'#include "{self._base_filename_no_ext + ".cuh"}"\n')
        cuda_file.write('\n')

        # Convert each expression to C++ and CUDA code, writing the result to
        # the output file.
        for expr in parsed_exprs:
            (cpp, cuda) = self.__translate_expr(expr)
            cpp_file.write(cpp)
            cuda_file.write(cuda)

        cpp_file.close()

        # Write the header files.
        # TODO: add include guards to the header files.
        hpp_file = open(self._filename_no_ext + '.hpp', 'w')

        for proto in self.cpp_prototypes:
            hpp_file.write(proto)

        cuh_file = open(self._filename_no_ext + '.cuh', 'w')
        for proto in self.cuda_prototypes:
            cuh_file.write(proto)

        # Write the Makefile.
        makefile = open(self._path + '/Makefile', 'w')

        base_name = self._base_filename_no_ext
        cpp_name = self._base_filename_no_ext + '.cpp'
        hpp_name = self._base_filename_no_ext + '.hpp'
        cu_name  = self._base_filename_no_ext + '.cu'
        cuh_name = self._base_filename_no_ext + '.cuh'
        m = ''
        m += f'CUDA_PATH = /usr/local/cuda\n'
        m += f'CUDA_INC_PATH = $(CUDA_PATH)/include\n'
        m += f'CUDA_BIN_PATH = $(CUDA_PATH)/bin\n'
        m += f'CUDA_LIB_PATH = $(CUDA_PATH)/lib64\n'
        m += f'NVCC = $(CUDA_BIN_PATH)/nvcc\n'
        m += f'CUDAFLAGS = -g -dc -Wno-deprecated-gpu-targets --std=c++11 \\\n'
        m += f'            --expt-relaxed-constexpr\n'
        m += f'CUDA_LINK_FLAGS = -dlink -Wno-deprecated-gpu-targets\n'
        m += '\n'
        m += f'GPP=g++\n'
        m += f'CXXFLAGS = -g -Wall -D_REENTRANT -std=c++0x -pthread\n'
        m += f'INCLUDE = -I$(CUDA_INC_PATH)\n'
        m += f'LIBS = -L$(CUDA_LIB_PATH) -lcudart -lcufft -lsndfile\n'
        m += f'\n'
        m += f'all: {base_name}\n'
        m += f'\n'
        m += f'{cpp_name}.o: {cpp_name}\n'
        m += f'\t$(GPP) $(CXXFLAGS) -c -o $@ $(INCLUDE) $<\n'
        m += f'\n'
        m += f'{cu_name}.o: {cu_name}\n'
        m += f'\t$(NVCC) $(CUDAFLAGS) -c -o $@ $<\n'
        m += f'\n'
        m += f'cuda.o: {cu_name}.o\n'
        m += f'\t$(NVCC) $(CUDA_LINK_FLAGS) -o $@ $^\n'
        m += f'\n'
        m += f'{base_name}: {cpp_name}.o {cu_name}.o cuda.o\n'
        m += f'\t$(GPP) $(CXXFLAGS) -o $@ $(INCLUDE) $^ $(LIBS)\n'
        m += f'\n'
        m += f'clean:\n'
        m += f'\trm -f {base_name} *.o\n'
        m += '\n'
        m += f'full_clean: clean\n'
        m += f'\trm -f {cpp_name} {hpp_name} {cu_name} {cuh_name} Makefile\n'
        m += f'\n'
        m += f'.PHONY: clean full_clean\n'

        makefile.write(m)


def main():
    g = Generator('examples/add_lists.zb')
    g.generate(False)

main()
