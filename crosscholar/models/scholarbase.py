from urlman import URLFactory


class User:
    def __init__(self, id_=None, name=None, page=None, avatar=None, affiliation=None, citations_count=0,
                 citation_per_year=None):
        self.attrs = {
            'id':                [id_,  'Scholar Id',          0],
            'name':              [name,  'Author name',         1],
            'page':              [page,  'Profile Page URL',    2],
            'avatar':            [avatar,  'Avatar URL',          3],
            'affiliation':       [affiliation,  'Affiliation',         4],
            'citations_count':   [citations_count,     'Citations count',     5],
            'citation_per_year': [citation_per_year if citation_per_year is not None else {},    'Citations per year',  6]
        }

    def __setitem__(self, key, item):
        if key in self.attrs:
            self.attrs[key][0] = item
        else:
            self.attrs[key] = [item, key, len(self.attrs)]

    def __getitem__(self, key):
        if key in self.attrs:
            return self.attrs[key][0]
        return None

    def __delitem__(self, key):
        if key in self.attrs:
            del self.attrs[key]

    def as_txt(self):
        # Get items sorted in specified order:
        items = sorted(list(self.attrs.values()), key=lambda item: item[2])
        # Find largest label length:
        max_label_len = max([len(str(item[1])) for item in items])
        fmt = '%%%ds: %%s' % max_label_len
        res = []
        for item in items:
            if item[0] is not None and not isinstance(item[0], URLFactory):
                res.append(fmt % (item[1], item[0]))
            elif item[0] is not None and isinstance(item[0], URLFactory):
                res.append(fmt % (item[1], item[0].url))
        return '\n'.join(res)

    def as_csv(self, header=False, sep='|'):
        # Get keys sorted in specified order:
        keys = [pair[0] for pair in
                sorted([(key, val[2]) for key, val in list(self.attrs.items())],
                       key=lambda pair: pair[1])]
        res = []
        if header:
            res.append(sep.join(keys))
        res.append(sep.join([str(self.attrs[key][0]) if key != 'page' else self.attrs[key][0].url for key in keys]))
        return '\n'.join(res)

    def keys(self, sep='|'):
        keys = [pair[0] for pair in
                sorted([(key, val[2]) for key, val in list(self.attrs.items())],
                       key=lambda pair: pair[1])]

        return sep.join(keys)


class Work:
    """
    A class representing works listed on Google Scholar.

    The class provides basic dictionary-like behavior.
    """

    def __init__(self, gsc_title=None, url=None):
        # The triplets for each keyword correspond to (1) the actual
        # value, (2) a user-suitable label for the item, and (3) an
        # ordering index:
        self.attrs = {
            'id':                   [None, 'Scholar Id',             0],
            'doi':                  [None, 'DOI',                    1],
            'gsc_title':            [gsc_title, 'Scholar Title',     2],
            'crf_title':            [None, 'Crossref Title',         3],
            'match_ratio':          [0,    'Match ratio',            4],
            'url':                  [url,  'URL',                    5],
            'authors':              [None, 'Authors',                6],
            'gsc_publication':      [None, 'Scholar Publication',    7],
            'crf_publication':      [None, 'Crossref Publication',   8],
            'gsc_type':             [None, 'Scholar Type',           9],
            'crf_type':             [None, 'Crossref Type',         10],
            'volume':               [None, 'Scholar Volume',        11],
            'issue':                [None, 'Scholar Issue',         12],
            'pages':                [None, 'Scholar Pages',         13],
            'year':                 [None, 'Year',                  14],
            'citations_count':      [0,    'Citations Count',       15],
            'citations_url':        [None, 'Citations Page link',   16],
            'wos_citations_count':  [None, 'WOS Citations Count',   17],
            'wos_citations_url':    [None, 'WOS Citations URL',     18],
            'citations_per_year':   [{},   'Citations per year',    19],
            'user_id':              [None, 'User relationship',     20]
        }

        # The citation data in one of the standard export formats,
        # e.g. BibTeX.
        self.citation_data = None

    def __getitem__(self, key):
        if key in self.attrs:
            return self.attrs[key][0]
        return None

    def __len__(self):
        return len(self.attrs)

    def __setitem__(self, key, item):
        if key in self.attrs:
            self.attrs[key][0] = item
        else:
            self.attrs[key] = [item, key, len(self.attrs)]

    def __delitem__(self, key):
        if key in self.attrs:
            del self.attrs[key]

    def as_txt(self):
        # Get items sorted in specified order:
        items = sorted(list(self.attrs.values()), key=lambda item: item[2])
        # Find largest label length:
        max_label_len = max([len(str(item[1])) for item in items])
        fmt = '%%%ds: %%s' % max_label_len
        res = []
        for item in items:
            if item[0] is not None:
                res.append(fmt % (item[1], item[0]))
        return '\n'.join(res)

    def as_csv(self, header=False, sep='|'):
        # Get keys sorted in specified order:
        keys = [pair[0] for pair in
                sorted([(key, val[2]) for key, val in list(self.attrs.items())],
                       key=lambda pair: pair[1])]
        res = []
        if header:
            res.append(sep.join(keys))

        res.append(sep.join([str(self.attrs[key][0]) for key in keys]))

        return '\n'.join(res)

    def keys(self, sep='|'):
        keys = [pair[0] for pair in
                sorted([(key, val[2]) for key, val in list(self.attrs.items())],
                       key=lambda pair: pair[1])]

        return sep.join(keys)
