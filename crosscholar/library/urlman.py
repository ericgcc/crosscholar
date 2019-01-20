import binascii
from enum import Enum
from exceptions import (UrlError, KeywordsError)
from bs4 import BeautifulSoup
from random import choice


class ScholarURLType(Enum):
    BASE = "http://scholar.google.com"
    CITATIONS = "/citations?hl=en&view_op=search_authors&mauthors="
    CITATIONS_USER = "/citations?hl=en&oe=ASCII&user="
    SEARCH = "/scholar?hl=en&as_sdt=0%2C5&q=<title>&btnG="


class URLFactory:
    def __init__(self, type_: ScholarURLType = None, keywords=None, url=None, cstart=0, page_size=100):
        self.__keywords = keywords.replace(' ', '+') if keywords is not None else keywords
        self.type_ = type_
        self.__url = url
        self.__cstart = cstart
        self.__page_size = page_size

        if self.type_ == ScholarURLType.CITATIONS_USER and self.__url is None:
            raise UrlError()

    @property
    def url(self):
        if self.__url is None:
            raise UrlError()

        return self.__url

    @url.setter
    def url(self, value):
        self.__url = value

    @property
    def keywords(self):
        if self.__keywords is None:
            raise KeywordsError()

        return self.__keywords

    @keywords.setter
    def keywords(self, value):
        self.__keywords = value.replace(' ', '+')

    @property
    def cstart(self) -> int:
        return self.__cstart

    @cstart.setter
    def cstart(self, value: int) -> None:
        self.__keywords = value

    @property
    def page_size(self) -> int:
        return self.__page_size

    @page_size.setter
    def page_size(self, value: int) -> None:
        self.page_size = value

    def generate(self):
        if self.type_ == ScholarURLType.BASE:
            self.url = ScholarURLType.BASE.value
            return self.url

        if self.type_ == ScholarURLType.CITATIONS:
            self.url = ScholarURLType.BASE.value + ScholarURLType.CITATIONS.value + self.keywords
            return self.url

        # This url must be generated via the __init__ method
        if self.type_ == ScholarURLType.CITATIONS_USER and self.url is not None:
            return self.url

    def first_url(self):
        if self.type_ == ScholarURLType.CITATIONS_USER:
            return f"{self.url}&cstart=0&pagesize={self.page_size}"

        return self.url

    def next_url(self, soup: BeautifulSoup = None) -> str:
        if self.url is None:
            raise UrlError()

        if self.type_ == ScholarURLType.CITATIONS and soup is not None:
            raw_next_url = soup.find('button', attrs={"aria-label": "Next"})['onclick']
            return ScholarURLType.BASE.value + url_decoder(raw_next_url)

        if self.type_ == ScholarURLType.CITATIONS_USER:
            self.__cstart += self.__page_size
            return f"{self.url}&cstart={self.cstart}&pagesize={self.page_size}"

        return self.url


def url_decoder(raw_url):
    clear_url = raw_url[16:].strip('\'')
    while clear_url.find('\\x') != -1:
        index = clear_url.find('\\x')
        hex_letter = clear_url[index + 2:index + 4]
        clear_url = clear_url.replace("\\x" + hex_letter, binascii.unhexlify(bytes(hex_letter, 'utf-8'))
                                      .decode('utf-8'))
    return clear_url


def get_proxy(protocol: str = 'http'):
    def http():
        proxies = [
            '204.12.155.204:3128',
            '173.212.136.237:80',
            '120.29.152.86:65103',
            '113.11.64.62:65103',
            '138.197.192.64:65000',
            '119.81.189.194:8123',
            '109.254.185.60:3128',
            '109.236.111.45:53281',
            '113.254.79.252:80',
            '151.80.156.147:8080',
            '81.49.137.110:80',
            '163.172.59.200:8080',
            '103.74.108.110:53281',
            '103.89.244.54:62225',
            '107.172.4.203:1080',
            '107.172.4.202:1080',
            '107.175.146.13:1080',
            '107.175.146.12:1080',
            '107.175.146.11:1080',
            '107.175.146.8:1080',
            '104.168.33.205:1080',
            '104.168.33.202:1080',
            '104.168.33.201:1080',
            '104.168.33.199:1080',
            '104.168.33.195:1080',
            '107.174.26.75:1080',
            '107.174.26.74:1080',
            '107.174.26.73:1080',
            '107.174.26.72:1080',
            '107.174.26.70:1080',
            '107.174.26.68:1080',
            '107.174.26.67:1080',
            '107.172.4.205:1080',
            '107.172.4.204:1080',
            '107.172.4.200:1080',
            '107.172.4.199:1080',
            '107.172.4.196:1080',
            '107.175.146.5:1080',
            '107.175.146.10:1080',
            '107.175.146.4:1080',
            '107.175.146.9:1080',
            '107.175.146.7:1080',
            '107.175.146.6:1080',
            '107.175.146.2:1080',
            '104.168.33.204:1080',
            '104.168.33.203:1080',
            '104.168.33.200:1080',
            '104.168.33.198:1080',
            '104.168.33.197:1080',
            '104.168.33.196:1080',
            '104.168.33.194:1080',
            '107.174.26.77:1080',
            '107.174.26.76:1080'
        ]

        return choice(proxies)

    def https():
        proxies = [
            '185.44.69.44:3128',
            '158.69.223.85:80',
            '167.114.100.69:9999',
            '24.37.176.38:8080',
            '204.12.155.204:3128',
            '138.197.192.64:65000',
            '119.81.189.194:8123',
            '109.254.185.60:3128',
            '151.80.156.147:8080',
            '101.78.219.178:8080',
            '212.191.32.83:8080',
            '46.37.193.74:3128',
            '93.104.208.147:3128',
            '113.161.161.188:8080',
            '186.24.48.244:3128',
            '159.203.84.241:3128',
            '173.192.21.89:8123',
            '112.121.60.36:8085',
            '18.221.30.147:3128',
            '13.58.246.35:3128',
            '173.192.21.89:25',
            '36.55.226.137:3128',
            '123.63.242.115:3128',
            '175.209.34.197:8080',
            '128.199.115.85:80',
            '46.37.193.74:8080',
            '128.199.201.12:3128',
            '14.141.73.11:8080',
            '128.199.201.12:8080',
            '134.213.214.47:3129'
        ]

        return choice(proxies)

    if protocol == 'http':
        return http()
    elif protocol == 'https':
        return https()
