import os
import pandas as pd
import numpy as np
import re

pd.set_option("display.max_colwidth", None)
root = r"C:\SWG Restoration III\profiles\goopus\Restoration\mail_Banker/"
masterColumns = ["Mail ID", "Author", "Subject", "TimeStamp", "Content"]
salesColumns = masterColumns + ["Vendor", "Item", "Buyer", "Amount","Quality","Weapon","Type","Vendor Type"]
masterdf = pd.DataFrame([], columns=masterColumns)
data = []
salesdata = []

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
masterdf["Sale Flag"] = np.where(
    np.isin(masterdf["Subject"], "Vendor Sale Complete"), True, False
)

for index, row in masterdf[masterdf["Sale Flag"]].iterrows():
    items = re.match(
        r"Vendor: (?P<Vendor>.*?) has sold (?P<Item>.*?) to (?P<Buyer>.*?) for (?P<Amount>.*?) credits\.",
        row["Content"],
    ).groupdict()
    if "MM |" in items["Item"]:
        weaponData = re.match(r"MM \| (?P<Quality>.*?) (?P<Weapon>.*?$)",items["Item"]).groupdict()
        if "SAC" in items["Item"]:
            weaponData["Quality"] = "Enhanced"
        weaponTypes = pd.read_excel(r"C:\Users\Matt\Desktop\Weapons.xlsx")
        funkyArray = np.where(np.isin(weaponTypes["Weapon"].values,weaponData["Weapon"]),weaponTypes["Type"].values,"")
        weaponData["Type"] = "".join(x for x in funkyArray if x != "")
        weaponData["Vendor Type"] = "Weapon"
    else:
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
