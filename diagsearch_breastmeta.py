#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      kpchang
#
# Created:     11/09/2015
# Copyright:   (c) kpchang 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import sqlite3
import time
import pathlib
import csv
import re
from reportreading import diagclassifier
from pathsqlite import reportsqlwriter
from reportreading import diagclassifier
from reportreading import reportreader
import reportstatgen
import reportdatelib
import breastanalysis
import breastmacro
import json

NOAFS = 0
AFSNEG = 1
AFSPOS = 2
META_CATEGORY = "category"
META_AXILLARY = "axillary lymph node"
META_DISTANT = "distant metastasis"

ACIDFASTNEGATIVELIST = ["negative for myco", "acid[- ]fast[^.]+no myco[^.]+\.",
    "[Nn]o[^.^;]+micro[^.^;]+acid[- ]fast", "acid[- ]fast[^.^;]+no micro",
    "[Nn]o[^.^;]+micro[^.^;]+AFS", "[Nn]o[^.^;]+myco[^.^;]+acid[- ]fast",
    "no acid[ -]fast[^.^;^,]+positive"]
ACIDFASTPOSITIVELIST = ["acid[- ]fast[^.^;^,]+positive", "presence[^.^;]+mycobacte",
    "acid[- ]fast[^.^;]+presence of[^.^;]+myco", "positive[^.^;]+mycobac"]

def diag_match_all(keywords, crudedata, exclusion = []):
    """
        Take a crudedata from report in database, search for any keywords.
    """
    match = 0
    li = crudedata.split("|")
    for item in li:
        #print(item)
        if reportreader.contain_procedure(item.split(",")):
            #print(item)
            if all(word in item.lower() for word in keywords):
                #print("match")
                if not any(word in item.lower() for word in exclusion):
                    match += 1
    return match

def diag_match_net(crudedata, exclusion = []):
    diagcode = None

def diag_match_re(expression, crudedata):
    """
        Take a crudedata from report in database, search for any keywords.
    """
    match = re.search(expression, crudedata)
    return match

def diag_match_acid(crudedata):
    for pattern in ACIDFASTNEGATIVELIST:
        if diag_match_re(pattern, crudedata):
            return AFSNEG
    for pattern in ACIDFASTPOSITIVELIST:
        if diag_match_re(pattern, crudedata):
            return AFSPOS
    return NOAFS


def diag_match_crude(keywords, crudedata, exclusion = []):
    """
        Take a crudedata from report in database, search for any keywords.
    """
    match = 0
    if all(word in crudedata.lower() for word in keywords):
        if not any(word in item.lower() for word in exclusion):
            match += 1
    return match

def diag_match_any_crude(keywords, crudedata, exclusion = []):
    """
        Take a crudedata from report in database, search for any keywords.
    """
    match = 0
    if any(word in crudedata.lower() for word in keywords):
        if not any(word in item.lower() for word in exclusion):
            match += 1
    return match

def search_month_for_words(year, month, keywords, connection, exc=[]):
    reportlist = reportstatgen.take_monthly_data(connection, year, month)
    result = []
    for item in reportlist:
        if diag_match_all(keywords, item[1], exclusion=exc):
            result.append(item)
    return result

def search_month_for_words_include(year, month, keywords, connection, exc=[]):
    reportlist = reportstatgen.take_monthly_data_crude(connection, year, month)
    result = []
    for item in reportlist:
        if diag_match_all(keywords, item[1], exclusion=exc):
            result.append(item)
    return result

def search_month_for_words_crude_diag(year, month, keywords, connection, exc=[]):
    reportlist = reportstatgen.take_monthly_data(connection, year, month)
    result = []
    for item in reportlist:
        if diag_match_crude(keywords, item[1], exclusion=exc):
            result.append(item)
    return result

def search_month_for_words_re(year, month, expression, connection, exc=[]):
    reportlist = reportstatgen.take_monthly_data_crude(connection, year, month)
    result = []
    for item in reportlist:
        if "病理號" in item[2]:
            descolumn = item[2].split("病理號")[0]
        else:
            descolumn = item[2]
        match = diag_match_re(expression, item[1]+descolumn)
        if match:
            result.append((item[0], match.group(0), item[1], descolumn))
    return result

def search_month_for_words_acid_neg(year, month, connection, exc=[]):
    reportlist = reportstatgen.take_monthly_data_crude(connection, year, month)
    result = []
    for item in reportlist:
        if "病理號" in item[2]:
            descolumn = item[2].split("病理號")[0]
        else:
            descolumn = item[2]
        if diag_match_acid(item[1]+descolumn) == AFSNEG:
            result.append((item[0], item[1], descolumn, item[3]))
    return result

