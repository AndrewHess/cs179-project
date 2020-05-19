from enum import Enum

import error
from location import Location
from type import Type


class ExprEnum(Enum):
    LITERAL    = 1
    CREATE_VAR = 2
    SET_VAR    = 3
    GET_VAR    = 4
    DEFINE     = 5
    CALL       = 6


class Expr:
    exprClass = None

    def _check_type(self, loc, t, v):
        # Check that the type is as expected.
        actual_type = Type.get_type(v)
        if (t != actual_type):
            raise error.UnexpectedType(loc, t, actual_type)


class Literal(Expr):
    def __init__(self, _loc, _type, _val):
        self._check_type(_loc, _type, _val)

        # Setup the data.
        self.exprClass = ExprEnum.LITERAL
        self.loc = _loc     # Type Location
        self.type = _type   # Type Type
        self.val = _val     # Type corresponding to _type


class CreateVar(Expr):
    def __init__(self, _loc, _type, _name, _val):
        self._check_type(_loc, _type, _val)

        # Setup the data.
        self.exprClass = ExprEnum.CREATE_VAR
        self.loc = _loc     # Type Location
        self.type = _type   # Type Type
        self.name = _name   # Type string
        self.val = _val     # Type corresponding to _type


class SetVar(Expr):
    def __init__(self, _loc, _type, _name, _val):
        self._check_type(_loc, _type, _val)

        self.exprClass = ExprEnum.SET_VAR
        self.loc = _loc     # Type Location
        self.type = _type   # Type Type; the type of _val
        self.name = _name   # Type string
        self.val = _val


class GetVar(Expr):
    def __init__(self, _loc, _name):
        self.exprClass = ExprEnum.GET_VAR
        self.loc = _loc     # Type Location
        self.name = _name   # Type string
        self.type = None    # This is determined by a previous CREATE_VAR expr.


class Define(Expr):
    def __init__(self, _loc, _return_type, _name, _args, _body):
        self.exprClass = ExprEnum.DEFINE
        self.loc = _loc                  # Type Location
        self.return_type = _return_type  # Type Type
        self.name = _name                # Type string
        self.args = _args                # Type list of (Type, string) tuples
        self.body = _body                # Type list of Expr's


class Call(Expr):
    def __init__(self, _loc, _name, _params):
        self.exprClass = ExprEnum.CALL
        self.loc = _loc         # Type Location
        self.name = _name       # Type string
        self.params = _params   # Type list of Expr's
