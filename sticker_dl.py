'''Line sticker downloader'''

from PIL import Image, ImageSequence
import requests
import sys
import os
import re
import codecs
from apnggif import apnggif
from bs4 import BeautifulSoup
import json

def main():
    pack_ext = ""
    if len(sys.argv) > 1:
        pack_id = int(sys.argv[1])
        if len(sys.argv) > 2:
            pack_ext = sys.argv[2]
    else:
        pack_id = int(input("Enter the sticker pack ID: "))
    pack_meta = get_pack_meta(pack_id).text

    name_string = """"en":"""  # folder name will take pack's English title
    pack_name = get_pack_name(name_string, pack_meta)
    pack_name = decode_escapes(pack_name)
    pack_name = pack_name.strip()  # To remove empty sides spaces # Example Bug:  Sticker ID= 9721  Name= UNIVERSTAR BT21: Cuteness Overloaded! # noqa: E501
    print("\nThis pack contains stickers for", pack_name)

    if pack_ext == "":
        if """"hasAnimation":true""" in pack_meta:
            if sys.version_info[0] < 3:
                # https://stackoverflow.com/questions/31722883/python-nameerror-name-hello-is-not-defined
                # compatibility python v2
                pack_ext = input("\nAnimated stickers available! \n"
                                 "Enter png, apng, or gif, anything else to exit: ")  # noqa: E501
            else:
                pack_ext = input("\nAnimated stickers available! \n"
                                 "Enter png, apng, or gif, anything else to exit: ")  # noqa: E501
                if not (pack_ext == "png" or pack_ext == "apng" or pack_ext == "gif"):
                    print("Invalid input: exiting")
                    sys.exit()

        else:
            if sys.version_info[0] < 3:
                # https://stackoverflow.com/questions/31722883/python-nameerror-name-hello-is-not-defined
                # compatibility python v2
                pack_ext = input("\nOnly static stickers available! \n"
                                 "y to download, anything else to exit: ")
            else:
                pack_ext = input("\nOnly static stickers available! \n"
                                 "y to download. If there is animation n to try experimental gif method , anything else to exit: ")
                if not (pack_ext == "y" or pack_ext == "n"):
                        print("Invalid input: exiting")
                        sys.exit()
                

    id_string = """"id":"""
    list_ids = []

    current_id, start_index = 0, 0  # [4] Why have start_index included

    while start_index != -1:
        start_index, current_id, pack_meta = get_ids(id_string, pack_meta)
        # "Passing by assignment" mutable vs. immutable. Any reassignments done in called function will not reflect on return. But manipulating the parameter will reflect. # noqa: E501
        list_ids.append(current_id)

    list_ids.pop()  # [4] Why pop

    # [3] A less ugly way of checking menu values
    menu = {'apng': (get_apng,),
            'png': (get_png,),
            'y': (get_png,),
            'n': (get_gif_url,),
            'gif': (get_gif,)}  # D'OH! Originally said tuples wouldn't work, which was strange. Thanks to doing MIT problems, I realized I used (var) instead of (var,). Former will not be considered a tuple. # noqa: E501
    if pack_ext in menu:
        for choice in menu[pack_ext]:
            choice(pack_id, list_ids, pack_name)
    else:
        print("Nothing done. Program exiting...")
        sys.exit()

    print("\nDone! Program exiting...")

    sys.exit()


def get_pack_name(name_string, pack_meta):
    start_index = pack_meta.find(name_string)
    end_index = pack_meta.find(',', start_index + 1)
    sticker_name = pack_meta[start_index+len(name_string)+1:end_index-1]  # lower bound needs +1 to exclude the beginning " mark. -1 to make upper bound the , which is excluded from the range # noqa: E501
    return sticker_name


def get_ids(id_string, pack_meta):
    start_index = pack_meta.find(id_string)
    end_index = pack_meta.find(",", start_index + 1)
    sticker_id = pack_meta[start_index+len(id_string):end_index]
    return start_index, sticker_id, pack_meta[end_index:]


def validate_savepath(pack_name):
    decoded_name = decode_escapes(pack_name)
    save_name = "".join(i for i in decoded_name if i not in r'\/:*?"<>|')

    # python version selection
    if sys.version_info[0] < 3:
        # https://github.com/bamos/dcgan-completion.tensorflow/issues/20
        # compatibility python v2
        try:
            os.makedirs(str(save_name))
        except OSError:
            print("Skipping creation of %s because it exists already." % str(save_name))  # noqa: E501
    else:
        # python version >= 3
        os.makedirs(str(save_name), exist_ok=True)  # exist_ok = True doesn't raise exception if directory exists. Files already in directory are not erased # noqa: E501

    return save_name


def get_gif(pack_id, list_ids, pack_name):
    pack_name = validate_savepath(pack_name)
    for x in list_ids:
        temp_apng_path = os.path.join(str(pack_name), str(x) + '.apng')
        save_path = os.path.join(str(pack_name), str(x) + '.gif')
        url = 'https://sdl-stickershop.line.naver.jp/products/0/0/1/{}/iphone/animation/{}@2x.png'.format(pack_id, x)  # noqa: E501
        image = requests.get(url, stream=True)
        with open(temp_apng_path, 'wb') as f:
            for chunk in image.iter_content(chunk_size=10240):
                if chunk:
                    f.write(chunk)
        apnggif(temp_apng_path, save_path)
        gif = Image.open(save_path)
        frames = [frame.copy() for frame in ImageSequence.Iterator(gif)]
        frames[0].save(save_path, save_all=True, disposal=2, append_images=frames[1:], loop=0)
        gif = Image.open(save_path)
        os.remove(temp_apng_path)


