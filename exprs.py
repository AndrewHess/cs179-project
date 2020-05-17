from enum import Enum

from error import *
from location import Location
from type import Type


class ExprEnum(Enum):
    CREATE_VAR = 1
    SET_VAR    = 2
    DEFINE     = 3
    CALL       = 4


class Expr:
    exprClass = None


class CreateVar(Expr):
    def __init__(self, _loc, _type, _name, _val):
        # Check that the type is as expected.
        actual_type = Type.get_type(_val)
        if (_type != actual_type):
            raise TypeError(_loc, _type, actual_type)

        # Setup the data.
        self.exprClass = ExprEnum.CREATE_VAR
        self.type = _type   # Type Type
        self.name = _name   # Type string
        self.val = _val     # Variable with type corresponding to _type
