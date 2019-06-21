# -*- coding: utf-8 -*-
"""
Created on Wed Nov 28 09:26:19 2018
@author: Andreas
"""
import re

# Special sign library
class HQRegex:
    '''provides some regexes that I just seem to need everywhere.
    '''
    def re_en(self):
        # Some Regexes, as they might be needed in a lot of interpreter methods
        self.flags = r'(?im)'
        # captures reroll with some spelling errors
        self.reroll = r'(r\w*ll?s?\W*)'
        # search for: walrus, wallruss, black walrus, bunny, black bunny,
        # black bunnies, black shield
        self.walrus = r'(((black\W*)?((wal\w*s)|bunn?i?e?y?s?))|(black(\Ws\w*ds?))s?)'
        # captures shield, white shield, but not black shield
        self.shield = r'(white)?(?<!black)(\W?sh\w*lds?)'
        # captures skull, skulls, skullz.. .you name it
        self.skull = r'(skull?[sz]?)'
        # captures mishap in some spelling variants
        self.mishap = r'(mi?sh?a?ps?)'
        # captures variants of "dice" including spelling errors
        self.dice = r'(die|dices?)'
        # captures "one"
        self.one = r'((a|1|one)?\W*)'
        # captures "all"
        self.all = r'((all)\W*)'
        # captures successes
        self.success = r'(succ?ess?(es)?)\W*'
        # captures "by force" or "must"-like words
        self.force = r'(forced?|must|ha[sv]e?)(\s*to)?\W*'

        # captures the mentioning of "master" in the defense values
        self.master = r'master\W*'
        # captures the mentioning of "Guardian" among the defense capabilities
        self.guard = r'guardian\W*'

        self.mp = r'(Mind\s?Points?)|(mp)'
        self.bp = r'(Body\s?Points?)|(bp)'
        self.discard = r'(discard the card)|(Do not return ((the)|(this)) card to the deck.)'
        self.mastery = r'Mastery\s?Tests?'
        self.whitedie = r'((?:white)|(?:combat))\s?' + self.dice
        self.reddie = r'(red)|(movement)\s?'+self.dice
        self.coin = r'Gold\s?Coins?'

        self.numbers = r'\W(zero|no|null|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|[0-9])\W'
        self.numbergroup = r'(\w*)' + self.numbers + r'(\w*\W\w*\W\w*\W)'

        self.number_dict = {'(zero\W|null\W?)':0,
                            '\W(one\W?)':1,
                            '(two\W?)':2,
                            '(three\W?)':3,
                            '(four\W?)':4,
                            '(five\W?)':5,
                            '(six\W?)':6,
                            '(seven\W?)':7,
                            '(eight\W?)':8,
                            '(nine\W?)':9,
                            '(ten\W?)':10,
                            '(eleven\W?)':11,
                            '(twelve\W?)':12,
                            }
        self.int_in_str = r'\W?(\d+)\W?'



    def re_de(self):
        # Some Regexes, as they might be needed in a lot of interpreter methods
        # First, Flags that can be attached to the regexes
        self.flags = r'(?im)'
        # captures reroll with some spelling errors
        self.reroll = r'(wie?derholungs?w.*?\W*)'
        # search for: walrus, wallruss, black walrus, bunny, black bunny,
        # black bunnies, black shield
        self.walrus = r'(((schwar?z.*?\W*)?((wal\w*[sß])|(h[aä]s((chen)|([ei])))))|(schw.*?(\Ws\w*ds?))s?)'
        # captures shield, white shield, but not black shield
        self.shield = r'(wei[sß]e?r?n?)?(\W*?schi.*?de?s?n?)'
        # captures skull, skulls, skullz.. .you name it
        self.skull = r'(Toten)?\W?sch(ae)?ä?del'
        # captures mishap in some spelling variants
        self.mishap = r'(fehlschlag)|(mi((ß)(ss?))erfolg)'
        # captures variants of "dice" including spelling errors
        self.dice = r'(W.*?rfeln?)'
        # captures "one"
        self.one = r'(eine?)|(1)\W.*'
        # captures "all"
        self.all = r'((alle?s?n?)\W*)'
        # captures successes
        self.success = r'((Erfolg)|((ge)?gl.*kt))\W*'
        # captures "by force" or "must"-like words
        self.force = r'muss\W*'

        # captures the mentioning of "master" in the defense values
        self.master = r'(master)|(meister)\W*'
        # captures the mentioning of "Guardian" among the defense capabilities
        self.guard = r'(guardian)|(wächter)\W*'

        self.mp = r'(Intell?igenz?punkte?n?s?)|(int?\.?)|(IP)'
        self.bp = r'(KK)|(K.rperkraft(punkte?)?)|(Trefferp(unkte?)?)|(TP)|(LP)'
        self.discard = r'(lege die(se)? Karte( ab)?:?)'
        self.mastery = r'Magietest'
        self.whitedie = r'((?:wei[sß]e?r?n?)|(?:kampf))\s?' + self.dice
        self.reddie = r'((roter?n?)|(bewegungs?)\s?)'+self.dice
        self.coin = r'Gold\s?(m.nzen)?'

        self.numbers = r'(?:\W(kein|null|ein|zwei|beid|drei|vier|fünf|sechs|sieben|acht|neun|zehn|elf|zwölf|[0-9]{0,2})e?n?m?r?\W)'
        self.numbergroup = r'(\w*)' + self.numbers + r'(\w*\W\w*\W\w*\W)'

        self.number_dict = {'(kein\W?|null\W?)':0,
                            '(\W?eine?n?r?m?\W?)':1,
                            '(zwei\W?)':2,
                            '(drei\W?)':3,
                            '(vier\W?)':4,
                            '(fünf\W?)':5,
                            '(sechs\W?)':6,

                            '(sieben\W?)':7,
                            '(acht\W?)':8,
                            '(neun\W?)':9,
                            '(zehn\W?)':10,
                            '(elf\W?)':11,
                            '(zwölf\W?)':12,
                            }
        self.int_in_str = r'\W?(\d+)\W?'

    def __init__(self, country = 'en'):
        if country == 'en':
            self.re_en()
        elif country == 'de':
            self.re_de()
        else:
            self.re_en()

    def get_combat_dice(self, in_str, max_symbols = 4, dice_symbol = "╚"):
        ''' finds phrases referring to the white combat dice; and replaces them
        by the dice symbol.'''

        if not isinstance(in_str, str):
            return in_str
        in_str = str(in_str)
        dice_re = re.compile(self.numbers + self.whitedie, re.IGNORECASE)

        result = dice_re.search(in_str)
        if result and len(result.groups()) >= 3:
            for check in self.number_dict:
                nums = re.search(check, result.groups()[0])
                if nums:
                    nums = int(self.number_dict[check])
                    break

        if not nums:
            dice_re = re.compile(self.int_in_str + self.whitedie, re.IGNORECASE)
            result = dice_re.search(in_str)
            if result and len(result.groups()) >= 1:
                nums = int(result.groups()[0])

        if not nums:
            return in_str

        if nums > max_symbols:
            symbols = str(nums) + dice_symbol
        else:
            symbols = ""
            for i in range(0, nums):
                symbols += dice_symbol

        # put the findings in the input string for further use
        out_str = in_str[:result.span()[0]] + ' '
        out_str = out_str + symbols
        out_str = out_str + in_str[result.span()[1]:]
        return out_str





