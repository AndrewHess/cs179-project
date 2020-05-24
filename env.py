import error


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
        return list(self.env)


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
        return (None, None)