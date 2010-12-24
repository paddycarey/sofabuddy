#!/usr/bin/env python

class BaseError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class SeasonOrEpisodeNoNotFound(BaseError): pass
class ShowNameNotFound(BaseError): pass
