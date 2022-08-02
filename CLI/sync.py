from convert import TrackID, GetPlaylistInfo
from search import searchSong
import requests
from difflib import SequenceMatcher

def similar(name1, artist1, name2, artist2):
    return SequenceMatcher(None, name1, name2).ratio() + SequenceMatcher(None, artist1, artist2).ratio()

# Get Spotify Playlist songs
def spotifyPlaylistsongs (playlistLink):
    playlistInfo = GetPlaylistInfo(playlistLink)
    playlistTitle = playlistInfo[1].get('name')
    totalTracks = playlistInfo[1].get('total')
    print('Playlist Name:',playlistTitle)
    print('Playlist Total Tracks:',totalTracks)
    if (playlistInfo[0]):
        totalTracks = playlistInfo[1]['total']
    else:
        return 
    NumLoopCount = (totalTracks//100)+1
    return TrackID(playlistLink,NumLoopCount)

# Check for valid Deezer Link
def GetDeezerInfo(playlistLink):
    query = "https://api.deezer.com/playlist/{}".format(playlistLink[35:])
    response = requests.get(query)
    result = response.json()   
    if 'error' in result:
        return(False,"Error: "+ result['error']['message'])
    else:
        return(True, result)

# Get Deezer Playlist songs
def deezerPlaylistsongs (playlistLink,deezerToken):
    playlistSongs = []
    boolNext = False
    next_url = "https://api.deezer.com/playlist/{}/tracks".format(playlistLink)
    while(not boolNext):
        query = next_url
        response = requests.get(
            query,
            params={
                "access_token": "{}".format(deezerToken),   
                }
        )
        DeezerPlaylist_Result = response.json()   
        result_len = len(DeezerPlaylist_Result['data'])
        for i in range (0,result_len):
            songDict = {}
            songDict['ID'] = DeezerPlaylist_Result["data"][i]["id"]
            songDict['name'] = DeezerPlaylist_Result["data"][i]["title"]
            songDict['artist'] = DeezerPlaylist_Result["data"][i]["artist"]["name"]
            songDict['album'] = DeezerPlaylist_Result["data"][i]["album"]["title"]
            songDict['explicit'] = DeezerPlaylist_Result["data"][i]["explicit_lyrics"]
            playlistSongs.append(songDict)
        if 'next' in DeezerPlaylist_Result.keys():
            next_url = DeezerPlaylist_Result['next']
        else:
            boolNext = True
    return playlistSongs   

# Compare Deezer & Spotify Playlist
def comparePlaylist(spotifyPlaylist, deezerPlaylist):
    failedSync = []
    for sptfysongs in spotifyPlaylist:
        for dzersongs in deezerPlaylist:
            if similar(sptfysongs.get("name"),sptfysongs.get("artist"),dzersongs.get("name"),dzersongs.get("artist")) > 0.8:
                sptfysongs["deezerID"] = dzersongs.get("ID")
                deezerPlaylist.remove(dzersongs)
                break
    for items in spotifyPlaylist:
        if items.get("deezerID") == None:
            for elements in deezerPlaylist:
                remove_list = ['(','[',' feat',' ft','- ']
                sptfyname = items.get("name").lower()
                dezername = elements.get("name").lower()
                for rchar in remove_list:
                    if rchar in sptfyname:
                        location = sptfyname.find(rchar)
                        sptfyname = sptfyname[:location]
                        sptfyname = sptfyname.rstrip()
                    if rchar in dezername:
                        location = dezername.find(rchar)
                        dezername = dezername[:location]
                        dezername = dezername.rstrip()
                if similar(sptfyname,items.get("artist"),dezername,elements.get("artist")) > 0.8:
                    items["deezerID"] = elements.get("ID")
                    deezerPlaylist.remove(elements)
                    break
    for items in spotifyPlaylist:
        if items.get("deezerID") == None:
            result = searchSong(items)
            if result != "F":
                items["deezerID"] = result
            else:
                failedSync.append(items)
    return deezerPlaylist,spotifyPlaylist,failedSync

# Remove Song From Playlist
def removeSong(playlistLink,songID,deezerToken):
    query = "https://api.deezer.com/playlist/{}/tracks".format(playlistLink)
    response = requests.delete(
        query,
        params={
            "access_token": "{}".format(deezerToken),   
            "songs": "{}".format(songID)
            }
    )
    response_json = response.json()
    if not response_json:
        print("Error Removing from Playlist")

# Adds Song To Playlist
def addSongs(playlistLink,songID,deezerToken):
    query = "https://api.deezer.com/playlist/{}/tracks".format(playlistLink)
    response = requests.post(
                query,
                params={
                    "access_token": "{}".format(deezerToken),   
                    "songs": "{}".format(songID)
                }
            )
    response_json = response.json()
    if not response_json:
        print("Error Adding to Playlist")

# Order Song From Playlist
def orderDeezer(playlistLink,IDarray,deezerToken):
    query = "https://api.deezer.com/playlist/{}/tracks".format(playlistLink)
    response = requests.post(
        query,
        params={
            "access_token": "{}".format(deezerToken),   
            "order": "{}".format(IDarray)
            }
    )
    response_json = response.json()
    if not response_json:
        print("Error Updating Playlist")

def main(deezerLink,spotifyLink,deezerToken):
    deezerSong = []
    spotifySong = []
    spotifySong = spotifyPlaylistsongs(spotifyLink)
    spotifySong = spotifySong[0]
    deezerSong = deezerPlaylistsongs(deezerLink,deezerToken) 
    removeList,updateList,failedList = comparePlaylist(spotifySong,deezerSong)
    print(str(len(removeList)) + " Songs Removed:")
    for songs in removeList:
        removeSong(deezerLink,songs.get('ID'),deezerToken)
        print('\t>',songs.get('name'),'-',songs.get('artist'))
    print(str(len(updateList)) +" Songs Updated")
    print("Songs Added:")
    for songs in updateList:
        if str(type(songs.get("deezerID"))) == "<class 'tuple'>":
            songs['deezerID'] = songs.get('deezerID')[0]
            addSongs(deezerLink,songs.get('deezerID'),deezerToken)
            print('\t>',songs.get('name'),'-',songs.get('artist')[0])
    songIDarray = ([str(songs.get('deezerID')) for songs in updateList])
    dupRemove = []
    [dupRemove.append(x) for x in songIDarray if x not in dupRemove]
    songIDarray = ','.join(dupRemove)
    orderDeezer(deezerLink,songIDarray,deezerToken)
    print("Failed Songs:")
    for fails in failedList:
        print('\t>',fails.get('name'),'-',fails.get('artist')[0])
    print("Updated Playlist: {}".format("https://www.deezer.com/en/playlist/"+str(deezerLink)))