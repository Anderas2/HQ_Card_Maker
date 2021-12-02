# -*- coding: utf-8 -*-
"""
Created on Tue Oct 30 11:32:35 2018

@author: Andreas Wagener
"""

from PIL import Image

import res.cardsize as cardsize
#from os import path as ospath, curdir, makedirs, listdir, remove
from os import makedirs, listdir, path, remove
from pandas import read_excel, isnull, read_csv
import re
from math import ceil
import sys
sys.path.append('C:\\Users\\wagen\\25 Heroquest\\HQ_Card_Maker\\HQ_Card_Maker')
import multiprocessing as multi
from pathlib import Path
from collections import Counter
from res.make_one_card import make_base_card
from res.conf import Conf

# Todo List:
# TODO: use pathlib for paths

# TODO: Make special sign search more efficient
# TODO: Hand, Head, Body, Feet as signs?


def read_cards(link=None, **conf):
    ''' reads cards with picture path and as many titles and bodies as you
    like. If there is title_en and body_en, there will be a US and a EU version
    for it, otherwise only the eu version.
    '''
    # search in input folder for a csv file
    # if found, open it and generate a list of card dicts
    if link is None:
        files = []
        for file in listdir(conf['inputpath']):
            if file.endswith(".xlsx"):
                files.append(conf['inputpath'] + file)
    else:
        if r"edit?usp=sharing" in link:
            link = link.replace(r"edit?usp=sharing", "export?format=xlsx")
        files = []
        files.append(link)

    for file in files:
        # print(file)
        if file.endswith("xlsx"):
            in_pd = read_excel(file, engine='openpyxl')
        elif file.endswith("csv"):
            in_pd = read_csv(file)
        in_pd = in_pd[isnull(in_pd["title_en"]) == False]
        in_pd['Monster Symbols'] = in_pd['Monster Symbols'].fillna("")
        cards_raw = in_pd.to_dict(orient='records')
        language_versions = []
        for key in cards_raw[0].keys():
            if 'title_' in key:
                language_versions.append(key[-2:])

        # now go through the records, and append to each language everything
        # that can be found in the record. Append nothing if the language cell
        # is empty.
        cards = []
        for record in cards_raw:
            card = {}
            pic_name = record["pic_path"]
            if isnull(pic_name):
                pic_name = ""
            if path.isfile(pic_name):
                card["pic_path"] = pic_name

            elif path.isfile(conf['picpath'] / pic_name):
                card["pic_path"] = conf['picpath'] / pic_name

            elif path == "nopic":
                card["pic_path"] = "nopic"

            else:
                card["pic_path"] = conf['picpath'] / pic_name

            language = []
            for version in language_versions:
                # version contains "de", "en", "fr", "it" and so on
                content = {'language': version,
                           'title': record['title_' + version],
                           'body': record['body_' + version],
                           'formats': ['eu'],
                           'style': ['eu']
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
            card['monster_symbols'] = record['Monster Symbols']
            # splits card backs by comma, filters empty strings away
            try:
                back = record['card_back'].replace(" ", "")
                cardbacks = list(filter(None, back.split(",")))
                for cardback in cardbacks:
                    card['back'] = cardback
                    cards.append(card)
            except Exception as e:
                print(record)
                print()
                print(cardbacks)
                raise e
    return cards


def make_a_card(card):
    ''' Generates one card. Advantage: By having it separated card by card,
    it should be parallelizable theoretically.
    cardformat can be:
        ["zombicide", "44x67",
         "poker", "25x35",
         "us",
         "mini",
         "skat",
         "eu", "original"]

    '''
    try:
        conf = card['conf']
        cs = cardsize.cardsize(**conf)
        size = cs.card_sizing(fmt=card['cardformat'])

        # TODO: Use size info to make ratio,
        # especially make text frame wider or not depending on card size

        im = make_base_card(card,
                            style=card['style'],
                            cardsize=size,
                            use_specials=card['use_specials'],
                            )

        im = cs.card_sizing(im, fmt=card['cardformat'], style=card['style'])
        if 'print' in card:
            cs.save_png(im, card['print'], card['cardformat'])
        if 'phone' in card:
            cs.make_phone_online(
                im, phone=card['phone'], fmt=card['cardformat'])
        if 'online' in card:
            cs.make_phone_online(
                im, online=card['online'], fmt=card['cardformat'])
    except Exception as e:
        # print(card)
        raise e


def analyze_folders(card_list):
    # analyzes the folder structure in the card list and if it finds that there
    # are folders with only one single sub folder and without other content,
    # remove it.
    pass


def make_folder(path):
    try:
        makedirs(path)
    finally:
        return path


def make_folders(card_list):
    '''
    Parameters
    ----------
    card_list : a list of to-be-produced cards
    Makes a list of folders asked for by the cardlist.
    Controls if there are useless subfolders, if yes, removes them in the
    card list. Useless are folders with no sibling folders - why burying the
    results so deep then if there is no alternate?

    checks if all the asked-for folders in the cardlist are available
    and if not, creates the output folders.

    Returns
    -------
    Nothing.

    '''

    # collects all folders
    folders = set()
    for variant in ['phone', 'online', 'print']:
        for card in card_list:
            if variant in card:
                path = Path(card[variant])
                folders.add(str(path.parent))

    # checks if there are folders on the lowest level without siblings
    fol_parents = [str(Path(folder).parent) for folder in folders]
    cnt_fol_parents = Counter(fol_parents)
    folderstruct = {}
    for folder in folders:
        parentfolder = cnt_fol_parents[str(Path(folder).parent)]
        folderstruct[folder] = {"parent": Path(folder).parent,
                                "siblings": parentfolder}

    # removes sibling-less subfolders
    for variant in ['phone', 'online', 'print']:
        for card in card_list:
            if variant in card:
                full = Path(card[variant])
                cardname = full.name
                parent_str = str(full.parent)
                if folderstruct[parent_str]["siblings"] == 1:
                    card[variant] = full.parent.parent / cardname

    # collects all folders again
    folders = set()
    for variant in ['phone', 'online', 'print']:
        for card in card_list:
            if variant in card:
                path = Path(card[variant])
                folders.add(str(path.parent))

    # makes missing folders
    for folder in folders:
        make_folder(folder)


def construct_outpath(folder_structure=[],
                      path_parts={}):
    '''
    Parameters
    ----------
    folder_structure : TYPE, optional
        DESCRIPTION. The default is [].
        path_parts = {"style":style,
                    "card_back":this_card['card_back'],
                    "language":language,
                    "cardformat":size,
                    "cutformat":"online",
                    "cardname":this_card['name'],
                    "basepath":OUTPATH_BASE,
                                        }
    Returns
    -------
    return_path : string
        The path where the image shall be stored.
    '''
    return_path = Path(path_parts["basepath"])  # fails if it is missing

    for part in folder_structure:
        try:
            return_path = return_path / path_parts.get(part, "notfound")
        except Exception as e:
            print(return_path)
            print(part)
            print(path_parts.get(part, "notfound"))
            raise e

    cardname = path_parts.get("cardname", "noname")
    if path_parts.get("cutformat", "print") == "print":
        cardname = cardname + '.png'
    else:
        cardname = cardname + '.jpg'

    return_path = return_path / cardname

    return str(return_path)


def make_card_list(cards,
                   use_specials=True,
                   card_type='all',
                   clean=True,
                   cardformat=["original"],
                   folder_structure=["style", "card_back", "language",
                                     "cardformat", "cutformat"],
                   **conf):
    '''

    Parameters
    ----------
    cards : list of dicts with the entire input card list

    use_specials : bool, optional
        A bool defining if special signs from the font HQModern shall be used
        or not. The default is True.
    card_type : string, optional
        This is a filter string, to restrict the card generation to
        some of the cards. The "card back", "number" and "keywords" columns
        are taken for the search. The default is 'all', which gives back all
        cards.
    clean : bool, optional
        DESCRIPTION. The default is True.
    cardformat : List, optional
        cardformat can be one or a list of many of these:
         "zombicide", "44x67" for 44x67 mm cards offered by printerstudio
         "poker" "25x35", for 2.5x3.5 inch cards,
         "us" for the original us card size
         "mini" for the mini card size offered by printerstudio
         "skat" for the skat card size offered by printerstudio
         "eu", "original" is the european original card size
         "preview" is like the eu format, with added blur to prevent copying
    folder_structure: A list of directory ranks
        orders the structure of the output folder. Must contain the strings
            "style", "card_back", "language", "cardformat", "cutformat".
            If there are other strings, they are ignored; if there are strings
            missing, they are added in default order at the end.


    Returns
    -------
    card_list : List of Dictionaries, one dict per card

    Makes list of cards in simplified format. One list entry = one card
    This list then gets filtered by the filter options given.
    Advantage is, after the list has been made, one could work in parallel on
    the entries.
    '''
    # input control of cardformat variable
    if not isinstance(cardformat, list):
        if len(cardformat > 0):
            cardformat = [cardformat]
        else:
            cardformat = ["original"]

    # input control of folder_structure variable
    folder_levels = ["style", "card_back",
                     "language", "cardformat", "cutformat"]
    removelist = []
    for word in folder_structure:
        if word not in folder_levels:
            removelist.append(word)
    for word in removelist:
        folder_structure.remove(word)
    for folder_level in folder_levels:
        if folder_level not in folder_structure:
            folder_structure.append(folder_level)

    card_list = []

    for card in cards:
        for texts in card['language']:  # Any language in the input data
            for style in texts['style']:  # EU or US
                for size in cardformat:  # Any requested language
                    # A card can be in several decks
                    for back in card['back'].split(","):
                        this_card = make_list_entry(use_specials, card_type,
                                                    folder_structure, card,
                                                    texts, style, size, back,
                                                    **conf)
                        card_list.append(this_card)
    return card_list


def make_list_entry(use_specials, card_type, folder_structure,
                    card, texts, style, size, back, **conf):
    if (card_type == 'all'
            or any(card_type.lower() in item for item in card['tags'].lower())
            or card_type.lower() in card['tags'].lower()
            or any(card_type.lower() in item for item in back.lower())
            or card_type in str(card['No'])):
        this_card = {}
        this_card['use_specials'] = use_specials
        this_card['style'] = style
        this_card['cardformat'] = size
        this_card['title'] = texts['title']
        this_card['body'] = texts['body']
        this_card['pic_path'] = card['pic_path']
        this_card['language'] = texts['language']
        this_card['card_back'] = back
        this_card['monster_symbols'] = card['monster_symbols']
        this_card['conf'] = conf

        if '.' in str(card['No']):
            nr = str(int(card['No']))
        else:
            nr = str(card['No'])

        this_card['name'] = (nr + ' ' + texts['title'] + ' ' + card['tags']) \
            .replace("ä", "ae") \
            .replace("ö", "oe") \
            .replace("ü", "ue") \
            .replace("Ä", "Ae") \
            .replace("Ö", "Oe") \
            .replace("Ü", "Ue") \
            .replace("ß", "ss")
        this_card['name'] = re.sub(
            r'[^a-zA-Z0-9\s]', '', this_card['name'])

        path_parts = {"style": style,
                      "card_back": this_card['card_back'],
                      "language": texts['language'],
                      "cardformat": size,
                      "cutformat": "online",
                      "cardname": this_card['name'],
                      "basepath": conf['outpath_base'],
                      }

        # prepare "online" format only for original card sizes
        if size in ["eu", "original", "us", "preview"]:
            this_card['online'] = construct_outpath(folder_structure,
                                                    path_parts=path_parts)

        path_parts["cutformat"] = "print"
        this_card['print'] = construct_outpath(folder_structure,
                                               path_parts=path_parts)

        path_parts["cutformat"] = "phone"
        this_card['phone'] = construct_outpath(folder_structure,
                                               path_parts=path_parts)
        return this_card


def make_cards_from_list(card_list, mult=False):
    ''' generates cards from the card list. Important about this function:
        The switch between normal processing and multiprocessing is taking
        place here.
    '''
    if not mult:
        [make_a_card(card) for card in card_list]
    else:

        p = multi.Pool()
        p.map(make_a_card, card_list, chunksize=20)
        p.close
        p.join


def filter_by_folder(folder_list, card_list):
    if not isinstance(folder_list, list):
        folder_list = [folder_list]
    poplist = []
    new_card_list = []
    if "phone" not in folder_list:
        poplist.append("phone")
    if "online" not in folder_list:
        poplist.append("online")
    if "print" not in folder_list:
        poplist.append("print")
    for card in card_list:
        for folder in poplist:
            if folder in card:
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
    '''
    parameters:
    back_list: A list of card backs or a comma separated string of cardbacks;
    like "airspell, chaosspell" or "ewp, rules"
    '''
    if not isinstance(back_list, list):
        if back_list is None or back_list == "":
            return card_list
        back_list = back_list.split(", ")
        if not isinstance(back_list, list):
            back_list = [back_list]
    back_list = [back
                 for back in back_list
                 if len(back) >= 0]

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


def make_cards(cards, use_specials=True, card_type='all', clean=True,
               multiprocessor=True, fmtfilter=None,
               cardformat=["preview"], **config):
    '''
    fmtfilter contains a dict of lists with filters to be allowed.
    {"cutformat":["phone", "online", "print"]: phone without border,
     online with normal card sized border,
     print with bleed area for professional printers

    "languages":["de", "en", "us"]

    "card_backs":["artifact", "treasure"... ]all you can find in the list.

    "style": ["eu", "us"]}

    "cardformat": Any of the formats defined in the input/card_sizes folder
    '''
    if clean:
        clean_output_folder(config['outpath_base'])
    if "eu" in cardformat:
        cardformat.remove("eu")
        cardformat.append("original")
    card_list = make_card_list(cards,
                               use_specials=use_specials,
                               card_type=card_type,
                               clean=clean,
                               folder_structure=fmtfilter["folder_structure"],
                               cardformat=cardformat,
                               **config)
    analyze_folders(card_list)
    if fmtfilter and "cutformat" in fmtfilter:
        card_list = filter_by_folder(folder_list=fmtfilter["cutformat"],
                                     card_list=card_list)
        if len(card_list) == 0:
            print("cutformat filtered the entire list")
    if fmtfilter and "languages" in fmtfilter:
        card_list = filter_by_language(lan_list=fmtfilter["languages"],
                                       card_list=card_list)
        if len(card_list) == 0:
            print("language filtered the entire list")
    if fmtfilter and "card_backs" in fmtfilter:
        card_list = filter_by_back(back_list=fmtfilter["card_backs"],
                                   card_list=card_list)
        if len(card_list) == 0:
            print("card_backs filtered the entire list")
    if fmtfilter and "style" in fmtfilter:
        card_list = filter_by_style(style_list=fmtfilter["style"],
                                    card_list=card_list)
        if len(card_list) == 0:
            print("style filtered the entire list")

    make_folders(card_list)

    print(f"after filtering, {len(card_list)} cards remain")
    make_cards_from_list(card_list, mult=multiprocessor)


def make_preview(folder_path, **config):
    if path.isfile(folder_path + 'preview.jpg'):
        remove(folder_path + 'preview.jpg')
    files = []
    for file in listdir(folder_path):
        if file.endswith('.png') or file.endswith('.jpg'):
            files.append(folder_path + file)

    images = list(map(Image.open, files))

    widths, heights = zip(*(i.size for i in images))
    total_width = widths[0] * 3
    max_height = max(heights)
    pic_height = ceil(len(images) / 3) * max_height
    new_im = Image.new('RGB', (total_width, pic_height), config['vanilla'])
    x_offset = 0
    y_offset = 0
    i = 0
    for im in images:
        new_im.paste(im, (x_offset, y_offset))
        x_offset += im.size[0]
        i += 1
        if i == 3:
            i = 0
            y_offset = y_offset + max_height
            x_offset = 0

    new_im.save(folder_path + 'preview.jpg')


def clean_output_folder(path):
    import os
    import shutil
    folder = path
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=True)
        except Exception as e:
            print(e)