def search_month_for_words_acid_pos(year, month, connection, exc=[]):
    reportlist = reportstatgen.take_monthly_data_crude(connection, year, month)
    result = []
    for item in reportlist:
        if "病理號" in item[2]:
            descolumn = item[2].split("病理號")[0]
        else:
            descolumn = item[2]
        if diag_match_acid(item[1]+descolumn) == AFSPOS:
            result.append((item[0], item[1], descolumn, item[3]))
    return result

def search_month_for_words_cyto(year, month, keywords, connection, exc=[]):
    reportlist = reportstatgen.take_monthly_data_cyto(connection, year, month)
    result = []
    for item in reportlist:
        if diag_match_all(keywords, item[1], exclusion=exc):
            result.append(item)
    return result

def search_month_for_words_crude(year, month, keywords, connection, exc=[]):
    reportlist = reportstatgen.take_monthly_data_crude(connection, year, month)
    result = []
    for item in reportlist:
        if diag_match_crude(keywords, item[1]+item[2], exclusion=exc):
            result.append(item)
    return result

def search_month_for_words_any_crude(year, month, keywords, connection, exc=[]):
    reportlistin = reportstatgen.take_monthly_data_crude(connection, year, month)
    reportlistout = reportstatgen.take_monthly_data_crude_p(connection, year, month)
    reportlistsouth = reportstatgen.take_monthly_data_crude_n(connection, year, month)
    reportlist = reportlistin + reportlistout + reportlistsouth
    result = []
    for item in reportlist:
        if diag_match_any_crude(keywords, item[1]+item[2], exclusion=exc):
            result.append(item)
    return result

def breastclassify_month(year, month, connection, exc=[]):
    reportlistin = reportstatgen.take_monthly_data_crude(connection, year, month)
    reportlistout = reportstatgen.take_monthly_data_crude_p(connection, year, month)
    reportlistsouth = reportstatgen.take_monthly_data_crude_n(connection, year, month)
    reportlist = reportlistin + reportlistout + reportlistsouth
    result = []
    for item in reportlist:
        container = {reportreader.AGE_COLUMN:[], reportreader.DIAG_COLUMN:[],
                     reportreader.DESC_COLUMN:[], reportreader.REF_COLOMN:[],
                     reportreader.PATHOLOGYNO:[]}
        container[reportreader.PATHOLOGYNO] = item[0]
        container[reportreader.DIAG_COLUMN] = item[1].split("|")
        container[reportreader.DESC_COLUMN] = item[2].split("|")
        breastresult = breastanalysis.breast_classify(container)
        if breastresult == None:
            continue

        elif breastresult[0] == breastmacro.BREAST:
            ihcresult = breastanalysis.find_erprher(container)
            output = {}
            output[reportreader.PATHOLOGYNO] = container[reportreader.PATHOLOGYNO]
            output[breastmacro.BREASTCLASS] = breastresult[1]
            output[reportreader.DIAGNOSIS] = breastresult[2]
            output[breastmacro.ER] = ihcresult[breastmacro.ER]
            output[breastmacro.PR] = ihcresult[breastmacro.PR]
            output[breastmacro.HERTWO] = ihcresult[breastmacro.HERTWO]
            output[breastmacro.AR] = ihcresult[breastmacro.AR]
            result.append(output)

        elif breastresult[2] == breastmacro.METAC:
            #ihcresult = breastanalysis.find_erprher(container)
            origin = " ".join(container[reportreader.DESC_COLUMN])
            print(origin)
            match = re.search("[Ii]mmu.*\.", origin)
            ihctext = None
            if match:
                ihctext = match.group(0).split(")")
                print(ihctext)
                ihcresult = breastanalysis.find_erprher_meta(ihctext)
                print(ihcresult)
            output = {}
            output[reportreader.PATHOLOGYNO] = container[reportreader.PATHOLOGYNO]
            output[breastmacro.BREASTCLASS] = breastresult[1]
            output[reportreader.DIAGNOSIS] = breastmacro.METAC
            output[breastmacro.ER] = ihcresult[breastmacro.ER]
            output[breastmacro.PR] = ihcresult[breastmacro.PR]
            output[breastmacro.HERTWO] = ihcresult[breastmacro.HERTWO]
            output[breastmacro.AR] = ihcresult[breastmacro.AR]
            output[reportreader.DIAG_COLUMN] = container[reportreader.DIAG_COLUMN]
            output[reportreader.DESC_COLUMN] = container[reportreader.DESC_COLUMN]
            if "axilla" in ",".join(container[reportreader.DIAG_COLUMN]):
                output[META_CATEGORY] = META_AXILLARY
            else:
                output[META_CATEGORY] = META_DISTANT
            if ihctext:
                output["ihctext"] = ihctext
            else:
                output["ihctext"] = "None"
            #print(output)
            result.append(output)
    return result

