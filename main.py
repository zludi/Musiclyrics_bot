import telepot
import urllib3 as urllib
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from slugify import slugify
import codecs


path = '/home/user/Desktop/TelegramBot/Songs/'

database_path = '/home/user/Desktop/TelegramBot/Database/'
userdata_file_path = database_path + 'userdata.json'
songdata_file_path = database_path + 'songdata.json'
searchdata_file_path = database_path + 'searchdata.json'


TOKEN = '850124667:AAGTHBK716MdX5Lbbzv2rGd_1ZN0iw43PVM'


BASE_URL = 'http://www.youtubeinmp3.com/fetch/?format=JSON&video='


SUCCESS = 'Успешно'
FAIL = 'Неуспешно'
ERROR = 'Ошибка'
WELCOME_MSG = 'Чтобы начать, отправьте название песни. Чтобы получить текст песни отправьте сообщение в формате \'Текст <песня> - <исполнитель>\''
ONE_MB = 1000000
SONG_SENT_MESSAGE = 'Загрузна завершена'

BASE_LYRICS_URL = 'http://lyric-api.herokuapp.com/api/find/'
SLASH = '/'
LYRICS_ERROR_MSG = 'Текст не найден. Следуйте формату: Текст <песня> - <исполнитель>'
LYRICS_WAITING_MSG = 'Ищу текст. Подождите'


def handle(msg):
  print('Получено сообщение:', msg)
  username = msg['from']['first_name']
  chat_id = msg['from']['id']
  command = msg['text']


  print ('Им пользователя: ' + username)
  print ('Сообщение: %s' % command)

  if command == '/start':
     bot.sendMessage(chat_id, WELCOME_MSG)
     userdata = {'userid': msg['from']['id'],
                 'username': msg['from'],
     }
     savedata(userdata,userdata_file_path)
     return

  first_word = command.split(' ', 1)[0]
  print( 'Первое слово : ' + first_word)
  lower_first_word = first_word.lower()


  getlyrics = False
  if lower_first_word == 'текст' :
     getlyrics = True
     sendlyrics(msg)
  else:
     sendsong(msg)
     searchdata = {'userid': msg['from']['id'],
                   'username': msg['from'],
                   'searchterm': msg['text'],
                   'date' :  msg['date'],
                   'lyrics' : getlyrics
     }
     savedata(searchdata,searchdata_file_path)
  return

def sendlyrics(msg):
    username = msg['from']['first_name']
    chat_id = msg['from']['id']
    command = msg['text']

    bot.sendMessage(chat_id, LYRICS_WAITING_MSG)

    first_word = command.split(' ', 1)[0]
    s = command.split(first_word + ' ', 1)[1]
    p = s.index('-')
    song_name = s[:p]
    song_name = song_name.lower()

    if song_name[-1] == ' ' :
         song_name = song_name[0:-1].strip()
         print (song_name)

    artist_name = s[p+1:]
    artist_name = artist_name.lower()

    if artist_name[-1] == ' ' :
         artist_name = artist_name[0:-1]
         print( artist_name)

    artist_name = artist_name.replace(' ', '%20')
    song_name = song_name.replace(' ', '%20')

    print( artist_name)
    print (song_name)

    LYRICS_URL = BASE_LYRICS_URL + artist_name + SLASH + song_name
    print(LYRICS_URL)

    data = json.load(urllib.request.urlopen(LYRICS_URL))

    if data['lyric'] == '' :
         print('Текст не найден')
         bot.sendMessage(chat_id, LYRICS_ERROR_MSG)
    else :
         lyrics = data['lyric']
         print(lyrics)
         bot.sendMessage(chat_id, lyrics)
    return

def sendsong(msg):
  username = msg['from']['first_name']
  chat_id = msg['from']['id']
  command = msg['text']
  command = codecs.encode(command,'utf-8')
  bot.sendMessage(chat_id, username + ', песня отправляется...')


  query = urllib.quote(command)
  url = "https://www.youtube.com/results?search_query=" + query
  response = urllib.request.urlopen(url)


  html = response.read()
  soup = BeautifulSoup(html, "lxml")

  for vid in soup.findAll(attrs={'class':'yt-uix-tile-link'}):

        VIDEO_URL = 'https://www.youtube.com' + vid['href']

        JSON_URL = BASE_URL + VIDEO_URL
        print ('JSON URL : ' + JSON_URL)


        response = urllib.urlopen(JSON_URL)

        try:
             data = json.loads(response.read())
             print (data)


             if 'length' not in data:
                raise ValueError("Нет длительности")

                break
             if 'link' not in data:
                raise ValueError("Нет ссылки")

                break
             if 'title' not in data:
                raise ValueError("Нет названия")

                break

             length = data['length']

             DOWNLOAD_URL = data['link']

             title = data['title']


             title =  slugify(title)
             upload_file = path + title.lower() + '.mp3'


             if not (os.path.exists(upload_file)) :
                bot.sendMessage(chat_id, 'Загрузка началась.')

                downloadSong(DOWNLOAD_URL, upload_file)
                file_size = checkFileSize(upload_file)
                if (file_size < ONE_MB) :
                    os.remove(upload_file)

                    continue
                    bot.sendMessage(chat_id, SONG_SENT_MESSAGE)
                    print ('Загрузка завершена')
             else:
                    print ('Файл уже существует')




             audio = open(upload_file , 'rb')
             bot.sendAudio(chat_id, audio, length , '', title)


             songdata = {'searchterm': command,
                         'searchresult': title.lower(),
                         'date' :  msg['date']
             }
             savedata(songdata,songdata_file_path)
             break

        except ValueError:

             bot.sendMessage(chat_id, 'Песня не найдена. Попробуйте использовать другие данные')

             break

  return

def savedata(data, filename):
  msg  = json.dumps(data)
  with open(filename, 'a') as f:
    json.dump(msg, f)
    f.write(os.linesep)



def downloadSong(url, title):
  usock = urllib.request.urlopen(url)

  f = open(title, 'wb')
  try :
     file_size = int(usock.info().getheaders("Content-Length")[0])

  except IndexError:
     print ('Неизвестный размер файла')

  downloaded = 0
  block_size = 8192
  while True:
    buff = usock.read(block_size)
    if not buff:
        break

    downloaded = downloaded + len(buff)
    f.write(buff)
    #download_status = r"%3.2f%%" % (downloaded * 100.00 / file_size)
    #download_status = download_status + (len(download_status)+1) * chr(8)
    #print download_status,"done"

  f.close()

def checkFileSize(upload_file_path):
  b = os.path.getsize(upload_file_path)
  return b



bot = telepot.Bot(TOKEN)

#response = bot.getUpdates()

bot.getMe()
bot.notifyOnMessage(handle)
