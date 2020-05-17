from enum import Enum

class Type(Enum):
    INT     = 1
    FLOAT   = 2
    STRING  = 3
    UNKNOWN = 4


    def type_to_str(t):
        if t == Type.INT:
            return 'int'
        elif t == Type.FLOAT:
            return 'float'
        elif t == Type.STRING:
            return 'string'
        elif t == Type.UNKNOWN:
            return 'unknown'
        else:
            return '(bad parameter to type_to_str())'


    def get_type(v):
        if isinstance(v, int):
            return Type.INT
        elif isinstance(v, float):
            return Type.FLOAT
        elif isinstance(v, str):
            return Type.STRING
        else:
            return Type.UNKNOWN