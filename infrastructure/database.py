import sqlite3
from domain.entities import Song, Playlist

class Database:
    def __init__(self):
        self.conn = self.create_connection()
        self.create_tables()  # Ensure tables are created

    def create_connection(self):
        return sqlite3.connect('music.db')

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY,
                path TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlist_songs (
                playlist_id INTEGER,
                song_id INTEGER,
                FOREIGN KEY (playlist_id) REFERENCES playlists (id),
                FOREIGN KEY (song_id) REFERENCES songs (id)
            )
        ''')
        self.conn.commit()

    def close_connection(self):
        if self.conn:
            self.conn.close()

    def insert_song(self, song):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO songs (path) VALUES (?)", (song.path,))
        self.conn.commit()

    def get_all_songs(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT path FROM songs")
        songs = cursor.fetchall()
        return [Song(path[0]) for path in songs]

    def insert_playlist(self, playlist):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO playlists (name) VALUES (?)", (playlist.name,))
        self.conn.commit()

    def get_playlist_by_name(self, name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM playlists WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            playlist = Playlist(row[1])
            cursor.execute("SELECT songs.path FROM songs JOIN playlist_songs ON songs.id = playlist_songs.song_id WHERE playlist_songs.playlist_id = ?", (row[0],))
            songs = cursor.fetchall()
            for song in songs:
                playlist.add_song(Song(song[0]))
            return playlist
        return None

    def get_song_by_path(self, path):
        cursor = self.conn.cursor()
        cursor.execute("SELECT path FROM songs WHERE path = ?", (path,))
        row = cursor.fetchone()
        if row:
            return Song(row[0])
        return None

    def update_playlist(self, playlist):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM playlist_songs WHERE playlist_id = (SELECT id FROM playlists WHERE name = ?)", (playlist.name,))
        for song in playlist.songs:
            cursor.execute("INSERT INTO playlist_songs (playlist_id, song_id) VALUES ((SELECT id FROM playlists WHERE name = ?), (SELECT id FROM songs WHERE path = ?))", (playlist.name, song.path))
        self.conn.commit()

def create_connection():
    return sqlite3.connect('music.db')
