#Libraries
import os
import time
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from search import searchSong
from dotenv import load_dotenv 
load_dotenv('.env')
#Constant
    # Deezer API Info
APP_ID = os.getenv('APP_ID')
SECRET = os.getenv('SECRET')
REDIRECT_URL = os.getenv('REDIRECT_URL')
PERMS = "basic_access,manage_library,delete_library"
    # Spotify API Info
os.environ["SPOTIPY_CLIENT_ID"] = os.getenv('SPOTIPY_CLIENT_ID')
os.environ["SPOTIPY_CLIENT_SECRET"] = os.getenv('SPOTIPY_CLIENT_SECRET')
os.environ["SPOTIPY_REDIRECT_URI"] = os.getenv('SPOTIPY_REDIRECT_URI')

#Functions
# Input Check
def correctLink(firstPrint,inputPrint,parameter):
    ValidPlaylistLink = False
    while (not ValidPlaylistLink):
        print(firstPrint)
        inputLink = input(inputPrint)
        if parameter in inputLink:
            return inputLink
        else:
            print("Invalid Link")

# Authenticate Deezer API:
def DeezerOauth():
    redirectInput = correctLink("https://connect.deezer.com/oauth/auth.php?app_id={}&redirect_uri={}&perms={}".format(APP_ID,REDIRECT_URL,PERMS),"Enter the redirected link after appecting:","http://localhost:5000/callback?code=")
    deezerCode = redirectInput[36:]
    oauthResponse = requests.get("https://connect.deezer.com/oauth/access_token.php?app_id={}&secret={}&code={}".format(APP_ID,SECRET,deezerCode))
    deezerToken = oauthResponse.text
    end = deezerToken.find("expires")       # Deezer Token Currently Dont Expire
    deezerToken = deezerToken[13:end-1]
    file = open(".cache", "w")              # Store Deezer Token in .cache
    file.write(str(deezerToken)) 
    return deezerToken

# Check If Valid Deezer Token
def TestOauth(deezerToken):
    query = "https://api.deezer.com/user/me"
    response = requests.get(
                query,
                params={
                    "access_token": "{}".format(deezerToken),   
                }
            )
    response_json = response.json()
    if("error" in response_json):
        print(response_json)
        return False
    return True

# Get Spotify Playlist
def GetPlaylistInfo(spotifyPlaylistID):
    try:
        client_credentials_manager = SpotifyClientCredentials()
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        playlistInfo = sp.playlist(spotifyPlaylistID)
        spotifyPlaylist = {}
        spotifyPlaylist['name'] = playlistInfo["name"]
        spotifyPlaylist['total'] = int(playlistInfo["tracks"]["total"])
        spotifyPlaylist['owner'] = playlistInfo["owner"]["display_name"]
        spotifyPlaylist['cover'] = playlistInfo["images"][0]["url"]
        return (True,spotifyPlaylist)
    except Exception as e: 
        index = e.msg.rfind(':')
        return (False , e.msg[index+1:].strip())

# Spotify Track Info
def TrackID(SpotifyPlaylist_ID,NumLoopCount):
    NumOffset = 0
    playlistSongArray = []
    localSongs = []
    for x in range(NumLoopCount):
        client_credentials_manager = SpotifyClientCredentials()
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        spotifyJSON = sp.playlist_tracks(SpotifyPlaylist_ID,offset=NumOffset)
        numTracks = len(spotifyJSON["items"])
        for position in range(0,numTracks):
            if (str(spotifyJSON["items"][position]["track"]["uri"][:14]) == "spotify:track:"):
                songDict = {}
                songDict['name'] = spotifyJSON["items"][position]["track"]["name"]
                trackArtistInfo = spotifyJSON["items"][position]["track"]["artists"]
                trackArtist = []
                numArtist = str(trackArtistInfo).count("name")
                for rangeofArtist in range(0,numArtist):
                    trackArtist.append(trackArtistInfo[rangeofArtist]["name"])
                songDict['artist'] = trackArtist
                songDict['album'] = spotifyJSON["items"][position]["track"]["album"]["name"]
                songDict['duration'] = int((spotifyJSON["items"][position]["track"]["duration_ms"])/1000)
                songDict['explicit'] = spotifyJSON["items"][position]["track"]["explicit"]
                if ('remix' in songDict['name'].lower()):
                    songDict['remix'] = True
                else: songDict['remix'] = False
                songDict['position'] = position
                songDict['deezerID'] = None
                playlistSongArray.append(songDict)
            else:
                localSongs.append('> '+str(spotifyJSON["items"][position]["track"]["name"]+" - " + spotifyJSON["items"][position]["track"]["artists"][0]["name"])+ ' (Local Files)')
        NumOffset = NumOffset + 100
        time.sleep(4)
    return (playlistSongArray,localSongs)

