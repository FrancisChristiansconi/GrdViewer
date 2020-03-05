"""This module defines abstract object element.
These elements belong to an EarthPlot drawing.
"""
# import standard modules
# ==================================================================================================
import sys

# import third party modules
# ==================================================================================================
# abstract class toolbox
from abc import ABC, abstractmethod


class Element(ABC):
    """Abstract class Element describes an item to be displayed
    on the Earth map.
    """

    # dictionary for storing Element configuration
    _configuration = {}

    @staticmethod
    def __str__(self):
        """Convert instance to string
        """
        # get configuration of element
        conf = self.configure()

        # append configuration items into multilines string
        _str = ''
        for k, i in conf.items():
            _str += k + ' = ' + str(i) + ','

        # return .ini like string list
        return _str

    @abstractmethod
    def plot(self):
        """Abstract method plot is used by the EarthPlot parent instance
        to display the element on its EarthMap (Basemap instance).
        """
        pass

    @abstractmethod
    def clearplot(self):
        """Abstract method clearplot is used by the EarthPlot parent intance
        to clear the element from its EarthMap (Basemap instance).
        """
        pass

    @abstractmethod
    def configure(self, config):
        """Abstract method configure is used to configure the Element instance.
        Preferred implementation is to pass a dictionary to the method.
        This dictionary will be merge with instance configuration dictionary.
        """
        pass

    def set(self, key, fallback=None, dtype=None):
        """Try to return element key of dictionary conf. KeyError exception
        is handled. In case of KeyError exception, log message is printed
        on standard output and fallback value is returned.
        By default, fallback value is None
        """
        def convert_to_bool(input):
            if type(input) is bool:
                return input
            else:
                return (input == 'True')

        def convert_to_list(input, dtype):
            if type(input) is list:
                return input
            else:
                if input[0] == '[':
                    input = input[1:-2]
                return [convert[dtype](e) for e in input.split(',')]

        convert = {
            str: lambda s: s,
            float: float,
            complex: complex,
            int: int,
            bool: convert_to_bool,
            list: lambda l: convert_to_list(l, type(fallback[0]))
        }

        # initialize return value
        param = fallback
        try:
            if dtype is not None:
                param = convert[dtype](self._configuration[key])
            else:
                param = self._configuration[key]
        except KeyError:
            pass
        # return either the desired value or None
        return param
    # end of function set
# end of class Element

# end of module element
