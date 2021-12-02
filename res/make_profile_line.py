# -*- coding: utf-8 -*-
"""
Created on Fri Oct 30 08:03:46 2020

@author: wagen
"""
import sys
base = 'C:\\Users\\wagen\\25 Heroquest\\HQ_Card_Maker\\HQ_Card_Maker'
if base not in sys.path:
    sys.path.append(base)

from PIL import Image, ImageDraw
from res.conf import Conf
from pathlib import Path
from res.arrange_symbols import symbol_adder
from res.make_textframe import find_font, adjust_font_width
import re


class Positioning():
    ''' Contains:
    pad (int): Distance in pixel that elements keep from each other
    xmult, ymult (int): Distance to move from one square to the next
    squaresize: The standard square size for this grid
    '''

    def __init__(self, pad, xmult, ymult, squaresize):
        self.pad = pad
        self.xmult = xmult
        self.ymult = ymult
        self.squaresize = squaresize

    def x_center(self, column, im_width, sq_size=None):
        ''' finds a good starting position for the text, so that
        it is centered in total
        column: Which column in the grid does this square inhabit
        im_width (int): width of the image to be fitted
        sq_size (2-tuple): Size of the usable square in the grid. If nothing
            is given,
            the standard grid square size will be used, if somethign is given,
            the center of the alternate square will be used instead.

        returns x_pos: position for the image to start, so that the total
            image is centered in the grid square
        '''
        if sq_size is None:
            sq_size = self.squaresize
        # position inside the square
        x_pos = (sq_size[0] + self.pad - im_width) // 2
        # move the position by the position in the grid
        x_pos = x_pos + column * self.xmult
        return x_pos

    def y_center(self, row, im_height, sq_size=None):
        ''' finds a good starting position for the input image, so that
        it is centered in it's square

        row: Which position in the grid does this square inhabit
        im_height: height of the image to be fitted
        sq_size: Size of the usable square in the grid. If nothing is given,
            the standard grid square size will be used, if somethign is given,
            the center of the alternate square will be used instead.

        returns y_pos: position for the image to start, so that the total
            image is centered in the grid square
        '''
        if sq_size is None:
            sq_size = self.squaresize
        # position in the center of a row
        y_pos = (sq_size[1] + self.pad - im_height) // 2
        # shift by the number of rows
        y_pos = y_pos + row * self.ymult
        return y_pos


def interpret_profile_text(profile_str, language="en"):
    ''' A monster profile in Heroquest contains Name, Symbol,
    Speed (called "move"), AT, DE, BP, MP and a special rule.
    If no symbol is given, the name will be used to search the symbol list.
    If a symbol is given, it can have a color other than black.

    If only numbers are given, I assume the order above.

    If descriptions are given but no commas, I assume that the content
    follows the title ("AT 2 DE 4 rules: can cast "Fireball"").

    If the list is comma separated and has titles, the order doesn't
    matter. The rules section always has to be the last thing.

    profile = {"name":"",
                "symbol":"",
                "move":["Move",0],
                "at":["AT",0],
                "de":["DE",0],
                "bp":["BP",0],
                "mp":["MP,0],
                "rules":"",
                "symbol_image":{'symbol': '',
                                'color': '',
                                'index': 0}}
    '''
    profile = {}
    commas = profile_str.count(',')
    if commas > 3:
        values = profile_str.split(',')
        used_items = []  # take notes which item has been milked already
        rules_found = False  # after the keyword "rules" everything goes
        # into the rule pot
        for value in values:
            regex_check(profile, values,
                        used_items, rules_found,
                        value)

        # clean out interpreted items so that the rest is treated separate
        for index in used_items:
            values[index] = ""
        values = [value for value in values if value != ""]
        titles = ["name", "symbol", "move",
                  "at", "de", "bp", "mp"]

        # if there are values left over, treat them as if they were comma
        # separated values in the right order.
        # "rules" are out of this, they must be annotated as they are language
        # dependent.
        missing_titles = [i for i in titles if i not in profile]

        if (len(missing_titles) > 0
                and len(values) > 0):
            value_idx = 0
            for title in missing_titles:
                profile[title] = values[value_idx]
                values[value_idx] = ""
                value_idx += 1
                if value_idx >= len(values):
                    break

    # language specific adaptations go here
    # replace "d" with "w" in German for example
    if language == "de":
        titles_to_check = ["move", "at", "de", "bp", "mp"]
        for title in titles_to_check:
            profile[title][1] = profile[title][1].replace("d", "w")
    return profile


