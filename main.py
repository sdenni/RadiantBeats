import os
import tkinter as tk
from tkinter import filedialog, messagebox
from database import create_connection
import pygame
import subprocess as sp  # Add subprocess import

try:
    from moviepy import VideoFileClip
    print("moviepy imported successfully")  # Debug print
except ImportError as e:
    VideoFileClip = None
    messagebox.showerror("Import Error", f"Failed to import moviepy. Please ensure moviepy is installed. Error: {e}")
    print(f"Failed to import moviepy: {e}")  # Debug print

class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Player")
        self.root.geometry("600x400")

        self.playlist = []
        self.current_song_index = 0
        self.current_video = None

        pygame.mixer.init()

        self.ffplay_path = self.find_ffplay()  # Add ffplay path initialization

        self.create_widgets()

    def create_widgets(self):
        self.add_folder_button = tk.Button(self.root, text="Add Folder", command=self.add_folder)
        self.add_folder_button.pack()

        self.refresh_button = tk.Button(self.root, text="Refresh", command=self.refresh_songs)
        self.refresh_button.pack()

        self.play_button = tk.Button(self.root, text="Play", command=self.play_song)
        self.play_button.pack()

        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_song)
        self.stop_button.pack()

        self.song_listbox = tk.Listbox(self.root)
        self.song_listbox.pack(fill=tk.BOTH, expand=True)

        self.add_to_playlist_button = tk.Button(self.root, text="Add to Playlist", command=self.add_to_playlist)
        self.add_to_playlist_button.pack()

        self.add_to_favorites_button = tk.Button(self.root, text="Add to Favorites", command=self.add_to_favorites)
        self.add_to_favorites_button.pack()

    def add_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.scan_folder(folder_path)

    def scan_folder(self, folder_path):
        conn = create_connection()
        cursor = conn.cursor()
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".mp3") or file.endswith(".mp4"):
                    file_path = os.path.join(root, file)
                    cursor.execute("INSERT INTO songs (path) VALUES (?)", (file_path,))
        conn.commit()
        conn.close()
        self.refresh_songs()

    def refresh_songs(self):
        self.song_listbox.delete(0, tk.END)
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT path FROM songs")
        songs = cursor.fetchall()
        for song in songs:
            self.song_listbox.insert(tk.END, song[0])
        conn.close()

    def find_ffplay(self):
        """Find the ffplay executable in the system PATH."""
        for path in os.environ["PATH"].split(os.pathsep):
            ffplay_path = os.path.join(path, "ffplay.exe")
            if os.path.isfile(ffplay_path) and os.access(ffplay_path, os.X_OK):
                return ffplay_path
        return None

    def play_song(self):
        selected_song = self.song_listbox.get(tk.ACTIVE)
        if selected_song:
            print(f"Selected song: {selected_song}")  # Debug print
            if selected_song.endswith(".mp3"):
                pygame.mixer.music.load(selected_song)
                pygame.mixer.music.play()
            elif selected_song.endswith(".mp4"):
                if VideoFileClip:
                    try:
                        print("Loading video...")  # Debug print
                        print(selected_song)  # Debug print
                        self.current_video = VideoFileClip(selected_song)
                        print("Playing video...")  # Debug print
                        self.current_video.preview()
                    except Exception as e:
                        print(f"Error loading video: {e}")  # Debug print
                        messagebox.showerror("Playback Error", f"Failed to play video: {e}")
                else:
                    messagebox.showerror("Import Error", "moviepy is not available. Please ensure moviepy is installed.")
            elif selected_song.endswith(".wav"):
                if self.ffplay_path:
                    try:
                        print("Playing audio with ffplay...")  # Debug print
                        sp.Popen([f'"{self.ffplay_path}"', "-autoexit", f'"{selected_song}"'], shell=True)
                    except Exception as e:
                        print(f"Error playing audio: {e}")  # Debug print
                        messagebox.showerror("Playback Error", f"Failed to play audio: {e}")
                else:
                    messagebox.showerror("Playback Error", "ffplay is not available. Please ensure ffplay is installed and in your PATH.")

    def stop_song(self):
        pygame.mixer.music.stop()
        if self.current_video:
            self.current_video.close()
            self.current_video = None

    def add_to_playlist(self):
        selected_song = self.song_listbox.get(tk.ACTIVE)
        if selected_song:
            playlist_name = filedialog.askstring("Playlist Name", "Enter playlist name:")
            if playlist_name:
                conn = create_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO playlists (name) VALUES (?)", (playlist_name,))
                playlist_id = cursor.lastrowid
                cursor.execute("SELECT id FROM songs WHERE path = ?", (selected_song,))
                song_id = cursor.fetchone()[0]
                cursor.execute("INSERT INTO playlist_songs (playlist_id, song_id) VALUES (?, ?)", (playlist_id, song_id))
                conn.commit()
                conn.close()

    def add_to_favorites(self):
        selected_song = self.song_listbox.get(tk.ACTIVE)
        if selected_song:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM songs WHERE path = ?", (selected_song,))
            song_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO favorites (song_id) VALUES (?)", (song_id,))
            conn.commit()
            conn.close()

    def load_playlist(self, playlist_name):
        self.song_listbox.delete(0, tk.END)
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT songs.path FROM songs
            JOIN playlist_songs ON songs.id = playlist_songs.song_id
            JOIN playlists ON playlists.id = playlist_songs.playlist_id
            WHERE playlists.name = ?
        """, (playlist_name,))
        songs = cursor.fetchall()
        for song in songs:
            self.song_listbox.insert(tk.END, song[0])
        conn.close()

    def load_favorites(self):
        self.song_listbox.delete(0, tk.END)
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT songs.path FROM songs
            JOIN favorites ON songs.id = favorites.song_id
        """)
        songs = cursor.fetchall()
        for song in songs:
            self.song_listbox.insert(tk.END, song[0])
        conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayer(root)
    root.mainloop()