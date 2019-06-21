# -*- coding: utf-8 -*-
"""
Created on Tue Oct 30 11:32:35 2018

@author: Andreas Wagener
"""

from PIL import Image
from PIL import ImageFont
from PIL import ImageChops
from PIL import ImageDraw
import textwrap
import cardsize
#from os import path as ospath, curdir, makedirs, listdir, remove
from os import makedirs, listdir, path, remove
from pandas import read_excel, isnull
import re
from math import ceil
import sys
sys.path.append('C:\\Users\\Andreas\\25 Heroquest\\HQ_Card_Maker\\HQ_Card_Maker')
from HQRegex import HQRegex
import multiprocessing as multi
from pathlib import Path
hex(219)

DARKRED = (59,0,0)
VANILLA = (245,236,219)
COLORFORMAT = 'RGBA'

BASEPATH = 'C:\\Users\\Andreas\\25 Heroquest\\HQ_Card_Maker\\'
TEMPLATEFOLDER = BASEPATH + 'input\\card_sizes\\'
FONTFOLDER = BASEPATH + 'input\\fonts\\'
PICPATH = BASEPATH + 'input\\pics\\'

INPUT = BASEPATH + "input\\"

OUTPATH_BASE = BASEPATH + 'cards\\'
OUTPATH_ONLINE = 'online\\'
OUTPATH_PHONE = 'phone\\'
OUTPATH_PRINT = 'print\\'


POKERFRAME = TEMPLATEFOLDER + r'EU_Pokerframe.png'
NORMALFRAME = TEMPLATEFOLDER + r'EU_Frame.png'
HEADLINE = TEMPLATEFOLDER + r'headline_space.png'
HEADLINE_SIZE = (567, 96)
PICFRAME_SIZE = (500, 375)
TEXTFRAME_SIZE = (567, 522)
BASE_CARD_SIZE = (567, 995)

#%%
# Todo List:
# TODO: use pathlib for paths

# TODO: Make special sign search more efficient
# TODO: Hand, Head, Body, Feet as signs?



#%%

def read_cards(link = None):
    ''' reads cards with picture path and as many titles and bodies as you like.
    if there is title_en and body_en, there will be a US and a EU version
    for it, otherwise only the eu version.
    '''
    # search in input folder for a csv file
    # if found, open it and generate a list of card dicts
    if link == None:
        files = []
        for file in listdir(INPUT):
            if file.endswith(".xlsx"):
                files.append(INPUT + file)
    else:
        if r"edit?usp=sharing" in link:
            link = link.replace(r"edit?usp=sharing", "export?format=xlsx")
        files = []
        files.append(link)


    for file in files:
        in_pd = read_excel(file)
        in_pd = in_pd[isnull(in_pd["title_en"])==False]
        cards_raw = in_pd.to_dict(orient = 'records')
        language_versions = []
        for key in cards_raw[0].keys():
            if 'title_' in key:
                language_versions.append(key[-2:])

        # now go through the records, and append to each language everything that
        # can be found in the record. Append nothing if the language cell is empty.
        cards = []
        for record in cards_raw:
            card = {}
            pic_name = record['pic_path']
            if isnull(pic_name):
                pic_name = ""
            if path.isfile(pic_name):
                card['pic_path'] = pic_name

            elif path.isfile(PICPATH + pic_name):
                card['pic_path'] = PICPATH + pic_name

            else:
                card['pic_path'] = PICPATH + pic_name

            language = []
            for version in language_versions:
                # version contains "de", "en", "fr", "it" and so on
                # TODO: change format to actual card size format
                content = {'language': version,
                           'title': record['title_'+version],
                           'body': record['body_'+version],
                           'formats':['eu'],
                           'style':['eu']
                           }
                if version == 'en':
                    content['formats'].append('us')
                    content['style'].append('us')
                if not (isnull(content['title'])
                or isnull(content['body'])):
                    language.append(content)
            card['language'] = language
            card['tags'] = str(record['Tags']).lower()
            card['No'] = record['No']
            # splits card backs by comma, filters empty strings away
            back = record['card_back'].replace(" ", "")
            cardbacks = list(filter(None, back.split(",")))
            try:
                for cardback in cardbacks:
                    card['back'] = cardback
                    cards.append(card)
            except:
                print(record)
                print()
                print(cardbacks)
                raise
    return cards




#%%

