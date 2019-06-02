# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        breastmaingui
# Purpose:     GUI version for breastmain
#
# Author:      user
#
# Created:     11/05/2016
# Copyright:   (c) user 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import tkinter
from tkinter import ttk
from tkinter import filedialog
from tkinter import scrolledtext
import sys
import json
import csv
import pathlib
import breastmacro
import breastanalysis
import reportreader
import readlist
import time
from threading import Thread
from queue import LifoQueue

def take_monthlist_data_inv(breastlist):
    """
        take json dumped rawdata of breast, and count various data
    """
    #print("  Total invasive case: {0}".format(len(breastlist)))
    er_positive = 0
    pr_positive = 0
    ar_positive = 0
    hertwo_zero = 0
    hertwo_one = 0
    hertwo_two = 0
    hertwo_three = 0
    for item in breastlist:
        erresult = item[breastmacro.ER]
        prresult = item[breastmacro.PR]
        arresult = item[breastmacro.AR]
        hertworesult = item[breastmacro.HERTWO]
        if erresult:
            if erresult[0] == reportreader.POSITIVE:
                er_positive += 1
        if prresult:
            if prresult[0] == reportreader.POSITIVE:
                pr_positive += 1
        if arresult:
            if arresult[0] == reportreader.POSITIVE:
                ar_positive += 1
        if hertworesult != None:
            if hertworesult == 0:
                hertwo_zero += 1
            elif hertworesult == 1:
                hertwo_one += 1
            elif hertworesult == 2:
                hertwo_two += 1
            elif hertworesult == 3:
                hertwo_three += 1
    return (len(breastlist), er_positive, pr_positive, hertwo_zero, hertwo_one, hertwo_two, hertwo_three)

