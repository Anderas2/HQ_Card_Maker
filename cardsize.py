# -*- coding: utf-8 -*-
"""
Created on Sun Oct 28 04:57:49 2018

@author: Andreas
"""

inpath = 'C:\\Users\\Andreas\\Questimator\\input\\cardsize\\'
outpath = 'C:\\Users\\Andreas\\Questimator\\output\\cardsize\\'
normal_card = '526 Reinforcements Undeads Rising.png'


work_card = normal_card
infile = inpath  + work_card
outfile = outpath + work_card[:-3] + 'jpg'

from PIL import Image
from PIL import ImageChops
from PIL import ImageDraw
from os import path as ospath, curdir, makedirs, listdir, remove

DARKRED = (59,0,0)
VANILLA = (245,236,219)

TEMPLATEFOLDER = 'C:\\Users\\Andreas\\Questimator\\Code\\Card_Size\\'

POKERFRAME = TEMPLATEFOLDER + r'EU_Pokerframe.png'
NORMALFRAME = TEMPLATEFOLDER + r'EU_Frame.png'
HEADLINE = TEMPLATEFOLDER + r'headline_space.png'
HEADLINE_SIZE = (561, 96)

VERBOSITY = 0
def verbose(in_str):
    if VERBOSITY > 0:
        print(in_str)

def raw_bw_to_eu_test():
    infile = r'C:\Users\Andreas\Questimator\input\cardsize\to_multiply\526 Reinforcements Undeads Rising.png'
    framefile = r'C:\Users\Andreas\Questimator\input\cardsize\to_multiply\EU_Frame.png'
    framefile = POKERFRAME
    outfile = r'C:\Users\Andreas\Questimator\input\cardsize\to_multiply\505 Chaos Energy EU.png'
    im = Image.open(infile)
    raw_bw_card_to_useable(im, framefile, outfile)


def work_on_eu_folder(in_path=None, out_path=None):
    if in_path == None:
        in_path = 'C:\\Users\\Andreas\\Questimator\\input\\cardsize\\'
    if out_path == None:
        out_path_online = 'C:\\Users\\Andreas\\Questimator\\output\\cardsize\\online\\'
        out_path_phone = 'C:\\Users\\Andreas\\Questimator\\output\\cardsize\\phone\\'
    try:
        makedirs(in_path)
    except:
        pass
    try:
        makedirs(out_path_online)
    except:
        pass
    try:
        makedirs(out_path_phone)
    except:
        pass

    for file in listdir(in_path):
        if file.endswith(".png"):
            out_phon = out_path_phone + file[:-3] + 'jpg'
            out_onl = out_path_online + file[:-3] + 'jpg'
            im = Image.open(in_path + file)
            make_phone_online(im, out_phon, out_onl)

def work_on_raw_eu_folder(in_path=None, out_path=None, card_format="zombicide"):
    if in_path == None:
        in_path = 'C:\\Users\\Andreas\\Questimator\\input\\cardsize\\to_multiply\\'
    if out_path == None:
        out_path_online = 'C:\\Users\\Andreas\\Questimator\\output\\cardsize\\online\\'
        out_path_phone = 'C:\\Users\\Andreas\\Questimator\\output\\cardsize\\phone\\'
        out_path_print = 'C:\\Users\\Andreas\\Questimator\\output\\cardsize\\print\\'
    try:
        makedirs(in_path)
    except:
        pass
    try:
        makedirs(out_path_online)
    except:
        pass
    try:
        makedirs(out_path_phone)
    except:
        pass
    try:
        makedirs(out_path_print)
    except:
        pass

    for file in listdir(in_path):
        if file.endswith(".png"):
            out_phon = out_path_phone + file[:-3] + 'jpg'
            out_onl = out_path_online + file[:-3] + 'jpg'
            im = Image.open(in_path + file)
            im = card_sizing(im, card_format)
            out_print = out_path_print + file[:-3] + 'png'
            save_png(im, out_print)
            make_phone_online(im, out_phon, out_onl)

def make_phone_online(im, out_phon, out_onl):

    mob_im = card_to_mobilephone(im)
    save_jpg(mob_im, out_phon)

    online_im = card_to_forum(im, out_onl)
    save_jpg(online_im, out_onl)


def save_jpg(im, outfile):
    darkred = (59,0,0)
    background = Image.new('RGBA', im.size, darkred)
    if im.mode == "RGB":
        im = im.convert('RGBA')
    new_png = Image.alpha_composite(background, im)
    out_png = Image.new('RGB', im.size, (59,0,0))
    out_png.paste(new_png, mask=new_png.split()[3])
    out_png.save(outfile, fmt="jpeg", quality = 80)