def use_specialsigns(in_str, short_signlist = True, language = 'en'):
    hq_words = HQRegex(country = language)
    # comment, regex, sign as usable in HQModern font, color of the sign
    special_signs = [['Mind Point', re.compile(hq_words.mp, re.I|re.M), '♦', (0,0,255)],
                     ['Body Point', re.compile(hq_words.bp, re.I|re.M), '♥', (255,0,0)],
                     ['walrus', re.compile(hq_words.walrus, re.I|re.M), '│', (0,0,0)],
                     ['skull', re.compile(hq_words.skull, re.I|re.M), '─', (0,0,0)],
                     ['shield', re.compile(hq_words.shield, re.I|re.M), '━', (0,0,0)],
                     ['white die', re.compile(hq_words.whitedie, re.I|re.M), '┘', (0,0,0)],
                     ['red die', re.compile(hq_words.reddie, re.I|re.M), '┗', (255,0,0)],
                     ['discard the card', re.compile(hq_words.discard, re.I|re.M), '╱', (0,0,0)],
                     ['Mastery Test', re.compile(hq_words.mastery, re.I|re.M), '╳', (0,0,0)],
                     ['Gold Coin', re.compile(hq_words.coin, re.I|re.M), '╄', (0,0,0)],
                     ]
    if short_signlist == True:
        special_signs = special_signs[:-3]
    for searchword in special_signs:
        in_str = searchword[1].sub(searchword[2], in_str)
    sign_color_dict = {}
    for sign in special_signs:
        sign_color_dict[sign[2]] = sign[3]

    return in_str, sign_color_dict
#signs_small_set = ['♦','♥', '─','━','│','╱','╳','┘','┗']
#inv_signs = {v: k for k, v in special_signs.items()}