if __name__ == '__main__':
    multi.freeze_support()
    conf = Conf()
    config = conf.conf  # yeah I know it looks weird
    anderas_allcards_csv = config['inputpath'] / \
        config['anderas_local_allcards']
    #test_list = INPUT + "Test_Table.xlsx"

    #cards = read_cards(hq25_koboldspell)
    print("downloading card list")
    #cards = read_cards(anderas_allcards)
    cards = read_cards(config['anderas_allcards'], **config)
    print(f"found {len(cards)} cards")
    print("start making cards")
    '''    formatfilter contains a dict of lists with filters to be allowed.
    {"cutformat":["phone", "online", "print"] #determines the boder thickness
    and, to a degree, the resolution
    "languages":["de", "en", "us"]
    "card_backs":['airspell', 'artifact', 'chaosspell', 'controlspell',
                  'darknessspell', 'detectionspell', 'earthspell', 'elfspell',
                  'equipment', 'facebook', 'firespell', 'potion',
                  'protectionspell', 'ewp', 'room'
                  'skill', 'spellscroll', 'temple', 'treasure', 'waterspell']
    "style": ["eu", "us"]


    "folder_structure" = ["style", "card_back", "language", "cardformat"]  }'''

    '''
    cardformat can be one of these:
        ["zombicide", "44x67",
        "poker", "25x35","us", "mini", "skat", "eu", "original", "preview"]

    card_type is a filter. either "all" for all cards, or type in anything
    you can find in the columns "tags", "card_back" or the card number.
        '''
    make_cards(cards, use_specials=False,
               # card_type="reinforcements",
               clean=False,
               multiprocessor=False,
               fmtfilter={"cutformat": ["online"],
                          "languages": ["de"],
                          "card_backs": ["ekp"],
                          "style": ["eu"],  # ,"us"
                          # , "style", "cutformat", "cardformat", ]
                          "folder_structure": ["language", "card_back",
                                               "cardformat"]
                          },
               cardformat=["original"],
               **config
               )

    #make_preview(OUTPATH_BASE + 'eu_en\\' + OUTPATH_PHONE)
    #make_preview(OUTPATH_BASE + 'us_en\\' + OUTPATH_PRINT)
