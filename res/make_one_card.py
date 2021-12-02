# -*- coding: utf-8 -*-
from PIL import Image, ImageFont, ImageDraw, ImageChops
from res.arrange_symbols import symbol_adder
from res.make_textframe import make_text_body
from res.make_imageframe import make_picture
from res.make_profile_line import make_profile
import logging


def make_headline(msg, im=None, style="eu", **conf):
    ''' Changes font type fitting to the format defined in "style" (eu or us);
    then makes the headline and centers it. If it is too big, it will be made
    smaller to fit the card.'''
    size = 60
    for i in range(0, 31, 1):
        if style == "us":
            headfont = ImageFont.truetype(
                str(conf["fontfolder"] / "Romic.ttf"),
                size=size - i - 10,
                index=0)
        else:
            headfont = ImageFont.truetype(
                str(conf["fontfolder"] / "hq_gaze.ttf"),
                size=size - i,
                index=0)
        if im is None:
            im = Image.new(conf["colorformat"],
                           conf["headline_size"], 'white')

        draw = ImageDraw.Draw(im)
        i_w, i_h = im.size
        t_w, t_h = headfont.getsize(msg)
        if t_w < i_w:
            break

    offset = ((i_w - t_w) // 2, (i_h - t_h) // 2)
    draw.text(offset,
              msg,
              fill='black',
              font=headfont)
    return im


def make_base_card(card, style="eu", cardsize=None,
                   use_specials=True):
    ''' gets the dict that defines one card;
    makes headline, picture and text body;
    pastes everything together; applies vanilla - darkred colors,
    returns everything as image.
    '''
    # First check - if the card is marked as having no image, use the space
    # for more text
    conf = card['conf']
    logging.debug(conf)
    if card["pic_path"] != "nopic":
        im_pic = make_picture(card["pic_path"], fmt=card["cardformat"], **conf)
        has_image = True
        textframe_size = conf["textframe_size"]
    else:
        has_image = False
        textframe_size = conf["textframe_size"]
        textframe_size[1] += conf["picframe_size"][1]

    if cardsize:
        # if a card size was given, treat it as relative size compared to the
        # original. Picture width is the way to determine the "real" size
        #picture_width_px = 500
        #picture_width_percent = 0.8818
        #headline_height_percent = 0.09648

        ratio_change = (cardsize[0] / cardsize[1]
                        - conf["base_card_size"][0]
                        / conf["base_card_size"][1])

        textsize = (textframe_size[0]
                    + int(2.0 * textframe_size[0] * ratio_change),
                    int(textframe_size[1] * 1.))
    else:
        textsize = textframe_size

    im_head = make_headline(card['title'], style=style, **conf)

    # check if a monster profile or monster symbols are on the card
    if len(card['monster_symbols']) > 0:
        im_body = Image.new("RGBA", textsize, color=conf["vanilla"])
        # A monster statline is indicated by the word "profile:" and then
        # follows name and rule of the monster. All the rest of the statline
        # should normally be in the "monster_symbols" column, but can be there
        # too.
        if ("profile:" in card['monster_symbols']
                or "profile:" in card['body']):
            if "profile" in card['body']:
                profile = card['body'][card['body'].find("profile:"):]
                card['monster_symbols'] = profile + \
                    ", " + card['monster_symbols']
                card['body'] = card['body'][:card['body'].find("profile:")]

            profile_size = (textsize[0], textsize[1] // 2)
            im_lower_body = make_profile(card['monster_symbols'],
                                         im_size=profile_size,
                                         language=card['language'],
                                         **conf)
            new_textsize = (textsize[0], textsize[1] - profile_size[1])
        else:
            syms = symbol_adder(**conf)
            im_lower_body, new_textsize = syms.make_symbol_body(
                card['monster_symbols'],
                textsize)
        im_upper_body = make_text_body(card['body'],
                                       textsize=new_textsize,
                                       # use_specials=use_specials,
                                       language=card['language'],
                                       textcolor=conf["darkred"],
                                       **conf)
        im_body.paste(im_upper_body, (0, 0))
        im_body.paste(im_lower_body, (0, new_textsize[1]),
                      mask=im_lower_body)

    else:
        im_body = make_text_body(card['body'],
                                 textsize=textsize,
                                 # use_specials=use_specials,
                                 language=card['language'],
                                 textcolor=conf["darkred"],
                                 **conf)

    w = max(conf["base_card_size"][0], (textsize[0] + 6))
    bg_size = (w, conf["base_card_size"][1])
    bg_im = Image.new(conf["colorformat"], bg_size, 'white')
    back_width, back_height = bg_im.size

    # paste headline
    i_w, i_head_h = im_head.size
    offset = ((back_width - i_w) // 2, 0)
    bg_im.paste(im_head, offset)

    # paste image if one is available
    if has_image:
        i_w, i_pic_h = im_pic.size
        offset = ((back_width - i_w) // 2, i_head_h - 5)
        bg_im.paste(im_pic, offset)

    # apply "aged" colors to black and white card
    # multiply with vanilla colors to make white appear vanilla colored
    vanillalayer = Image.new('RGBA', bg_im.size, conf["vanilla"])
    bg_im = ImageChops.multiply(bg_im, vanillalayer)
    #bg_im = ImageChops.darker(bg_im, vanillalayer)

    # choose inverse multiplication change the black areas to darkred
    # and grey areas to mid-red
    darkredlayer = Image.new('RGBA', bg_im.size, conf["darkred"])
    darkredlayer = ImageChops.invert(darkredlayer)
    bg_im = ImageChops.invert(bg_im)
    bg_im = ImageChops.multiply(bg_im, darkredlayer)
    bg_im = ImageChops.invert(bg_im)

    # Text body is pasted after anything else, to avoid killing the color
    # of the symbols that are maybe inside.
    i_w, i_body_h = im_body.size
    offset = ((back_width - i_w) // 2, (back_height - i_body_h))
    bg_im.paste(im_body, offset)
    return bg_im
