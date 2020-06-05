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
            if '.' in x:
                assert(len(x) > 5 and x[-5:] == '.size')
                x = x[:-5]

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
        start_val_expr = None
        end_val_expr = None

        referenced_variables = []

        # Get the start expression.
        if expr.init.exprClass != ExprEnum.CREATE_VAR and \
           expr.init.exprClass != ExprEnum.SET_VAR:
            return
        if expr.init.val.exprClass == ExprEnum.GET_VAR:
            referenced_variables.append(expr.init.val.name)
        elif expr.init.val.exprClass != ExprEnum.LITERAL:
            return

        start_val_expr = expr.init.val
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

        def flip_inequality(inequality):
            if inequality == '<':
                return '>'
            elif inequality == '>':
                return '<'
            elif inequality == '<=':
                return '>='
            elif inequality == '>=':
                return '<='
            else:
                return inequality

        # The comparison should be between the loop index and either or literal
        # or a variable. Store the end expression, which is the expression in
        # the test that does not use the index. The end expression may have to
        # be updated if the test uses something like '<=' instead of '<'.
        test_lit_val = None
        test_vars_names = [None, None]
        for i in range(2):
            if expr.test.params[i].exprClass == ExprEnum.LITERAL:
                if test_lit_val is not None:
                    # We already read a literal, so the comparison is between
                    # two literals and isn't worth parallelizing.
                    return

                test_lit_val = expr.test.params[i].val
                end_val_expr = expr.test.params[i]
            elif expr.test.params[i].exprClass == ExprEnum.GET_VAR:
                test_vars_names[i] = expr.test.params[i].name

                if expr.test.params[i].name is not index_name:
                    end_val_expr = expr.test.params[i]
                    referenced_variables.append(expr.test.params[i].name)
                elif expr.test.params[i].name == index_name and i == 1:
                    # Flip the inequality so that instead of something like
                    # `10 > index', we get `index < 10'.
                    test_call_name = flip_inequality(test_call_name)
            else:
                # Something unexpected was found.
                return

        # Exactly 2 non-None values should be in test_vars_names and
        # test_lit_val combined.
        combined = [test_lit_val] + test_vars_names
        if sum([0 if x is None else 1 for x in combined]) != 2:
            return

        # The test should involve the index variable.
        if index_name not in test_vars_names:
            return

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

        # Determine the end value expression so that the parallel loop can go
        # from the start index value (inclusive) to the end index value
        # (excusive).
        if test_call_name == '<=' and update_call_name == '+':
            # Increment end_val_expr.
            one_expr = Literal(end_val_expr.loc, Type.INT, 1)
            end_val_expr = Call(end_val_expr.loc, '+', [end_val_expr, one_expr])
        elif test_call_name == '>=' and update_call_name == '-':
            # Decrement end_val_expr.
            one_expr = Literal(end_val_expr.loc, Type.INT, 1)
            end_val_expr = Call(end_val_expr.loc, '-', [end_val_expr, one_expr])

        if update_call_name == '-':
            # We want to start the parallelized iterations at the lowest index,
            # for simplicity.
            tmp = start_val_expr
            start_val_expr = end_val_expr
            end_val_expr = tmp

        # Make sure the index is not set inside the loop.
        all_sets = []
        for e in expr.body:
            all_sets += self.__deep_find_sets(e)

        if index_name in all_sets:
            return

        # # If a non-list variable is set inside the loop, then the loop cannot
        # # be parallelized (yet) due to synchronization.
        # for x in all_sets:
        #     print(f'analyzer looking up variable {x}')
        #     x_type = expr.env.lookup_variable(expr.loc, x)
        #     print(f'analyzer found variable {x}')
        #     if x_type == Type.INT or x_type == Type.FLOAT or \
        #        x_type == Type.STRING:
        #         return

        # TODO: Do not parallelize if two iterations of the loop set the same
        #       location in any list, as this too causes race conditions.

        # TODO: Do not parallelize if one iterations sets something in a list
        #       and another iteration uses that list value.

        # Determine the variables that are used but not created by the loop. If
        # a non-list variable is set inside the loop but not created in the
        # loop, then the loop cannot be parallelized (yet) due to
        # synchronization issues.
        (used_variables, _) = self.__deep_used_not_created(expr, [])
        for x in used_variables:
            if x in all_sets:
                x_type = expr.env.lookup_variable(expr.loc, x)
                if  x_type == Type.INT or x_type == Type.FLOAT or \
                        x_type == Type.STRING:
                    return

        for var in referenced_variables:
            if '.' in var:
                assert(len(var) > 5 and var[-5:] == '.size')
                var = var[:-5]

            if var not in used_variables:
                used_variables.append(var)

        # Create the parallelized loop expression.
        parallel_loop = ParallelLoop(expr.loc, index_name, start_val_expr,
                                     end_val_expr, used_variables, expr.body)
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
