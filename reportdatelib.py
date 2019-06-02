#-------------------------------------------------------------------------------
# Name:        reportdatelib
# Purpose:     get information from csvfile generated from CMUH HIS system
#              and access report finished date
#
# Author:      kpchang
#
# Created:     16/08/2016
# Copyright:   (c) kpchang 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import csv
import pathlib
import sqlite3
import datetime
import random
from operator import itemgetter
from reportreading import diagclassifier
from reportreading import reportreader


def takereportcsv(filename, dbname, sourcename):
    """
        Import a csvfile of structure provided by CMUH, into newdb in dbname,
        with report source sourcename
    """
    li = []
    newdb = sqlite3.connect(dbname)
    create_duedate_table(newdb)
    sourcedb = sqlite3.connect(sourcename)
    with open(filename, newline="", encoding="big5", errors="ignore") as csvfile:
        spamreader = csv.reader(csvfile)
        print("reading the csv file {0}".format(filename))
        for row in spamreader:
            if len(row[9]) == 7:
                year = int(row[9][:3]) + 1911
                month = int(row[9][3:5])
                day = int(row[9][5:])
            else:
                (year, month, day) = (-1,-1,-1)
            id = row[2]
            doc = row[7]
            try:
                if id[0].isdigit():
                    try:
                        diagnosis_column = row[10]
                        write_path_table_duedate(id, 0, doc, year, month, day,
                                            diagnosis_column, newdb)
                        #newdb.commit()
                    except TypeError:
                        continue
            except IndexError:
                continue
            """
            else:
                (category, diagnosis_column) = (-1, "")
            """
            """
            if category == 0:
                write_path_table_duedate(id, category, doc, year, month, day,
                                        diagnosis_column, newdb
            """
    newdb.commit()
    newdb.close()
    sourcedb.close()

def read_db_by_duedate(year, month, day, connection):
    c = connection.cursor()
    c.execute('''SELECT * FROM reports_finishdate
            WHERE finish_year = ? AND finish_month = ? AND finish_day = ?''', (year, month, day))
    return c.fetchall()

def create_duedate_table(connection):
    """
        Create a sql table of particular format in given db if the table does
        not exist. Requires a sql connection as argument.
    """
    try:
        c = connection.cursor()
        c.execute('''CREATE TABLE reports_finishdate
        (pathology_number    text    PRIMARY KEY,
        pathology_category  int,
        report_physician    text,
        finish_year        int,
        finish_month       int,
        finish_day         int,
        diagnosis_column    text)
        ''')
        connection.commit()

    except sqlite3.OperationalError:
        pass

def find_report_by_number(pathnumber, connection):
    c = connection.cursor()
    c.execute('''SELECT pathology_category, diagnosis_column FROM reports
                  WHERE pathology_number=?''', (pathnumber,))
    connection.commit()
    return c.fetchone()

def write_path_table_duedate(id, category, doc, year, month, day, diagnosis, connection):
    """
        Write a pathologic report into a connected database.
    """
    c = connection.cursor()
    try:
        print(id, category, doc, year, month, day, diagnosis)
        c.execute('''INSERT INTO reports_finishdate
            (pathology_number, pathology_category, report_physician,
             finish_year, finish_month, finish_day, diagnosis_column)
            VALUES(?,?,?,?,?,?,?)''', (id, category, doc, year, month, day, diagnosis))
    except sqlite3.IntegrityError:
        pass

def report_yesterday(someyear, somemonth, someday):
    thisday = datetime.date(someyear, somemonth, someday)
    oneday = datetime.timedelta(days = 1)
    yesterday = thisday - oneday
    return (yesterday.year, yesterday.month, yesterday.day)

def report_nextweek(someyear, somemonth, someday):
    thisday = datetime.date(someyear, somemonth, someday)
    oneday = datetime.timedelta(days = 1)
    for i in range(7):
        thisday = thisday + oneday
    return(thisday.year, thisday.month, thisday.day)

def read_nonmalignant(year, month, day, connection):
    allreport = read_db_by_duedate(year, month, day, connection)
    li = []
    for item in allreport:
        if diagclassifier.diag_classify(item[6])[1] == diagclassifier.OTHERS:
            if item[0][0] == "F":
                pass
            else:
                pathology_number = item[0]
                doc = item[2]
                firstdiag = read_first_diag(item[6])
                diag_data = reportreader.take_diag_data(firstdiag)
                thisorgan = diag_data[reportreader.ORGANNAME]
                thisdiagnosis = ",".join(diag_data[reportreader.DIAGNOSIS])
                li.append((year, month, day, pathology_number, doc, thisorgan, thisdiagnosis))
    return li

def random_read_nonmalignant_seven(thisyear, thismonth, thisday, connection):
    li = []
    for i in range(7):
        (thisyear, thismonth, thisday) = report_yesterday(thisyear, thismonth, thisday)
        li = li + read_nonmalignant(thisyear, thismonth, thisday, connection)
    if len(li)>25:
        return random.sample(li, 25)
    else:
        return li

def read_first_diag(sometext):
    """
        Read first diagnosis column from a list of diagnoses separated by "|"
    """
    li = sometext.split("|")
    i = 0
    # only recognize first diagnosis column when contain_procedure
    while True:
        words = li[i].split(",")
        #print(words)
        if i >= (len(li)-1):
            break
        elif "section report" in li[i]:
            #print(li[i])
            i = i+1
            continue
        elif "addendum" in li[i]:
            i = i+1
            continue
        elif reportreader.contain_procedure(words):
            #print(True)
            break
        else:
            #print(False)
            i = i+1
            continue
    return(li[i])

def write_random_twentyfive(year, month, day, connection, directory):
    csvfilename = directory + str(year) + "_" + str(month) + "_" + str(day) + "非惡性切片同儕複閱.csv"
    filedate =str(year) +"_" + str(month) + "_" + str(day)
    print("writing {0}".format(csvfilename))
    testlist = random_read_nonmalignant_seven(year, month, day, connection)
    sortlist = sorted(testlist, key=itemgetter(3))
    with open(csvfilename, "w", encoding = "big5", newline='') as casecsv:
        spamwriter = csv.writer(casecsv)
        spamwriter.writerow(["非惡性切片同儕複閱討論會", "日期:", filedate])
        spamwriter.writerow(["病理編號", "病理診斷", "診斷醫師"])
        for item in sortlist:
            pathono = item[3]
            diagnosis = item[5] + ", " + item[6]
            doctor = item[4]
            spamwriter.writerow([pathono, diagnosis, doctor])


def main():
    takereportcsv("D:\\報告存檔\\1050701_1050901.csv", "D:\\報告存檔\\duedatedb.db", "D:\\報告存檔\\testcase2016.db")
    newdb = sqlite3.connect("D:\\報告存檔\\duedatedb.db")
    #print(read_db_by_duedate(2013, 12, 13, newdb))
    thisyear = 2016
    thismonth = 8
    thisday = 26
    for i in range(2):
        (thisyear, thismonth, thisday) = report_nextweek(thisyear, thismonth, thisday)
        write_random_twentyfive(thisyear, thismonth, thisday, newdb, "D:\\報告存檔\\nonmalignant\\")
    newdb.close()

if __name__ == '__main__':
    main()
