# -*- coding: utf-8 -*-
"""
Created on Sun Oct 28 04:57:49 2018

This is a very old version of the card generator. It basically takes a folder
full of cards and cuts new card formats from the existing ones.
@author: Andreas
"""

from PIL import Image
from PIL import ImageChops
#from PIL import ImageDraw
from os import makedirs, listdir
import logging


class cardsize():
    def __init__(self, preview_divisor=2, **config):
        self.log = logging.basicConfig(level=logging.WARNING)
        self.inpath = config['inputpath']
        self.outpath = config['outpath_base']
        self.normal_card = '526 Reinforcements Undeads Rising.png'
        self.templatefolder = config['basepath'] / config['templatefolder']

        self.work_card = self.normal_card
        self.infile = self.inpath / self.work_card
        self.outfile = self.outpath / (self.work_card[:-3] + 'jpg')

        self.darkred = config['darkred']
        self.vanilla = config['vanilla']

        self.POKERFRAME = self.templatefolder / config['pokerframe']
        self.NORMALFRAME = self.templatefolder / config['normalframe']
        self.MINIFRAME = self.templatefolder / config['miniframe']
        self.SKATFRAME = self.templatefolder / config['skatframe']
        self.EU_USFRAME = self.templatefolder / config['eu_us_frame']
        self.ZOMBICIDEFRAME = self.templatefolder / config['zombicideframe']
        self.PREVIEWFRAME = self.templatefolder / config['previewframe']

        self.HEADLINE = self.templatefolder / config['headline']
        self.HEADLINE_SIZE = config['headline_size']

        self.PREVIEW_DIVISOR = preview_divisor

        # self.log.debug(in_str)

    def check_folders(self,
                      in_path=None,
                      out_path_online=None,
                      out_path_phone=None):
        ''' checks if the given folders exist and if not, generates them.
        '''
        if in_path == None:
            print('Error in module cardsize, function work_on_eu_folder')
            print('no in_path was given')
            return 0
        if out_path_online == None:
            print('Error in module cardsize, function work_on_eu_folder')
            print('no out_path_online was given')
            return 0
        if out_path_phone == None:
            print('Error in module cardsize, function work_on_eu_folder')
            print('no out_path_phone was given')
            return 0
        try:
            makedirs(in_path)
            makedirs(out_path_online)
            makedirs(out_path_phone)
        finally:
            pass

    def work_on_eu_folder(self,
                          in_path=None,
                          out_path_online=None,
                          out_path_phone=None):
        ''' Checks the paths that were given. If they do not exist yet,
        they are made.
        Then it crops the printer versions down to phone and online
            versions of each picture found in the in_path.

        in_path: Folder containing images
        out_path_online: Target folder to save online format cards to
        out_path_phone: Target folder to save phone format cards to
        '''
        self.check_folders(in_path, out_path_online, out_path_phone)

        for file in listdir(in_path):
            if file.endswith(".png"):
                im = Image.open(in_path + file)

                phone = out_path_phone + file[:-3] + 'jpg'
                online = out_path_online + file[:-3] + 'jpg'
                self.make_phone_online(im, phone, online)

    def work_on_raw_eu_folder(self,
                              in_path=None,
                              out_path_online=None,
                              out_path_phone=None,
                              out_path_print=None,
                              card_format="zombicide"):
        ''' Checks the paths that were given. If they do not exist yet,
        they are made.

        First adjust the size of the card pictures to some format defined
            with the NORMALFRAME attribute
        Then it crops the printer versions down to phone and online
            versions of each picture found in the in_path.

        in_path: Folder containing images
        out_path_online: Target folder to save online format cards to
        out_path_phone: Target folder to save phone format cards to
        '''
        self.check_folders(in_path, out_path_online, out_path_phone)
        # additional check of print path
        if out_path_print is None:
            print('Error in module cardsize, function _work_on_raw_eu_folder')
            print('no out_path_print was given')
        try:
            makedirs(out_path_print)
        finally:
            pass

        for file in listdir(in_path):
            if file.endswith(".png"):
                im = Image.open(in_path + file)

                im = self.card_sizing(im, card_format)
                out_print = out_path_print + file[:-3] + 'png'
                self.save_png(im, out_print)

                phone = out_path_phone + file[:-3] + 'jpg'
                online = out_path_online + file[:-3] + 'jpg'
                self.make_phone_online(im, phone, online)

    def make_phone_online(self,
                          im,
                          phone=None,
                          online=None,
                          fmt=None):
        ''' Uses the supersized printer card format and makes
        two card formats: One that is best for mobile phones: No borders.
        One that is good for online presentation: Normal card border, compressed image format.
        Then saves it in jpg to save disk space

        im: Card image to treat in PIL format

        phone: folder to save phone format playcards to

        online: folder to save online format playcards to
        '''
        if phone:
            mob_im = self.card_to_mobilephone(im, fmt)
            self.save_jpg(mob_im, phone)
        if online:
            online_im = self.card_to_forum(im, online, fmt)
            self.save_jpg(online_im, online)

    def save_convert(self, im):
        background = Image.new('RGBA', im.size, self.darkred)
        if im.mode == "RGB":
            im = im.convert('RGBA')
        new_png = Image.alpha_composite(background, im)
        out_png = Image.new('RGB', im.size, self.darkred)
        out_png.paste(new_png, mask=new_png.split()[3])
        return out_png

    def save_jpg(self, im, outfile):
        ''' failsafe function to save a file as jpg.
        PIL has some problems with combining RGB and RGBA pictures, so they
        are converted back and forth before saving.
        '''
        out_png = self.save_convert(im)
        #background = Image.new('RGBA', im.size, self.darkred)
        # if im.mode == "RGB":
        #    im = im.convert('RGBA')
        #new_png = Image.alpha_composite(background, im)
        #out_png = Image.new('RGB', im.size, self.darkred)
        #out_png.paste(new_png, mask=new_png.split()[3])
        out_png.save(outfile, fmt="jpeg", quality=80)

    def save_png(self, im, outfile, fmt):
        out_png = self.save_convert(im)

        #background = Image.new('RGBA', im.size, self.darkred)
        # if im.mode == "RGB":
        #    im = im.convert('RGBA')
        #new_png = Image.alpha_composite(background, im)
        #out_png = Image.new('RGB', im.size, self.darkred)
        #out_png.paste(new_png, mask=new_png.split()[3])
        out_png.save(outfile)

    def card_sizing(self, im=None, fmt=None, style="eu"):
        '''return a darkred image having the img in exact center;
        adapted to fit images of Heroquest Cards;
        brings them to a format suitable for some Printerstudio sizes
        by adding a 70 pixel border all around. 70 pixel is 2x3mm which
        will be cut off by the professional printer'''

        frame_f = self.NORMALFRAME
        # original eu card size in mm
        x = 53.7
        y = 80
        if fmt is not None:
            fmt = fmt.lower()
            if fmt in ["zombicide", "44x67"]:
                x = 44
                y = 67
                frame_f = self.ZOMBICIDEFRAME
            elif fmt == "us":
                # 56mm x 89 mm
                x = 56
                y = 89
                frame_f = self.EU_USFRAME
                #frame_f = None
            elif (fmt == "25x35") or ("poker" in fmt.lower()):
                '2,5 x 3,5 inch format'
                x = 63.5
                y = 89
                frame_f = self.POKERFRAME
            elif fmt == "agressive_test":
                size = (460, 400)
            elif "mini" in fmt.lower():
                x = 44.5
                y = 63.5
                frame_f = self.MINIFRAME
            elif "skat" in fmt.lower():
                x = 59
                y = 91
                frame_f = self.SKATFRAME

            else:
                # none of those special formats found, assume original cards
                x = 53.7
                y = 80
                frame_f = self.NORMALFRAME

        dpi = 300
        security = 140

        # make the size of the frame
        size = (int(1.5 + x / 25.4 * dpi) + 70, int(1.5 + y / 25.4 * dpi) + 70)
        # content has to fit in the frame, so remove frame and remove security
        thumbsize = (size[0] - security, size[1] - security)
        self.size = size

        # check if the original image fits into the frame: The actual content
        # is again 6mm x 2 = 140pixel smaller than the frame.
        if not im:
            # if no image was given, it is just a request for the correct size
            return thumbsize

        if (im.size[0] > size[0] - security
                or im.size[1] > size[1] - security):
            im.thumbnail(thumbsize, Image.ANTIALIAS)
        #BASE_CARD_SIZE = (567, 995)

        # resize image by stuffing to the borders or crop
        im_sized = Image.new('RGBA', size, self.vanilla)
        s_w, s_h = im_sized.size
        im_w, im_h = im.size
        offset = ((s_w - im_w) // 2, (s_h - im_h) // 2)
        im_sized.paste(im, offset)  # paste image in the middle of the new card

        # If a frame was chosen, apply frame.
        if frame_f is not None and style == "eu":
            frame = Image.open(frame_f)  # load frame
            # get sizes to paste the frame in the middle.
            f_w, f_h = frame.size
            im_w, im_h = im_sized.size
            offset = ((im_w - f_w) // 2, (im_h - f_h) // 2)
            # The frame is black on the outside and white on the inside.
            # So I make a new black picture and paste the new frame on top
            layer = Image.new('RGBA', im_sized.size, self.darkred)
            #layer = ImageChops.lighter(layer, frame)
            layer.paste(frame, offset)
            layer = ImageChops.lighter(layer, Image.new(
                'RGBA', im_sized.size, self.darkred))
            # and paste the original in the middle, take only the darker colors
            im_sized = ImageChops.darker(im_sized, layer)

        if "preview" in fmt.lower():
            thumbsize = (im_sized.size[0] // self.PREVIEW_DIVISOR,
                         im_sized.size[1] // self.PREVIEW_DIVISOR)
            im_sized.thumbnail(thumbsize, Image.ANTIALIAS)
        return im_sized

    def raw_bw_card_to_useable(self, im, framefile=None, us=False):
        ''' needs exact same card sizes of framefile and im.
        if us, no frame will be applied. The rest is same-ish.
        '''
        if us == False:
            if framefile is None:
                framefile = self.NORMALFRAME
            frame = Image.open(framefile)
            f_w, f_h = frame.size
            im_w, im_h = im.size
            offset = ((im_w - f_w) // 2, (im_h - f_h) // 2)
            layer = Image.new('RGBA', im.size, (255, 255, 255))
            layer.paste(frame, offset)

            im = ImageChops.darker(im, layer)

        # multiplication to change white areas to vanilla color
        vanillalayer = Image.new('RGBA', im.size, self.vanilla)
        im = ImageChops.darker(im, vanillalayer)

        # choose lighter color to change the dark areas to darkred
        darkredlayer = Image.new('RGBA', im.size, self.darkred)
        im = ImageChops.lighter(im, darkredlayer)

        return im

    def card_to_mobilephone(self, im, fmt=None):
        '''takes any card and removes printer stripes all around'''
        # im.show()
        return self.trim(im, fmt)

    def card_to_forum(self, im, outfile, fmt=None):
        '''takes any card and removes printer stripes all around'''
        return self.trim_half(im, fmt)

    def trim(self, im, fmt=None):
        '''removes a border around an image '''
        # get a picture full of background color
        imloc = im.convert("RGB")
        bg = Image.new(imloc.mode, imloc.size, imloc.getpixel((0, 0)))
        # substract the background color - every pixel with backgorund color
        # should now be reliably zero
        diff = ImageChops.difference(imloc, bg)

        # the add operation enhances contrast by roughly four and moves the
        # zero point to color-brightness 100. This absolutely ensures that
        # the border is tight around the image
        diff = ImageChops.add(diff, diff, 2.0, -100)

        # TODO: Works not with the US format
        bbox = diff.getbbox()  # this fails only if the difference op fails.
        if bbox:
            bbox = tuple([bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2])
            return im.crop(bbox)
        else:
            print("trim function didn't find bounding box")
            return im

    def trim_half(self, im, fmt=None):
        ''' returns half the border around an image.
        The print-security border should be 70 pixel all around,
        that's 3mm of the picture and 3mm which are cut off,
        so in total 6 mm times 300 dpi.'''
        factor = 1
        if fmt and "preview" in fmt.lower():
            factor = self.PREVIEW_DIVISOR
        cut_off = 35 // factor
        bbox = (cut_off, cut_off, im.size[0] - cut_off, im.size[1] - cut_off)
        return im.crop(bbox)
