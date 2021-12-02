import configparser
from ast import literal_eval
from pathlib import Path


class Conf():
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.conf = {}
        sizes = dict(self.config.items('sizes'))
        self.sizes = {key: literal_eval(sizes[key])
                      for key in sizes}
        self.conf.update(self.sizes)

        colors = dict(self.config.items('colors'))
        colors['vanilla'] = literal_eval(colors['vanilla'])
        colors['darkred'] = literal_eval(colors['darkred'])
        self.conf.update(colors)

        paths = dict(self.config.items('paths'))
        paths['basepath'] = Path(paths['basepath'])
        paths['inputpath'] = paths['basepath'] / paths['inputpath']
        paths['picpath'] = paths['basepath'] / paths['picpath']
        paths['fontfolder'] = paths['basepath'] / paths['fontfolder']
        paths['notfound_image'] = paths['basepath'] / paths['notfound_image']
        paths['outpath_base'] = paths['basepath'] / paths['outpath_base']
        paths['outpath_online'] = paths['basepath'] / paths['outpath_online']
        paths['outpath_phone'] = paths['basepath'] / paths['outpath_phone']
        paths['outpath_print'] = paths['basepath'] / paths['outpath_print']
        paths['templatefolder'] = paths['basepath'] / paths['templatefolder']
        paths['pokerframe'] = paths['templatefolder'] / paths['pokerframe']
        paths['normalframe'] = paths['templatefolder'] / paths['normalframe']
        paths['headline'] = paths['templatefolder'] / paths['headline']
        self.conf.update(paths)

        downloads = dict(self.config.items('downloads'))
        self.conf.update(downloads)

    def get(self, name):
        if name in self.config.sections():
            return dict(self.config.items(name))
        else:
            return None