def regex_check(profile, values, used_items, rules_found, value):

    if rules_found:
        profile["rules"] = profile["rules"] + ", " + value
        used_items.append(values.index(value))

    if ("rules" in value.lower()
            or "regeln" in value.lower()):
        rules_found = True
        regex = re.compile(r'\s?(rules|regeln):?\s?', re.IGNORECASE)
        profile["rules"] = regex.sub("", value)
        used_items.append(values.index(value))
        value = ""

    if "name" in value.lower():
        regex = re.compile(r'\s?name:?\s?', re.IGNORECASE)
        profile["name"] = regex.sub("", value)
        regex = re.compile(r'\s?profile:?\s?', re.IGNORECASE)
        profile["name"] = regex.sub("", profile["name"])
        used_items.append(values.index(value))

    if "symbol" in value.lower():
        regex = re.compile(r'\s?symbol:?\s?', re.IGNORECASE)
        profile["symbol"] = regex.sub("", value)
        used_items.append(values.index(value))

    if "move" in value.lower() or "speed" in value.lower():
        regex = re.compile(
            (r'(\s?(move|speed|tempo|bewegung):?\s?)(\d\w?\d?)'),
            re.IGNORECASE)
        if regex.match(value):
            profile["move"] = ["Move", regex.sub(r"\3", value)]
            used_items.append(values.index(value))

    if "at" in value.lower():
        regex = re.compile(r'\s?at:?\s?(\d\w?\d?)', re.IGNORECASE)
        if regex.match(value):
            profile["at"] = ["AT", regex.sub(r"\1", value)]
            used_items.append(values.index(value))

    if "de" in value.lower():
        regex = re.compile(r'\s?de:?\s?(\d\w?\d?)', re.IGNORECASE)
        if regex.match(value):
            profile["de"] = ["DE", regex.sub(r"\1", value)]
            used_items.append(values.index(value))

    if "bp" in value.lower():
        regex = re.compile(r'\s?(bp|lp|lebenspunkte|körperkraft):?\s?(\d\d?)',
                           re.IGNORECASE)
        if regex.match(value):
            profile["bp"] = ["BP", regex.sub(r"\2", value)]
            used_items.append(values.index(value))

    if "mp" in value.lower():
        regex = re.compile(r'\s?(mp|ip|intelligenz):?\s?(\d\d?)',
                           re.IGNORECASE)
        if regex.match(value):
            profile["mp"] = ["MP", regex.sub(r"\2", value)]
            used_items.append(values.index(value))


