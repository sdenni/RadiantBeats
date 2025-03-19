from domain.entities import Song, Playlist
from infrastructure.database import Database

class MusicService:
    def __init__(self):
        self.db = Database()

    def add_song(self, path):
        song = Song(path)
        self.db.insert_song(song)

    def get_all_songs(self):
        return self.db.get_all_songs()

    def create_playlist(self, name):
        playlist = Playlist(name)
        self.db.insert_playlist(playlist)

    def add_song_to_playlist(self, playlist_name, song_path):
        playlist = self.db.get_playlist_by_name(playlist_name)
        song = self.db.get_song_by_path(song_path)
        playlist.add_song(song)
        self.db.update_playlist(playlist)
