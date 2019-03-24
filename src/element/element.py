"""This module defines abstract object element. These elements belong to an EarthPlot drawing.
"""

# import third party modules
#==================================================================================================
# abstract class toolbox
from abc import ABC, abstractmethod


class Element(ABC):
    """Abstract class Element describes an item to be displayed on the Earth map.
    """

    @abstractmethod
    def plot(self):
        """Abstract method plot is used by the EarthPlot parent instance to display the element
        on its EarthMap (Basemap instance).
        """
        pass

    @abstractmethod
    def clearplot(self):
        """Abstract method clearplot is used by the EarthPlot parent intance to clear the
        element from its EarthMap (Basemap instance).
        """
        pass

    @abstractmethod
    def configure(self, config):
        """Abstract method configure is used to configure the Element instance.
        Preferred implementation is to pass a dictionary to the method. This dictionary will be
        merge with instance configuration dictionary.
        """
        pass

    @staticmethod
    def set(conf, key, fallback=None):
        """Try to return element key of dictionary conf. KeyError exception is handled.
        In case of KeyError exception, log message is printed on standard output and fallback
        value is returned. By default, fallback value is None
        """
        # initialize return value
        param = fallback
        try:
            param = conf[key]
        except KeyError as err:
            print('KeyError: {0} not defined'.format(err.args[0]))
        # return either the desired value or None
        return param
    # end of function set
# end of class Element

# end of module element
