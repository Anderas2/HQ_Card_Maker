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
# Read a CSV with cards and make a list of card dicts
# make a picture frame, 4 pixel wide, around the center image




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
        files = []
        files.append(link)
    for file in files:
        in_pd = read_excel(file)
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
                content = {'language': version,
                           'title': record['title_'+version],
                           'body': record['body_'+version],
                           'formats':['eu']
                           }
                if version == 'en':
                    content['formats'].append('us')
                if not (isnull(content['title'])
                or isnull(content['body'])):
                    language.append(content)
            card['language'] = language
            card['tags'] = str(record['Tags']).lower()
            card['No'] = record['No']
            cards.append(card)
    return cards


# example card for debugging
card = {'language':
            [{'language':'en',
                "title":"Dazzling Gemstone!",
                 "body":  "In a forgotten corner you find a dazzling jewel " +
                    "worth 135 gold coins! Whenever you move, this gem " +
                    "might draw your gaze to its splendor. \n"+
                    "Discount any movement die rolled above your mind point total. " +
                    "You may discard this card if both dice are doubles " +
                    "and not discounted. \n" +
                    "If you keep this card, mark the gold coins "+
                    "on your sheet after the Quest and "+
                    "return it to the deck.",
                "formats":['eu', 'us'],
                },
            {'language':'de',
                "title":"Schillernder Edelstein",
                 "body":"In einer vergessenen Ecke findest Du ein schillerndes " +
                   "Juwel im Wert von 135 Gold! "
                   "Wenn du dich bewegst, zieht das Juwel den Blick auf "+
                   "seine Pracht.\n Entferne jeden Bewegungswürfel der mehr "+
                   "Augen zeigt als du ♦ hast. Du darfst diese " +
                   "Karte abwerfen, wenn du einen Pasch würfelst. \n"+
                   "Wenn du die Karte behältst, schreibe dir das Gold am Ende " +
                   "der Quest auf.",
               "formats":['eu'],
              }
            ],
       "pic_id": "Gemstone",
       "pic_path": PICPATH + "Gemstone.png" ,
       }
cards = []
cards.append(card)

#%%

def use_specialsigns(in_str, short_signlist = True, language = 'en'):
    in_str = card['language'][0]['body']
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
def wrap_text_on_card(in_text,
                      maxwidth = 38, # text width in letters
                      maxheight = 13 # text height in lines
                      ):
    new_msg = re.split('\n', in_text)
#    new_msg = in_text
    lines = []
    for line in new_msg:
        lines.append(textwrap.wrap(line, width=maxwidth, replace_whitespace = False))
#    messages = textwrap.wrap(in_text, width = maxwidth, replace_whitespace=False)
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

#%%
def replace_specials(msg, signs):
    for sign in signs:
            msg = msg.replace(sign, signs[sign])
    return msg
#%%

def make_text_body(msg="Empty Card",
              im=None,
              textcolor='black',
              use_specials = True,
              language = 'en'):

    # maxwidth = 38 for fontsize = 32
    # maxwidth = 34 for fontsize = 38
    maxletters = [33, 38]
    fontsizes = [38, 32]
    pads = [8, 5, 4] # minimum distance between two lines in pixel

    if use_specials == True:
        msg, sign_colors = use_specialsigns(msg, language=language)
    else:
        sign_colors = {'♦':(0,0,255),
                       '♥':(255,0,0)}
    if im == None:
        im = Image.new(COLORFORMAT, TEXTFRAME_SIZE, VANILLA)
    draw = ImageDraw.Draw(im)

    # measure text size and check if it works
    for i, fontsize in enumerate(fontsizes):
        maxwidth =  maxletters[i]
        if language == 'de':
            # because of many CAPITAL letters in german,
            # we need to use less letters per line.
            maxwidth = maxwidth - 2

        for pad in pads:
            msg_lines = wrap_text_on_card(msg, maxwidth = maxwidth)
            font = ImageFont.truetype(FONTFOLDER + "HQModern.ttf", fontsize)
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

    # vertically centered starting position
    current_h = (im_h - text_h) // 2

    for line in msg_lines:
        # check if colored special signs appear in the line.
        # every text part will have a color property.
        textparts = []
        textparts.append ({'text': '',
                          'color': textcolor})

        if len(line)<=1: # empty line, don't do the rest.
            textparts[-1]['text']=' '
        else:
            allgroups = re.split('(\s)',line) # split in words, keep separators
            words = allgroups[0::2]
            separators = allgroups[1::2]
            if len(separators) < len(words):
                separators.append('')
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

        # every part has it's assigned color now.
        # print it along the line, part for part
        # check text size for center positioning
        t_w, t_h = draw.textsize(line, font=font)
        start_w_pos = (im_w - t_w) // 2 # determine start for centered text
        current_w = start_w_pos
        for textpart in textparts:
            t_w, t_h = draw.textsize(textpart['text'],
                                 font=font)
            draw.text((current_w, current_h),
                      textpart['text'],
                      font=font,
                      fill = textpart['color'])
            current_w += t_w

        current_h += move_h
    return im