class MainApp(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.queue = LifoQueue()
        self.grid(column = 0, row = 0)
        self.dirbutton = ttk.Button(self, text='開啟資料夾', command=self.askdirectory)
        self.dirbutton.grid(column = 0, row = 0, sticky = (tkinter.W, tkinter.E))
        ttk.Label(self, text="路徑:").grid(column = 1, row = 0, sticky = (tkinter.W, tkinter.E))
        self.dirinput = ttk.Entry(self, width=60)
        self.dirinput.grid(column = 2, row = 0, sticky = (tkinter.W,tkinter.E))
        self.runbutton = ttk.Button(self, text="執行", command = self.analysisrun)
        self.runbutton.grid(column = 0, row = 1, sticky = (tkinter.W, tkinter.E))
        self.actionlabel = ttk.Label(self)
        self.actionlabel.grid(column = 1, row = 1, sticky=(tkinter.W, tkinter.E))
        self.filelabel = ttk.Label(self)
        self.filelabel.grid(column = 2, row = 1, sticky=(tkinter.W, tkinter.E))
        self.outputarea = scrolledtext.ScrolledText(self, height = 15, width = 80)
        self.outputarea.grid(column = 0, row = 2, columnspan = 3)
        self.maindic = {}
        self.filedic = {}

    def analysisrun(self):
        maindir = self.dirinput.get()
        resultdirpath = pathlib.Path(maindir + "\\result")
        if not resultdirpath.is_dir():
            resultdirpath.mkdir()
        self.setactionlabel("讀取檔案中....")
        beforefileread = time.time()
        self.update_idletasks()
        self.fill_dic_with_refresh(maindir)
        afterfileread = time.time()
        #write crude data
        self.setactionlabel("尋找breast cancer:")
        self.update()
        for k in self.maindic.keys():
            self.update()
            invfname = maindir + "\\result" + "\\" + k + "inv.json"
            cisfname = maindir+ "\\result" + "\\" + k + "cis.json"
            invasive_raw = []
            cis_raw = []
            for item in self.maindic[k]:
                if not item[0].isdigit():
                    continue
                else:
                    self.update()
                    self.setfilelabel(item)
                    self.outputarea.see(tkinter.END)
                    currentreport = reportreader.read_report_text(self.filedic[item])
                    currentclass = breastanalysis.breast_classify(currentreport)
                    ihcresult = breastanalysis.find_erprher(currentreport)
                    if not currentclass:
                        continue
                    if currentclass[0] == breastmacro.BREAST and currentclass[1] == breastmacro.INVASIVE_CARCINOMA:
                        invdic = {}
                        if ihcresult[breastmacro.ER]:
                            invdic[breastmacro.ER] = list(ihcresult[breastmacro.ER])
                        else:
                            invdic[breastmacro.ER] = None
                        if ihcresult[breastmacro.PR]:
                            invdic[breastmacro.PR] = list(ihcresult[breastmacro.PR])
                        else:
                            invdic[breastmacro.PR] = None
                        if ihcresult[breastmacro.AR]:
                            invdic[breastmacro.AR] = list(ihcresult[breastmacro.AR])
                        else:
                            invdic[breastmacro.AR] = None
                        invdic[breastmacro.HERTWO] = ihcresult[breastmacro.HERTWO]
                        invdic[reportreader.ORGANNAME] = breastmacro.BREAST
                        invdic[breastmacro.BREASTCLASS] = breastmacro.INVASIVE_CARCINOMA
                        invdic[reportreader.DIAGNOSIS] = currentclass[2]
                        invdic[reportreader.PATHOLOGYNO] = item
                        invasive_raw.append(invdic)
                        outputstr = "找到乳癌: {0}, cell type: {5}, ER: {1}, PR: {2}, AR: {3}, Her-2: {4}\n".format(item,
                                    invdic[breastmacro.ER], invdic[breastmacro.PR], invdic[breastmacro.AR], invdic[breastmacro.HERTWO],
                                    currentclass[2])
                        self.tooutput(outputstr)
                        self.update()
                    if currentclass[0] == breastmacro.BREAST and currentclass[1] == breastmacro.CIS:
                        cisdic = {}
                        if ihcresult[breastmacro.ER]:
                            cisdic[breastmacro.ER] = list(ihcresult[breastmacro.ER])
                        else:
                            cisdic[breastmacro.ER] = None
                        if ihcresult[breastmacro.PR]:
                            cisdic[breastmacro.PR] = list(ihcresult[breastmacro.PR])
                        else:
                            cisdic[breastmacro.PR] = None
                        cisdic[reportreader.ORGANNAME] = breastmacro.BREAST
                        cisdic[breastmacro.BREASTCLASS] = breastmacro.CIS
                        cisdic[reportreader.DIAGNOSIS] = currentclass[2]
                        cisdic[reportreader.PATHOLOGYNO] = item
                        cis_raw.append(cisdic)
                        self.update()
            with open(invfname, encoding="utf-8", mode="w") as f:
                json.dump(invasive_raw, f)
            with open(cisfname, encoding="utf-8", mode="w") as f:
                json.dump(cis_raw, f)
        self.update()
        afteranalysis = time.time()
        self.setactionlabel("統計結果中")
        self.update_idletasks()
        listrawinv = list(resultdirpath.glob("*inv.json"))
        csvpath = maindir + "\\result\\result.csv"
        with open(csvpath, mode = "w", encoding = "utf-8", newline="") as csvfile:
            spamwriter = csv.writer(csvfile)
            spamwriter.writerow(["月份", "total invasive", "ER positive",
                "PR positive", "AR positive", "HER2 score 0", "HER2 score 1+",
                "HER2 score 2+", "HER2 score 3+"])
            for item in listrawinv:
                itemcsv = maindir + "\\result\\" + item.name[:5] + "invlist.csv"
                currentmonth = item.name[:5]
                with item.open(mode = "r", encoding="utf-8") as f:
                    itemdata = json.load(f)
        #print(item)
                with open(itemcsv, mode = "w", encoding = "utf-8", newline="") as itemcsvfile:
                    secondspamwriter = csv.writer(itemcsvfile)
                    for data in itemdata:
                        secondspamwriter.writerow([data[reportreader.PATHOLOGYNO], data[reportreader.DIAGNOSIS],
                        "ER:{0}".format(data[breastmacro.ER]), "PR:{0}".format(data[breastmacro.PR]), "AR:{0}".format(data[breastmacro.AR]),
                        "Her-2:{}".format(data[breastmacro.HERTWO])])
                ihcdata = take_monthlist_data_inv(itemdata)
                spamwriter.writerow([currentmonth] + list(ihcdata))
                resultrow = ["total invasive", "ER positive",
                    "PR positive", "AR positive", "HER2 score 0", "HER2 score 1+",
                    "HER2 score 2+", "HER2 score 3+"]
                outputstr = "Month: {0}".format(currentmonth)
                for (k,v) in enumerate(resultrow):
                    try:
                        outputstr = outputstr + " {0}:{1}\n".format(v, ihcdata[k])
                    except IndexError:
                        continue
                self.tooutput(outputstr)
                self.update_idletasks()
                self.outputarea.see(tkinter.END)
        outputstr = "讀檔案總共花:{0}秒，分析總共花: {1}秒".format(afterfileread-beforefileread, afteranalysis-afterfileread)
        self.tooutput(outputstr)
        self.update_idletasks()
        self.outputarea.see(tkinter.END)


    def askdirectory(self):
        self.dirinput.delete(0, "end")
        self.dirinput.insert(0, filedialog.askdirectory())

    def setfilelabel(self, txt):
        self.filelabel.config(text = txt)

    def setactionlabel(self, txt):
        self.actionlabel.config(text = txt)

    def tooutput(self, txt):
        self.outputarea.insert(tkinter.INSERT, txt)

    def refresh(self):
        self.update()
        print("refresh")
        if not self.queue.empty():
            txt = self.queue.qsize()
            print(txt)
            self.setfilelabel(txt)
            self.update()
        self.after(500, self.refresh)

    def fill_dic_with_refresh(self, maindir):
        t = Thread(target = self.fill_dic, args=[maindir])
        t.start()
        while True:
            txt = self.queue.get()
            self.setfilelabel(txt)
            self.update()
            self.update_idletasks()
            if not t.is_alive():
                break

    def fill_dic(self, maindir):
        self.maindic, self.filedic = readlist.make_dic_from_folder(maindir, self.queue)


def main():
    """
    maindir = "K:\\2015"
    resultdirpath = pathlib.Path(maindir + "\\result")
    csvpath = maindir + "\\result\\result.csv"
    listrawinv = list(resultdirpath.glob("*inv.json"))
    with open(csvpath, mode = "w", encoding = "utf-8", newline="") as csvfile:
            spamwriter = csv.writer(csvfile)
            spamwriter.writerow(["月份", "total invasive", "ER positive",
                "PR positive", "HER2 score 0", "HER2 score 1+",
                "HER2 score 2+", "HER2 score 3+"])
            for item in listrawinv:
                itemcsv = maindir + "\\result\\" + item.name[:5] + "invlist.csv"
                currentmonth = item.name[:5]
                with item.open(mode = "r", encoding="utf-8") as f:
                    itemdata = json.load(f)
        #print(item)
                with open(itemcsv, mode = "w", encoding = "utf-8", newline="") as itemcsvfile:
                    secondspamwriter = csv.writer(itemcsvfile)
                    for data in itemdata:
                        secondspamwriter.writerow([data[reportreader.PATHOLOGYNO], data[reportreader.DIAGNOSIS],
                        "ER:{0}".format(data[breastmacro.ER]), "PR:{0}".format(data[breastmacro.PR]),
                        "Her-2:{}".format(data[breastmacro.HERTWO])])
                ihcdata = take_monthlist_data_inv(itemdata)
                spamwriter.writerow([currentmonth] + list(ihcdata))
                resultrow = ["total invasive", "ER positive",
                    "PR positive", "HER2 score 0", "HER2 score 1+",
                    "HER2 score 2+", "HER2 score 3+"]
    """
    root = tkinter.Tk()
    root.wm_title("乳癌ER, PR, Her-2統計軟體")
    app = MainApp(root)
    root.mainloop()
if __name__ == '__main__':
    main()
