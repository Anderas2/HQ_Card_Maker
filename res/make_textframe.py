# -*- coding: utf-8 -*-
from PIL import ImageFont, Image, ImageDraw
from math import ceil, floor
import re
import textwrap
from res.HQRegex import HQRegex


def use_specialsigns(in_str, short_signlist=True, language='en'):
    hq_words = HQRegex(country=language)
    # comment, regex, sign as usable in HQModern font, color of the sign
    special_signs = [['Mind Point', re.compile(
        hq_words.mp, re.I | re.M), '♦', (0, 0, 255)],
        ['Body Point', re.compile(
            hq_words.bp, re.I | re.M), '♥', (255, 0, 0)],
        ['walrus', re.compile(
            hq_words.walrus, re.I | re.M), '│', (0, 0, 0)],
        ['skull', re.compile(
            hq_words.skull, re.I | re.M), '─', (0, 0, 0)],
        ['shield', re.compile(
            hq_words.shield, re.I | re.M), '━', (0, 0, 0)],
        ['white die', re.compile(
            hq_words.whitedie, re.I | re.M), '┘', (0, 0, 0)],
        ['red die', re.compile(
            hq_words.reddie, re.I | re.M), '┗', (255, 0, 0)],
        ['discard the card', re.compile(
            hq_words.discard, re.I | re.M), '╱', (0, 0, 0)],
        ['Mastery Test', re.compile(
            hq_words.mastery, re.I | re.M), '╳', (0, 0, 0)],
        ['Gold Coin', re.compile(
            hq_words.coin, re.I | re.M), '╄', (0, 0, 0)],
    ]
    if short_signlist:
        special_signs = special_signs[:-3]
    for searchword in special_signs:
        in_str = searchword[1].sub(searchword[2], in_str)
    sign_color_dict = {}
    for sign in special_signs:
        sign_color_dict[sign[2]] = sign[3]

    return in_str, sign_color_dict
#signs_small_set = ['♦','♥', '─','━','│','╱','╳','┘','┗']
#inv_signs = {v: k for k, v in special_signs.items()}


def replace_specials(msg, signs):
    ''' unfinished function to implement the special signs of HQ Modern.
    The dream is to have certain symbols replaced, like the ever-repeating
    sentence "Discard this card".
    '''
    # TODO: Finish this function and implement it!
    for sign in signs:
        msg = msg.replace(sign, signs[sign])
    return msg


def find_max_width(in_text, text_w_px, font, security=True):
    """ Finds the maximum width of text as measured in letters.
    As it is a little bit inexact along the lines due to different
    numbers of CAPITAL letters, a little bit is removed for security
    before giving back the result. """

    text_w = font.getsize(in_text)[0]  # gets text width in pixel
    if security:
        # adds three quarters of a text row for security
        number_of_rows = ceil(text_w / text_w_px + 0.25)
        return len(in_text) // number_of_rows
    else:
        # removes 1 letter so to fills end-to-end without cutting the
        # last letter
        return floor(len(in_text) * text_w_px / text_w) - 1


def wrap_text_on_card(in_text,
                      maxwidth=38,  # text width in letters
                      # maxheight=13  # text height in lines
                      ):
    ''' Gets a text in_text and splits it into lines to fit the defined
    margins maxwidth is the maximum number of letters per line. It will be
    adjusted from outside.
    maxheight is the maximum number of lines for this text space.
        maxheight is currently not used.
    returns a list of text lines.
    '''
    # first, split into lines by newlines coming from the text
    new_msg = re.split('\n', in_text)

    # now split the rest fitting to the space restrictions
    lines = []
    for line in new_msg:
        lines.append(textwrap.wrap(line, width=int(maxwidth),
                                   replace_whitespace=False))
    # special signs and newlines are not treated very well by the textwrap
    # function, so I treat them well now.
    messages = []
    for sublist in lines:
        if len(sublist) == 0:
            sublist = [' ']
        for item in sublist:
            if len(item) <= 1:
                item = ' '
            messages.append(item)
    return messages


def make_textparts(line, sign_colors, textcolor):
    '''disassembles the text line, checks word by word if there is some
    part of the text that shall have a special color as specified in
    sign_colors. Makes a list of dicts that gives text parts and their
    associated colors.

    The result looks like that:

        [{'color': 'black', 'text': 'Lorem ipsum '},
         {'color': (0, 0, 255), 'text': '♦'},
         {'color': 'black', 'text': ' dolor sit amet,'}]

    line: One line of text
    sign_colors: A dict of words or signs and the color they shall have
    textcolor: The color that all the rest of hte text shall have

    '''
    # check if colored special signs appear in the line.
    # every text part will have a color property.
    textparts = []
    textparts.append({'text': '',
                      'color': textcolor})

    if len(line) <= 1:  # empty line, don't do the rest.
        textparts[-1]['text'] = ' '
    else:
        # assign colors to words, word-by-word
        allgroups = re.split(r'(\s)', line)  # split in words, keep separators
        words = allgroups[0::2]
        separators = allgroups[1::2]
        if len(separators) < len(words):
            separators.append('')  # add one entry at the end of the list
        for i, word in enumerate(words):
            if word not in sign_colors.keys():
                # standard text, just add to the last part of the standard
                # text
                textparts[-1]['text'] += word + separators[i]
            else:
                # special colored sign. Make a new text part with a special
                # color and the sign inside, then start the next standard
                # text part.
                textparts.append({'text': word,
                                  'color': sign_colors[word]})
                textparts.append({'text': separators[i],
                                  'color': textcolor})
    return textparts


