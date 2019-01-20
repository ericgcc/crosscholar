# Python imports
from pathlib import Path
from functools import reduce

# Vendor imports
import toml

# Crosscholar modules imports
from exceptions import ConfigurationError


class Configuration:

    def __init__(self, f):
        try:
            self.__config = toml.load(f)
        except FileNotFoundError:
            print(f"Toml configuration file '{f}' not found")
            exit(1)

        self.download_dir = self.get_download_dir()
        self.limits = self.get_limits()
        self.driver = self.get_driver_dir()

        self.crossref = self.__config['crossref']['enabled'] if 'enabled' in self.__config['crossref'] else True

        if self.crossref:
            self.crossref_to = self.get_crossref_mail()

        self.notify = self.__config['notify']['enabled'] if 'enabled' in self.__config['notify'] else False

        if self.notify:
            self.notify_from, self.notify_pass, self.notify_host, self.notify_to = self.get_notify()

    def get_download_dir(self):
        return self.__config['download_dir'] if 'download_dir' in self.__config else \
            str(Path.home()) + "\\Downloads\\crosscholar\\"

    def get_driver_dir(self):
        if 'driver_dir' not in self.__config:
            raise ConfigurationError("Missing parameter in toml configuration file: key 'driver_dir'")

        return self.__config['driver_dir']

    def get_crossref_mail(self):
        if not ('crossref' in self.__config and 'mail_to' in self.__config['crossref']):
            raise ConfigurationError("Missing parameter in toml configuration file: Table 'crossref', key 'mail_to'")

        return self.__config['crossref']['mail_to']

    def get_notify(self):
        if 'mail_from' not in self.__config['notify']:
            raise ConfigurationError("Missing parameter in toml configuration file: Table 'notify', key 'mail_from'")

        if 'mail_pass' not in self.__config['notify']:
            raise ConfigurationError("Missing parameter in toml configuration file: Table 'notify', key 'mail_pass'")

        if 'mail_host' not in self.__config['notify']:
            raise ConfigurationError("Missing parameter in toml configuration file: Table 'notify', key 'mail_host'")

        if 'mail_to' not in self.__config['notify']:
            raise ConfigurationError("Missing parameter in toml configuration file: Table 'notify', key 'mail_to'")

        return self.__config['notify']['mail_from'], self.__config['notify']['mail_pass'], \
            self.__config['notify']['mail_host'], self.__config['notify']['mail_to']

    def get_limits(self):
        if 'limits' in self.__config:
            product = reduce(lambda x, y: x*y, self.__config['limits']) == 0

            # Checking if limits is a list of non-zero positive integers
            if not all(isinstance(x, int) for x in self.__config) or product <= 0:
                return None

            return tuple(self.__config['limits'])
        return None
