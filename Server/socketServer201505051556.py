'''
WatchOut Socket Server main program
Prepared by Jacky Li@OUHK BSC WebTech
Date:201505051556
'''
import socket,datetime,base64,time,sqlite3, threading, sys, os, json
from bottle import request, route, run, template, response
from json import dumps



HOST = None              # Symbolic name meaning all available interfaces
PORT = 8990              # Arbitrary non-privileged port
s = None                 # Initial socket temp Data
now = None               #Initial Daytime
threads = {}
x=0
global kdata
global newthread 

def start():
     serverlog("WatchOut Socket Server Start....",True)
     for res in socket.getaddrinfo(HOST, PORT, socket.AF_INET,
                                  socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
          af, socktype, proto, canonname, sa = res
          try:
               s = socket.socket(af, socktype, proto)
          except socket.error as msg:
               s = None
               continue
          try:
               s.bind(sa)
               s.listen(5)
               acceptClient(s)
          except socket.error as msg:
               s.close()
               s = None
               continue
          break
     if s is None:
          serverlog("Could not open socket",True)
          sys.exit(1)

class ServerThread(threading.Thread):
    def __init__(self, conn, addr):
             threading.Thread.__init__(self)
             self.conn = conn
             serverlog("Connected by"+str(addr),True)

    def run(self):
        global kdata
        global newthread 
        strArr=[] #Socket Data Buffering
        bac=[]
        bc=None
        #toString("testing")
        while True:
            try:
                line = self.conn.recv(1024)
                toString(line)
            except:
                serverlog("Cannot recieve data",True)
                break
            if not line: break
            strArr.append(line)
            #try:
            if "}]" in line:
                st = "".join(strArr)
                now = getCurrentDaytime()
                write2Txt("fallData"+now.strftime("%Y%m%d")+".txt",st)
                myjson = json.loads(st.replace("\n",""))
                if(myjson[0]['func']=="1"):
                    serverlog(myjson[1]['status'],True)
                    if(checkTableExists("falllog")==True):
                        dbSQLexecute(["INSERT INTO falllog (dayTime,status,latitude,longitude) VALUES(?,?,?,?)",myjson[1]['tStamp'],myjson[1]['status'],myjson[1]['latitude'],myjson[1]['longitude']],"Insert1")
                    elif(checkTableExists("falllog")==False):
                        dbSQLexecute(["CREATE TABLE falllog (id INTEGER PRIMARY KEY, dayTime Varchar NOT NULL, status Varchar NOT NULL,latitude Varchar NOT NULL,longitude Varchar NOT NULL)"],"Create")
                        dbSQLexecute(["INSERT INTO falllog (dayTime,status,latitude,longitude) VALUES(?,?,?,?)",myjson[1]['tStamp'],myjson[1]['status'],myjson[1]['latitude'],myjson[1]['longitude']],"Insert1")
                    sendBroadcastMessage(str(myjson[1]['status'])+"\n")
                elif(myjson[0]['func']=="2"):
                    kdata = ""
                    kdata = myjson[1]['data']
                    serverlog(kdata,False)
                elif(myjson[0]['func']=="3"):
                    toString(myjson[1]['n'])
                elif(myjson[0]['func']=="4"):
                    oldkey=""
                    currentThread=""
                    for client in threads:
                        if threads.get(client) == threading.current_thread():
                            oldkey = client
                            currentThread = threads[client]
                    threads[myjson[1]['username']] = currentThread
                    removethread(client,True)
                    toString(str(threads))
                    
                st=None
                strArr=[]
                line=None
            '''except:
                serverlog("Server Error!",True)
                self.conn.close()
                serverlog("Connection closed",True)
                break'''
        self.conn.close()
        serverlog("Connection closed",True)
        removethread(threading.current_thread(),False)

def sendBroadcastMessage(msg):
    for sthread in threads.keys():
        sendMessgse(threads[sthread],msg)

def sendMessgse(thread,msg):
    thread.conn.send(msg)

def removethread(name,select):
    oldkey=""
    if select == True:
        del threads[name]
    elif select == False:
        for client in threads:
            if threads.get(client) == name:
                oldkey = client
        del threads[oldkey]
        
def acceptClient(s):
    global newthread 
    while True:
        conn, addr = s.accept()
        newthread = ServerThread(conn, addr)
        newthread.start()
        key = 'client'+str(len(threads)+1)
        threads[key] = newthread
        #threads.append(newthread)
        serverlog("Thread Status: "+str(threads),True)

def serverlog(msg,boo):
    if boo==True:
        now = getCurrentDaytime()
        log = "["+now.isoformat()+"]: "+msg
        toString(log)
        write2Txt("Serverlog"+now.strftime("%Y%m%d")+".txt",log)
    elif boo==False:
        now = getCurrentDaytime()
        log = "["+now.isoformat()+"]: Received "+str(len(msg))+" byte(s) data."
        toString(log)
        write2Txt("Serverlog"+now.strftime("%Y%m%d")+".txt",log)

def write2Txt(fileName,_input):
    with open(fileName, "a") as myfile:
        myfile.write(_input+"\n")

def Bwrite2Txt(fileName,_input):
    with open(fileName, "w") as myfile:
        print>> myfile,_input

def getCurrentDaytime():
    return datetime.datetime.now()

def toString(printData):
    print(printData+"\n")

def checkTableExists(tablename):
    try:
        dbcon = sqlite3.connect('falllog.db')
        dbcur = dbcon.cursor()
        dbcur.execute("""
            SELECT COUNT(*)
            FROM sqlite_master WHERE type = 'table' AND name = '{0}'
            """.format(tablename.replace('\'', '\'\'')))
        if dbcur.fetchone()[0] == 1:
            dbcur.close()
            return True
        dbcur.close()
        return False
    except:
        serverlog("checkTableExists Exception",True)
        
def dbSQLexecute(SQL,command):
    try:
        db = sqlite3.connect('falllog.db')
        if(command=="Insert1"):
            db.execute(SQL[0],(SQL[1],SQL[2],SQL[3],SQL[4]))
            db.commit()
        elif(command=="Insert2"):
            db.execute(SQL[0],(SQL[1],SQL[2],SQL[3],SQL[4],SQL[5],SQL[6],SQL[7],SQL[8]))
            db.commit()
        elif(command=="Create"):
            db.execute(SQL[0])
            db.commit()
        elif(command=="Select"):
            c = db.cursor()
            c.execute(SQL[0])
            data = c.fetchall()
            c.close()
            return data
    except:
        serverlog("dbSQLexecute Exception",True)
        
@route('/fetchfalllog')
def fetchFallLog():
    try:
        fallloglist = []
        data = dbSQLexecute(["SELECT dayTime, status, latitude, longitude  FROM falllog"],"Select")
        response.content_type = 'application/json'
        for row in data:
            fallloglist.append({"dateTime":row[0],"status":row[1],"latitude":row[2],"longitude":row[3]}) 
        return dumps({"android":fallloglist})   
    except:
        serverlog("fetchFallLog Exception",True)
        
@route('/fetchimage')
def fetchImage():
    try:
        global kdata
        response.content_type = 'application/json'
        return dumps([{"id":"kinect","data":kdata}])
    except:
        "sss"
        #serverlog("FetchImage Exception",False)

@route('/fetchsetting')
def fetchSetting():
    try:
        settinglist = []
        data = dbSQLexecute(["SELECT username,elderlyname,elderlydob,elderlygender,elderlyheight,elderlyweight,phonenumber,emServices FROM setting"],"Select")
        response.content_type = 'application/json'
        for row in data:
            settinglist.append({"username":row[0],"elderlyname":row[1],"elderlydob":row[2],"elderlygender":row[3],"elderlyheight":row[4],"elderlyweight":row[5],"phonenumber":row[6],"emServices":row[7]}) 
        return dumps({"android":settinglist[-1]})   
    except:
        serverlog("FetchSetting Exception",True)
        
@route('/storesetting', method='POST')
def storeSetting():
    try:
        response.status = 300
        revJson = request.forms.get('settings')
        myjson = json.loads(revJson)
        if(checkTableExists("setting")==True):
            dbSQLexecute(["INSERT INTO setting (username,elderlyname,elderlydob,elderlygender,elderlyheight,elderlyweight,phonenumber,emServices) VALUES(?,?,?,?,?,?,?,?)",myjson['username'],myjson['elderlyname'],myjson['elderlydob'],myjson['elderlygender'],myjson['elderlyheight'],myjson['elderlyweight'],myjson['phonenumber'],myjson['emServices']],"Insert2")
        elif(checkTableExists("setting")==False):
            dbSQLexecute(["CREATE TABLE setting (id INTEGER PRIMARY KEY, username Varchar NOT NULL, elderlyname Varchar NOT NULL,elderlydob Varchar NOT NULL,elderlygender Varchar NOT NULL,elderlyheight Varchar NOT NULL,elderlyweight Varchar NOT NULL,phonenumber Varchar NOT NULL,emServices Varchar NOT NULL)"],"Create")
            dbSQLexecute(["INSERT INTO setting (username,elderlyname,elderlydob,elderlygender,elderlyheight,elderlyweight,phonenumber,emServices) VALUES(?,?,?,?,?,?,?,?)",myjson['username'],myjson['elderlyname'],myjson['elderlydob'],myjson['elderlygender'],myjson['elderlyheight'],myjson['elderlyweight'],myjson['phonenumber'],myjson['emServices']],"Insert2")
    except:
        serverlog("StoreSetting Exception",True)
    
if __name__ == "__main__":
    while True:
        try:
             sock = threading.Thread(target=start)
             sock.daemon = True
             sock.start()
             bot = threading.Thread(target=run(host='0.0.0.0', port=8991))
             bot.daemon = True
             bot.start()
        finally:
            s = None
            strArr=[]
            line=None
            serverlog("Connection closed",True)
            serverlog("Restart Socket Server",True)

            
            
       
