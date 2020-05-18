from location import Location

class Error(Exception):
    ''' Base class for errors. '''
    loc = None  # Type Location

    def print(self):
        print(f'type error in {self.loc.to_string()}: ', end='')
        self._print_end()


    def _print_end(self):
        ''' This method should be overwritten in child classes. '''
        print('internal error: __print_end() not overwritten')


class UnexpectedType(Error):
    def __init__(self, _loc, _expected_type, _actual_type):
        self.loc = _loc                         # Type Location
        self.expected_type = _expected_type     # Type Type
        self.actual_type = _actual_type         # Type Type


    def _print_end(self):
        print(f'expected type {self.expected_type} but got ' + \
              f'type {self.actual_type}')


class InvalidType(Error):
    def __init__(self, _loc, _invalid_type):
        self.loc = _loc                     # Type Location
        self.invalid_type = _invalid_type   # Type string


    def _print_end(self):
        print(f'invalid type: {self.invalid_type}')


class IncompatibleType(Error):
    def __init__(self, _loc, _type_name, _val):
        self.loc = _loc                 # Type Location
        self.type_name = _type_name     # String like "float", "string", ...
        self.val = _val                 # String like "4.32", "hi", ...


    def _print_end(self):
        print(f'"{self.val}" is not of type {self.type_name}')


class InvalidExprStart(Error):
    def __init__(self, _loc, _expected_start, _actual_start):
        self.loc = _loc                         # Type Location
        self.expected_start = _expected_start   # Type Type
        self.actual_start = _actual_start       # Type Type


    def _print_end(self):
        print(f'expected expression to start with "{self.expected_start}" ' + \
              f'but found "{self.actual_start}" at start')


class InternalError(Error):
    def __init__(self, _loc, _msg):
        self.loc = _loc     # Type Location
        self.msg = _msg     # Type string


    def _print_end(self):
        print(f'internal error: {msg}')
