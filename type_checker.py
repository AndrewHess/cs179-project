import env
import error
from expr import ExprEnum
from type import Type


class TypeChecker:
    ''' Validate types and add environment info for all parsed expressions. '''

    def __init__(self, _parsed_exprs):
        self.parsed_exprs = _parsed_exprs
        self._env = env.Env()


    def __validate_type_of_value(self, loc, t, v):
        ''' Check that the value has the given type. '''
        actual_type = Type.get_type(loc, v)
        if t != actual_type:
            raise error.UnexpectedType(loc, t, actual_type)


    def __validate_type_of_expr(self, loc, t, e):
        ''' Check that the expression has the given type. '''
        if t != e.type:
            raise error.UnexpectedType(loc, t, e.type)


    def __lookup_variable(self, loc, expr_name):
        ''' Find a variable in the environment and return its type. '''

        # Make sure the variable already exists.
        (name, type_lst, is_var) = self._env.get_entry_for_name(expr_name)

        if name is None:
            error_str = f'variable {expr_name} does not exist'
            raise error.Name(loc, error_str)

        if len(type_lst) != 1 or not is_var:
            error_str = f'{expr_name} is a function; expected a variable'
            raise error.Syntax(loc, error_str)

        # Make sure the variable has a type.
        if type_lst == [Type.UNDETERMINED] or type_lst == [Type.NONE]:
            error_str = f'variable {expr_name} has bad type: {type_lst[0]}'
            raise error.Type(loc, error_str)

        return type_lst[0]


    def __lookup_function(self, loc, expr_name):
        '''
        Find a function in the environment.

        Return a tuple with two elements. The first is the return type of the
        function and the second is a list of types for the arguments.
        '''

        # Make sure the function already exists.
        (name, type_lst, is_var) = self._env.get_entry_for_name(expr_name)

        if name is None:
            error_str = f'function {expr_name} does not exist'
            raise error.Name(loc, error_str)

        if is_var:
            error_str = f'{expr_name} is a variable; expected a function'
            raise error.Syntax(loc, error_str)

        if len(type_lst) == 0:
            error_str = f'{expr_name} has no return type'
            raise error.InternalError(loc, error_str)

        # Make sure the function has a return type.
        ret_type = type_lst[0]
        if ret_type == Type.UNDETERMINED or ret_type == Type.NONE:
            error_str = f'function {expr_name} has bad return type: {ret_type}'
            raise error.Type(loc, error_str)

        # Make sure the parameter types are valid.
        for param_type in type_lst[1:]:
            if param_type == Type.UNDETERMINED or param_type == Type.NONE:
                error_str =  f'function {expr_name} has bad '
                error_str += f'paramter type: {param_type}'
                raise error.Type(expr.loc, error_str)

        return (ret_type, type_lst[1:])


    def __validate_single_expr(self, expr):
        ''' Validate one parsed expression and add environment info. '''

        if expr.exprClass == ExprEnum.LITERAL:
            self.__validate_literal_expr_type(expr)
        elif expr.exprClass == ExprEnum.CREATE_VAR:
            self.__validate_create_var_expr_type(expr)
        elif expr.exprClass == ExprEnum.SET_VAR:
            self.__validate_set_var_expr_type(expr)
        elif expr.exprClass == ExprEnum.GET_VAR:
            self.__validate_get_var_expr_type(expr)
        elif expr.exprClass == ExprEnum.DEFINE:
            self.__validate_define_expr_type(expr)
        elif expr.exprClass == ExprEnum.CALL:
            self.__validate_call_expr_type(expr)
        elif expr.exprClass == ExprEnum.IF:
            self.__validate_if_expr_type(expr)
        elif expr.exprClass == ExprEnum.LOOP:
            self.__validate_loop_expr_type(expr)
        elif expr.exprClass == ExprEnum.LIST:
            self.__validate_list_expr_type(expr)
        elif expr.exprClass == ExprEnum.LIST_AT:
            self.__validate_list_at_expr_type(expr)
        elif expr.exprClass == ExprEnum.LIST_SET:
            self.__validate_list_set_expr_type(expr)
        elif expr.exprClass == ExprEnum.PRIM_FUNC:
            self.__validate_list_prim_func_type(expr)
        else:
            error_str = f'unknown expression type: {expr.exprClass}'
            raise error.InternalError(expr.loc, error_str)

        # Set the environment for this expressions.
        expr.env = self._env.copy()


    def __validate_literal_expr_type(self, expr):
        ''' Typecheck and add environment data for a single Literal Expr. '''

        # Literals do not have names, so do not update the environment.
        # Just check that the value has the specified type.
        self.__validate_type_of_value(expr.loc, expr.type, expr.val)


    def __validate_create_var_expr_type(self, expr):
        ''' Typecheck and add environment data for a single CreateVar Expr. '''

        # Make sure the name is not in the current scope.
        if self._env.name_in_scope(expr.name):
            error_str = f'variable {expr.name} already created in this scope'
            raise error.Name(expr.loc, error_str)

        # Validate the expression that the value is set to.
        self.__validate_single_expr(expr.val)

        # Validate the types and update the environment.
        self.__validate_type_of_expr(expr.loc, expr.type, expr.val)
        self._env.add(expr.name, [expr.type], True)


    def __validate_set_var_expr_type(self, expr):
        ''' Typecheck and add environment data for a single SetVar Expr. '''

        if expr.type != Type.UNDETERMINED:
            error_str = f'expected SetVar to have UNDETERMINED type'
            raise error.InternalError(expr.loc, error_str)

        # Get the type of the variable.
        expr_type = self.__lookup_variable(expr.loc, expr.name)

        # Validate the expression that the value is set to.
        self.__validate_single_expr(expr.val)

        # Validate the types and update the expression type. There is no need
        # to update the environment because no function/variable was created.
        self.__validate_type_of_expr(expr.loc, expr_type, expr.val)
        expr.type = expr_type


    def __validate_get_var_expr_type(self, expr):
        ''' Typecheck and add environment data for a single GetVar Expr. '''

        if expr.type != Type.UNDETERMINED:
            error_str = f'expected GetVar to have UNDETERMINED type'
            raise error.InternalError(expr.loc, error_str)

        # Get the type of the variable and set expr.type.
        expr.type = self.__lookup_variable(expr.loc, expr.name)


    def __validate_define_expr_type(self, expr):
        ''' Typecheck and add environment data for a single Define Expr. '''

        # Make sure the name is not in the current scope.
        if self._env.name_in_scope(expr.name):
            error_str = f'function {expr.name} already defined in this scope'
            raise error.Name(expr.loc, error_str)

        # Update the environment before validating the body expressions so that
        # recursive functions are allowed (i.e. the body expression can find
        # the return type of this function).
        func_type = [expr.type]  # This is the return type.

        for arg in expr.args:
            # arg[0] is the type and arg[1] is the name.
            func_type.append(arg[0])

        self._env.add(expr.name, func_type, False)

        # The function body is in a new scope.
        self._env.push_scope()

        # Add the function arguments to the environment so that the body can
        # use them.
        for arg in expr.args:
            # arg[0] is the type and arg[1] is the name.
            self._env.add(arg[1], [arg[0]], True)

        # Validate all of body expressions.
        for e in expr.body:
            self.__validate_single_expr(e)

        # The last body expression is returned from the function, so it must
        # have the correct type.
        if len(expr.body) == 0:
            error_str = f'expected body to have an expression to return'
            raise error.Syntax(expr.loc, error_str)

        ret_expr = expr.body[-1]
        self.__validate_type_of_expr(ret_expr.loc, func_type[0], ret_expr)

        # The function body scope ended.
        self._env.pop_scope(expr.loc)


    def __validate_call_expr_type(self, expr):
        ''' Typecheck and add environment data for a single Call Expr. '''

        if expr.type != Type.UNDETERMINED:
            error_str = f'expected Call to have UNDETERMINED type'
            raise error.InternalError(expr.loc, error_str)

        # The print function can take many arguments after the initial string,
        # so relax the type checking for it becuase optional arguments are not
        # yet supported.
        if expr.name == 'print':
            # The first argument should be a string.
            if len(expr.params) < 1:
                error_str  = f'print() expected one or more arguments'
                raise error.Call(expr.loc, error_str)

            arg1 = expr.params[0]
            self.__validate_single_expr(arg1)
            self.__validate_type_of_expr(arg1.loc, Type.STRING, arg1)

            expr.type = Type.NONE
            return

        # The function is not print, so it must be in the environment.
        # Get the type of the function.
        (ret_type, args_types) = self.__lookup_function(expr.loc, expr.name)

        # Check that the number of arguments is correct.
        if len(expr.params) != len(args_types):
            error_str  = f'{expr.name}() expected {len(args_types)} arguments '
            error_str += f'but found {len(expr.params)}'
            raise error.Call(expr.loc, error_str)

        # Check that the arguments have the correct type.
        for (param_e, arg_type) in zip(expr.params, args_types):
            self.__validate_single_expr(param_e)
            self.__validate_type_of_expr(param_e.loc, arg_type, param_e)

        # Type checking succeeded.
        expr.type = ret_type


    def __validate_if_expr_type(self, expr):
        ''' Typecheck and add environment data for a single If Expr. '''

        if expr.type != Type.NONE:
            error_str = f'expected If to have NONE type'
            raise error.InternalError(expr.loc, error_str)

        # An If expression has no type, so just typecheck its subexpressions.
        self.__validate_single_expr(expr.cond)

        for e in expr.then:
            self.__validate_single_expr(e)

        for e in expr.otherwise:
            self.__validate_single_expr(e)


    def __validate_loop_expr_type(self, expr):
        ''' Typecheck and add environment data for a single Loop Expr. '''

        if expr.type != Type.NONE:
            error_str = f'expected Loop to have NONE type'
            raise error.InternalError(expr.loc, error_str)

        # A Loop expression has no type, so just typecheck its subexpressions.
        self.__validate_single_expr(expr.init)
        self.__validate_single_expr(expr.test)
        self.__validate_single_expr(expr.update)

        # The loop body is in a new scope.
        self._env.push_scope()

        for e in expr.body:
            self.__validate_single_expr(e)

        # The body scope ended.
        self._env.pop_scope(expr.loc)


    def __validate_list_expr_type(self, expr):
        ''' Typecheck and add environment data for a single List Expr. '''

        if expr.type != Type.UNDETERMINED:
            error_str = f'expected List to have UNDETERMINED type'
            raise error.InternalError(expr.loc, error_str)

        # The size of the list should be an integer.
        self.__validate_single_expr(expr.size)
        self.__validate_type_of_expr(expr.size.loc, Type.INT, expr.size)

        # Determine the type of the list from the element type.
        if expr.elem_type == Type.INT:
            expr.type = Type.LIST_INT
        elif expr.elem_type == Type.FLOAT:
            expr.type = Type.LIST_FLOAT
        elif expr.elem_type == Type.STRING:
            expr.type = Type.LIST_STRING
        else:
            raise error.InvalidType(expr.loc, expr.elem_type)

        # Add the new list to the environment.
        self._env.add(expr.name, [expr.type], True)


    def __validate_list_at_expr_type(self, expr):
        ''' Typecheck and add environment data for a single ListAt Expr. '''

        if expr.type != Type.UNDETERMINED:
            error_str = f'expected ListAt to have UNDETERMINED type'
            raise error.InternalError(expr.loc, error_str)

        # Get the type of the list.
        list_type = self.__lookup_variable(expr.loc, expr.name)

        # Determine the type of the list element.
        elem_type = None
        if list_type == Type.LIST_INT:
            elem_type = Type.INT
        elif list_type == Type.LIST_FLOAT:
            elem_type = Type.FLOAT
        elif list_type == Type.LIST_STRING:
            elem_type = Type.STRING
        else:
            error_str = f'expected list type but got {list_type}'
            raise error.Type(expr.loc, error_str)

        # Make sure the index has type int.
        self.__validate_single_expr(expr.index)
        self.__validate_type_of_expr(expr.index.loc, Type.INT, expr.index)

        # ListAt returns a list element, so it has the list element type.
        expr.type = elem_type


    def __validate_list_set_expr_type(self, expr):
        ''' Typecheck and add environment data for a single ListSet Expr. '''

        if expr.type != Type.NONE:
            error_str = f'expected ListSet to have NONE type'
            raise error.InternalError(expr.loc, error_str)

        # Get the type of the list.
        list_type = self.__lookup_variable(expr.loc, expr.name)

        # Determine the type of the list element.
        elem_type = None
        if list_type == Type.LIST_INT:
            elem_type = Type.INT
        elif list_type == Type.LIST_FLOAT:
            elem_type = Type.FLOAT
        elif list_type == Type.LIST_STRING:
            elem_type = Type.STRING
        else:
            error_str = f'expected list type but got {list_type}'
            raise error.Type(expr.loc, error_str)

        # Make sure the index has type int.
        self.__validate_single_expr(expr.index)
        self.__validate_type_of_expr(expr.index.loc, Type.INT, expr.index)

        # Make sure the type of the new value matches the element type.
        self.__validate_single_expr(expr.val)
        self.__validate_type_of_expr(expr.val.loc, elem_type, expr.val)


    def __validate_list_prim_func_type(self, expr):
        ''' Add environment data for a single PrimFunc Expr. '''

        # PrimFunc expressions don't have a body so there is not much to
        # validate, but the environment must be updated so later code can call
        # the primitive functions.

        if expr.type == Type.UNDETERMINED or expr.type == Type.NONE:
            error_str  = f'primitive function {expr.name} has bad '
            error_str += f'return type: {type_lst[0]}'
            raise error.InternalError(expr.loc, error_str)

        type_lst = [expr.type]

        for arg_type in expr.arg_types:
            type_lst.append(arg_type)

        # Update the environment.
        self._env.add(expr.name, type_lst, False)


    def validate_exprs(self):
        ''' Validate each parsed expression and add environment info. '''

        for expr in self.parsed_exprs:
            self.__validate_single_expr(expr)
