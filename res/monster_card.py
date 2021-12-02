# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from PIL import ImageFont, Image, ImageDraw

carddict = {"name": "Goblin",
            "Rules": "Nothing special",
            "Move": 10,
            "AT": 2,
            "DE": 1,
            "MP": 1,
            "BP": 1,
            "Symbol": "Goblin",
            "Picture": "Goblin"}


class monstercard(object):
    def __init__(self,
                 carddict=None,
                 **kwargs
                 ):

        self.unpack_kwargs(kwargs)

    def unpack_kwargs(self, kwargs):
        basepath = kwargs.get("basepath")
        self.fontfolder = kwargs.get("fontfolder", basepath + 'input\\fonts\\')
        self.templatefolder = kwargs.get(
            "templatefolder", basepath + 'input\\card_sizes\\')
        self.colorformat = kwargs.get("colorformat", "RGBA")
        self.headline_size = kwargs.get("headline_size", (567, 96))
        self.style = kwargs.get("style", "eu").lower()

    def make_headline(self, headline_txt):
        ''' Changes font type fitting to the format defined in "style"
        (eu or us); then makes the headline and centers it. If it is too big,
        it will be made smaller to fit the card.'''
        size = 60

        im = Image.new(self.colorformat, self.headline_size, 'white')
        draw = ImageDraw.Draw(im)
        i_w, i_h = im.size

        for i in range(0, 31, 1):
            if self.style == "us":
                headfont = ImageFont.truetype(self.fontfolder + "Romic.ttf",
                                              size=size - i - 10,
                                              index=0)
            else:
                headfont = ImageFont.truetype(self.fontfolder + "hq_gaze.ttf",
                                              size=size - i,
                                              index=0)
            t_w, t_h = headfont.getsize(headline_txt)
            if t_w < i_w:
                break

        offset = ((i_w - t_w) // 2, (i_h - t_h) // 2)
        draw.text(offset,
                  headline_txt,
                  fill='black',
                  font=headfont)
        return im