def get_gif_url(pack_id, list_ids, pack_name):
    response = requests.get("https://store.line.me/stickershop/product/{}/en".format(pack_id))
    html = response.content.decode()
    list_urls = []
    for i in list_urls:
        print(i)
    parsed_html = BeautifulSoup(html, 'html.parser').find(class_="FnStickerList")
    for i in parsed_html.find_all('li'):
        if not json.loads(i["data-preview"])["popupUrl"] == "":
            list_urls.append(json.loads(i["data-preview"])["popupUrl"])
        elif not json.loads(i["data-preview"])["animationUrl"] == "":
            list_urls.append(json.loads(i["data-preview"])["animationUrl"])
        else:
            print("There is no animations")
            return
    pack_name = validate_savepath(pack_name)
    count = 0
    for x in list_urls:
        temp_apng_path = os.path.join(str(pack_name), str(count) + '.apng')
        save_path = os.path.join(str(pack_name), str(count) + '.gif')
        url = x # noqa: E501
        image = requests.get(url, stream=True)
        with open(temp_apng_path, 'wb') as f:
            for chunk in image.iter_content(chunk_size=10240):
                if chunk:
                    f.write(chunk)
        gif = Image.open(temp_apng_path)
        gif.save(save_path, save_all=True, disposal=2, loop=0)
        gif.close()
        os.remove(temp_apng_path)
        count += 1


def get_apng(pack_id, list_ids, pack_name):
    pack_name = validate_savepath(pack_name)
    for x in list_ids:
        # save_path = os.path.join(str(pack_name), str(x) + '.gif')
        save_path = os.path.join(str(pack_name), str(x) + '.apng')
        # url = 'http://lstk.ddns.net/animg/{}.gif'.format(x)
        url = 'https://sdl-stickershop.line.naver.jp/products/0/0/1/{}/iphone/animation/{}@2x.png'.format(pack_id, x)  # noqa: E501
        image = requests.get(url, stream=True)
        with open(save_path, 'wb') as f:
            for chunk in image.iter_content(chunk_size=10240):
                if chunk:
                    f.write(chunk)


def get_png(pack_id, list_ids, pack_name):
    pack_name = validate_savepath(pack_name)
    for x in list_ids:
        save_path = os.path.join(str(pack_name), str(x) + '.png')
        url = 'http://dl.stickershop.line.naver.jp/stickershop/v1/sticker/{}/iphone/sticker@2x.png'.format(x)  # noqa: E501
        image = requests.get(url, stream=True)
        with open(save_path, 'wb') as f:  # http://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py Understood! with construct is a fancy way of try/catch that cleans up, even with exceptions thrown  # noqa: E501
            for chunk in image.iter_content(chunk_size=10240):  # chunk_size is in bytes # noqa: E501
                if chunk:
                    f.write(chunk)


def get_pack_meta(pack_id):

    pack_url = "http://dl.stickershop.line.naver.jp/products/0/0/1/{}/android/productInfo.meta".format(pack_id)  # noqa: E501
    pack_meta = requests.get(pack_url)

    # http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html Status codes
    # It seems that normal request gives 200. Not sure what it means for program if non200 code is given. Will work with 200 for now.  # noqa: E501

    if pack_meta.status_code == 200:
        return pack_meta
    else:
        print("{} did not return 200 status code, possibly invalid sticker ID. Program exiting...".format(pack_id))  # noqa: E501
        sys.exit()


unicode_sanitizer = re.compile(r'''  # compile pattern into object, use with match()
    ( \\U........      # 8-digit hex escapes, backslash U followed by 8 non-newline characters  # noqa: E501
    | \\u....          # 4-digit hex escapes, bksl u followed by 4 non-newline characters  # noqa: E501
    | \\x..            # 2-digit hex escapes, bksl x followed by 2 non-newline characters  # noqa: E501
    | \\[0-7]{1,3}     # Octal escapes, bksl followed by 1 to 3 numbers within range of 0-7  # noqa: E501
    | \\N\{[^}]+\}     # Unicode characters by name, uses name index
    | \\[\\'"abfnrtv]  # Single-character escapes, e.g. tab, backspace, quotes
    )''', re.VERBOSE)  # re.UNICODE not necessary in Py3, matches Unicode by default. re.VERBOSE allows separated sections  # noqa: E501


def decode_escapes(orig):
    def decode_match(match):
        return codecs.decode(match.group(0), 'unicode-escape')
    return unicode_sanitizer.sub(decode_match, orig)  # sub returns string with replaced patterns  # noqa: E501


if __name__ == '__main__':
    main()


'''
[1] http://stackoverflow.com/questions/11435331/python-requests-and-unicode
Solve Unicode with r.content instead of r.text
[2] w+ creates file if it doesn't exist, truncates if it exists. b is for binary, Windows is picky. Never hurts to add b for platform friendliness
[3] http://stackoverflow.com/questions/3260057/how-to-check-variable-against-2-possible-values-python
leads to http://stackoverflow.com/questions/13186542/functions-in-python-dictionary
For multiple functions per key: http://stackoverflow.com/questions/9205081/python-is-there-a-way-to-store-a-function-in-a-list-or-dictionary-so-that-when
How clever.
http://stackoverflow.com/a/9139961 If I didn't have a check for key in dict, this would've been another way.
[4] Originally had a conditional in the while state to check if the start_index was -1 to make sure it doesn't get added.
But a single pop at the end is much better than the if check in every loop iteration.
[5] http://stackoverflow.com/questions/4020539/process-escape-sequences-in-a-string-in-python
Regular expression saves the day.
'''  # noqa: E501

'''
putting "# nopep8" (or "# noqa") on the last line of a multiline string disables all physical checks for lines in the string
https://github.com/PyCQA/pycodestyle/pull/243
'''
