import os
import time
from convert import DeezerOauth, TestOauth, correctLink, GetPlaylistInfo
from sync import GetDeezerInfo
from convert import main as convertMain
from sync import main as syncMain

def correctLink(firstPrint,inputPrint,parameter,intPlatform):
    ValidPlaylistLink = False
    while (not ValidPlaylistLink):
        print(firstPrint)
        inputLink = input(inputPrint)
        if parameter in inputLink:
            if intPlatform == 1:
                resultData = GetPlaylistInfo(inputLink)
                if resultData[0]:
                    print(resultData[1].get('name'))
                    print(resultData[1].get('total'))
                    if resultData[1].get('total') > 2000:
                        print("Playlist Total Track Exceeds 2000 Limit")
                    else:
                        return inputLink[34:56]
                else: print("Invalid Link")
            elif intPlatform == 2:
                resultData = GetDeezerInfo(inputLink)
                if resultData[0]:
                    print(resultData[1].get('title'))
                    print(resultData[1].get('nb_tracks'))
                    return inputLink[35:]
                else: print("Invalid Link")
        else:
            print("Invalid Link")

def tokenCached():
    if not (os.path.isfile('./.cache')):
        deezerToken = DeezerOauth()
        return deezerToken
    else:
        f = open(".cache", "r")
        deezerToken = f.read()
        if not (TestOauth(deezerToken)):
            deezerToken = DeezerOauth()
            return deezerToken
        else:
            print("Deezer Authenticated Successful")
            return deezerToken
def main():
    os.system('cls')
    while (True):
        print("Spotify2Deezer".center(os.get_terminal_size().columns))
        print("V1.0".center(os.get_terminal_size().columns))
        print("Select 1, 2, or 3:")
        print("1. Convert Spotify Playlist to Deezer Playlist")
        print("2. Sync Spotify Playlist with Deezer Playlist")
        print("3. Exit")
        userInput = input("Selection: ")
        try:
            if int(userInput) in [1,2,3]:
                userInput = int(userInput)
                break
        except: 
            print("Invalid Input")
            time.sleep(0.25)
            os.system('cls')
    if userInput == 1:
        os.system('cls')
        print("Spotify to Deezer Playlist Converter".center(os.get_terminal_size().columns))
        deezerToken = tokenCached()
        spotifyPlaylistID = correctLink("Enter Spotify Playlist Link (ex. https://open.spotify.com/playlist/...)","Enter the playlist link:","https://open.spotify.com/playlist/",1) 
        convertMain(spotifyPlaylistID,deezerToken)
    elif userInput == 2:
        os.system('cls')
        print("Spotify to Deezer Playlist Sync".center(os.get_terminal_size().columns))
        deezerToken = tokenCached()
        spotifyPlaylistID = correctLink("Enter Spotify Playlist Link (ex. https://open.spotify.com/playlist/...)","Enter the playlist link:","https://open.spotify.com/playlist/",1) 
        deezerPlaylistID = correctLink("Enter Deezer Playlist Link (ex. https://www.deezer.com/en/playlist/...)","Enter the playlist link:","https://www.deezer.com/en/playlist/",2)
        GetDeezerInfo(deezerPlaylistID)
        syncMain(deezerPlaylistID,spotifyPlaylistID,deezerToken)
    else:
        print("Exiting...")
        quit()

if __name__ == "__main__":
    main()