def search_year_for_words(year, keywords, connection, ex=[]):
    result = []
    for i in range(12):
        mo = i+1
        result = result + search_month_for_words(year, mo, keywords, connection, exc=ex)
    return result

def search_year_for_words_include(year, keywords, connection, ex=[]):
    result = []
    for i in range(12):
        mo = i+1
        result = result + search_month_for_words_include(year, mo, keywords, connection, exc=ex)
    return result

def search_year_for_words_cyto(year, keywords, connection, ex=[]):
    result = []
    for i in range(12):
        mo = i+1
        result = result + search_month_for_words_cyto(year, mo, keywords, connection, exc=ex)
    return result

def search_year_for_words_crude(year, keywords, connection, ex=[]):
    result = []
    for i in range(12):
        mo = i+1
        result = result + search_month_for_words_crude(year, mo, keywords, connection, exc=ex)
    return result

def search_year_for_words_crude_diag(year, keywords, connection, ex=[]):
    result = []
    for i in range(12):
        mo = i+1
        result = result + search_month_for_words_crude_diag(year, mo, keywords, connection, exc=ex)
    return result

def search_year_for_words_any_crude(year, keywords, connection, ex=[]):
    result = []
    for i in range(12):
        mo = i+1
        result = result + search_month_for_words_any_crude(year, mo, keywords, connection, exc=ex)
    return result

def search_year_for_words_acid_neg(year, connection):
    result = []
    for i in range(12):
        mo = i+1
        result = result + search_month_for_words_acid_neg(year, mo, connection)
    return result

def search_year_for_words_acid_pos(year, connection):
    result = []
    for i in range(12):
        mo = i+1
        result = result + search_month_for_words_acid_pos(year, mo, connection)
    return result


