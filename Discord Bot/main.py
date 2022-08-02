import os
import discord
import requests
from dotenv import load_dotenv 
from discord.ext import tasks
from datetime import datetime, timedelta

import dataStorage
from convert import main as convertMain
from convert import TestOauth, GetPlaylistInfo
from sync import main as syncMain
from sync import GetDeezerInfo
from tiktok import tiktokVideo

load_dotenv('.env')

APP_ID = os.getenv('APP_ID')
SECRET = os.getenv('SECRET')
REDIRECT_URL = os.getenv('REDIRECT_URL')
PERMS = "basic_access,manage_library,delete_library"

bot = discord.Bot()

# Message sent to user after sync
def syncReport(link,songsAdd,songsRemove,songFail):
  strAdds = 'All Synced 🔄'
  strRemove = 'All Synced 🔄'
  strFails = 'Nothing Failed :partying_face:'
  if len(songsAdd) > 0:
    strAdds = ''
    for songs in songsAdd:
      strAdds += "> {} - {} \n".format(songs.get('name'),songs.get('artist')[0])
  if len(songsRemove) > 0:
    strRemove = ''
    for songs in songsRemove:
      strRemove += "> {} - {} \n".format(songs.get('name'),songs.get('artist'))
  if len(songFail) > 0:
    strFails = ''
    for songs in songFail:
      strFails += "> {} - {} \n".format(songs.get('name'),songs.get('artist')[0])
  embedVar = discord.Embed(title="Sync Report", color=0x26f3f7)
  embedVar.add_field(name='{} Songs Added'.format(len(songsAdd)), value=strAdds, inline=False)
  embedVar.add_field(name='{} Songs Removed'.format(len(songsRemove)), value=strRemove, inline=False)
  embedVar.add_field(name='{} Songs Failed'.format(len(songFail)), value=strFails, inline=False)
  embedVar.add_field(name='Playlist Link', value=link, inline=False)
  return embedVar

# Message sent to user after convert
def convertReport(link,songsSuccess,songsFailed,lstSongsFailed,lstSongsLocal):
  strFails = 'Nothing Failed :partying_face:' 
  if len(lstSongsFailed) or len(lstSongsLocal) > 0:
    strFails = ''
    for songs in lstSongsFailed:
      strFails += "> {} - {} \n".format(songs.get('name'),songs.get('artist')[0])
    for songs in lstSongsLocal:
      strFails += "{} \n".format(songs)
    songsFailed += len(lstSongsLocal)
  embedVar = discord.Embed(title="Convert Report", color=0x26f3f7)
  embedVar.add_field(name='Successful Tracks', value="{} Tracks Converted".format(songsSuccess), inline=False)
  embedVar.add_field(name='{} Failed Tracks'.format(songsFailed) , value=strFails, inline=False)
  embedVar.add_field(name='Playlist Link', value="{}".format(link), inline=False)
  return embedVar

# Message sent to user after error
def userReport(errorTitle,errorName,errorMsg):
  embedError = discord.Embed(title=errorTitle, color=discord.Colour.red())
  embedError.add_field(name=errorName,value=errorMsg,inline=False)
  return embedError
  
@bot.event
async def on_ready():
    """Sends messages once bot connects and sets bot activity.
    Also starts any background tasks"""
    print(f'{bot.user} has connected to Discord!')
    syncCheck.start()

@tasks.loop(minutes=1)
async def syncCheck():
  data = dataStorage.getSyncList()
  for dic in data:
    if dic.get('sync') != None:
      for syncInfo in dic.get('sync'):
        savedTime = datetime.strptime(str(syncInfo[2]), "%m/%d/%Y- %H:%M:%S")
        currentTime = datetime.now()
        if savedTime.time() <= currentTime.time() and savedTime.date() <= currentTime.date() or savedTime.date() < currentTime.date():
          nxtTime = currentTime + timedelta(hours=int(syncInfo[3]))
          token = dataStorage.ErrorInfo(dic.get('user'))
          if token[0]:
            token = token[1]
            spotifylink = syncInfo[0]
            deezerlink = syncInfo[1]
            resultSync = syncMain(deezerlink,spotifylink,token)
            if resultSync[0] and len(resultSync[2]) > 0 or len(resultSync[3]) > 0 or len(resultSync[4]) > 0:
              reportEmbed = syncReport(resultSync[1],resultSync[2],resultSync[3],resultSync[4])
              userDM = await bot.fetch_user(int(dic.get('user')))
              await userDM.send(embed=reportEmbed)
          syncInfo[2] = nxtTime.strftime("%m/%d/%Y- %H:%M:%S")
          dataStorage.setNewTime(data)

