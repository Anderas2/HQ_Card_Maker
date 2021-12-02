# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 12:20:12 2020

@author: wagen
"""
import sys
base = 'C:\\Users\\wagen\\25 Heroquest\\HQ_Card_Maker\\HQ_Card_Maker'
if base not in sys.path:
    sys.path.append(base)
from res.arrange_symbols import symbol_adder
import logging
import json
logging.basicConfig(level=logging.INFO)
from res.conf import Conf
from pathlib import Path
from time import sleep

conf = Conf()
config = conf.conf  # yeah I know it looks weird

sym = symbol_adder(symbol_path=Path(config["basepath"] / config["symbols"]))

hits = {}
hits = sym.hit_rate_singular_words(hits, "Peachy")
hits = {k: v for k, v in sorted(hits.items(),
                                key=lambda item: item[1],
                                reverse=True)}
print("Testing Peachy: " + json.dumps(hits, sort_keys=False, indent=4))
hits = sym.hit_rate_singular_words(hits, "Zombie")
hits = {k: v for k, v in sorted(hits.items(),
                                key=lambda item: item[1],
                                reverse=True)}
print("adding 'Zombie' to the dict: "
      + json.dumps(hits, sort_keys=False, indent=4))


hits = {}
hits = sym.hit_rate_singular_words(hits, "DND")
hits = {k: v for k, v in sorted(hits.items(),
                                key=lambda item: item[1],
                                reverse=True)}
print("Testing DND: " + json.dumps(hits, sort_keys=False, indent=4))
hits = sym.hit_rate_singular_words(hits, "Zombie")
hits = {k: v for k, v in sorted(hits.items(),
                                key=lambda item: item[1],
                                reverse=True)}
print("adding 'Goblin' to the dict: "
      + json.dumps(hits, sort_keys=False, indent=4))

sym.identify_symbols("Red Zombie")


#sym.identify_symbols("Goblin Spear")
#sym.identify_color("Goblin Spear Peachy")
im, size = sym.make_symbol_body(
    "Peachy Zombie, Yellow Goblin Spearman, Green Goblin Archer, "
    + "Red Zombie, Blue DND Goblin, Pink Goblin, Green Goblin",
    (600, 600))
im.show()
im.close()