def make_profile(profile_str,
                 im_size=(400, 300),
                 language="en",
                 ** conf):

    profile = interpret_profile_text(profile_str, language)
    sym = symbol_adder(**conf)
    sym.identify_colors_and_symbols(profile['symbol'])
    profile['symbol_image'] = sym.symbols
    profile['symbol_image'] = sym.load_symbols_and_update_colors(
        symbols=profile['symbol_image'])

    fontfolder = Path(conf['basepath']) / conf['fontfolder']
    pad = 4
    # 2 squares for the symbol, 5x1 squares for the values
    x_max_cols = 7
    # 2 rows for the profile line, 1 row for the name, 2 rows for the rules
    rule_rows = 2
    y_max_rows = 3 + rule_rows
    y_grid_rows = 2  # needs to get 1 more per row added
    x_mult = (im_size[0] - 2) / x_max_cols
    y_mult = (im_size[1] - 2) / y_max_rows
    # one by one, add headlines and their values from the profile
    sq_size = (int(x_mult - pad), int(y_mult - pad))
    #black = (0, 0, 0, 255)
    darkred = conf['darkred']
    transparent = (255, 255, 255, 0)

    # persists some base values and gives some practical methods
    cen = Positioning(pad, x_mult, y_mult, sq_size)

    # To define the grid lines
    # "line_name": [(startx, starty), (endx, endy)]
    # in grid coodinates, not pixel coordinates
    inner_grid_lines = {
        "middle": [(2, 1), (x_max_cols, 1)],
        # "move": [(2, 0), (2, y_grid_rows)],
        "at": [(3, 0), (3, y_grid_rows)],
        "de": [(4, 0), (4, y_grid_rows)],
        "bp": [(5, 0), (5, y_grid_rows)],
        "mp": [(6, 0), (6, y_grid_rows)],
    }
    cols = {
        "headline": 0,
        "rules": 0,
        "symbol": 0,
        "move": 2,
        "at": 3,
        "de": 4,
        "bp": 5,
        "mp": 6,
    }
    rows = {"headline": 0,
            "top_grid": 1,
            "bottom_grid": y_grid_rows,
            }
    texts = {'de': {
        'name': "Name",
                'move': "Tempo",
                'at': "AT",
                'de': "DE",
                'bp': "LP",
                'mp': "IP",
                'rules': "Regeln"},
             'en': {
        'name': "Name",
                'move': "Move",
                'at': "AT",
                'de': "DE",
                'bp': "BP",
                'mp': "MP",
                'rules': "Rules"},
             }
    rows["rules"] = rows["bottom_grid"] + 1
    # place the symbol centered between grid top and grid bottom
    rows["symbol"] = (rows["top_grid"] + rows["bottom_grid"]) / 2

    top_text_area = [0, 0, 7, 1]  # Headline Square
    # how many rows to move the grid down
    y_grid_shift = top_text_area[3]

    # determine font size
    fontpath = fontfolder / "HQModern.ttf"
    smallfont, t_h = adjust_font_width(fontpath, msg=texts[language]["move"],
                                       max_size=sq_size, **conf)
    bigfont, t_h = adjust_font_width(fontpath, msg="ABC",
                                     max_size=sq_size, **conf)
    ############################################################
    # start making: symbol first. This is im-to-im pasting
    # the rest is drawing
    im = Image.new(mode=conf['colorformat'], size=im_size, color=transparent)

    symsquare = (sq_size[0] * 2, sq_size[1] * 2)
    im = paste_symbol(im, profile, cen,
                      cols["symbol"], rows["symbol"], symsquare)

    ##########################################################
    # Add the name on top
    # start a draw on the im, then put everything inside th draw
    draw = draw_grid(im, x_mult, y_mult, darkred,
                     inner_grid_lines, y_grid_shift)
    msg = profile['name']
    text_size = draw.textsize(msg, bigfont)
    x_pos = cen.x_center(cols["headline"], text_size[0], im_size)
    y_pos = cen.y_center(rows["headline"], text_size[1])
    draw.text((x_pos, y_pos), msg, font=bigfont, fill=darkred)

    ###########################################################
    # paste the value names (which are stored in texts[language])
    profile_values = ['at', 'de', 'bp', 'mp']
    # move is treated separately cause it needs another font size
    msg = texts[language]['move']
    paste_txt(draw, msg, cen,
              cols['move'], rows["top_grid"], smallfont, darkred)

    for item in profile_values:
        msg = texts[language][item]
        paste_txt(draw, msg, cen,
                  cols[item], rows["top_grid"], bigfont, darkred)

    ###########################################################
    # paste the value contents (which are stored in profile[item][1])
    profile_values = ['move', 'at', 'de', 'bp', 'mp']
    for item in profile_values:
        paste_txt(draw, profile[item][1], cen,
                  cols[item], rows["bottom_grid"], bigfont, darkred)

    #########################################################
    # Add the special rule if available
    # adjust y_pos to bottom row
    if ("rules" in profile and len(profile["rules"]) > 0):
        msg = texts[language]["rules"] + ": " + profile['rules']
        add_special_rule(msg, draw, cen, language,
                         cols["rules"], rows["rules"], rule_rows,
                         fontpath, bigfont, darkred, **conf)
    return im


