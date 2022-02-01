import os
import glob
import sys
import fitz
import PySimpleGUI as sg
from sys import exit
from gtts import gTTS
import pygame
from pygame import mixer
from PIL import Image
import pytesseract
import pyttsx3

def preprocessing():
    k = 1
    for i in range(page_count):
        pix, img = get_page(i)
        output = os.path.join(final_directory, r"image_"+str(k)+"_to_read.png")
        pix.writePNG(output)
        k+=1

    mytext = []
    language = 'en'

    # Here we load the image(s) created in Text_to_speech folder and read the text in image via pytesseract Optical Character Recognition (OCR) software
    # thus reading text in images and giving us a string
    for file in os.listdir(final_directory):
        if ".png" in file:
            print(file)
            data = pytesseract.image_to_string(Image.open(os.path.join(final_directory,file)),lang="eng")
            data = data.replace("|","I") # For some reason the image to text translation would put | instead of the letter I. So we replace | with I
            data = data.split('\n')
            mytext.append(data)

    newtext= ""
    for text in mytext:
        for line in text:
            line = line.strip()
            # If line is small, ignore it
            if len(line.split(" ")) < 10 and len(line.split(" "))>0:
                newtext= newtext + " " + str(line) + "\n"

            elif len(line.split(" "))<2:
                pass
            else:
                if line[-1]!=".":
                    newtext = newtext + " " + str(line)
                else:
                    newtext = newtext + " " + line + "\n"

    return newtext

def get_page(pno, zoom=0):
    """Return a PNG image for a document page number. If zoom is other than 0, one of the 4 page quadrants are zoomed-in instead and the corresponding clip returned.

    """
    dlist = dlist_tab[pno]  # get display list

    if not dlist:  # create if not yet there
        dlist_tab[pno] = doc[pno].getDisplayList()
        dlist = dlist_tab[pno]

    pix = dlist.getPixmap(alpha=False)
    
    return pix, pix.getPNGData()  # return the PNG image

def play_pdf(readtext):
    print("Playing")
    engine = pyttsx3.init()
    engine.say(readtext)
    engine.runAndWait()

def save_pdf(readtext):
    engine.save_to_file(readtext, 'audio.mp3')
    engine.runAndWait()

def main():
    sg.theme('Dark Blue 3')

    global dlist_tab, doc, final_directory, page_count, loc, readtext

    if len(sys.argv) == 1:
        fname = sg.popup_get_file(
            'PDF Browser', 'PDF file to open', file_types=(("PDF Files", "*.pdf"),))
        if fname is None:
            exit(0)
    else:
        fname = sys.argv[1]

    doc = fitz.open(fname)
    page_count = len(doc)
    file_name = fname[fname.rindex("/")+1:-4]

    print(file_name)

    # storage for page display lists
    dlist_tab = [None] * page_count

    title = "AudioBook"

    cur_page = 0
    _, data = get_page(cur_page)  # show page 1 for start
    image_elem = sg.Image(data=data)
    goto = sg.InputText(str(cur_page + 1), size=(5, 1))

    layout = [
        [
            sg.Button('Reset'),
            sg.Button('Prev'),
            sg.Button('Next'),
            sg.Text('Page:'),
            goto,
            sg.Button('Play AudioBook'),
            sg.Button('Stop'),
            sg.Button("Save Audio")
        ],
        [image_elem],
    ]
    my_keys = ("Next", "Next:34", "Prev", "Prior:33", "MouseWheel:Down", "MouseWheel:Up")


    window = sg.Window(title, layout,
                       return_keyboard_events=True, use_default_focus=False)

    current_directory = os.getcwd()
    final_directory = os.path.join(current_directory, r'Audio_Files')

    if not os.path.exists(final_directory):
        os.makedirs(final_directory)

    all_files = os.listdir(final_directory)
    sorted(all_files)

    for file in all_files:
        filepath = os.path.join(final_directory,file)
        print(filepath)
        os.chmod(filepath, 0o777)
        os.remove(filepath)

    loc = final_directory  +"/"+ file_name + ".mp3"

    readtext = preprocessing()

    old_page = 0

    while True:
        event, values = window.read()
        
        force_page = False
        if event == sg.WIN_CLOSED:
            print("Closing")
            break
        if event == "Reset":
            window.close()
            main()
            break

        print("Event: " + event)

        if event in ("Escape:27",):  # this spares me a 'Quit' button!
            break
        if event[0] == chr(13):  # surprise: this is 'Enter'!
            try:
                cur_page = int(values[0]) - 1  # check if valid
                while cur_page < 0:
                    cur_page += page_count
            except:
                cur_page = 0  # this guy's trying to fool me
            goto.update(str(cur_page + 1))

        elif event in ("Next", "Next:34", "MouseWheel:Down"):
            cur_page += 1
        elif event in ("Prev", "Prior:33", "MouseWheel:Up"):
            cur_page -= 1

        if event == "Play AudioBook":
            play_pdf(readtext)

        if event == "Save Audio":
            save_pdf(readtext)
        
        # sanitize page number
        if cur_page >= page_count:  # wrap around
            cur_page = 0
        while cur_page < 0:  # we show conventional page numbers
            cur_page += page_count

        # prevent creating same data again
        if cur_page != old_page:
            force_page = True

        if force_page:
            _, data = get_page(cur_page)
            image_elem.update(data=data)
            old_page = cur_page

        # update page number field
        if event in my_keys or not values[0]:
            goto.update(str(cur_page + 1))

if __name__ == '__main__':
    main()