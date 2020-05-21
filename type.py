from enum import Enum
import error


class Type(Enum):
    INT         = 1
    FLOAT       = 2
    STRING      = 3
    LIST_INT    = 4
    LIST_FLOAT  = 5
    LIST_STRING = 6
    UNKNOWN     = 7


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
            raise error.InternalError(loc, f'type_to_str: unknown type: {t}')


    def str_to_type(loc, s):
        if s == 'int':
            return Type.INT
        elif s == 'float':
            return Type.FLOAT
        elif s == 'string':
            return Type.STRING
        else:
            raise error.InvalidType(loc, s)


    def get_type(loc, v):
        if isinstance(v, int):
            return Type.INT
        elif isinstance(v, float):
            return Type.FLOAT
        elif isinstance(v, str):
            return Type.STRING


    def get_type_from_string_val(loc, v):
        '''
        Return the intended type of 'v', which is of type string. Some examples
        of expected behavior are:
        v = "1245" -> Type.INT
        v = "12.4" -> Type.FLOAT
        v = "'hi'" -> Type.STRING
        '''

        if v[0] == '\'':
            if v[-1] != '\'':
                raise error.Syntax(loc, f'invalid string: {v}')
            return Type.STRING
        elif '.' in v:
            return Type.FLOAT
        else:
            return Type.INT


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
                if val[0] != '\'' or val[-1] != '\'':
                    raise error.Syntax(loc, f'invalid string: {val}')
                return str(val[1: -1])
            else:
                error_str = f'convert_type: unknown type {type_enum}'
                raise error.InternalError(loc, error_str)
        except ValueError:
            type_str = Type.type_to_str(loc, type_enum)
            raise error.IncompatibleType(loc, type_str, val)


    def enum_to_c_type(loc, type_enum):
        ''' Return a string of the C++ type for the type 'type_enum'. '''

        if type_enum == Type.INT:
            return 'int'
        elif type_enum == Type.FLOAT:
            return 'float'
        elif type_enum == Type.STRING:
            return 'char *'
        elif type_enum == Type.LIST_INT:
            return 'int *'
        elif type_enum == Type.LIST_FLOAT:
            return 'float *'
        elif type_enum == Type.LIST_STRING:
            return 'char **'
        else:
            error.InternalError(loc, f'bad enum_to_c_type param: {type_enum}')