def add_special_rule(msg, draw, cen, language,
                     col, row, n_rows,
                     fontpath, font, color,
                     **conf):
    '''Adds the special rule under the profile line.
    rule (str): The rule you want to have added
    draw (ImageDraw.Draw): Reference to an existing drawing
    cen: Object giving image details and functions for centering
    col (int): The place on the profile grid where the text shall go.
        attention - it is assumed that from this col to the right border
        of the image, all the space is available (as opposed to the other
        text placement functions which use just one grid square)
    row (int): The place on the profile where the text shall go
    n_rows(int): How many lines we may use for the text
    fontpath (pathlib path): In case a new fontsize has to be found, the path
        to the original font
    font: The sized font used elsewhere in the profile (preferred)
    color (4-tuple int): The color the new text shall have in rgba
    conf: The configuration dict used everywhere
    '''

    text_size = draw.textsize(msg, font)
    if text_size[0] > draw.im.size[0] - cen.pad:
        wish_size = (draw.im.size[0] - cen.pad, cen.squaresize[1] * n_rows)
        font, move_h, text_h, msg_lines = find_font(fontpath=fontpath,
                                                    msg=msg,
                                                    textsize=wish_size,
                                                    language=language,
                                                    wrap=True,
                                                    security=False,
                                                    max_fontsize=font.size,
                                                    **conf)
    else:
        msg_lines = [msg]

    y_pos = cen.y_center(row, text_size[1])
    for textline in msg_lines:
        text_size = draw.textsize(textline, font)
        x_pos = cen.x_center(col, text_size[0], draw.im.size)
        draw.text((x_pos, y_pos), textline, font=font, fill=color)
        y_pos = y_pos + text_size[1]


def paste_txt(draw, msg, cen, col, row, font, color):
    text_size = draw.textsize(msg, font)
    y_pos = cen.y_center(row, text_size[1])
    x_pos = cen.x_center(col, text_size[0])
    draw.text((x_pos, y_pos), msg, font=font, fill=color)


def paste_symbol(im, profile, cen,
                 col, row, symsquare) -> Image:
    sym = profile['symbol_image'][0]['image']
    # check if the symbol is too big, and if yes, shrink it
    if (sym.size[0] > symsquare[0]
            or sym.size[1] > symsquare[1]):
        ratio = min(symsquare[0] / sym.size[0],
                    symsquare[1] / sym.size[1])
        sym = sym.resize((int(sym.size[0] * ratio),
                          int(sym.size[1] * ratio)))
    y_pos = cen.y_center(row, sym.size[1])
    x_pos = cen.x_center(col,
                         sym.size[0], symsquare)

    im.paste(sym, (int(x_pos), int(y_pos)), mask=sym)
    return im


def draw_grid(im, x_step, y_step, color, grid, y_grid_shift, lwidth=3):
    '''
    draws a grid on the image
    im (PIL.Image): The image canvas to draw the grid on
    x_step, y_step: The step size from grid square to grid square in pixel
    color (4-tuple): The color to be used in RGBA format
    grid (dict): A dict of named squares with top, bottom, left, right coords
    y_grid_shift (int): How  many rows to move the center square down from the
        top of the image
    lwdith (int): line width of drawing
    '''
    draw = ImageDraw.Draw(im)
    for key in grid:
        coords = grid[key]
        draw.line((coords[0][0] * x_step,
                   (coords[0][1] + y_grid_shift) * y_step,
                   coords[1][0] * x_step,
                   (coords[1][1] + y_grid_shift) * y_step),
                  fill=color,
                  width=lwidth)
    return draw


if __name__ == "__main__":
    configuration = Conf()
    conf = configuration.conf
    profile_str = ("Goblin Spearman Superhero, Symbol: green Goblin Spearman, "
                   + "Rules: Can move one square after attacking, "
                   + "Move 2d6, AT 2, DE 3, BP 3, MP 4, ")
    im = make_profile(profile_str, language="de", ** conf)

    # write to stdout
    im.show()
    from time import sleep
    sleep(10)
    im.close()
