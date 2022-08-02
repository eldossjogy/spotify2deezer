import requests
import urllib.parse
import unidecode
from difflib import SequenceMatcher
remove_list = ['(','[',' feat',' ft','- ']

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def get_score(tracks):
        return (tracks['score'])

# Best Result Based on Score 
def scoreSelection(oldNameAlbum,artist,boolexplicit,boolRemix,duration,best_result):
    for tracks in best_result:
        if ((boolRemix == tracks.get('remix')) and (boolexplicit == tracks.get('explicit'))):
            tracks['score'] = 1
        elif (boolexplicit == tracks.get('explicit')):
            tracks['score'] = 0.5
        else:
            tracks['score'] = 0.25
        tracks['score'] += (similar(oldNameAlbum.get('name'),tracks.get('name')) + similar(artist[0],tracks.get('artist')) + similar(oldNameAlbum.get('album'),tracks.get('album'))) * (tracks.get('rank')/10000000)
        if (tracks.get('duration') < duration):
            tracks['score'] *= (tracks.get('duration')/duration)
        elif (tracks.get('duration')>duration):
            tracks['score'] *= (duration/tracks.get('duration'))   
    best_result.sort(key = get_score)
    if (len(best_result) > 0):
        return(best_result[-1].get('score'),best_result[-1].get('name'),best_result[-1].get('ID'))

# Request Deezer Search 
def deezerSearch(name,artist,album,boolexplicit,boolRemix,duration,testNum,oldNameAlbum):
    bestResult = []
    for differentArtist in artist:
        if(testNum == 0):
            query = "https://api.deezer.com/search?q=artist:\"{}\" track:\"{}\" album:\"{}\"".format(differentArtist,name,album)
        if(testNum == 1):
            query = 'https://api.deezer.com/search?q=artist:"{}" track:"{}" album:"{}"'.format(differentArtist,name,album)
        if(testNum == 2):
            search = 'artist:"{}" track:"{}" album:"{}"'.format(differentArtist,name,album) 
            search = search.replace(' ', '%20')
            query = "https://api.deezer.com/search?q={}".format(search)
        if(testNum == 3):
            search = name + " " + differentArtist + " " + album    
            search = urllib.parse.quote(search)
            query = "https://api.deezer.com/search?q={}".format(search)
        if(testNum == 4):
            query = "https://api.deezer.com/search?q={}".format(name)
        response = requests.get(query)
        if(str(response) == '<Response [403]>'):
            numResult = 0
        else:
            response_json = response.json()
        try:
            numResult = len(response_json["data"])
        except:
            numResult = 0
        for results in range(0,numResult):
            resultDict = {}
            resultDict['ID'] = response_json["data"][results]["id"]
            resultDict['name'] = response_json["data"][results]["title"]
            resultDict['artist'] = response_json["data"][results]["artist"]["name"]
            resultDict['album'] = response_json["data"][results]["album"]["title"]
            resultDict['duration'] = response_json["data"][results]["duration"]
            resultDict['explicit'] = response_json["data"][results]["explicit_lyrics"]
            resultDict['rank'] = response_json["data"][results]["rank"]
            if ('remix' in resultDict.get('name').lower()):
                resultDict['remix'] = True
            else: resultDict['remix'] = False
            if (not(name.isalnum()) or not(resultDict.get('name').isalnum())):
                name = ''.join(char for char in name if char.isalnum())
                resultName = ''.join(char for char in resultDict.get('name') if char.isalnum())
            else: resultName = resultDict.get('name')
            resultName = resultName.lower()
            resultArtist = resultDict.get('artist').lower()
            for artists in artist:
                if((resultName == name.lower() or name.lower() in resultName or resultName in name.lower()) and (resultArtist in artists.lower() or artists.lower() in resultArtist)):
                    if (('remix' in name.lower()) == ('remix' in resultName) or ((boolRemix) == ('remix' in resultName))):
                        bestResult.append(resultDict)
    oldbest = 0
    for tracks in bestResult:
        if ((boolRemix == tracks.get('remix')) and (boolexplicit == tracks.get('explicit'))):
            oldbest = tracks.get('ID')
            break
    if (oldbest == 0):
        for tracks in bestResult:
            if (boolexplicit == tracks.get('explicit')):
                oldbest = tracks.get('ID')
                break
    if (len(bestResult) > 0 and oldbest == 0):
        oldbest = bestResult[0].get('ID')
    
    newbest = scoreSelection(oldNameAlbum,artist,boolexplicit,boolRemix,duration,bestResult)
    return(oldbest,newbest)

# Control Deezer Search Test Num
def searchSong(trackInfo):
    oldNameAlbum = {'name':trackInfo.get('name'),'album':trackInfo.get('album')}
    # Search #1:
    resultID = deezerSearch(trackInfo.get('name'),trackInfo.get('artist'),trackInfo.get('album'),trackInfo.get('explicit'),trackInfo.get('remix'),trackInfo.get('duration'),0,oldNameAlbum)
    if (resultID != (0,None)):
        return resultID   
    editName = trackInfo.get('name').lower()
    editAlbum = trackInfo.get('album').lower()
    for removeCharacter in remove_list:
        if (removeCharacter in editName or removeCharacter in editAlbum):
            if (removeCharacter in editName):
                location = editName.find(removeCharacter)
                editName = editName[:location]
                editName = editName.rstrip()
            if (removeCharacter in editAlbum):
                location = editAlbum.find(removeCharacter)
                editAlbum = editAlbum[:location]
                editAlbum = editAlbum.rstrip()  
    # Search #2:
    for testNum in range(0,5):
        resultID = deezerSearch(editName,trackInfo.get('artist'),editAlbum,trackInfo.get('explicit'),trackInfo.get('remix'),trackInfo.get('duration'),testNum,oldNameAlbum)
        if (resultID != (0,None)):
            return resultID
    editName = unidecode.unidecode(editName)
    # Search #3:
    for testNum in range(0,5):
        resultID = deezerSearch(editName,trackInfo.get('artist'),'',trackInfo.get('explicit'),trackInfo.get('remix'),trackInfo.get('duration'),testNum,oldNameAlbum)
        if (resultID != (0,None)):
            return resultID
    return 'F'