def adjust_font_width(fontpath, msg, max_size, **conf):
    fontsizes = [38, 32] + list(range(31, 14, -1))  # fontsizes to be used
    if fontpath.exists():
        fontfile = fontpath
    if not fontfile.exists():
        fontfile = conf["fontfolder"] / fontpath
    if not fontfile.exists():
        fontfile = conf["fontfolder"] / "HQModern.ttf"

    for i, fontsize in enumerate(fontsizes):
        font = ImageFont.truetype(str(fontfile), fontsize)
        text_size = font.getsize(msg)
        if text_size[0] < max_size[0]:
            break
    return font, text_size[1]


def find_font(fontpath, msg, textsize, language="en",
              wrap=True, security=True, max_fontsize=None, **conf):
    '''
    check the text size and see if it works with the im restrictions
    if not, switch to smaller padding and/or smaller font size.
    maxwidth = 38 for fontsize = 32
    maxwidth = 34 for fontsize = 38

    Parameters
    ----------
    fontpath : string
        path to a font that shall be used.
    msg : string
        text to be treated.
    textsize : 2-tuple (x, y)
        image size where the text shall fit
    language : 'en' or 'de', optional
        if set on "de", less letters per line will be used because there are
        many CAPITAL letters in German using more space. The default is "en".
    wrap : bool, optional
        Shall the text be wrapped to fit in the space. The default is True.

    Returns
    -------
    font : returns the chosen font including size as ImageDraw needs it.
    move_h : pixel to move for the next line.
    text_h : estimated text height in total.
    msg_lines : all message lines after the wrap did it's work; or one single
    line if wrap was turned off.

    '''

    # check the text size and see if it works with the im restrictions
    # if not, switch to smaller padding and/or smaller font size.
    # maxwidth = 38 for fontsize = 32
    # maxwidth = 34 for fontsize = 38
    fontsizes = [38, 32] + list(range(31, 14, -1))  # fontsizes to be used
    if max_fontsize:
        fontsizes = [size
                     for size in fontsizes
                     if size <= max_fontsize]
    pads = [12, 10, 8, 5, 4, 2]  # minimum distance between two lines in pixel
    if fontpath.exists():
        fontfile = fontpath
    if not fontfile.exists():
        fontfile = conf["fontfolder"] / fontpath
    if not fontfile.exists():
        fontfile = conf["fontfolder"] / "HQModern.ttf"

    for i, fontsize in enumerate(fontsizes):
        font = ImageFont.truetype(str(fontfile), fontsize)
        maxwidth = find_max_width(msg, textsize[0], font, security=security)

        if language == 'de':
            # because of many CAPITAL letters in german,
            # we need to use less letters per line.
            maxwidth = maxwidth - 2

        for pad in pads:
            if wrap:
                msg_lines = wrap_text_on_card(msg, maxwidth=maxwidth)
            else:
                msg_lines = [msg]

            line_h = 0
            for line in msg_lines:
                t_h = font.getsize(line)[1]
                line_h = max(t_h, line_h)

            # calculate full text height
            # vertical movement per line
            move_h = (line_h + pad)

            # text height plus minimum distance between the lines
            text_h = (move_h * len(msg_lines))
            if text_h < textsize[1]:
                break

        if text_h < textsize[1]:
            break
    return font, move_h, text_h, msg_lines


def make_text_body(msg="Empty Card",
                   # symbols="",
                   textcolor='black',
                   textsize=None,
                   # use_specials=False,
                   language='en',
                   **conf):
    ''' Makes the text body for a play card.
    msg: The text that shall be on the playcard.
    symbols: a string giving instructions as to what symbols to use
    textcolor: you can define any color here. default is black.
    use_specials: shall the special signs of hq_modern be used or not.
    language: The text can be in different languages. This is important for
        the regexes that replace repeating sentences with special signs.
    returns: An image of the text fitting with the dimensions of the input
        image.
    '''
    if textsize is None:
        textsize = conf["textframe_size"]
    textsize = int(textsize[0]), int(textsize[1] * 1.)
    im = Image.new(conf["colorformat"], textsize, conf["vanilla"])
    draw = ImageDraw.Draw(im)
    sign_colors = {'♦': (0, 0, 255),
                   '♥': (255, 0, 0)}
    fontpath = conf["fontfolder"] / "HQModern.ttf"
    font, move_h, text_h, msg_lines = find_font(fontpath=fontpath,
                                                msg=msg,
                                                textsize=textsize,
                                                language=language,
                                                **conf)
    # Make vertically centered starting position
    current_h = (textsize[1] - text_h) // 2
    # now, line by line, make texts
    for line in msg_lines:
        textparts = make_textparts(line, sign_colors, textcolor)

        # every part has it's assigned color now.
        # print it along the line, part for part
        # check text size for center positioning
        # Text size should be good now.
        # determine start for horizontally centered text
        t_w, t_h = draw.textsize(line, font=font)
        start_w_pos = (textsize[0] - t_w) // 2
        current_w = start_w_pos
        for textpart in textparts:
            t_w, t_h = draw.textsize(textpart['text'],
                                     font=font)
            draw.text((current_w, current_h),
                      textpart['text'],
                      font=font,
                      fill=textpart['color'])
            current_w += t_w  # move position forward to new place
        current_h += move_h
    return im
