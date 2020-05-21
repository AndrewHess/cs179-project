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
    IF         = 7
    LOOP       = 8
    LIST       = 9
    LIST_AT    = 10
    LIST_SET   = 11


class Expr:
    exprClass = None

    def _check_type(self, loc, t, v):
        # Check that the type is as expected.
        actual_type = Type.get_type(loc, v)
        if (t != actual_type):
            raise error.UnexpectedType(loc, t, actual_type)


class Literal(Expr):
    def __init__(self, _loc, _type, _val):
        self._check_type(_loc, _type, _val)

        self.exprClass = ExprEnum.LITERAL
        self.loc = _loc     # Type Location
        self.type = _type   # Type Type
        self.val = _val     # Type _type


class CreateVar(Expr):
    def __init__(self, _loc, _type, _name, _val):
        self.exprClass = ExprEnum.CREATE_VAR
        self.loc = _loc     # Type Location
        self.type = _type   # Type Type
        self.name = _name   # Type string
        self.val = _val     # Type Expr


class SetVar(Expr):
    def __init__(self, _loc, _type, _name, _val):
        self.exprClass = ExprEnum.SET_VAR
        self.loc = _loc     # Type Location
        self.type = _type   # Type Type; the type of _val
        self.name = _name   # Type string
        self.val = _val     # Type Expr


class GetVar(Expr):
    def __init__(self, _loc, _name):
        self.exprClass = ExprEnum.GET_VAR
        self.loc = _loc     # Type Location
        self.name = _name   # Type string
        self.type = None    # Type is determined by a previous CREATE_VAR expr


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
        self.return_type = None # Type is determined by a previous DEFINE expr


class If(Expr):
    def __init__(self, _loc, _cond, _then, _otherwise):
        self.exprClass = ExprEnum.IF
        self.loc = _loc                 # Type Location
        self.cond = _cond               # Type Expr
        self.then = _then               # Type list of Expr's
        self.otherwise = _otherwise     # Type list of Expr's


class Loop(Expr):
    def __init__(self, _loc, _init, _test, _update, _body):
        self.exprClass = ExprEnum.LOOP
        self.loc = _loc         # Type Location
        self.init = _init       # Type Expr
        self.test = _test       # Type Expr
        self.update = _update   # Type Expr
        self.body = _body       # Type list of Expr's


class List(Expr):
    def __init__(self, _loc, _elem_type, _name, _size):
        self.exprClass = ExprEnum.LIST
        self.loc = _loc                 # Type Location
        self.elem_type = _elem_type     # Type Type
        self.name = _name               # Type string
        self.size = _size               # Type Expr; should evaluate to an int

        # Determine the type of the list from the element type.
        self.type = None
        if _elem_type == Type.INT:
            self.type = Type.LIST_INT
        elif _elem_type == Type.FLOAT:
            self.type = Type.LIST_FLOAT
        elif _elem_type == Type.STRING:
            self.type = Type.LIST_STRING
        else:
            raise error.InvalidType(loc, _elem_type)


class ListAt(Expr):
    def __init__(self, _loc, _list, _index):
        self.exprClass = ExprEnum.LIST_AT
        self.loc = _loc         # Type Location
        self.list = _list       # Type string; the name of the list
        self.index = _index     # Type Expr; should evaluate to an int


class ListSet(Expr):
    def __init__(self, _loc, _list, _index, _val):
        self.exprClass = ExprEnum.LIST_SET
        self.loc = _loc         # Type Location
        self.list = _list       # Type string; the name of the list
        self.index = _index     # Type Expr; should evaluate to an int
        self.val = _val         # Type Expr; should have type list.elem_type
