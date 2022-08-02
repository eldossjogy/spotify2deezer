import os
import psycopg2
from convert import TestOauth
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv('.env')


DATABASE_URL = os.getenv('DATABASE_URL')
con = psycopg2.connect(DATABASE_URL)
cur = con.cursor()

# Creates key for Fernet
def create_key():
  key = Fernet.generate_key()
  key = os.getenv('KEY')
  return key

# Gets key for Fernet
def get_key():
    try:
      key = os.getenv('KEY')
      return key
    except:
      return create_key()

# Encrypts token
def encrypt(message):
    key = get_key()
    f=Fernet(key)
    encoded = message.encode()
    encrypted = f.encrypt(encoded)
    encrypted = encrypted.decode("ISO-8859-1")
    return encrypted

# Decrypts token
def decrypt(encrypted):
    key = get_key()
    f=Fernet(key)
    encrypted = encrypted.encode("ISO-8859-1")
    decrypted = f.decrypt(encrypted)
    decrypted = decrypted.decode()
    return decrypted

# Creates Table on PSQL Database
def createTable():
  cur.execute("CREATE TABLE userInfo ( userid VARCHAR ( 50 ) UNIQUE NOT NULL, token VARCHAR ( 255 ) UNIQUE, sync TEXT[][]);")
  cur.execute("ALTER TABLE userinfo ALTER COLUMN sync SET DEFAULT '{}';")
  con.commit()

# Stores Token and UserID into Database
# def storeInfo(userID,deezerToken):
def storeInfo(userid,token):
  encryptToken = encrypt(token)
  cur.execute("INSERT INTO userInfo(userid, token, sync) values(%s,%s,%s)",[str(userid), str(encryptToken),[]])
  con.commit()

# Checks for valid token
# def ErrorInfo(userID):
def ErrorInfo(userid):
  cur.execute("SELECT token FROM userinfo WHERE userid = '{}';".format(str(userid)))
  token = cur.fetchone()
  if token == None:
    return (False,'DM')
  else:
    token = token[0]
    decryptToken = decrypt(token)
    result = TestOauth(decryptToken)
    if result:
      return (result, decryptToken)
    else:
      return (result, 'Invalid Token')

# Check for valid user
def checkUser(userid):
    cur.execute("SELECT * FROM userinfo WHERE userid = '{}'".format(str(userid)))
    token = cur.fetchone()
    if token == None:
        return False
    return True

# Adds sync to synclist
def addSync(userid,sptfyLink,dzrLink,nxtTime,intHrs):
  newSync = [sptfyLink,dzrLink,nxtTime.strftime("%m/%d/%Y- %H:%M:%S"),str(intHrs)]
  cur.execute("SELECT sync FROM userinfo WHERE userid = '{}';".format(str(userid)))
  syncList = cur.fetchone() 
  cur.execute("UPDATE userinfo SET sync[{}] = ARRAY {} WHERE userid='{}';".format(len(syncList[0]),newSync, str(userid)))
  con.commit()

# Returns synclist of user
def syncList(userid):
  cur.execute("SELECT sync FROM userinfo WHERE userid = '{}';".format(str(userid)))
  syncList = cur.fetchone()
  if syncList == None:
    return (False,"No Entries in Sync List")
  else:
    synclist = syncList[0]
    if len(synclist) == 0:
      return (False,"No Entries in Sync List")
    else:
      lstSyncList = []
      for strList in synclist:
        strList = strList.replace('{','')
        strList = strList.replace('}','')
        lstSync = strList.split(",")
        lstSyncList.append(lstSync)
      return (True, lstSyncList)


# Removes syncs in Synclist
# def updateSync(userID,rSync):
def updateSync(userid,index):
  cur.execute("SELECT sync FROM userinfo WHERE userid = '{}';".format(str(userid)))
  syncList = cur.fetchone()[0]
  syncList.pop(index)
  if len(syncList) > 0:
      cur.execute("UPDATE userinfo SET sync = ARRAY {} WHERE userid='{}' RETURNING *;".format(syncList, str(userid)))
  else:
      cur.execute("UPDATE userinfo SET sync = ARRAY[]::TEXT[] WHERE userid='{}' RETURNING *;".format(str(userid)))
  con.commit()

# Returns all user synclists
def getSyncList():
  cur.execute("SELECT userid,sync FROM userinfo;")
  syncList = cur.fetchall()
  lstSync = []
  for info in syncList:
    infoDict = {}
    lstAllSync = []
    infoDict['user'] = info[0]
    for strSync in info[1]:
      strList = strSync.replace('{','')
      strList = strList.replace('}','')
      strList = strList.replace('"','')
      syncList = strList.split(",")
      lstAllSync.append(syncList)
    infoDict['sync'] = lstAllSync
    lstSync.append(infoDict)
  return lstSync
  
# Update new sync time
def setNewTime(newData):
  for userdict in newData:
    syncList = userdict.get('sync')
    for i in range(0,len(syncList)):
      cur.execute("UPDATE userinfo SET sync[{}] = ARRAY {} WHERE userid='{}';".format(i,syncList[i], str(userdict.get('user'))))
      con.commit()
  print("Changed")
