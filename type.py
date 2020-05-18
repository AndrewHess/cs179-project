from enum import Enum
import error


class Type(Enum):
    INT     = 1
    FLOAT   = 2
    STRING  = 3
    UNKNOWN = 4


    def type_to_str(loc, t):
        if t == Type.INT:
            return 'int'
        elif t == Type.FLOAT:
            return 'float'
        elif t == Type.STRING:
            return 'string'
        elif t == Type.UNKNOWN:
            return 'unknown'
        else:
            raise error.InternalError(loc, f'unknown type: {t}')


    def str_to_type(loc, s):
        if s == 'int':
            return Type.INT
        elif s == 'float':
            return Type.FLOAT
        elif s == 'string':
            return Type.STRING
        else:
            raise error.InvalidType(loc, s)



    def get_type(v):
        if isinstance(v, int):
            return Type.INT
        elif isinstance(v, float):
            return Type.FLOAT
        elif isinstance(v, str):
            return Type.STRING
        else:
            return Type.UNKNOWN


    def convert_type(loc, type_enum, val):
        '''
        type_enum: Type.INT, Type.FLOAT, ...
        val: string that will be converted to type 'type_enum'

        Return 'val' as a value of the type corresponding to 'type_enum'. For
        example:

        convert_type(loc, Type.INT, "67")       -> 67
        convert_type(loc, Type.FLOAT, "0.43")   -> 0.43
        convert_type(loc, Type.STRING, "hello") -> "hello"
        '''

        try:
            if type_enum == Type.INT:
                return int(val)
            elif type_enum == Type.FLOAT:
                return float(val)
            elif type_enum == Type.STRING:
                return str(val)
            else:
                raise error.InternalError(loc, f'unknown type {type_enum}')
        except ValueError:
            type_str = Type.type_to_str(loc, type_enum)
            raise error.IncompatibleType(loc, type_str, val)