#%%

def open_image(pic_path, pic_size):
    '''if the image exists, opens the image. Otherwise, makes an image
    of pic_size with an error message inside'''
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
    bg_w, bg_h = bg_im.size
    offset = ((bg_w - i_w) // 2, (bg_h - i_h) // 2)
    bg_im.paste(im, offset)
    bg_im
    return bg_im


#%%
def make_base_card(card, style = "eu", use_specials=True):
    im_head = make_headline(card['title'], style = style)
    im_pic = make_picture(card["pic_path"])
    im_body = make_text_body(card['body'],
                             use_specials=use_specials,
                             language = card['language'],
                             textcolor = DARKRED)

    #BASE_CARD_SIZE = (567, 995)
    bg_im = Image.new(COLORFORMAT, BASE_CARD_SIZE, 'white')

    bg_w, bg_h = bg_im.size

    i_w, i_head_h = im_head.size
    offset = ((bg_w - i_w) // 2, 0)
    bg_im.paste(im_head, offset)

    i_w, i_pic_h = im_pic.size
    offset = ((bg_w - i_w) // 2, i_head_h-5 )
    bg_im.paste(im_pic, offset)

    # apply "aged" colors to black and white card
    # choose darker colors to make white appear vanilla colored
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
#%%

def make_folder(path):
    try:
        makedirs(path)
    except:
        pass
    return path

def make_cards(cards, use_specials = True, card_type = 'all'):
    for card in cards:
        for language in card['language']:
            for cardformat in language['formats']:
                if (card_type == 'all'
                or card_type.lower() in card['tags']):
                    this_card = {}
                    this_card['title'] = language['title']
                    this_card['body'] = language['body']
                    this_card['pic_path'] = card['pic_path']
                    this_card['language'] = language['language']
                    card_name = str(card['No'])[:-2] + ' ' + language['title']

                    out_base = OUTPATH_BASE + cardformat + '_' + language['language'] + '\\'
                    out_phon = make_folder(out_base + OUTPATH_PHONE) +  card_name + '.jpg'
                    out_onl = make_folder(out_base + OUTPATH_ONLINE) + card_name + '.jpg'
                    out_print = make_folder(out_base + OUTPATH_PRINT) + card_name + '.png'

                    im = make_base_card(this_card, style=cardformat, use_specials=use_specials)
                    im = cardsize.card_sizing(im, fmt=cardformat)
                    cardsize.save_png(im, out_print)
                    cardsize.make_phone_online(im, out_phon, out_onl)
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
hq25_swampspell = "https://docs.google.com/spreadsheets/d/1omrpqC8eupy4G2DD4zW7vaci68kGg6o0L4vBlTZeOOU/export?format=xlsx"
hq25_treasure = "https://docs.google.com/spreadsheets/d/1-ZABwdSaDR6dZLPAzyCFdsj6XlzRCwQRtW-_TLWG1os/export?format=xlsx"
hq25_artifacts = "https://docs.google.com/spreadsheets/d/14ygpowS7sQ521ykDj7nA0gileswH-6BO3lkBPjsVI2c/export?format=xlsx"
hq25_koboldspell = "https://docs.google.com/spreadsheets/d/1oJxs1JpDD171nNeJnRtgKI0ni-n9Sz6I6HmbgmICpsI/export?format=xlsx"

anderas_allcards = "https://docs.google.com/spreadsheets/d/1qQq0dLraUhs6_WnAGd2meji5QS2sDg1hW_OOCnE3Km8/export?format=xlsx"

test_list = INPUT + "Test_Table.xlsx"

#cards = read_cards(hq25_koboldspell)
cards = read_cards(anderas_allcards)
clean_output_folder(OUTPATH_BASE)
#make_cards(cards, use_specials = False, card_type = "potion")
make_cards(cards, use_specials = False, card_type = "defense")
#make_cards(cards, use_specials = False, card_type = "treasure")
#make_cards(cards, use_specials = False, card_type = "all")
make_preview(OUTPATH_BASE + 'us_en\\' + OUTPATH_PRINT)
#make_preview(OUTPATH_BASE + 'eu_en\\' + OUTPATH_PHONE)
