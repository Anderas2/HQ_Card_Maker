# -*- coding: utf-8 -*-

from PIL import Image, ImageFilter


def open_image(pic_path, pic_size, **conf):
    '''if the image exists, opens the image and make it fitting to pic_size.
    Otherwise, makes an image of pic_size with an error message inside
    '''
    try:
        im = Image.open(pic_path)
    except Exception as e:
        print(e)
        im = Image.open(conf["notfound_image"])
    return im


def make_picture(pic_path, pic_size=None, bgcolor=None,
                 fmt="normal", **conf):
    if pic_size is None:
        pic_size = conf["picframe_size"]
    if bgcolor is None:
        bgcolor = 'white'

    # make a new background image in the right size
    bg_im = Image.new(conf["colorformat"], pic_size, 'black')
    bg_im_w, bg_im_h = bg_im.size
    image_area = (bg_im_w - 6, bg_im_h - 6)  # usable image area
    bg_im_w, bg_im_h = image_area
    im = open_image(pic_path, image_area)
    im_w, im_h = im.size

    # zoom bigger if the usable background image is bigger than the image
    if bg_im_w > im_w or bg_im_h > im_h:
        ratio = max(bg_im_w / im_w, bg_im_h / im_h)
        newsize = (int(im_w * ratio), int(im_h * ratio))
        im = im.resize(newsize, resample=Image.LANCZOS)

    # zoom smaller if the usable image area is smaller than the image
    if bg_im_w < im_w or bg_im_h < im_h:
        ratio = max(bg_im_w / im_w, bg_im_h / im_h)
        newsize = (int(im_w * ratio), int(im_h * ratio))
        im = im.resize(newsize, resample=Image.LANCZOS)

    # crop in case of wrong aspect ratio
    im = crop_to_frame(bg_im_w, bg_im_h, im)
    if "preview" in fmt.lower():
        im = im.filter(ImageFilter.GaussianBlur(1))

    # image was resized or cropped, so we need to ask for the size again.
    im_w, im_h = im.size
    # position the image in the center of the background image bg
    bg_w, bg_h = bg_im.size
    offset = ((bg_w - im_w) // 2, (bg_h - im_h) // 2)
    # and paste it on top of the background
    bg_im.paste(im, offset)
    bg_im
    return bg_im


def crop_to_frame(bg_im_w, bg_im_h, im):
    ''' if the image had the wrong aspect ratio, it is centered and then
    exceed areas are cropped so that the middle part is left over. More
    sophisticated croppings would have to be done manually.
    bg_im_w: (int), width of available area
    bg_im_h: (int), height of available area
    im (PIL.Image): image to crop

    returns: im (PIL.Image): cropped image
    '''
    im_w, im_h = im.size
    if bg_im_w < im_w:
        crop_w = (im_w - bg_im_w) // 2
    else:
        crop_w = 0
    if bg_im_h < im_h:
        crop_h = (im_h - bg_im_h) // 2
    else:
        crop_h = 0
    im = im.crop((crop_w, crop_h, im_w - crop_w, im_h - crop_h))
    return im