@bot.slash_command(name='help', description='Help')
async def help(ctx):
  embedHelp = discord.Embed(title="Help", color=0x6721ac)
  embedHelp.add_field(name="TikTok (Prone to not work)", value="Sends the video given a TikTok link.", inline=False)
  embedHelp.add_field(name="Login", value="Login to Deezer using command. Required to use features below.", inline=False)
  embedHelp.add_field(name="Convert", value="Given Spotify playlist link converts to a Deezer playlist", inline=False)
  embedHelp.add_field(name="Sync", value="Given Spotify and Deezer playlist link and an interval hour, syncs the Deezer playlist with Spotify playlist.", inline=False)
  embedHelp.add_field(name="SyncList", value="Shows list of synced playlists.", inline=False)
  embedHelp.add_field(name="Remove Sync", value="Removes synced playlist from list given its index.", inline=False)
  await ctx.respond(embed=embedHelp)

@bot.slash_command(name='tiktok', description='Display TikTok Videos From Link')
async def tiktok(ctx, link: str):
  try:
    await ctx.defer()
    result = tiktokVideo(link)
  except:
    embedError = discord.Embed(title="Error", color=discord.Colour.red())
    embedError.add_field(name="Unexpected Error", value="Report bugs via Github", inline=True)
    await ctx.respond(embed=embedError)
  if result[0]:
    with open('video.mp4', 'rb') as f:
      video = discord.File(f)
      await ctx.respond(file=video)
  else:
    embedError = discord.Embed(title="Error", color=discord.Colour.red())
    embedError.add_field(name='{}'.format(result[1]), value='{}'.format(result[2]), inline=True)
    await ctx.respond(embed=embedError)

@bot.slash_command(name='login', description='Login to the Deezer App')
async def login(ctx):
  userLogin = (dataStorage.ErrorInfo(str(ctx.author.id)))
  if userLogin[0]:
    await ctx.respond('Successfully Logged In')
  else:
    try:
      await ctx.author.send("https://connect.deezer.com/oauth/auth.php?app_id={}&redirect_uri={}&perms={}".format(APP_ID,REDIRECT_URL,PERMS)+ '\n Enter the redirect link after authenticating')
      await ctx.respond('Follow instructions in your DM.')
    except:
      await ctx.respond('DM Failed. Please Check Pirvacy Settings.')
      pass

@bot.slash_command(name='convert', description='Convert Spotify Playlist to Deezer Playlist')
async def convert(ctx, link: str):
  userLogin = (dataStorage.ErrorInfo(str(ctx.author.id)))
  if userLogin[0]:
    userInputLink = link.strip()
    if userInputLink[:34] == "https://open.spotify.com/playlist/":
      spotifyPlaylistID = userInputLink[34:56]
      playlistInfo = GetPlaylistInfo(spotifyPlaylistID)
      if playlistInfo[0]:
        playlistInfo = playlistInfo[1]
        embedVar = discord.Embed(title="Converting Playlist To Deezer", color=discord.Colour.green())
        embedVar.set_thumbnail(url=playlistInfo.get('cover'))
        embedVar.add_field(name='Name', value=playlistInfo.get('name'), inline=True)
        embedVar.add_field(name='Tracks', value=str(playlistInfo.get('total')), inline=True)
        embedVar.add_field(name='Owner', value=playlistInfo.get('owner'), inline=True)
        await ctx.respond(embed=embedVar)
        convertInfo = convertMain(spotifyPlaylistID,userLogin[1])
        if convertInfo[0]:
          reportEmbed = convertReport(convertInfo[1],convertInfo[2],convertInfo[3],convertInfo[4],convertInfo[5])
          await ctx.respond(embed=reportEmbed)
        else:
          embedFailed = userReport("Converting Failed",convertInfo[1],"Try another playlist.")
          await ctx.respond(embed=embedFailed)
      else:
        embedError = userReport("Convert Error",str(playlistInfo[1]).capitalize(),"Enter Spotify Playlist Link (ex. https://open.spotify.com/playlist/...)")
        await ctx.respond(embed=embedError)
    else:
        embedError = userReport("Convert Error","Invalid Spotify Playlist Link","Enter Spotify Playlist Link (ex. https://open.spotify.com/playlist/...)")
        await ctx.respond(embed=embedError)
  else:
    embedError = userReport("Login Error","User Not Registered","Use /login to login and use these features")
    await ctx.respond(embed=embedError)

