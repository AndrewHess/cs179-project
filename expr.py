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
    PRIM_FUNC  = 12
    PARA_LOOP  = 13


class Expr:
    exprClass = Type.NONE
    env = None


class Literal(Expr):
    def __init__(self, _loc, _type, _val):
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
    def __init__(self, _loc, _name, _val):
        self.exprClass = ExprEnum.SET_VAR
        self.loc = _loc                 # Type Location
        self.type = Type.UNDETERMINED   # Type depends on previous CREATE_VAR
        self.name = _name               # Type string
        self.val = _val                 # Type Expr


class GetVar(Expr):
    def __init__(self, _loc, _name):
        self.exprClass = ExprEnum.GET_VAR
        self.loc = _loc                 # Type Location
        self.name = _name               # Type string
        self.type = Type.UNDETERMINED   # Type depends on previous CREATE_VAR


class Define(Expr):
    def __init__(self, _loc, _return_type, _name, _args, _body):
        self.exprClass = ExprEnum.DEFINE
        self.loc = _loc           # Type Location
        self.type = _return_type  # Type Type
        self.name = _name         # Type string
        self.args = _args         # Type list of (Type, string) tuples
        self.body = _body         # Type list of Expr's


class Call(Expr):
    def __init__(self, _loc, _name, _params):
        self.exprClass = ExprEnum.CALL
        self.loc = _loc                 # Type Location
        self.name = _name               # Type string
        self.params = _params           # Type list of Expr's
        self.type = Type.UNDETERMINED   # Type depnds on previous DEFINE


class If(Expr):
    def __init__(self, _loc, _cond, _then, _otherwise):
        self.exprClass = ExprEnum.IF
        self.loc = _loc                 # Type Location
        self.cond = _cond               # Type Expr
        self.then = _then               # Type list of Expr's
        self.otherwise = _otherwise     # Type list of Expr's
        self.type = Type.NONE           # An If expression has no type


class Loop(Expr):
    def __init__(self, _loc, _init, _test, _update, _body, _no_para):
        self.exprClass = ExprEnum.LOOP
        self.loc = _loc         # Type Location
        self.init = _init       # Type Expr
        self.test = _test       # Type Expr
        self.update = _update   # Type Expr
        self.body = _body       # Type list of Expr's
        self.type = Type.NONE   # A Loop expression has no type
        self.no_para = _no_para # True if parallelization should not be tried.


class List(Expr):
    def __init__(self, _loc, _elem_type, _name, _size):
        self.exprClass = ExprEnum.LIST
        self.loc = _loc                 # Type Location
        self.elem_type = _elem_type     # Type Type
        self.name = _name               # Type string
        self.size = _size               # Type Expr; should evaluate to an int
        self.type = Type.UNDETERMINED   # Type depends on _elem_type


class ListAt(Expr):
    def __init__(self, _loc, _list, _index):
        self.exprClass = ExprEnum.LIST_AT
        self.loc = _loc                 # Type Location
        self.name = _list               # Type string; the name of the list
        self.index = _index             # Type Expr; should evaluate to an int
        self.type = Type.UNDETERMINED   # Type depends on previous LIST


class ListSet(Expr):
    def __init__(self, _loc, _list, _index, _val):
        self.exprClass = ExprEnum.LIST_SET
        self.loc = _loc         # Type Location
        self.name = _list       # Type string; the name of the list
        self.index = _index     # Type Expr; should evaluate to an int
        self.val = _val         # Type Expr with Type list.elem_type
        self.type = Type.NONE   # Type depends on previous LIST


class PrimFunc(Expr):
    def __init__(self, _loc, _return_type, _name, _arg_types):
        self.exprClass = ExprEnum.PRIM_FUNC
        self.loc = _loc             # Type Location
        self.type = _return_type    # Type Type
        self.name = _name           # Type string
        self.arg_types = _arg_types # Type list of Type's for argument types


class ParallelLoop(Expr):
    def __init__(self, _loc, _index_name, _start_index, _end_index,
                 _used_vars, _body):
        self.exprClass = ExprEnum.PARA_LOOP
        self.loc = _loc                     # Type Location
        self.index_name = _index_name       # Type string
        self.start_index = _start_index     # Type Expr
        self.end_index = _end_index         # Type Expr
        self.used_vars = _used_vars         # List of strings (names)
        self.body = _body                   # Type list of Expr's
        self.type = Type.NONE               # A Loop expression has no type