def main():
    foldername = "F:\\2015breast"
    folderpath = pathlib.Path(foldername)
    dbpath = folderpath / "testcase2015.db"
    conn = sqlite3.connect(str(dbpath))
    for k in range(1, 13):
        invfname = foldername + "\\" + str(k) + "inv.json"
        cisfname = foldername + "\\" + str(k) + "cis.json"
        metafname = foldername + "\\" + str(k) + "meta.json"
        li = breastclassify_month(2015, k, conn)
        invasive_raw = []
        cis_raw = []
        meta_raw = []
        for item in li:
            if item[breastmacro.BREASTCLASS] == breastmacro.INVASIVE_CARCINOMA:
                if item[reportreader.DIAGNOSIS] == breastmacro.METAC:
                    meta_raw.append(item)
                else:
                    invasive_raw.append(item)
            elif item[breastmacro.BREASTCLASS] == breastmacro.CIS:
                cis_raw.append(item)
            with open(invfname, encoding="utf-8", mode="w") as f:
                json.dump(invasive_raw, f)
            with open(cisfname, encoding="utf-8", mode="w") as f:
                json.dump(cis_raw, f)
            with open(metafname, encoding="utf-8", mode="w") as f:
                json.dump(meta_raw, f)
    listrawinv = list(folderpath.glob("*inv.json"))
    listrawmeta = list(folderpath.glob("*meta.json"))
    listcsvpath = foldername + "\\invlist.csv"
    listtriple = foldername + "\\triplenegative.csv"
    listmeta = "G:\\Dropbox\\2019paper\\meta2015.csv"
    with open(listcsvpath, mode = "w", encoding = "utf-8", newline="") as listcsv:
        print("writing all breast cancer:")
        spamwriter = csv.writer(listcsv)
        for item in listrawinv:
            with item.open(mode = "r", encoding="utf-8") as f:
                itemdata = json.load(f)
            for data in itemdata:
                spamwriter.writerow([data[reportreader.PATHOLOGYNO], data[reportreader.DIAGNOSIS],
                        "ER:{0}".format(data[breastmacro.ER]), "PR:{0}".format(data[breastmacro.PR]),
                        "Her-2:{}".format(data[breastmacro.HERTWO]), "AR:{0}".format(data[breastmacro.AR])])
    with open(listmeta, mode = "w", encoding = "utf-8", newline="") as listcsv:
        print("writing all meta:")
        spamwriter = csv.writer(listcsv)
        for item in listrawmeta:
            with item.open(mode = "r", encoding="utf-8") as f:
                itemdata = json.load(f)
            for data in itemdata:
                spamwriter.writerow([data[reportreader.PATHOLOGYNO], data[reportreader.DIAGNOSIS],
                        "ER:{0}".format(data[breastmacro.ER]), "PR:{0}".format(data[breastmacro.PR]),
                        "Her-2:{}".format(data[breastmacro.HERTWO]), data[META_CATEGORY],
                        data[reportreader.DIAG_COLUMN], data[reportreader.DESC_COLUMN],
                        data["ihctext"]])
    with open(listtriple, mode = "w", encoding = "utf-8", newline="") as listcsv:
        print("writing all triple negative breast cancer:")
        spamwriter = csv.writer(listcsv)
        for item in listrawinv:
            with item.open(mode = "r", encoding="utf-8") as f:
                itemdata = json.load(f)
            for data in itemdata:
                negativity = 1
                if data[breastmacro.ER] is None:
                    negativity = 0
                elif data[breastmacro.ER][0] == reportreader.POSITIVE:
                    negativity = 0
                if data[breastmacro.PR] is None:
                    negativity = 0
                elif data[breastmacro.PR][0] == reportreader.POSITIVE:
                    negativity = 0
                if data[breastmacro.HERTWO] is None:
                    negativity = 0
                elif data[breastmacro.HERTWO] > 1:
                    negativity = 0
                if negativity == 1:
                    spamwriter.writerow([data[reportreader.PATHOLOGYNO], data[reportreader.DIAGNOSIS],
                        "ER:{0}".format(data[breastmacro.ER]), "PR:{0}".format(data[breastmacro.PR]),
                        "Her-2:{}".format(data[breastmacro.HERTWO]), "AR:{0}".format(data[breastmacro.AR])])

    #print(li)
    """
    folderpath = pathlib.Path("D:\\")
    dbpath = folderpath / "testcase2015.db"
    csvpath = folderpath / "ALK_2015.csv"
    conn = sqlite3.connect(str(dbpath))

    csvpath = folderpath / "2015alk3.csv"
    keywords = ["alk-lung: positive", "alk-lung (positive)", "positive for alk-lung", "alk-lung(diffuse)", "alk-lung (diffuse)", "alk-lung (focal)", "alk-lung(focal)", "alk-lung(+)", "alk-lung (+)"]
    exclusion = []
    li = search_year_for_words_any_crude(2015, keywords, conn, exclusion)
    print(li)

    with csvpath.open("w", encoding="big5", newline="") as csvfile:
        spamwriter = csv.writer(csvfile)
        spamwriter.writerow(["病理號", "診斷及描述", "病歷號"])
        for item in li:
            spamwriter.writerow([item[0], item[1]+item[2], item[3]])

    conn.close()
    """

    """
    #dbpath = folderpath / "testcase2015.db"
    #conn = sqlite3.connect(str(dbpath))
    li_two = search_year_for_words_any_crude(2015, keywords, conn, exclusion)
    print(li_two)
    conn.close()
    """
    """
    dbpath = folderpath / "testcase2014.db"
    conn = sqlite3.connect(str(dbpath))
    li_three = search_year_for_words_any_crude(2014, keywords, conn, exclusion)
    conn.close()
    li = li + li_two + li_three
    newli = []
    for item in li:
        c = dueconn.cursor()
        c.execute('''SELECT report_physician FROM reports_finishdate
                  WHERE pathology_number=?''', (item,))
        doc = c.fetchone()
        if doc:
            newli.append((doc[0].split("(")[0], item))
    with open(str(csvpath), "w", encoding = "big5", newline='') as casecsv:
        spamwriter = csv.writer(casecsv)
        for item in newli:
            spamwriter.writerow(item)
    """

    """
    with csvpath.open("w", encoding="big5", newline="") as csvfile:
        spamwriter = csv.writer(csvfile)
        spamwriter.writerow(["病理號", "病歷號", "報告內容"])
        for item in li:
            spamwriter.writerow([item[0], item[2], item[1]])
    """


if __name__ == '__main__':
    main()
