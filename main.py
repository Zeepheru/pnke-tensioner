from numpy import source
import requests
import os
import re
import json
import urllib
import time
import bs4
import pandas as pd
from tqdm import tqdm
import shutil

from PIL import Image


"""
LIkely to just take large chunks of code from pnke-derpi
esepecially download handling, as well as the 

so what I'll be writing for now is likely mostly going to be the scraping code,
hence the filename.
"""

re_format = r'(?<=\.)[a-zA-Z0-9]{2,4}$'
Image.MAX_IMAGE_PIXELS = None # disabling the protecting lol

## misc
def source_code(link): #bs4 prep
    response = requests.get(link) 
    if response.status_code == 200:
        pass
    else:
        return False

    response.raise_for_status()
    # output = response.text
    output = bs4.BeautifulSoup(response.text,'lxml')
    return output

def dumpjson(data):
    return json.dumps(data, indent=4, sort_keys=True)

##
def oryx():
    # just code here for a single site,
    # notionally temp code, to make it cleaner at some point

    rus_url = "https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-equipment.html" # russian losses
    ukr_url = "https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-ukrainian.html"

    def scrape_oryx_UKR(url):
        """
        returns row_list

        """

        # getting the html to look at:
        soup = source_code(url)
        article = soup.article.div
        stuff = article.contents[3] # done by looking through the html, NOT SCALABLE
        
        stuffs = stuff.contents[5]

        re_header = r'.+(?=-|\()'
        current_equip_type = ""
        row_list = []# the recommended way is to turn this into a df
        nat = ""

        for s in stuffs:
            if s.name == "h3":
                # print(s.text) 
                try:
                    current_equip_type = re.search(re_header, s.text).group() # eg tanks, AFV, IFV
                    current_equip_type = re.sub(r' $', "", current_equip_type)
                    
                    if current_equip_type.lower().replace(" ", "") == "russia":
                        nat = "rus"
                    elif current_equip_type.lower().replace(" ", "") == "ukraine":
                        nat = "ukr"
                    # print(current_equip_type)
                except:
                    pass

            elif s.name == "ul":
                # print(s.prettify())

                for li in s:
                    # should be the exact model of type (eg T-64BV)
                    if len(li.contents) == 1:
                        # fuck this shit
                        li = li.span

                    model = re.sub(r'^\W+[0-9]+ ', "", str(li.contents[1])) # yes
                    model = re.sub(r':\W$', "", model)

                    for a in li.contents:
                        if a.name == "a":
                            try:
                                status = re.search(r'(?<=[0-9], ).*?(?=( \S)|\))', a.string).group()
                                # note: '9, 10, 11, 12, 13, 14, 15, 16, 17 and 18, captured' - not accounted for
                            except:
                                status = ""
                            row_list.append([current_equip_type, model, a["href"], nat, status])
        return row_list

    def scrape_oryx_RUS(url):
        """
        returns row_list

        """

        # getting the html to look at:
        soup = source_code(url)
        article = soup.article.div
        stuff = article.contents[-2] # done by looking through the html, NOT SCALABLE
        
        stuffs = stuff.contents

        re_header = r'.+(?=-|\()'
        current_equip_type = ""
        row_list = []# the recommended way is to turn this into a df
        nat = ""

        for s in stuffs:
            if s.name == "h3":
                # print(s.text) 
                try:
                    current_equip_type = re.search(re_header, s.text).group() # eg tanks, AFV, IFV
                    
                    if current_equip_type.lower().replace(" ", "") == "russia":
                        nat = "rus"
                    elif current_equip_type.lower().replace(" ", "") == "ukraine":
                        nat = "ukr"
                    # print(current_equip_type)
                except:
                    pass

            elif s.name == "ul":
                # print(s.prettify())

                for li in s:
                    # should be the exact model of type (eg T-64BV)
                    if len(li.contents) == 1:
                        # fuck this shit
                        li = li.span

                    model = re.sub(r'^\W+[0-9]+ ', "", str(li.contents[1])) # yes
                    model = re.sub(r':\W$', "", model)

                    for a in li.contents:
                        if a.name == "a":
                            try:
                                status = re.search(r'(?<=[0-9], ).*?(?=( \S)|\))', a.string).group()
                                # note: '9, 10, 11, 12, 13, 14, 15, 16, 17 and 18, captured' - not accounted for
                            except:
                                status = ""
                            row_list.append([current_equip_type, model, a["href"], nat, status])
        return row_list

    row_list = []
    row_list += scrape_oryx_UKR(ukr_url)
    row_list += scrape_oryx_RUS(rus_url)

    df = pd.DataFrame(row_list, columns=['type','model','src','nat','status'])
    
    # save to csv
    df.to_csv(os.path.join("data", "oryx_data" + ".csv"), index = False, header=True)

def downloadFile(url, filepath):
    r = requests.get(url, stream=True)
    total_size = int(r.headers.get('content-length', 0))
    block_size = 1024 #1 Kibibyte
    t=tqdm(total=total_size, unit='iB', unit_scale=True)  

    print("Downloading to: {}".format(filepath))

    with open(filepath, 'wb') as f:
        for data in r.iter_content(block_size):
            t.update(len(data))
            f.write(data)
    t.close()

def loadDefCsv():
    return pd.read_csv(os.path.join("data", "oryx_data" + ".csv"))

def downloadImages(df):
    # downloads all images in the given df.
    df["src"].apply(lambda x: downloadFile(x, 
        os.path.join("data", "oryx_imgs", x.rsplit('/',1)[1].strip())
            )
        )

def oryxDealWithIt(df):

    df_rus = df.loc[df['nat'] == "rus"]

    ## number of each type of equipment
    # print(df_rus['type'].value_counts())

    """
    Trucks, Vehicles and Jeeps                          724
    Infantry Fighting Vehicles                          664
    Tanks                                               613
    Armoured Fighting Vehicles                          324
    Engineering Vehicles And Equipment                  132
    Armoured Personnel Carriers                         105
    Infantry Mobility Vehicles                          104
    Self-Propelled Artillery                            103
    Command Posts And Communications Stations            72
    Surface-To-Air Missile Systems                       59
    Unmanned Aerial Vehicles                             55
    Multiple Rocket Launchers                            55
    Towed Artillery                                      40
    Helicopters                                          35
    Aircraft                                             26
    Mine-Resistant Ambush Protected (MRAP) Vehicles      25
    Self-Propelled Anti-Tank Missile Systems             14
    Self-Propelled Anti-Aircraft Guns                    12
    Heavy Mortars                                        10
    Radars                                               10
    Naval Ships                                           9
    Jammers And Deception Systems                         8
    Anti-Aircraft Guns                                    6
    Logistics Trains                                      2
    """

##
def main():
    oryxDealWithIt(loadDefCsv())

    downloadImages(loadDefCsv())
    # oryx()

if __name__ == "__main__":
    main()