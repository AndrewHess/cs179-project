from location import Location

class Error(Exception):
    ''' Base class for errors. '''
    loc = None  # Type Location

    def print(self):
        print(f'type error in {self.loc.to_string()}: ', end='')
        __print_end(self)


    def __print_end(self):
        ''' This method should be overwritten in child classes. '''
        print('internal error: __print_end() not overwritten')


class UnexpectedType(Error):
    def __init__(self, _loc, _expected_type, _actual_type):
        self.loc = _loc                         # Type Location
        self.expected_type = _expected_type     # Type Type
        self.actual_type = _actual_type         # Type Type


    def __print_end(self):
        print(f'expected type {self.expected_type} but got ' + \
              f'type {self.actual_type}')


class InvalidType(Error):
    def __init__(self, _loc, _invalid_type):
        self.loc = _loc                     # Type Location
        self.invalid_type = _invalid_type   # Type string


    def __print_end(self):
        print(f'invalid type: {self.invalid_type}')
