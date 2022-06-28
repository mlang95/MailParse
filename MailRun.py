import os
import pandas as pd
import numpy as np
import re
'''
This script is used for pulling and parsing mail information from vendor sales to better understand how to manage production / inventory.
This script can only be used correctly once the root path is corrected to the character you want to run it off of AND
you /mailsave in game. Once you mailsave, it should send to a similar path, but you may need to verify that your root path isn't elsewhere
Also, you will likely have to modify your code based on your own keyword usage in your item naming.

For example,
I classify weapons by quality tiers: Clearance, Sliced, Enhanced, Premium, Custom
In addition, I wrote a quick csv to parse weapon types from weapon names: E11 Carbine -> Carbine, Republic Blaster -> Pistol, etc.

'''



root = r"C:\SWG Restoration III\profiles\goopus\Restoration\mail_Banker/" #Goopus = Account Name, Banker = Character name
masterColumns = ["Mail ID", "Author", "Subject", "TimeStamp", "Content"]
salesColumns = masterColumns + ["Vendor", "Item", "Buyer", "Amount","Quality","Weapon","Type","Vendor Type","Range Type"]
masterdf = pd.DataFrame([], columns=masterColumns)
data = []
salesdata = []
#opening each individual piece of mail and grabbing initial raw data
for file in os.listdir(root):
    with open(root + file, "r") as mail:
        mails = mail.readlines()
        mailid = mails[0].replace("\n", "")
        author = mails[1].replace("\n", "")
        subject = mails[2].replace("\n", "")
        timestamp = int(mails[3].replace("\n", "").replace("TIMESTAMP: ", ""))
        content = "".join(i for i in mails[4:])
        data.append([mailid, author, subject, timestamp, content])
masterdf = pd.DataFrame(data, columns=masterColumns)
masterdf["TimeStamp"] = pd.to_datetime(masterdf["TimeStamp"], unit="s")
#Sales only occur when the subject is "Vendor Sale Complete", and since that's the only thing we are currently interested in, we slice by it
masterdf["Sale Flag"] = np.where(
    np.isin(masterdf["Subject"], "Vendor Sale Complete"), True, False
)
#low record count so we for loop through all of our sales and begin parsing the raw data
for index, row in masterdf[masterdf["Sale Flag"]].iterrows():
    #items variable is always in the below format
    items = re.match(
        r"Vendor: (?P<Vendor>.*?) has sold (?P<Item>.*?) to (?P<Buyer>.*?) for (?P<Amount>.*?) credits\.",
        row["Content"],
    ).groupdict()
    #"MM | " is a tag for every item I sell, so we can use it to grab the quality and weapon type
    if "MM |" in items["Item"]:
        weaponTypes = pd.read_excel(r"C:\Users\Matt\Desktop\Weapons.xlsx")
        weaponData = re.match(r"MM \| (?P<Quality>.*?) (?P<Weapon>.*?$)",items["Item"]).groupdict()
        #Some Items have more specific naming conventions, and all of them are Enhanced Quality
        if "SAC " in items["Item"]:
            type = items["Item"].split("SAC ")[-1].replace("Enhanced ","")
            print(type,items["Buyer"])
            funkyArray = np.where(np.isin(weaponTypes["Weapon"].values,type),weaponTypes["Type"].values,"")
            weaponData["Type"] = "".join(x for x in funkyArray if x != "")
            weaponData["Quality"] = "Enhanced"
            
        elif "Output" in items["Item"]:
            type = items["Item"].split("Max Output ")[-1]
            funkyArray = np.where(np.isin(weaponTypes["Weapon"].values,type),weaponTypes["Type"].values,"")
            weaponData["Type"] = "".join(x for x in funkyArray if x != "")
            weaponData["Quality"] = "Enhanced"
            
        else:
            #Couldn't find an elegant solution, so wrote a funky np.where to check if the weapon type exists inside the record and then join all the non-empty info (one record)
            funkyArray = np.where(np.isin(weaponTypes["Weapon"].values,weaponData["Weapon"]),weaponTypes["Type"].values,"")
            weaponData["Type"] = "".join(x for x in funkyArray if x != "")
            
        weaponData["Vendor Type"] = "Weapon"
        try:
            weaponData["Range Type"] = weaponTypes.loc[weaponTypes["Type"]==weaponData["Type"]]["RangeType"].to_list()[0]
        except:
            weaponData["Range Type"] = ""
    else:
        # Vendor Type is an important way to slice between our core sales and our various other data
        weaponData = {"Quality": "","Weapon":"","Type": "","Vendor Type":"Other"}
    salesdata.append(
        [
            row["Mail ID"],
            row["Author"],
            row["Subject"],
            row["TimeStamp"],
            row["Content"],
            *items.values(),
            *weaponData.values()
        ]
    )
salesdf = pd.DataFrame(salesdata, columns=salesColumns)
# salesdf[salesdf["Vendor"]=="MM Weapons"]["Amount"].astype(np.int).sum()
salesdf.set_index("Mail ID").to_csv(r"C:\Users\Matt\Desktop\MM Sales.csv")
