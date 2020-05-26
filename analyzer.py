from expr import *


class Analyzer:
    ''' Mark some parsed expressions to run in parallel. '''

    def __init__(self, _parsed_exprs):
        self.parsed_exprs = _parsed_exprs  # Type list of Expr's


    def __deep_find_calls(self, expr):
        '''
        Return a list of names of every function called directly or indirectly
        by the given expression.
        '''

        if expr.exprClass == ExprEnum.LITERAL:
            return []
        elif expr.exprClass == ExprEnum.CREATE_VAR:
            return self.__deep_find_calls(expr.val)
        elif expr.exprClass == ExprEnum.SET_VAR:
            return self.__deep_find_calls(expr.val)
        elif expr.exprClass == ExprEnum.GET_VAR:
            return []
        elif expr.exprClass == ExprEnum.DEFINE:
            return []
        elif expr.exprClass == ExprEnum.CALL:
            # TODO: also include any functions called by this function.
            funcs = [expr.name]

            for p in expr.params:
                funcs += self.__deep_find_calls(p)

            return funcs
        elif expr.exprClass == ExprEnum.IF:
            # Include any functions that could possibly be called.
            funcs = self.__deep_find_calls(expr.cond)

            for e in expr.then:
                funcs += self.__deep_find_calls(e)

            for e in expr.otherwise:
                funcs += self.__deep_find_calls(e)

            return funcs
        elif expr.exprClass == ExprEnum.LOOP:
            funcs = self.__deep_find_calls(expr.init)
            funcs += self.__deep_find_calls(expr.test)
            funcs += self.__deep_find_calls(expr.update)

            for e in expr.body:
                funcs += self.__deep_find_calls(e)

            return funcs
        elif expr.exprClass == ExprEnum.LIST:
            return self.__deep_find_calls(expr.size)
        elif expr.exprClass == ExprEnum.LIST_AT:
            return self.__deep_find_calls(expr.index)
        elif expr.exprClass == ExprEnum.LIST_SET:
            funcs = self.__deep_find_calls(expr.index)
            funcs += self.__deep_find_calls(expr.val)

            return funcs
        elif expr.exprClass == ExprEnum.PRIM_FUNC:
            return [expr.name]
        else:
            error_str = f'unknown expression type: {expr.exprClass}'
            raise error.InternalError(expr.loc, error_str)


    def __deep_find_sets(self, expr):
        '''
        Return a list of names of every variable set directly or indirectly by
        the given expression.
        '''

        if expr.exprClass == ExprEnum.LITERAL:
            return []
        elif expr.exprClass == ExprEnum.CREATE_VAR:
            return self.__deep_find_sets(expr.val)
        elif expr.exprClass == ExprEnum.SET_VAR:
            return [expr.name] + self.__deep_find_sets(expr.val)
        elif expr.exprClass == ExprEnum.GET_VAR:
            return []
        elif expr.exprClass == ExprEnum.DEFINE:
            return []
        elif expr.exprClass == ExprEnum.CALL:
            # TODO: also include any sets called by this function.
            sets = []

            for e in expr.params:
                sets += self.__deep_find_sets(e)

            return sets
        elif expr.exprClass == ExprEnum.IF:
            # Include any sets that could possibly be called.
            sets = self.__deep_find_sets(expr.cond)

            for e in expr.then:
                sets += self.__deep_find_sets(e)

            for e in expr.otherwise:
                sets += self.__deep_find_sets(e)

            return sets
        elif expr.exprClass == ExprEnum.LOOP:
            sets = self.__deep_find_sets(expr.init)
            sets += self.__deep_find_sets(expr.test)
            sets += self.__deep_find_sets(expr.update)

            for e in expr.body:
                sets += self.__deep_find_sets(e)

            return sets
        elif expr.exprClass == ExprEnum.LIST:
            return self.__deep_find_sets(expr.size)
        elif expr.exprClass == ExprEnum.LIST_AT:
            return self.__deep_find_sets(expr.index)
        elif expr.exprClass == ExprEnum.LIST_SET:
            sets = self.__deep_find_sets(expr.index)
            sets += self.__deep_find_sets(expr.val)

            return sets
        elif expr.exprClass == ExprEnum.PRIM_FUNC:
            return []
        else:
            error_str = f'unknown expression type: {expr.exprClass}'
            raise error.InternalError(expr.loc, error_str)


    def __deep_used_not_created(self, expr, created):
        '''
        Return a tuple containing:
            1. A list of names of variables that were accessed but not created
               as part of the expression.
            2. A list of names of variables created by the experssion, combined
               with the input 'created' list.
        '''

        used = []

        if expr.exprClass == ExprEnum.LITERAL:
            pass
        elif expr.exprClass == ExprEnum.CREATE_VAR:
            created += [expr.name]
            (used, created) = self.__deep_used_not_created(expr.val, created)
        elif expr.exprClass == ExprEnum.SET_VAR:
            (used, created) = self.__deep_used_not_created(expr.val, created)
            used += [expr.name]
        elif expr.exprClass == ExprEnum.GET_VAR:
            used = [expr.name]
        elif expr.exprClass == ExprEnum.DEFINE:
            pass
        elif expr.exprClass == ExprEnum.CALL:
            # TODO: also include any accesses due to the called function.
            for e in expr.params:
                (u, created) = self.__deep_used_not_created(e, created)
                used += u

        elif expr.exprClass == ExprEnum.IF:
            # Include any accesses that could possibly occur.
            (used, created) = self.__deep_used_not_created(expr.cond, created)

            # This must be done with care to appropriately address the possible
            # case where variable x is created before the If expression, the
            # 'then' part creates a variable x in the new scope and uses it,
            # and the 'else' part uses the original x variable.

            then_create = list(created)  # Make a copy of the 'created' list
            for e in expr.then:
                (u, then_create) = self.__deep_used_not_created(e, then_create)

                for x in u:
                    if x not in then_create:
                        used.append(x)

            else_create = list(created)
            for e in expr.otherwise:
                (u, else_create) = self.__deep_used_not_created(e, else_create)

                for x in u:
                    if x not in else_create:
                        used.append(x)

            return (used, created)
        elif expr.exprClass == ExprEnum.LOOP:
            (u1, created) = self.__deep_used_not_created(expr.init, created)
            (u2, created) = self.__deep_used_not_created(expr.test, created)
            (u3, created) = self.__deep_used_not_created(expr.update, created)

            used = u1 + u2 + u3

            for e in expr.body:
                (u, created) = self.__deep_used_not_created(e, created)
                used += u

        elif expr.exprClass == ExprEnum.LIST:
            created += [expr.name]
            (used, created) = self.__deep_used_not_created(expr.size, created)
        elif expr.exprClass == ExprEnum.LIST_AT:
            (used, created) = self.__deep_used_not_created(expr.index, created)
            used += [expr.name]
        elif expr.exprClass == ExprEnum.LIST_SET:
            (u1, created) = self.__deep_used_not_created(expr.index, created)
            (u2, created) = self.__deep_used_not_created(expr.val, created)

            used = u1 + u2 + [expr.name]
        elif expr.exprClass == ExprEnum.PRIM_FUNC:
            pass
        else:
            error_str = f'unknown expression type: {expr.exprClass}'
            raise error.InternalError(expr.loc, error_str)

        # Find all of the variables that were used but not created.
        used_not_created = []

        for x in used:
            if x not in created and x not in used_not_created:
                used_not_created.append(x)

        return (used_not_created, created)


    def __maybe_parallelize_loop(self, expr):
        '''
        Parallelize the loop expression if it can be, and update
        self.parsed_exprs with the parallelized expression.
        '''

        # Do not parallelize a loop that uses rand() because running in
        # parallel vs sequential could cause different results, which is very
        # unintuitive if a fixed seed is used.
        if 'rand' in self.__deep_find_calls(expr):
            return

        # Determine the number of iterations.
        index_name = None
        start = None
        end = None

        # Get the start value.
        if expr.init.exprClass != ExprEnum.CREATE_VAR:
            return
        if expr.init.val.exprClass != ExprEnum.LITERAL:
            return
        start = expr.init.val.val
        index_name = expr.init.name

        # Determine the stop criterion.
        if expr.test.exprClass != ExprEnum.CALL:
            return

        test_call_name = expr.test.name
        if test_call_name not in ['<', '<=', '>', '>=', '!=']:
            return

        # The call should have two parameters. If not, this should have already
        # been caught by the type checker, so this code is not reached.
        assert(len(expr.test.params) == 2)

        # The comparison should be between a literal and the loop index.
        test_end_val = None
        test_var_name = None
        for i in range(2):
            if expr.test.params[i].exprClass == ExprEnum.LITERAL:
                test_end_val = expr.test.params[i].val
            elif expr.test.params[i].exprClass == ExprEnum.GET_VAR:
                test_var_name = expr.test.params[i].name

        if test_end_val is None or test_var_name is None:
            return

        if test_var_name is not index_name:
            return

        # Set an approximate end value. This may need to be udpated if the
        # test uses something like '<=' instead of '<'.
        end = test_end_val

        # The update should be addition or subtraction of a literal from the
        # loop index.
        if expr.update.exprClass != ExprEnum.SET_VAR:
            return

        if expr.update.name != index_name:
            return

        if expr.update.val.exprClass != ExprEnum.CALL:
            return

        update_call_name = expr.update.val.name
        if update_call_name not in ['+', '-']:
            return

        # The call should have two parameters. If not, this should have already
        # been caught by the type checker, so this code is not reached.
        assert(len(expr.update.val.params) == 2)

        update_val = None
        update_var_name = None

        for i in range(2):
            if expr.update.val.params[i].exprClass == ExprEnum.GET_VAR:
                update_var_name = expr.update.val.params[i].name
            elif expr.update.val.params[i].exprClass == ExprEnum.LITERAL:
                update_val = expr.update.val.params[i].val

        if update_val is None or update_var_name is None:
            return

        if update_var_name is not index_name:
            return

        # Make sure the update is not something like i = 1 - i.
        if update_call_name == '-' and \
           expr.update.val.params[0].exprClass != ExprEnum.GET_VAR:
            return

        # TODO: do not require the update to be by 1.
        if update_val != 1:
            return

        # TODO: check for infinite loops.

        # Determine the number of iterations. The current implementation
        # requires that udpate_val is 1.
        if test_call_name == '<=' and update_call_name == '+':
            end += 1
        elif test_call_name == '>=' and update_call_name == '-':
            end -= 1

        iters = abs(start - end)

        if iters == 0:
            return

        # Make sure the index is not set inside the loop.
        all_sets = []
        for e in expr.body:
            all_sets += self.__deep_find_sets(e)

        if index_name in all_sets:
            return

        # If a non-list variable is set inside the loop, then the loop cannot
        # be parallelized (yet) due to synchronization.
        for x in all_sets:
            x_type = expr.env.lookup_variable(expr.loc, x)
            if x_type == Type.INT or x_type == Type.FLOAT or \
               x_type == Type.STRING:
                return

        # TODO: Do not parallelize if two iterations of the loop set the same
        #       location in any list, as this too causes race conditions.

        # TODO: Do not parallelize if one iterations sets something in a list
        #       and another iteration uses that list value.

        # Determine the variables that are used but not created by the loop.
        (used_variables, _) = self.__deep_used_not_created(expr, [])

        # Since the loop is parallelized we can choose to start at the lowest
        # index for simplicity in generating the CUDA code.
        start = min(start, end)
        parallel_loop = ParallelLoop(expr.loc, index_name, start, iters,
                                     used_variables, expr.body)
        parallel_loop.env = expr.env

        return parallel_loop


    def __deep_analyze_expr(self, expr):
        '''
        Try to parallelize the expression and any subexpressions.

        The new version of the expression (which may be the same as the old
        version) is returned.
        '''

        if expr.exprClass == ExprEnum.LITERAL:
            pass
        elif expr.exprClass == ExprEnum.CREATE_VAR:
            expr.val = self.__deep_analyze_expr(expr.val)
        elif expr.exprClass == ExprEnum.SET_VAR:
            expr.val = self.__deep_analyze_expr(expr.val)
        elif expr.exprClass == ExprEnum.GET_VAR:
            pass
        elif expr.exprClass == ExprEnum.DEFINE:
            for (i, e) in enumerate(expr.body):
                expr.body[i] = self.__deep_analyze_expr(e)
        elif expr.exprClass == ExprEnum.CALL:
            for (i, e) in enumerate(expr.params):
                expr.params[i] = self.__deep_analyze_expr(e)
        elif expr.exprClass == ExprEnum.IF:
            expr.cond = self.__deep_analyze_expr(expr.cond)

            for (i, e) in enumerate(expr.then):
                expr.then[i] = self.__deep_analyze_expr(e)

            for (i, e) in enumerate(expr.otherwise):
                expr.otherwise[i] = self.__deep_analyze_expr(e)

        elif expr.exprClass == ExprEnum.LOOP:
            # Actually try to parallelize a loop.
            parallel_loop = self.__maybe_parallelize_loop(expr)
            if parallel_loop is not None:
                expr = parallel_loop

        elif expr.exprClass == ExprEnum.LIST:
            expr.size = self.__deep_analyze_expr(expr.size)
        elif expr.exprClass == ExprEnum.LIST_AT:
            expr.index = self.__deep_analyze_expr(expr.index)
        elif expr.exprClass == ExprEnum.LIST_SET:
            expr.index = self.__deep_analyze_expr(expr.index)
            expr.val = self.__deep_analyze_expr(expr.val)
        elif expr.exprClass == ExprEnum.PRIM_FUNC:
            pass
        else:
            error_str = f'unknown expression type: {expr.exprClass}'
            raise error.InternalError(expr.loc, error_str)

        return expr


    def analyze(self):
        ''' Try to parallelize each expressions. '''

        for (i, e) in enumerate(self.parsed_exprs):
            self.parsed_exprs[i] = self.__deep_analyze_expr(e)