def save_png(im, outfile):
    darkred = (59,0,0)
    background = Image.new('RGBA', im.size, darkred)
    if im.mode == "RGB":
        im = im.convert('RGBA')
    new_png = Image.alpha_composite(background, im)
    out_png = Image.new('RGB', im.size, (59,0,0))
    out_png.paste(new_png, mask=new_png.split()[3])
    out_png.save(outfile)

def card_sizing(im, fmt=None):
    '''return a darkred image having the img in exact center;
    adapted to fit for 783 x 1146 images of Heroquest Cards;
    brings them to a format suitable for the smallest Printerstudio size
    with cards of 44x67 mm.'''

    size = im.size
    frame_f = NORMALFRAME

    if fmt != None:
        fmt = fmt.lower()
        if fmt in ["zombicide", "44x67", "eu"]:
            size = (830, 1196)
            frame_f = NORMALFRAME
        elif fmt == "us":
            size = (725, 1094)
            frame_f = None
        elif fmt == "25x35" or fmt == "poker":
            '2,5 x 3,5 inch format'
            size = (822, 1122) # advertised for by Printerstudio
            size = (852, 1222) # works better with printestudio
            frame_f = POKERFRAME
        elif fmt == "agressive_test":
            size = (460, 400)

    # resize image by stuffing to the borders or crop
    im_sized = Image.new('RGBA', size, VANILLA)
    s_w, s_h = im_sized.size
    im_w, im_h = im.size
    offset = ((s_w - im_w) // 2, (s_h - im_h) // 2)
    im_sized.paste(im, offset) # paste image in the middle of the new card

    # If a frame was chosen, apply frame.
    if frame_f != None:
        frame = Image.open(frame_f) #load frame
        # get sizes to paste the frame in the middle.
        f_w, f_h = frame.size
        im_w, im_h = im_sized.size
        offset = ((im_w - f_w) // 2, (im_h - f_h) // 2)
        # The frame is black on the outside and white on the inside.
        # So I make a new black picture and paste the new frame on top
        layer = Image.new('RGBA', im_sized.size, DARKRED)
        #layer = ImageChops.lighter(layer, frame)
        layer.paste(frame, offset)
        layer = ImageChops.lighter(layer, Image.new('RGBA', im_sized.size, DARKRED))
        # and paste the original in the middle, take only the darker colors
        im_sized = ImageChops.darker(im_sized, layer)

    return im_sized



def raw_bw_card_to_useable(im, framefile=None, us=False):
    ''' needs exact same card sizes of framefile and im.
    if us, no frame will be applied. The rest is same-ish.
    '''
    if us == False:
        if framefile == None:
            framefile = NORMALFRAME
        frame = Image.open(framefile)
        f_w, f_h = frame.size
        im_w, im_h = im.size
        offset = ((im_w - f_w) // 2, (im_h - f_h) // 2)
        layer = Image.new('RGBA', im.size, (255, 255, 255))
        layer.paste(frame, offset)

        im = ImageChops.darker(im, layer)

    darkred = (59,0,0)
    vanilla = (245,236,219)
    # multiplication to change white areas to vanilla color
    vanillalayer = Image.new('RGBA', im.size, vanilla)
    im = ImageChops.darker(im, vanillalayer)

    # choose lighter color to change the dark areas to darkred
    darkredlayer = Image.new('RGBA', im.size, darkred)

    im = ImageChops.lighter(im, darkredlayer)

    return im




def card_to_mobilephone(im):
    '''takes any card and removes printer stripes all around'''
    return trim(im)

def card_to_forum(im, outfile):
    '''takes any card and removes printer stripes all around'''
    return trim_half(im)

def trim(im):
    '''removes a border around an image '''
    bg = Image.new(im.mode, im.size, im.getpixel((0,0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        bbox = tuple([bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2])
        return im.crop(bbox)
    else: return im

def trim_half(im):
    ''' returns half the border around an image '''
    bg = Image.new(im.mode, im.size, im.getpixel((0,0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        bbox = tuple([int(bbox[0]/2),
                      int(bbox[1]/2),
                      int(im.size[0]/2 + bbox[2]/2),
                      int(im.size[1]/2 + bbox[3]/2)
                          ])
        return im.crop(bbox)
    else: return im