#%%
def make_headline(msg, im=None, style="eu"):
    ''' Changes font type fitting to the format defined in "style" (eu or us);
    then makes the headline and centers it. If it is too big, it will be made
    smaller to fit the card.'''
    size = 60
    for i in range(0, 31, 1):
        if style == "us":
            headfont = ImageFont.truetype(FONTFOLDER + "Romic.ttf",
                                          size = size - i - 10,
                                          index = 0)
        else:
            headfont = ImageFont.truetype(FONTFOLDER + "hq_gaze.ttf",
                                          size = size - i,
                                          index = 0)
        if im == None:
            im = Image.new(COLORFORMAT, HEADLINE_SIZE, 'white')

        draw = ImageDraw.Draw(im)
        i_w, i_h = im.size
        t_w, t_h = headfont.getsize(msg)
        if t_w < i_w:
            break

    offset = ((i_w - t_w)//2, (i_h - t_h)//2)
    draw.text(offset,
              msg,
              fill = 'black',
              font=headfont)
    return im

#%%

def find_max_width(in_text, text_w_px, font):
    text_w_px
    text_w = font.getsize(in_text)[0]
    overlength = round(text_w / text_w_px + 1 )
    return len(in_text) // overlength


def wrap_text_on_card(in_text,
                      maxwidth = 38, # text width in letters
                      maxheight = 13 # text height in lines
                      ):
    ''' Gets a text in_text and splits it into lines to fit the defined margins
    maxwidth is the maximum number of letters per line. It will be adjusted from
    outside.
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
                                   replace_whitespace = False))

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

#    if len(messages) > maxheight:
#        messages = 'This text was too long, please edit'
    return messages

def make_textparts(line, sign_colors, textcolor):
    '''disassembles the text line, checks word by word if there is some
    part of the text that shall have a special color as specified in sign_colors.
    Makes a list of dicts that gives text parts and their associated colors.

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
    textparts.append ({'text': '',
                      'color': textcolor})

    if len(line)<=1: # empty line, don't do the rest.
        textparts[-1]['text']=' '
    else:
        # assign colors to words, word-by-word
        allgroups = re.split('(\s)',line) # split in words, keep separators
        words = allgroups[0::2]
        separators = allgroups[1::2]
        if len(separators) < len(words):
            separators.append('') # add one entry at the end of the list
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
                textparts.append ({'text': separators[i],
                                  'color': textcolor})
    return textparts


#%%
def replace_specials(msg, signs):
    ''' unfinished function to implement the special signs of HQ Modern.
    The dream is to have certain symbols replaced, like the ever-repeating
    sentence "Discard this card".
    '''
    # TODO: Finish this function and implement it!
    for sign in signs:
            msg = msg.replace(sign, signs[sign])
    return msg
#%%


def make_text_body(msg="Empty Card",
              textcolor='black',
              textsize = None,
              use_specials = False,
              language = 'en'):
    ''' Makes the text body for a play card.
    msg: The text that shall be on the playcard.
    im: An input image that can be used as size restriction for the text
    textcolor: you can define any color here. default is black.
    use_specials: shall the special signs of hq_modern be used or not.
    language: The text can be in different languages. This is important for
        the regexes that replace repeating sentences with special signs.
    returns: An image of the text fitting with the dimensions of the input
        image.
    '''
    if textsize == None:
        textsize = TEXTFRAME_SIZE

    im = Image.new(COLORFORMAT, textsize, VANILLA)
    draw = ImageDraw.Draw(im)

    sign_colors = {'♦':(0,0,255),
                   '♥':(255,0,0)}

    # check the text size and see if it works with the im restrictions
    # if not, switch to smaller padding and/or smaller font size.
    # maxwidth = 38 for fontsize = 32
    # maxwidth = 34 for fontsize = 38

    fontsizes = [38, 32] + list(range(31, 24, -1)) # fontsizes to be used
    pads = [8, 5, 4, 2] # minimum distance between two lines in pixel

    for i, fontsize in enumerate(fontsizes):


        font = ImageFont.truetype(FONTFOLDER + "HQModern.ttf", fontsize)
        maxwidth = find_max_width(msg, textsize[0], font)
        if language == 'de':
            # because of many CAPITAL letters in german,
            # we need to use less letters per line.
            maxwidth = maxwidth - 2

        for pad in pads:
            msg_lines = wrap_text_on_card(msg, maxwidth = maxwidth)

            im_w, im_h = im.size
            line_h = 0
            for line in msg_lines:
                t_w, t_h = draw.textsize(line, font=font) # get the height
                line_h = max(t_h, line_h)

            # calculate full text height
            # vertical movement per line
            move_h = (line_h + pad)

            # text height plus minimum distance between the lines
            text_h = (move_h * len(msg_lines))
            if text_h < im_h:
                break

        if text_h < im_h:
            break

    # Make vertically centered starting position
    current_h = (im_h - text_h) // 2

    # now, line by line, make texts
    for line in msg_lines:
        textparts = make_textparts(line, sign_colors, textcolor)

        # every part has it's assigned color now.
        # print it along the line, part for part
        # check text size for center positioning
        # Text size should be good now.

        # determine start for horizontally centered text
        t_w, t_h = draw.textsize(line, font=font)
        start_w_pos = (im_w - t_w) // 2

        current_w = start_w_pos
        for textpart in textparts:
            t_w, t_h = draw.textsize(textpart['text'],
                                     font=font)
            draw.text((current_w, current_h),
                      textpart['text'],
                      font=font,
                      fill = textpart['color'])
            current_w += t_w # move position forward to new place

        current_h += move_h

    return im


#%%

def open_image(pic_path, pic_size):
    '''if the image exists, opens the image and make it fitting to pic_size.
    Otherwise, makes an image of pic_size with an error message inside
    '''
    try:
        im = Image.open(pic_path)
    except:
        im = Image.open(PICPATH + "no_picture_here.png")
    return im

def make_picture(pic_path, pic_size = None, bgcolor = None):
    if pic_size == None:
        pic_size = PICFRAME_SIZE
    if bgcolor == None:
        bgcolor = 'white'
    # make a new background image in the right size
    bg_im = Image.new(COLORFORMAT, pic_size, 'black')

    s_w, s_h = bg_im.size
    image_area = (s_w-6, s_h-6)

    im = open_image(pic_path, image_area)

    ia_w, ia_h = image_area
    i_w, i_h = im.size

    # make bigger if the image area is bigger than the image
    if ia_w > i_w or ia_h > i_h:
        ratio = max(ia_w/i_w, ia_h/i_h)
        newsize = (int(i_w*ratio), int(i_h*ratio))
        im = im.resize(newsize, resample = Image.LANCZOS)

    # make smaller if the image area is smaller than the image
    if ia_w < i_w or ia_h < i_h:
        ratio = max(ia_w/i_w, ia_h/i_h)
        newsize = (int(i_w*ratio), int(i_h*ratio))
        im = im.resize(newsize, resample = Image.LANCZOS)

    # if the image had the wrong aspect ratio, exceed areas are cropped
    # so that the middle part is left over. More sophisticated croppings would
    # have to be done in Photoshop.
    i_w, i_h = im.size
    if ia_w < i_w:
        crop_w = (i_w - ia_w)//2
    else:
        crop_w = 0
    if ia_h < i_h:
        crop_h = (i_h - ia_h)//2
    else:
        crop_h = 0
    im = im.crop((crop_w, crop_h, i_w - crop_w, i_h -crop_h))
    i_w, i_h = im.size # probably resized, so we need to ask for the size again.

    # position the image i in the center of the background image bg
    bg_w, bg_h = bg_im.size
    offset = ((bg_w - i_w) // 2, (bg_h - i_h) // 2)
    # and paste it on top of the background
    bg_im.paste(im, offset)
    bg_im
    return bg_im


#%%
def make_base_card(card, style = "eu", cardsize = None, use_specials=True):
    ''' gets the dict that defines one card;
    makes headline, picture and text body;
    pastes everything together; applies vanilla - darkred colors,
    returns everything as image.
    '''
    if cardsize:
        # if a card size was given, treat it as relative size compared to the
        # original. Picture width is the way to determine the "real" size
        #picture_width_px = 500
        #picture_width_percent = 0.8818
        #headline_height_percent = 0.09648

        ratio_change = cardsize[0]/cardsize[1] - BASE_CARD_SIZE[0]/BASE_CARD_SIZE[1]
        textsize = (TEXTFRAME_SIZE[0] + int(2. * TEXTFRAME_SIZE[0] * ratio_change),
                    TEXTFRAME_SIZE[1])

    else:
        textsize = TEXTFRAME_SIZE

    im_head = make_headline(card['title'], style = style)
    im_pic = make_picture(card["pic_path"])
    im_body = make_text_body(card['body'],
                             textsize = textsize,
                             use_specials=use_specials,
                             language = card['language'],
                             textcolor = DARKRED)

    #BASE_CARD_SIZE = (567, 995)
    w = max(BASE_CARD_SIZE[0], textsize[0])
    bg_size = (w, BASE_CARD_SIZE[1])
    bg_im = Image.new(COLORFORMAT, bg_size, 'white')
    bg_w, bg_h = bg_im.size

    # paste headline
    i_w, i_head_h = im_head.size
    offset = ((bg_w - i_w) // 2, 0)
    bg_im.paste(im_head, offset)

    # paste image
    i_w, i_pic_h = im_pic.size
    offset = ((bg_w - i_w) // 2, i_head_h-5 )
    bg_im.paste(im_pic, offset)

    # apply "aged" colors to black and white card
    # multiply with vanilla colors to make white appear vanilla colored
    vanillalayer = Image.new('RGBA', bg_im.size, VANILLA)
    bg_im = ImageChops.multiply(bg_im, vanillalayer)
    #bg_im = ImageChops.darker(bg_im, vanillalayer)

    # choose inverse multiplication change the black areas to darkred
    # and grey areas to mid-red
    darkredlayer = Image.new('RGBA', bg_im.size, DARKRED)
    darkredlayer = ImageChops.invert(darkredlayer)
    bg_im = ImageChops.invert(bg_im)
    bg_im = ImageChops.multiply(bg_im, darkredlayer)
    bg_im = ImageChops.invert(bg_im)

    # Text body is pasted after anything else, to avoid killing the colored
    # symbols that are maybe inside.
    i_w, i_body_h = im_body.size
    offset = ((bg_w - i_w) // 2, (bg_h - i_body_h) )
    bg_im.paste(im_body, offset)
    return bg_im

def make_a_card(card):
    ''' Generates one card. Advantage: By having it separated card by card,
    it should be parallelizable theoretically.
    cardformat can be:
        ["zombicide", "44x67", "poker", "25x35","us", "mini", "skat", "eu", "original"]

    '''
    try:
        cs = cardsize.cardsize()
        size = cs.card_sizing(fmt = card['cardformat'])

        # TODO: Use size info to make ratio,
        # especially make text frame wider or not depending on card size

        im = make_base_card(card,
                            style=card['style'],
                            cardsize = size,
                            use_specials=card['use_specials'])

        im = cs.card_sizing(im, fmt = card['cardformat'], style = card['style'])
        if 'out_print' in card:
            cs.save_png(im, card['out_print'])
        if 'out_phon' in card:
            cs.make_phone_online(im, out_phon = card['out_phon'])
        if 'out_onl' in card:
            cs.make_phone_online(im, out_onl = card['out_onl'])
    except:
        print(card)
        raise


#%%

def make_folder(path):
    try:
        makedirs(path)
    except:
        pass
    return path

def make_folders(card_list):
    folders = set()
    for variant in ['out_phon','out_onl','out_print']:
        for card in card_list:
            if variant in card:
                path = Path(card[variant])
                folders.add(str(path.parent))
    for folder in folders:
        make_folder(folder)

def make_card_list(cards, use_specials = True, card_type = 'all', clean = True, cardformat = "eu"):

    card_list = []
    # make list of cards in simplified format. One list entry = one card
    for card in cards:
        for language in card['language']:
            for style in language['style']:
                if (card_type == 'all'
                or card_type.lower() in card['tags'].lower()):
                    this_card = {}
                    this_card['use_specials'] = use_specials
                    this_card['style'] = style
                    this_card['cardformat'] = cardformat # TODO: Change to actual format
                    this_card['title'] = language['title']
                    this_card['body'] = language['body']
                    this_card['pic_path'] = card['pic_path']
                    this_card['language'] = language['language']
                    if '.' in str(card['No']):
                        nr = str(int(card['No']))
                    else:
                        nr = str(card['No'])
                    this_card['name'] = nr + ' ' + language['title'] + ' ' + card['tags']
                    this_card['out_base'] = OUTPATH_BASE + style + '_' + language['language'] + '\\'
                    this_card['out_phon'] = this_card['out_base'] + OUTPATH_PHONE + card['back'] + '\\' +  this_card['name'] + '.jpg'
                    this_card['out_onl'] = this_card['out_base'] + OUTPATH_ONLINE + card['back'] + '\\' + this_card['name'] + '.jpg'
                    this_card['out_print'] = this_card['out_base'] + OUTPATH_PRINT + card['back'] + '\\' + this_card['name'] + '.png'

                    this_card['card_back'] = card['back']
                    card_list.append(this_card)
    return card_list


#%%
def make_cards_from_list(card_list, mult = False):
    ''' generates cards from the card list. Important about this function:
        The switch between normal processing and multiprocessing is taking
        place here.
    '''
    if not mult:
        [make_a_card(card) for card in card_list]
    else:

        p = multi.Pool()
        p.map(make_a_card, card_list, chunksize = 20)
        p.close
        p.join


def filter_by_folder(folder_list, card_list):
    if not isinstance(folder_list, list):
        folder_list = [folder_list]
    poplist = []
    new_card_list = []
    if not "out_phon" in folder_list:
        poplist.append("out_phon")
    if not "out_onl" in folder_list:
        poplist.append("out_onl")
    if not "out_print" in folder_list:
        poplist.append("out_print")
    for card in card_list:
        for folder in poplist:
            card.pop(folder)
        new_card_list.append(card)
    return new_card_list


def filter_by_language(lan_list, card_list):
    if not isinstance(lan_list, list):
        lan_list = [lan_list]

    new_card_list = []
    for card in card_list:
        if card["language"] in lan_list:
            new_card_list.append(card)
    return new_card_list


def filter_by_back(back_list, card_list):
    if not isinstance(back_list, list):
        back_list = [back_list]

    new_card_list = []
    for card in card_list:
        if card['card_back'] in back_list:
            new_card_list.append(card)
    return new_card_list


def filter_by_style(style_list, card_list):
    if not isinstance(style_list, list):
        style_list = [style_list]

    new_card_list = []
    for card in card_list:
        if card['style'] in style_list:
            new_card_list.append(card)
    return new_card_list


def make_cards(cards, use_specials = True, card_type = 'all', clean = True,
               multiprocessor = True, formatfilter = None, cardformat = "eu"):
    '''
    formatfilter contains a dict of lists with filters to be allowed.
    {"folders":["out_phon", "out_onl", "out_print"]
    "languages":["de", "en", "us"]
    "card_backs":["artifact", "treasure"... ]all you can find in the list.
    "style": ["eu", "us"]}
    '''
    if clean:
        clean_output_folder(OUTPATH_BASE)
    card_list = make_card_list(cards,
                               use_specials = use_specials,
                               card_type = card_type,
                               clean = clean,
                               cardformat = cardformat)
    if formatfilter and "folders" in formatfilter:
        card_list = filter_by_folder(folder_list = formatfilter["folders"],
                                     card_list = card_list)
    if formatfilter and "languages" in formatfilter:
        card_list = filter_by_language(lan_list = formatfilter["languages"],
                                     card_list = card_list)
    if formatfilter and "card_backs" in formatfilter:
        card_list = filter_by_back(back_list = formatfilter["card_backs"],
                                     card_list = card_list)
    if formatfilter and "style" in formatfilter:
        card_list = filter_by_style(style_list = formatfilter["style"],
                                     card_list = card_list)

    make_folders(card_list)


    make_cards_from_list(card_list, mult = multiprocessor)

#%%
def make_preview(folder_path):
    if path.isfile(folder_path + 'preview.jpg'):
        remove(folder_path + 'preview.jpg')
    files = []
    for file in listdir(folder_path):
        if file.endswith('.png') or file.endswith('.jpg'):
            files.append(folder_path + file)

    images = list(map(Image.open, files))

    widths, heights = zip(*(i.size for i in images))
    total_width = widths[0]*3
    max_height = max(heights)
    pic_height = ceil(len(images)/3)*max_height
    new_im = Image.new('RGB', (total_width, pic_height), VANILLA)
    x_offset = 0
    y_offset = 0
    i = 0
    for im in images:
        new_im.paste(im, (x_offset,y_offset))
        x_offset += im.size[0]
        i +=1
        if i == 3 :
            i = 0
            y_offset = y_offset + max_height
            x_offset = 0

    new_im.save(folder_path + 'preview.jpg')

def clean_output_folder(path):
    import os, shutil
    folder = path
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path): shutil.rmtree(file_path, ignore_errors=True)
        except Exception as e:
            print(e)

#%%


if __name__ == '__main__':
    multi.freeze_support()
    hq25_swampspell = "https://docs.google.com/spreadsheets/d/1omrpqC8eupy4G2DD4zW7vaci68kGg6o0L4vBlTZeOOU/export?format=xlsx"
    hq25_treasure = "https://docs.google.com/spreadsheets/d/1-ZABwdSaDR6dZLPAzyCFdsj6XlzRCwQRtW-_TLWG1os/export?format=xlsx"
    hq25_artifacts = "https://docs.google.com/spreadsheets/d/14ygpowS7sQ521ykDj7nA0gileswH-6BO3lkBPjsVI2c/export?format=xlsx"
    hq25_koboldspell = "https://docs.google.com/spreadsheets/d/1oJxs1JpDD171nNeJnRtgKI0ni-n9Sz6I6HmbgmICpsI/export?format=xlsx"

    anderas_allcards = "https://docs.google.com/spreadsheets/d/1qQq0dLraUhs6_WnAGd2meji5QS2sDg1hW_OOCnE3Km8/export?format=xlsx"

    test_list = INPUT + "Test_Table.xlsx"

    #cards = read_cards(hq25_koboldspell)
    cards = read_cards(anderas_allcards)
    '''    formatfilter contains a dict of lists with filters to be allowed.
    {"folders":["out_phon", "out_onl", "out_print"]
    "languages":["de", "en", "us"]
    "card_backs":["artifact", "treasure"... ]all you can find in the list.
    "style": ["eu", "us"]}'''

    '''
    cardformat can be one of these:
        ["zombicide", "44x67", "poker", "25x35","us", "mini", "skat", "eu", "original"] '''
    #make_cards(cards, use_specials = False, card_type = "potion")
    make_cards(cards, use_specials = False, card_type = "dungeonsdark", clean = False,
               multiprocessor = False, formatfilter = {"folders": "out_onl",
                                                      "languages": ["de"],
                                                      "style": "eu"
                                                      },
               cardformat = "original"
               )
#    make_cards(cards, use_specials = False, card_type = "air spell", clean = False,
#               multiprocessor = True, formatfilter = {"folders": "out_onl",
#                                                      "languages": ["de"],
#                                                      "style": "eu"
#                                                      }
#               )

    #make_cards(cards, use_specials = False, card_type = "change", clean = False)
    #make_cards(cards, use_specials = False, card_type = "treasure")
    #make_cards(cards, use_specials = False, card_type = "all")


    #make_preview(OUTPATH_BASE + 'eu_en\\' + OUTPATH_PHONE)
    #make_preview(OUTPATH_BASE + 'us_en\\' + OUTPATH_PRINT)