# Create Deezer Playlist
def DeezerCreatePlaylist(playlistTitle,deezerToken):
    query = "https://api.deezer.com/user/me"
    response = requests.get(
                query,
                params={
                    "access_token": "{}".format(deezerToken),   
                }
            )
    response_json = response.json()
    deezer_userid = response_json["id"]
    query = "https://api.deezer.com/user/{}/playlists".format(deezer_userid)
    response = requests.post(
                query,
                params={
                    "access_token": "{}".format(deezerToken),   
                    "title":"{}".format(playlistTitle),
                }
            )
    response_json = response.json()
    return response_json["id"]

# Create Songs to Deezer Playlist
def AddSongToPlaylist(songArray,PlaylistID,deezerToken):
    for songinfo in songArray:
        query = "https://api.deezer.com/playlist/{}/tracks".format(PlaylistID)
        response = requests.post(
                    query,
                    params={
                        "access_token": "{}".format(deezerToken),   
                        "songs": "{}".format(songinfo.get('deezerID'))
                    }
                )

def main(spotifyLink,deezerToken):
    tracksFound = 0
    tracksFailed = 0
    songArray = []
    localSongs = []
    failSongs = []
    spotifyPlaylistInfo = GetPlaylistInfo(spotifyLink)
    playlistTitle = spotifyPlaylistInfo[1].get('name')
    totalTracks = spotifyPlaylistInfo[1].get('total')
    if totalTracks <= 2000:
        NumLoopCount = (totalTracks//100)+1
        print('Playlist Name:',playlistTitle)
        print('Playlist Total Tracks:',totalTracks)
        print('Getting Spotify Song Information...')
        infoArray = TrackID(spotifyLink,NumLoopCount)                               # Spotify Information
        songArray,localSongs = infoArray[0],infoArray[1]
        print('Finding Songs on Deezer...')
        for trackInfo in songArray:
            rID=searchSong(trackInfo)
            if (rID == 'F'):                                                        # Track Not Found
                tracksFailed += 1
                failSongs.append(trackInfo)
            else:
                tracksFound += 1
                if (rID[1] == None):                                                # If only oldBest (Very RARE!)
                    trackInfo['deezerID'] = rID[0]
                else:                                                               # Both oldBest and newBest are found
                    trackInfo['deezerID'] = rID[1][2]
                    if (rID[0] == rID[1][2]):                                       # Check 2 best IDs
                        if (trackInfo.get('name') == trackInfo.get('album')):       # If album name and track name same 
                            trackInfo['album'] = ''
                            nrID=searchSong(trackInfo)                              # Search with no album name
                            if (nrID != 'F' and rID[1] != None):                    # If the new id isnt the same id 
                                if (nrID[0] != rID[0] and nrID[0] == nrID[1][2]):
                                    if (nrID[1][0] > rID[1][0]):                    # If  the id has a better score then current id
                                        lstrID = list(rID)
                                        lstrID[1] = nrID[1]
                                        rID = tuple(lstrID)      
                                        trackInfo['deezerID'] = rID[1][2]           # Change current newbest to new newbest
        print(str(tracksFound)+" Tracks Found on Deezer") 
        if len(localSongs) + tracksFailed > 0:
            print("Failed Songs (" + str(len(localSongs) + tracksFailed) + "):")
            for fails in failSongs:
                print('\t>',fails.get('name'),'-',fails.get('artist')[0])
            print("Local Songs:")
            for local in localSongs:
                print(local)
        print('Creating Deezer Playlist...')
        deezerPlaylistID = DeezerCreatePlaylist(playlistTitle,deezerToken)
        print('Adding Songs To Deezer Playlist...')
        AddSongToPlaylist(songArray,deezerPlaylistID,deezerToken)
        print("Deezer Playlist Link: {}".format("https://www.deezer.com/en/playlist/"+str(deezerPlaylistID)))
    else:
        print("Playlist Total Track Exceeds 2000 Limit")