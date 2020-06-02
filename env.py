import error
from type import Type

class Env:
    def __init__(self):
        # Setup the environment, which is a list of (name, List of Type's, bool)
        # tuples. The list of Type's has the second entry as the type of the
        # variable or return type of the function. If there are more elements
        # in the list in the tuple, they are the types of the parameters that
        # must be passed to the function. The third element of the tuple is
        # true if the entry corresponds to a variable and false if it
        # corresponds to a function.
        #
        # The (outer) list may also contain elements that are 'None'. These
        # represent a new scope so that scopes can be popped off easilty.
        self.env = []


    def copy(self):
        ''' Return a copy of the environment. '''
        e = Env()
        e.env = list(self.env)
        return e


    def push_scope(self):
        self.env.append(None)


    def pop_scope(self, loc):
        ''' Pop off 'env' until a None element is popped. '''

        # Find the index of the last None element.
        ind = None
        for i in range(len(self.env) - 1, -1, -1):
            if self.env[i] == None:
                ind = i
                break

        # Make sure a None element was found.
        if ind == None:
            error_str = 'tried popping scope without previous scope'
            raise error.InternalError(loc, error_str)

        # Pop the scope.
        self.env = self.env[:ind]


    def add(self, name, type_lst, is_var):
        assert(isinstance(name, str))
        assert(isinstance(type_lst, list))
        assert(isinstance(is_var, bool))

        self.env.append((name, type_lst, is_var))

        if type_lst == [Type.LIST_INT] or type_lst == [Type.LIST_FLOAT] or \
           type_lst == [Type.LIST_STRING]:
            self.env.append((f'{name}.size', [Type.INT], True))


    def name_in_scope(self, name):
        ''' Check if the given name is in the current scope. '''

        for entry in self.env[::-1]:
            if entry == None:
                # The end of the scope was reached.
                break

            if entry[0] == name:
                return True

        return False


    def get_entry_for_name(self, name):
        ''' Return the environment entry for a given name. '''

        for entry in self.env[::-1]:
            if entry == None:
                # Move into the next highest scope.
                continue

            if entry[0] == name:
                return entry

        # The given name is not in the environment.
        return (None, None, None)


    def lookup_variable(self, loc, expr_name):
        ''' Find a variable in the environment and return its type. '''

        # Make sure the variable already exists.
        (name, type_lst, is_var) = self.get_entry_for_name(expr_name)

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


    def lookup_function(self, loc, expr_name):
        '''
        Find a function in the environment.

        Return a tuple with two elements. The first is the return type of the
        function and the second is a list of types for the arguments.
        '''

        # Make sure the function already exists.
        (name, type_lst, is_var) = self.get_entry_for_name(expr_name)

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
