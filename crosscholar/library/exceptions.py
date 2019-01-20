class UrlError(Exception):
    def __init__(self):
        Exception.__init__(self, 'The URL has not been generated yet')


class KeywordsError(Exception):
    def __init__(self):
        Exception.__init__(self, "There aren't keywords for this search")


class ConfigurationError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)