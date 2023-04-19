
from os import listdir, remove
#from striprtf.striprtf import rtf_to_text
from RoseUtils.rtf_reader import read_rtf as openrtf
import sqlite3 #Save to database
from xlsxwriter.workbook import Workbook #to export the database into an excel file
from datetime import datetime
import time #just for timing the script
import traceback
from time import sleep, perf_counter
from dataclasses import dataclass

def run(self):
    try:

        class Shift():
            def __init__(self, line, next):
                self.id = line[0:9].strip()
                self.name = line[9:35].strip()
                self.name = self.name.split(" ")[0][0:7].strip() + " " + self.name.split(" ")[-1][0]
                self.start = truetime(line[41:49])
                self.end = truetime(line[49:58])
                self.length = float(line[60:65].strip())
                self.second_end = 0.0
                self.total_length = 0.0
                self.second_start = 0.0
                self.break_length = 0.5
                self.skip = False
                if "*" in line[49:58]: 
                    self.br = True
                    self.break_length = 0.5
                    self.skip = True
                else:
                    self.br = False
                    if line[0:7] == next[0:7]:
                        self.br = True
                        self.second_start = truetime(next[41:49].strip())
                        self.second_length = float(next[60:65].strip())
                        self.second_end = truetime(next[49:58].strip())
                        self.break_length = self.second_start - self.end
                        self.total_length = float(line[60:65].strip()) + float(next[60:65].strip()) + self.break_length

                        
            




        start = perf_counter()
        ####### Change the 3 variables below. Inlude double "\\"s, including 2 at the end of paths
        self.append_text.emit("Running Breaks Report")
        
        sleep(.01)
        if self.rcp:
            MAXSHIFTWA = 5.1
            MAXSHIFTOR = 6.1
            CCD = False
            RCP = True
            #GM_NAMES = ("Mel",'tyler','kim','kristina','cara','nicole','jordan','sean',
            #            'forrest','yerey','dan','jordan P','kim','maranda')
            #GM_ID_LIST = ("10131868","10039186","10039195","10039300","10039462","10039205","10039288",
            #              "10039248","10006085","10039389","10039191","10124254","10039195","10002623")
            databasefile = self.rcpdatabase
            MINBREAK = 0.5
            MAXECLUDE = 0.02
        else:
            CCD = True
            RCP = False
            MAXSHIFTWA = 5.1
            MAXSHIFTOR = 5.1
            #GM_ID_LIST = ("10165861","10039358","10162686","10162376","10177223","10161583","10165345","10039345",
            #              "10162343","10039243","10039305","10039312","10161595","10171661","10173335")
            databasefile = self.ccddatabase
            MINBREAK = 0.5
            MAXECLUDE = 0.02
        CCDMINORS = ['10177606', '10190883', '10207907', '10208525', '10213678', 
                    '10217298', '10217507', '10217795', '10218511', '10220538', 
                    '10220694', '10220775', '10223219', '10223898', '10229576', 
                    '10230110', '10231447', '10232090', '10233456', '10233457', 
                    '10235741', '10237288', '10239955']
        ZOCDOWNLOAD_FOLDER = self.zocdownloadfolder   
        DATABASE_FILE = databasefile
        EXPORT_EXCEL_FILE = databasefile[:databasefile.rfind("/")]+"/Breaks.xlsx"
        EXPORT_EXCEL_FILE2 = databasefile[:databasefile.rfind("/")]+"/timeclock.xlsx"
        WASHINGTON_STORES = ["2236","3498","2953"]
        
        ###### End of user setup section

        if CCD: MAXSHIFTOR = MAXSHIFTWA

        start_time = time.perf_counter()
        con = sqlite3.connect(DATABASE_FILE)
        cursor=con.cursor()

        ###### If there isn't a 'breaks' table in the database, create one
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS breaks(
                id INTEGER PRIMARY KEY,
                date TEXT,
                store TEXT,
                item TEXT,
                value TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS timeclock(
                id INTEGER PRIMARY KEY,
                date TEXT,
                store TEXT,
                tm TEXT,
                intime TEXT,
                outtime TEXT,
                hours TEXT,
                position TEXT
            )
        ''')
        #### OLD CODE BELOW
        '''def openrtf(file): #Call this to open an rtf file with the filepath in the thing.
                            #Will return a list of strings for each line of the file
            with open(file, 'r', errors="ignore") as file:
                text = file.read()
            text = rtf_to_text(text)
            textlist = text.splitlines()
            return textlist #returns a list containing entire RTF file'''
        ####### END OLD CODE

        def truetime(time:str) ->float: 
            '''Pass in a string 12:30pm -> 12.50'''
            h = float(time[0:2])
            m = float(time[3:5])
            if time[5:7] == "pm": h +=12
            if h == 12: h = 0
            m = (m/60)
            if h+m > 24: h -=12
            return h+m
        
        def ampm(time:float) ->str:
            '''Pass in time in decimals of hours 12.50 -> 12:30pm'''
            if time > 24: time = time - 24
            if time > 12:
                a = "pm"
                h = int(time-12)
            else:
                a = "am"
                h = int(time)
            m = time-int(time)
            m = int(m * 60)
            if len(str(m))==1: m = f"0{m}"
            return f"{h}:{m}{a}"



        def findline(text:str,start:int) -> int: #Returns the number of the first line containing the text supplied
            i = start
            while i < len(dor):
                if dor[i].find(text) == -1:
                    i+=1
                else:
                    return i
            return 0

        def dayPart(dayPartLine:int, part:str) ->str: #Returns the OTD and CSC concatenated for the daypart
            if (findline(part,dayPartLine) - dayPartLine) > 20:
                return ""
            OTD = dor[findline(part,dayPartLine)][53:58].strip()
            CSC = str(int(round(float(dor[findline(part,dayPartLine)][122:128].strip()),0)))
            return f"{OTD} {CSC}%"

        def aggSales(agg):
            if findline(agg,0) == 0:
                return 0
            else:
                return dor[findline(agg,0)][76:83].strip()
            
        
        
        def breaks(list:list,skip:bool,breakscount:int,position:str)->int: ###Searches for missed and short breaks
            shiftslist = [i[0:70].strip() for i in list]       
            shifts = []
            shiftslist.append('                                                                  ')
            
            i = 0
            while i < len(shiftslist)-1:
                shifts.append(Shift(shiftslist[i], shiftslist[i+1]))
                if shiftslist[i][0:8] == shiftslist[i+1][0:8]: i+=1
                i +=1

            state = 'WA'
            if RCP and store not in WASHINGTON_STORES: state = 'OR'
            if state == 'wa':   #washington
                max = MAXSHIFTWA
                
            else:               #oregon
                if skip:
                    max = MAXSHIFTOR+2
                else:
                    max = MAXSHIFTOR


            for shift in shifts:
                dbentry = []
                if "Till " in shift.name:
                    if shift.length > 1:
                        cursor.execute("INSERT INTO breaks(date,store,item,value) VALUES(?,?,?,?)", (date,store,"breaks","Till"))
                    continue
                if shift.br == False and float(shift.length) > max:
                    dbentry.append(f"{shift.name} NB {shift.length}")
                    breakscount +=1
                else:
                    if shift.br == True and shift.break_length < 0.5 and shift.break_length > 0.05:
                        dbentry.append(f"{shift.name} SB {int(shift.break_length * 60)}")
                if shift.skip == False and shift.br == True: # Check early and late breaks
                    if state == 'OR':
                        if shift.total_length < 7 and shift.total_length > 6:
                            if shift.length < 2:
                                dbentry.append(f"{shift.name} EB {shift.length}")
                            if shift.length > 5:
                                dbentry.append(f"{shift.name} LB {shift.length}")
                        if shift.total_length > 7:
                            if shift.length < 2:
                                dbentry.append(f"{shift.name} EB {shift.length}")
                            if shift.length > 6:
                                dbentry.append(f"{shift.name} LB {shift.length}")
                    if state == 'WA':
                        if shift.length < 2:
                            dbentry.append(f"{shift.name} EB {shift.length}")
                        if shift.length > 5:
                            dbentry.append(f"{shift.name} LB {shift.length}")
                for entry in dbentry:
                    if shift.id in CCDMINORS:
                        cursor.execute("INSERT INTO breaks(date,store,item,value) VALUES(?,?,?,?)", (date,store,"breaksM",entry))
                    else:
                        cursor.execute("INSERT INTO breaks(date,store,item,value) VALUES(?,?,?,?)", (date,store,"breaks",entry))
                    

                    
                        
                



            return breakscount






        fileList = [file for file in listdir(ZOCDOWNLOAD_FOLDER) if file.startswith("ODMDOR")] #create list of files to loop through -> filelist
        for file in fileList:
            file = ZOCDOWNLOAD_FOLDER + file
            dor = openrtf(file)
            breakscount = 0
            ##Store, Date and CSC. All simple
            store = dor[0][83:87]
            #print(f"Opening store #{store} from file {file}")
            self.append_text.emit(f"Breaks Report: Opening store #{store}")
            
            sleep(.01)
            date = dor[3].strip()
            csc = f'{dor[findline("Void Unmade Orders",0)][126:].strip()}%'
            excess = dor[findline("Excess",0)][65:70].strip()
            void = dor[findline("Void",0)][30:38].strip()
            
            cashvar = dor[findline("Total Cash",0)][80:].strip()
            if dor[findline("Total Cash",0)][73:78] == "Short": cashvar = -cashvar # type: ignore

            '''
            ordersumline = findline("Order Summary",0)
            deliveries = dor[ordersumline+1][26:30].strip()
            carryouts = dor[ordersumline+2][26:30].strip()
            cancelled = dor[ordersumline+3][26:30].strip()
            voidorders = dor[ordersumline+4][26:30].strip()
            runs = dor[ordersumline+1][96:102].strip()
            '''




            ###Delete Headers from DOR
            header1 = dor[0]
            header2 = dor[1]
            header3 = dor[2]
            header4 = dor[3]
            while header1 in dor:
                dor.remove(header1)
            while header2 in dor:
                dor.remove(header2)
            while header3 in dor:
                dor.remove(header3)
            while header4 in dor:
                dor.remove(header4)
            for line in dor:
                if len(line) == len(header1): dor.remove(line)
                if len(line) == 0: dor.remove(line)
                try: 
                    if 'PAPA JOHNS PIZZA - RESTAURANT' in line: dor.remove(line)
                except:
                    pass
            for line in dor:
                if "PAPA JOHNS PIZZA - RESTAURANT" in line:
                    dor.remove(line)



            ###Dayparts
            dayPartLine = findline("DayPart",0)
            lunch = dayPart(dayPartLine, "Lunch")
            afternoon = dayPart(dayPartLine, "Afternoon")
            dinner = dayPart(dayPartLine, "Dinner")
            evening = dayPart(dayPartLine, "Evening")

            ###Aggregators
            uber = aggSales("Uber Eats :")
            doordash = aggSales("Doordash :")
            grubhub = aggSales("Grubhub :")
            
            ###Timeclocks setup
            timeclockstart = findline("Emp #",0)
            driverline = findline("Driver - Own Car",timeclockstart)
            instoreline = findline("In Store",timeclockstart)
            managerline = findline("Manager",timeclockstart)
            endline = findline("Non Operational",timeclockstart)
            if endline == 0: endline = findline("******** Unassigned Orders",timeclockstart)
            if driverline != 0: #no drivers
                if instoreline == 0:
                    drivers = dor[driverline+1:managerline-1]
                else:
                    drivers = dor[driverline+1:instoreline-1]
            if instoreline != 0: instores = dor[instoreline+1:managerline-1]
            managers = dor[managerline+1:endline-1]

            ##### Deposit
            ccDepLine = findline("      CC       ",0)
            if ccDepLine == 0:
                deposit = "No CC Deposit"
            else:
                deposit = dor[ccDepLine-1][64:71]
            
            ##### Travel Payouts
            travel = 0
            for i in range(33,50):
                if dor[i][15:34].strip() == "Travel":
                    travel = travel + float(dor[i][50:63].strip())


            ### Find short and missing breaks 
            ################# DATABASE CALLs ARE IN THE "noBreak" and "shortBreak" FUNCTIONS
            if driverline != 0: breakscount = breaks(drivers,False,breakscount,'Driver') # type: ignore
            if instoreline != 0: breakscount = breaks(instores,False,breakscount,'Instore') # type: ignore
            if RCP: breakscount = breaks(managers,True,breakscount,'Manager')
            if breakscount == 0:
                cursor.execute("INSERT INTO breaks(date,store,item,value) VALUES(?,?,?,?)", (date,store,"breaks","None Missed!"))
            mgrs = []
            outtimes = []
            intimes = []
            for tm in managers: #loop through the managers, building 3 lists, names, in times, out times. Times are stored as X.XX hours
                if "PAPA JOHNS PIZZA - RESTAURANT" in tm:
                    managers.remove(tm)
                    continue
                if len(tm) < 10:
                    continue
                name = tm[8:30].strip()
                name = name.split(' ')
                name = name[0][0]+name[1][0]
                mgrs.append(name)
                if truetime(tm[49:56]) < 6: #if it's less than 6am add 24 hours
                    outtimes.append(truetime(tm[49:56])+24) 
                else:
                    outtimes.append(truetime(tm[49:56]))
                intimes.append(truetime(tm[41:48]))
                if tm[49:56] == "12:00am" and tm[41:48] == "12:00am": #Exclude the GM
                    mgrs.pop()
                    intimes.pop()
                    outtimes.pop()
            closer = f"{mgrs[outtimes.index(max(outtimes))]} {ampm(max(outtimes))}"
            opener = f"{mgrs[intimes.index(min(intimes))]} {ampm(min(intimes))}"

                       
            #### EZCater paid outs
            x = findline("Cash Paid Out",10)
            for i in range(x,x+30):
                line = dor[i]
                if "EzCater" in dor[i]:
                    cursor.execute("INSERT INTO breaks(date,store,item,value) VALUES(?,?,?,?)", (date,store,"ezcater PO",float(dor[i][50:64].strip())))
                    
           
            #####Insert everything other than breaks into the database
            database = [(date, store, "CSC",csc),
                        (date, store, "Lunch", lunch),
                        (date, store, "Afternoon", afternoon),
                        (date, store, "Dinner", dinner),
                        (date, store, "Evening", evening),
                        (date, store, "Doordash",doordash),
                        (date, store, "Grubhub",grubhub),
                        (date, store, "Uber",uber),
                        (date, store, "Closing MGR",closer),
                        (date, store, "Opening MGR",opener),
                        (date, store, "Deposit",deposit),
                        (date, store, "Voids",void),
                        (date, store, "Travel", travel),
                        (date, store, "Excess Mileage",excess)]

            ezcater = findline("EZCater",0) ### Find EZCAter Payments
            if ezcater != 0 and ezcater < 50:
                database.append((date, store, "ezcater",float(dor[ezcater][73:90].strip()) + float(dor[ezcater][89:].strip())))

         

            cursor.executemany("INSERT INTO breaks(date,store,item,value) VALUES(?,?,?,?)", database)
            if self.check_delete:
                remove(file)

            
        con.commit()

        #### Export database to excel file
        workbook = Workbook(EXPORT_EXCEL_FILE)
        worksheet = workbook.add_worksheet()
        
        
        cursor.execute("select * from breaks")
        mysel=cursor.execute("select * from breaks")
        for i, row in enumerate(mysel):
            for j, value in enumerate(row):
                worksheet.write(i, j, row[j])
                

        workbook.close()

        workbook = Workbook(EXPORT_EXCEL_FILE2)
        worksheet = workbook.add_worksheet()
        
        
        cursor.execute("select * from timeclock")
        mysel=cursor.execute("select * from timeclock")
        for i, row in enumerate(mysel):
            for j, value in enumerate(row):
                worksheet.write(i, j, row[j])
                

        workbook.close()
        
        con.close()
        end_time = time.perf_counter()
        #print(f"Completed {len(fileList)} stores in {end_time - start_time} seconds")
        self.append_text.emit(f"Breaks Report: Completed {len(fileList)} stores in {round(end_time - start_time,2)} seconds")
        sleep(.01)
    except:
        self.append_text.emit("ENCOUNTERED ERROR")
        self.append_text.emit("Please send the contents of this box to Justin")
        self.append_text.emit(traceback.format_exc())
        pass