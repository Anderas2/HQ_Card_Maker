# -*- coding: utf-8 -*-
"""
Interprets symbol strings as colors plus symbols; makes a list from them,
arranges them in a neat way for the eye.
"""
import matplotlib.colors as colors
from pathlib import Path
from difflib import get_close_matches, SequenceMatcher
from PIL import Image
from PIL import ImageChops
from collections import defaultdict
import logging
import json
import re


def camel_case_split(identifier):
    matches = re.finditer(
        '.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)',
        identifier)
    list_of_words = [m.group(0) for m in matches]
    list_of_words = [list(word.split(" ")) for word in list_of_words]
    list_of_words = [item for sublist in list_of_words for item in sublist]
    new_list = []
    for number, word in enumerate(list_of_words):
        if len(word) > 1:
            new_list.append(word)
        else:
            new_list[number - 1] = new_list[number - 1] + word
            new_list.append(word)
    new_list = [word for word in new_list if len(word) > 1]
    return " ".join(new_list)


def word_indexer(list_of_str):
    word_locations = defaultdict(list)
    for line_num, line in enumerate(list_of_str):
        for word in line.split(" "):
            word_locations[word.lower()].append(line_num)
    return word_locations


class symbol_adder():
    def __init__(self,
                 symbol_path="",
                 **conf):
        self.log = logging.getLogger("Color and symbol finder")
        replacement_path = Path(conf['basepath']) / conf['symbols']

        if not isinstance(symbol_path, Path):
            self.symbol_path = replacement_path
            self.log.debug("Did not receive a symbol path, defaulting to \n"
                           + str(self.symbol_path))
        else:
            self.symbol_path = Path(symbol_path)

        self.translator = {"ork": "orc"}
        self.equipments = ["archer", "bow", "spear", "spearman"]

        try:
            self.symbol_paths = [symbol.name
                                 for symbol in self.symbol_path.iterdir()
                                 if symbol.name.endswith("png")]
            self.available_symbols = [symbol.split(".")[:-2]
                                      + [symbol.split(".")[-2]]
                                      for symbol in self.symbol_paths]
            self.available_symbols = [" ".join(symlist)
                                         .replace("_EU", "")
                                         .replace("_US", "")
                                         .replace("_", "")
                                      for symlist in self.available_symbols]
            self.available_symbols = [camel_case_split(title)
                                      for title in self.available_symbols]
            self.word_locations = word_indexer(self.available_symbols)

        except Exception as e:
            self.log.error(
                f"The symbol path given does not exist {symbol_path}")
            raise e

    def get_colors(self, in_str):
        in_str = in_str.lower().strip()

        if in_str == "green":
            return (9, 95, 8)
        elif in_str == "red":
            return (141, 25, 25)
        elif in_str == "yellow":
            return (204, 150, 24)
        elif in_str == "purple":
            return (151, 110, 163)
        elif in_str in ["us green", "usgreen", "monster", "monstergreen",
                        "monster green"]:
            return (100, 160, 110,)
        elif in_str in ["hero", "us red", "usred", "hero red", "hero_red",
                        "herored"]:
            return (201, 22, 58,)
        elif in_str in ["us maroon", "maroon", "furniture"]:
            return (153, 67, 100,)
        elif in_str in ["us orange", "usorange", "trap"]:
            return (250, 124, 50,)
        else:
            if colors.is_color_like(in_str):
                color = colors.to_rgba_array(in_str)
            else:

                css_color = get_close_matches(in_str, colors.CSS4_COLORS)
                if len(css_color) > 0:
                    ratio_css = SequenceMatcher(
                        b=css_color[0], a=in_str).ratio()
                else:
                    ratio_css = 0
                xkcd_color = get_close_matches(
                    "xkcd:" + in_str, colors.XKCD_COLORS)
                ratio_xkcd = SequenceMatcher(
                    b=xkcd_color[0], a="xkcd:" + in_str).ratio()
                if ratio_xkcd > ratio_css:
                    choice = xkcd_color[0]
                else:
                    choice = css_color[0]

                color = colors.to_rgba_array(choice)
            color = color * 255
            color = list(color[0])
            color = [int(c) for c in color]
            return tuple(color)

    def add_dicts(self, dict1, dict2):
        return {k: dict1.get(k, 0) + dict2.get(k, 0)
                for k in dict1.keys() | dict2.keys()}

    def identify_colors_and_symbols(self, monster_symbols):
        ''' Takes a string like "red skeleton, light blue goblin, green orc"
        and tries to find a) all those colors and b) all those symbols.

        The interpretation relies heavily on comma separation of the symbols;
        and on the fact that in english grammar, the color comes before the
        symbol; plus if it is a described color like "bluish green"; it still
        ends with a clean color word.

        It stores both in a class dictionary called "symbols" with
            "symbol" - the name of the symbol as found in the list
            "color" the color as entered by the user
            "index" the index of the symbol on the input folder symbol list


        It also makes a set of symbols to determine how many of those symbols
        actually have been unique, so that every graphic has to be loaded only
        once.
        '''

        symbols = []
        symbols_unique = set()
        symbol_list = monster_symbols.split(', ')

        for contents in symbol_list:
            colorword, contents = self.identify_color(contents)
            symbol = self.identify_symbols(contents)

            try:
                symbols.append({"symbol": symbol,
                                "color": colorword,
                                "index": self.available_symbols.index(symbol)})
            except Exception as e:
                self.log.error("There was a problem with this symbol:")
                self.log.error(f"symbol: {symbol}")
                self.log.error(f"color_str: {colorword}")
                self.log.error(f"in_str: {contents}")
                raise e
            symbols_unique.add(self.available_symbols.index(symbol))

        self.symbols_unique = symbols_unique
        self.symbols = symbols

    def identify_color(self, contents):
        """Identifies a color from a Symbol String like "Green Goblin Archer".
        It will default to black, if no sufficiently great match was found. It
        searches the xkcd color list, the heroquest color list and the official
        python colors library for matches.

        Args:
            contents (str): a symbol string like "yellow skeleton",
                            "ork red" or "Mummy"

        Returns:
            str: the best matching word for a color. Defaults to black if
            nothing was found.
        """
        colorword = None
        # xkcd has some girlish colors on the list, fruitnames and the like :-)
        xkcd_clist = [item[5:] for item in list(colors.XKCD_COLORS.keys())]
        xkcd_clist.remove("spearmint")  # could be mixed with "spearman"
        hq_clist = ['us green', 'usgreen', 'monster', 'monstergreen',
                    'monster green', 'hero', 'us red', 'usred', 'hero red',
                    'hero_red', 'herored', 'us maroon', 'maroon', 'furniture',
                    'us orange', 'usorange', 'trap']
        full_clist = hq_clist + xkcd_clist

        # some monster words that don't need to be searched in the colorlist
        monsterlist = ["skeleton", "zombie", "mummy", "orc", "ork", "goblin",
                       "fimir",
                       "warrior", "chaos", "gargoyle", "spear", "arrow", "man",
                       "ogre", "dwarf",
                       "spearman", "archer", "helmsman", "mercenary", "hero"]

        for word in contents.split():
            word = word.lower()
            if word in monsterlist:
                continue

            # store the last color-word the algo can find
            cmatch = get_close_matches(word, full_clist, n=6, cutoff=0.8)

            if len(cmatch) > 0:
                cmatch = cmatch[0]
                ratio = SequenceMatcher(a=word, b=cmatch).ratio()
            else:
                ratio = 0
            # if the colorword matches exactly one of he listed words,
            # or not exactly but the ratio is quite good,
            # or it is a colors-defined word, we won.
            if (colors.is_color_like(word)
                    or word in hq_clist
                    or word in xkcd_clist):
                self.log.debug(
                    f"The word {word} matched exactly "
                    + "with a listed color word.")
                colorword = word
                wordreplace = re.compile(re.escape(word), re.IGNORECASE)
                contents = wordreplace.sub('', contents).strip()
                break
            elif ratio > 0.75:
                colorword = cmatch
                self.log.info(f"Word: {word}")
                self.log.info(f"color match: {cmatch}")
                self.log.info(f"ratio: {ratio: .2f}")
                wordreplace = re.compile(re.escape(word), re.IGNORECASE)
                contents = wordreplace.sub('', contents).strip()
            else:
                self.log.debug(
                    f"couldn't findt the word '{word}' in the color lists,"
                    + " defaulting to black")
                colorword = "black"  # default color
        if colorword is None:
            self.log.info(
                f"with '{contents}'' as input, we could not find a color")
            colorword = "black"
        return colorword, contents

    def identify_symbols(self, contents):
        """Gets a symbol string like "Green Goblin Archer" and tries to find
        out which symbol this probably means.
        It searches each word of the description individually in the list of
        filenames available in
        self.available_symbols; adds their probabilities together (bonus if
        the word has been found exactly
        in the filename); and returns the highest rated symbol.
        Attention, that means a symbol is not exactly found some similar symbol
        is returned.
        If no Orc Archer is existing, it may return an Orc, or an Elf Archer,
        depending which fit is better from language processing point of view.

        contents (list of str): a string representing the customer wish for a
        symbol; like "HeroRed Ann the Nun" or "Green Goblin"
        or "purple Fimir Spearman"
        """
        hits = {}
        for word in contents.split():
            hits = self.hit_rate_singular_words(hits, word)
        line_hits = {}
        for key in hits:
            for line_number in self.word_locations[key]:
                if line_number in line_hits:
                    line_hits[line_number] += hits[key]
                else:
                    line_hits[line_number] = hits[key]
        symbol_ratios = {self.available_symbols[key]: line_hits[key]
                         for key in line_hits}
        symbol_ratios = {k: v for k, v in sorted(symbol_ratios.items(),
                                                 key=lambda item: item[1],
                                                 reverse=True)}
        self.log.debug(
            f"symbol ratios for '{contents}' are: \n"
            + json.dumps(symbol_ratios, sort_keys=False, indent=4))

        # check if we have several winners, if yes, sort them again
        max_symbol = max(symbol_ratios, key=symbol_ratios.get)
        max_val = symbol_ratios[max_symbol]
        winnerlist = [symbol
                      for symbol in symbol_ratios
                      if symbol_ratios[symbol] > (max_val - 0.05)]
        if len(winnerlist) > 1:
            symbol_ratios = self.hit_rate_phrase(contents, winnerlist)
            self.log.info(
                f"symbol ratios for '{contents}' are after correction: \n"
                + json.dumps(symbol_ratios, sort_keys=False, indent=4))
        return max(symbol_ratios, key=symbol_ratios.get)

    def hit_rate_phrase(self, phrase, winnerlist) -> dict:
        phrase = phrase.lower()
        smatch = get_close_matches(
            phrase, winnerlist, n=8, cutoff=0.2)
        if len(smatch) > 0:
            new_ratios = {match: SequenceMatcher(
                a=phrase, b=match).ratio() for match in smatch}
        else:
            new_ratios = {}
        return new_ratios

    def hit_rate_singular_words(self, hits_dict, word) -> dict:
        word = word.lower()
        # game specific preprocessing
        # returns the word itself if it is not found in the dictionary
        word = self.translator.get(word, word)
        # find best matching monster symbols
        smatch = get_close_matches(
            word, self.word_locations.keys(), n=6, cutoff=0.6)
        if len(smatch) > 0:
            new_ratios = {match: SequenceMatcher(
                a=word, b=match).ratio() for match in smatch}
            for symbol in new_ratios:
                self.bonus_ratio(word, new_ratios, symbol)
            hits_dict = self.add_dicts(hits_dict, new_ratios)
        return hits_dict

    def bonus_ratio(self, word, new_ratios, symbol):
        ''' because the soft matching does not always return perfect results,
            there is a bonus if the searched for word appears exactly in
            the results, and an additional bonus if it also has exactly the
            same length.

            word: the word we have found by soft matching
            symbol: the original string of the symbol
            new_ratios: Reference of the ratio dict, to be changed in this
                method.
        '''
        if word.lower() in symbol.lower():
            if len(word) == len(symbol):
                new_ratios[symbol] += 0.5
            else:
                new_ratios[symbol] += 0.3

    def load_symbols_and_update_colors(self, symbols=None):

        # if nothing is given, load them all, store in the class
        if not symbols:
            symbols = self.symbols
            returning = False
        else:  # check if everything needed is there
            try:
                if("color" not in symbols[0]
                        or "symbol" not in symbols[0]
                        or "index" not in symbols[0]):
                    self.log.warning(
                        "missing information in symbols."
                        + " Continue with standard")
                    self.log.warning("expect a list of dicts of the form:")
                    self.log.warning(
                        "[{'symbol': 'IceGremlin', 'color': 'black'},]")
                    self.log.warning("but received:")
                    self.log.warning(symbols)
                    symbols = self.symbols
            except Exception as e:
                self.log.error(symbols)
                raise e
            else:
                # check was fine, return the symbols in the end
                returning = True

        # load raw symbols
        for idx in self.symbols_unique:
            im = Image.open(self.symbol_path / self.symbol_paths[idx])
            for item in symbols:
                if item["index"] == idx:
                    item["image"] = im.convert("RGBA")

        for item in symbols:
            im_alpha = item['image'].getchannel("A")  # save alpha channel
            c_im = Image.new("RGBA",
                             item['image'].size,
                             self.get_colors(item['color']))
            c_im.putalpha(im_alpha)
            item['image'] = ImageChops.lighter(item['image'], c_im)

        if returning:
            return symbols

    def make_symbol_body(self,
                         monster_symbols,
                         textsize):
        ''' searches for symbols, tries to cut off as little as possible from
        the text size, uses this space for a symbol-filled area, gives back a
        reduced text size for the other functions and the finished assembled
        image.
        '''
        # interpret user texts
        self.identify_colors_and_symbols(monster_symbols)
        # load symbols and change their color
        self.load_symbols_and_update_colors()

        max_symbols = 5  # per row
        symbol_rows = {1: [0, 1, 0],
                       2: [0, 2, 0],
                       3: [0, 3, 0],
                       4: [0, 4, 0],
                       5: [3, 2, 0],
                       6: [3, 3, 0],
                       7: [4, 3, 0],
                       8: [4, 4, 0],
                       9: [5, 4, 0],
                       10: [5, 5, 0],
                       11: [3, 5, 3],
                       12: [4, 4, 4],
                       13: [4, 5, 4],
                       14: [5, 4, 5],
                       15: [5, 5, 5],
                       }

        row_composition = symbol_rows[len(self.symbols)]
        number_of_rows = sum(x > 0 for x in row_composition)

        # correct size of symbols
        # half the text space is reserved for text, symbols fill the other half
        im_height = int(textsize[1] / 2)

        # find the max space per symbol, so that max_symbols fit per row,
        # plus 8 pixel bleed
        x_bleed = 4
        size_x = (textsize[0] // max_symbols) - (x_bleed * max_symbols)

        # shrink the symbols so that maximum 3 rows fit;
        # normally shrink so that two rows fit.
        rows_used = max(number_of_rows, 2)
        y_bleed = (12 / rows_used)
        size_y = (im_height - 4) // rows_used - (y_bleed * rows_used)

        size_min = min(size_x, size_y)
        # add some pixel distance between the symbols
        step_x = size_x + x_bleed
        step_y = size_y + y_bleed

        for entry in self.symbols:
            size = entry['image'].size
            symbol_min = min(size)
            factor = size_min / symbol_min
            entry['image'] = entry['image'].resize(
                (int(size[0] * factor), int(size[1] * factor)))

        # combine symbols into one output picture
        out_im = Image.new(
            'RGBA', (textsize[0], im_height), color=(255, 255, 255, 0))
        symbol_pointer = 0

        for row_no in range(0, number_of_rows):
            y = row_no * step_y

            symbolcount = row_composition[row_no]
            space_need = symbolcount * step_x
            start_x = (textsize[0] - space_need) // 2
            for i in range(0, symbolcount):
                sym_size = self.symbols[symbol_pointer]['image'].size
                y_correction = 0
                if sym_size[1] < step_y:
                    y_correction = (step_y - sym_size[1]) / 2

                x = start_x + i * step_x
                out_im.paste(self.symbols[symbol_pointer]['image'],
                             (int(x), int(y + y_correction)),
                             self.symbols[symbol_pointer]['image'])
                symbol_pointer += 1

        # calculate left-over textsize
        textsize = (textsize[0], textsize[1] - im_height)
        return out_im, textsize
