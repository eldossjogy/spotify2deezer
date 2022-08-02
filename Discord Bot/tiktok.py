import os
import ffmpeg
import requests
userAgent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36"

def download(url):
    r = requests.get(url) 
    with open("video.mp4",'wb') as f:
        f.write(r.content)
        
# src: https://stackoverflow.com/questions/64430805/how-to-compress-video-to-target-size-by-python
def compress_video(video_full_path, output_file_name, target_size):
  max_audio_bitrate = 256000
  probe = ffmpeg.probe(video_full_path)
  duration = float(probe['format']['duration'])
  target_total_bitrate = (target_size * 1024 * 8) / (1.073741824 * duration)
  print(target_total_bitrate)
  audio_bitrate = max_audio_bitrate
  video_bitrate = target_total_bitrate - audio_bitrate

  i = ffmpeg.input(video_full_path)
  ffmpeg.output(i, os.devnull,
                **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 1, 'f': 'mp4'}
                ).overwrite_output().run()
  ffmpeg.output(i, output_file_name,
                **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 2, 'c:a': 'aac', 'b:a': audio_bitrate}
                ).overwrite_output().run()
  try:
    os.remove("ffmpeg2pass-0.log")
    os.remove("ffmpeg2pass-0.log.mbtree")
  except: pass

def tiktokVideo(url):
    res = requests.get(url, headers={"user-agent": userAgent})
    strInfo = res.text 
    strIndexStart = strInfo.find("downloadAddr")
    strIndexEnd = strInfo.find("shareCover")
    link = strInfo[strIndexStart+15:strIndexEnd-3]
    link = link.replace("u002F","")
    link = link.replace("\\","/")
    print("Link: ",link)

    if link != '':
        download(link)
        size = int(os.stat('video.mp4').st_size )*0.000001
        if size > 8:
            compress_video('video.mp4', 'compress.mp4', 8 * 1000)
            os.remove("video.mp4")
            os.rename('compress.mp4', 'video.mp4')
            return(True,'Success')
        else:
            return(True,'Success')
    else:
        return(False,"Link Error","Provided link is invalid")
