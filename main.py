import asyncio
import os
import time

import aiohttp
import requests
import vk_api
import vk_audio
import re


def auth(login, password):
    vk_session = vk_api.VkApi(login=login, password=password)
    vk_session.auth()
    vk = vk_audio.VkAudio(vk=vk_session)
    return vk

def get_valid_filename(s):
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)

def get_playlist(vk):
    data = vk.load()
    playlists = data.Playlists
    print(f'You have got {len(playlists)} playlists. They go as follows:')
    index = 1
    for index in range(len(playlists)+1):
        print(f'{index}. {playlists[index-1].title}')
    print('which one would you like to download?')
    # TODO добавить валидацию input'a
    index = int(input('Enter the corresponding index >>'))
    return playlists[index-1]


def get_songs(playlist):
    songs = playlist.Audios.load_audios()
    songs_to_download = []

    for song in songs:
        songs_to_download.append((song.artist, song.title, song.url))
    return songs_to_download


def download_song(artist, title, url):
    try:
        r = requests.get(url=url)
        if r.status_code == 200:
            data = r.content
            save_to_mp3(data, artist, title)
        else:
            print('Something went wrong! Status code returned:', r.status_code)
    except Exception as e:
        print('something went wrong:', e, url)


def save_to_mp3(data, artist, title):
    filename = f'{artist} - {title}.mp3'
    filename = get_valid_filename(filename)
    with open(filename, 'wb') as file:
        file.write(data)
        print(filename, 'was successfully downloaded.')


async def fetch_song(artist, title, url, session):
    try:
        async with session.get(url) as response:
            data = await response.read()
            save_to_mp3(data, artist, title)
    except Exception as e:
        print(url, e)

async def async_download(songs):
    tasks = []

    async with aiohttp.ClientSession() as session:
        for song in songs:
            try:
                artist, title, url = song
                task = fetch_song(artist, title, url, session)
                tasks.append(task)
            except Exception as e:
                print(url, e)
                continue

        await asyncio.gather(*tasks)


def main():
    print('Hi. In order to auth, please prvide your vk login and password')
    login = input('Login>>')
    password = input('Password>>')
    vk = auth(login=login, password=password)
    playlist = get_playlist(vk)
    songs = get_songs(playlist)
    print('you are about to download', len(songs), 'songs. ')
    input('this is a blocking func please do not press any button. its for science!')
    path = f'{playlist.title}/'
    if not os.path.exists(path):
        os.makedirs(path)
    os.chdir(path)
    while True:
        print('Press 1 for synchronous download and 2 for asynchronous download')
        ans = input('>>')
        if ans == '1':
            t0 = time.time()
            for song in songs:
                download_song(*song)
            print('Finished in', time.time() - t0, 'seconds')
        elif ans == '2':
            t0 = time.time()
            asyncio.run(async_download(songs))
            print('Finished in', time.time() - t0, 'seconds')
        else:
            print('invalid input. try again:')


if __name__ == '__main__':
    main()
