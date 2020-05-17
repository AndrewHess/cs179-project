from location import Location

class Error(Exception):
    ''' Base class for errors. '''
    loc = None  # Type Location

    def print(self):
        ''' This method should be overwritten in child classes. '''
        print('internal error: print_error not overwritten')


class TypeError(Error):
    def __init__(self, _loc, _expected_type, _actual_type):
        self.loc = _loc                         # Type Location
        self.expected_type = _expected_type     # Type Type
        self.actual_type = _actual_type         # Type Type


    def print(self):
        etype = self.expected_type
        atype = self.actual_type

        print(f'type error in {self.loc.to_string()}: ', end='')
        print(f'expected type {etype} but got type {atype}')