@bot.slash_command(name='sync', description='Sync Spotify Playlist & Deezer Playlist at Intervals (Use 0 to Not Sync Later)')
async def sync(ctx, spotifylink: str, deezerlink: str, intervalhour: int):
  userLogin = dataStorage.ErrorInfo(str(ctx.author.id))
  if userLogin[0]:
    sptfyInfo = GetPlaylistInfo(spotifylink)
    dzrInfo = GetDeezerInfo(deezerlink)
    if sptfyInfo[0] and dzrInfo[0]:
      embedVar = discord.Embed(title="Syncing Playlist With Deezer Playlist", color=discord.Colour.green())
      embedVar.set_thumbnail(url=sptfyInfo[1].get('cover'))
      embedVar.add_field(name='Spotify Name', value=sptfyInfo[1].get('name'), inline=True)
      embedVar.add_field(name='Tracks', value=str(sptfyInfo[1].get('total')), inline=True)
      embedVar.add_field(name='Owner', value=sptfyInfo[1].get('owner'), inline=True)
      embedVar.add_field(name='Deezer Name', value=dzrInfo[1].get('title'), inline=True)
      embedVar.add_field(name='Tracks', value=str(dzrInfo[1].get('nb_tracks')), inline=True)
      embedVar.add_field(name='Owner', value=str(dzrInfo[1].get('creator').get('name')), inline=True)
      await ctx.respond(embed=embedVar)
      resultSync = syncMain(deezerlink,spotifylink,userLogin[1])
      if resultSync[0]:
        reportEmbed = syncReport(resultSync[1],resultSync[2],resultSync[3],resultSync[4])
        await ctx.respond(embed=reportEmbed)
        if intervalhour > 0:
          nextTime = datetime.now() + timedelta(hours=intervalhour)
          dataStorage.addSync(str(ctx.author.id),spotifylink,deezerlink,nextTime,intervalhour)
      else:
        print("sync failed")
    else:
      embedError = discord.Embed(title='Sync Error', color=discord.Colour.red())
      embedError.add_field(name="Invalid Playlist Links",value="Enter Spotify Playlist Link (ex. https://open.spotify.com/playlist/...) \n Enter Deezer Playlist Link (ex. https://www.deezer.com/en/playlist/...)",inline=False)
      await ctx.respond(embed=embedError)
  else:
    embedError = userReport("Login Error","User Not Registered","Use /login to login and use these features")
    await ctx.respond(embed=embedError)

@bot.slash_command(name='synclist', description='List of Syncs')
async def synclist(ctx):
  lstSync = dataStorage.syncList(str(ctx.author.id))
  if lstSync[0]:
    embedList = discord.Embed(title="List of Syncing Playlists", color=discord.Colour.green())
    count = 0
    for syncInfo in lstSync[1]:
      spotifylink = syncInfo[0]
      deezerlink = syncInfo[1]
      nxtSync = syncInfo[2]
      nxtSync=nxtSync.replace('"','')
      nxtSync = datetime.strptime(nxtSync, "%m/%d/%Y- %H:%M:%S")
      sptfyInfo = GetPlaylistInfo(spotifylink)
      dzrInfo = GetDeezerInfo(deezerlink)
      sptfyTitle = sptfyInfo[1].get('name')
      dzrTitle = dzrInfo[1].get('title')
      count +=1
      currTime = datetime.now()
      dd = nxtSync - currTime 
      embedList.add_field(name="{}. {} → {}".format(str(count),str(sptfyTitle),str(dzrTitle)),value="[Spotify Link]({}) → [Deezer Link]({}) \n Next Sync: {}".format(spotifylink,deezerlink,str(dd)[:-7]),inline=False)
    if len(lstSync[1]) == 0:
      embedList.add_field(name="No Playlists To Sync",value="Use /sync to start syncing a playlist.")
    await ctx.respond(embed=embedList)
  else:
    embedError = userReport("SyncList Error","No Entry",lstSync[1])
    await ctx.respond(embed=embedError)

@bot.slash_command(name='removesync', description='Remove a Synced Playlist')
async def removesync(ctx, index: int):
  userExist = dataStorage.checkUser(str(ctx.author.id))
  syncExist = dataStorage.syncList(str(ctx.author.id))
  if userExist and syncExist[0]:
    lstSync = syncExist[1]
    try:
      spotifylink = lstSync[index-1][0]
      deezerlink = lstSync[index-1][1]
      sptfyInfo = GetPlaylistInfo(spotifylink)
      dzrInfo = GetDeezerInfo(deezerlink)
      sptfyTitle = sptfyInfo[1].get('name')
      dzrTitle = dzrInfo[1].get('title')
      dataStorage.updateSync(str(ctx.author.id),index-1)
      embedRemove = discord.Embed(title='Removed Sync', color=discord.Colour.green())
      embedRemove.add_field(name="{} → {}".format(str(sptfyTitle),str(dzrTitle)),value="[Spotify Link]({}) → [Deezer Link]({})".format(spotifylink,deezerlink),inline=False)
      await ctx.respond(embed=embedRemove)
    except:
      embedRemove = userReport("Remove Sync","No Sync In Index","Use /synclist to show list of syncs")
      await ctx.respond(embed=embedRemove)
  else:
    embedError = userReport("Login Error","User Not Registered","Use /login to login and use these features")
    await ctx.respond(embed=embedError)
    
@bot.event
async def on_message(ctx):
  userDM = ctx.content
  userID = ctx.author.id
  if ctx.guild is None and not ctx.author.bot:
    if userDM[:36] == 'http://localhost:5000/callback?code=':
      code = userDM[36:]
      response = requests.get("https://connect.deezer.com/oauth/access_token.php?app_id={}&secret={}&code={}".format(APP_ID,SECRET,code))
      deezerToken = response.text
      end = deezerToken.find("expires")
      deezerToken = deezerToken[13:end-1]
      result = TestOauth(deezerToken)
      if result:
        dataStorage.storeInfo(userID,deezerToken)
        await ctx.author.send('Successfully Logged In')
      else:
        await ctx.author.send('Failed To Verify Token')

bot.run(os.getenv('TOKEN'))