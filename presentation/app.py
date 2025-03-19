import os
import tkinter as tk
from tkinter import filedialog, messagebox
from application.services import MusicService
import pygame
import subprocess as sp
from ffplay_audio_previewer import FFPLAY_AudioPreviewer

try:
    from moviepy import VideoFileClip
    print("moviepy imported successfully")
except ImportError as e:
    VideoFileClip = None
    messagebox.showerror("Import Error", f"Failed to import moviepy. Please ensure moviepy is installed. Error: {e}")
    print(f"Failed to import moviepy: {e}")

class RadiantBeats:
    def __init__(self, root, connection):
        self.root = root
        self.connection = connection
        
        self.root = root
        self.root.title("Radiant Beats")
        self.root.geometry("600x400")

        self.music_service = MusicService()
        self.current_song_index = 0
        self.current_video = None
        self.audio_previewer = FFPLAY_AudioPreviewer()

        pygame.mixer.init()

        self.ffplay_path = self.find_ffplay()

        self.create_widgets()
        self.refresh_songs()  

    def create_widgets(self):
        self.add_folder_button = tk.Button(self.root, text="Add Folder", command=self.add_folder)
        self.add_folder_button.pack()

        self.refresh_button = tk.Button(self.root, text="Refresh", command=self.refresh_songs)
        self.refresh_button.pack()

        self.play_button = tk.Button(self.root, text="Play", command=self.play_song)
        self.play_button.pack()

        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_song)
        self.stop_button.pack()

        self.delete_all_button = tk.Button(self.root, text="Delete All", command=self.delete_all_songs)
        self.delete_all_button.pack()

        self.delete_selected_button = tk.Button(self.root, text="Delete Selected", command=self.delete_selected_song)
        self.delete_selected_button.pack()

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
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".mp3") or file.endswith(".mp4"):
                    file_path = os.path.join(root, file)
                    self.music_service.add_song(file_path)
        self.refresh_songs()

    def refresh_songs(self):
        self.song_listbox.delete(0, tk.END)
        songs = self.music_service.get_all_songs()
        for song in songs:
            self.song_listbox.insert(tk.END, song.path)

    def find_ffplay(self):
        for path in os.environ["PATH"].split(os.pathsep):
            ffplay_path = os.path.join(path, "ffplay.exe")
            if os.path.isfile(ffplay_path) and os.access(ffplay_path, os.X_OK):
                return ffplay_path
        return None

    def play_song(self):
        selected_song = self.song_listbox.get(tk.ACTIVE)
        if selected_song:
            print(f"Selected song: {selected_song}")
            if selected_song.endswith(".mp3"):
                pygame.mixer.music.load(selected_song)
                pygame.mixer.music.play()
            elif selected_song.endswith(".mp4"):
                if VideoFileClip:
                    try:
                        print("Loading video...")
                        print(selected_song)
                        self.current_video = VideoFileClip(selected_song)
                        print("Playing video...")
                        self.current_video.preview()
                    except Exception as e:
                        print(f"Error loading video: {e}")
                        messagebox.showerror("Playback Error", f"Failed to play video: {e}")
                else:
                    messagebox.showerror("Import Error", "moviepy is not available. Please ensure moviepy is installed.")
            elif selected_song.endswith(".wav"):
                if self.ffplay_path:
                    try:
                        print("Playing audio with ffplay...")
                        sp.Popen([f'"{self.ffplay_path}"', "-autoexit", f'"{selected_song}"'], shell=True)
                    except Exception as e:
                        print(f"Error playing audio: {e}")
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
                self.music_service.create_playlist(playlist_name)
                self.music_service.add_song_to_playlist(playlist_name, selected_song)

    def add_to_favorites(self):
        selected_song = self.song_listbox.get(tk.ACTIVE)
        if selected_song:
            self.music_service.add_song_to_playlist("Favorites", selected_song)

    def load_playlist(self, playlist_name):
        self.song_listbox.delete(0, tk.END)
        playlist = self.music_service.get_playlist_by_name(playlist_name)
        if playlist:
            for song in playlist.songs:
                self.song_listbox.insert(tk.END, song.path)

    def load_favorites(self):
        self.load_playlist("Favorites")

    def delete_all_songs(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM songs")
            self.connection.commit()
            self.refresh_songs()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to delete all songs: {e}")

    def delete_selected_song(self):
        selected_song = self.song_listbox.get(tk.ACTIVE)
        if selected_song:
            try:
                cursor = self.connection.cursor()
                cursor.execute("DELETE FROM songs WHERE path = ?", (selected_song,))
                self.connection.commit()
                self.refresh_songs()
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to delete selected song: {e}")

    def on_closing(self):
        self.connection.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    connection = create_connection()  # Ensure the connection is created
    app = RadiantBeats(root, connection)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
