import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog  # Import simpledialog for custom dialogs
from application.services import MusicService
import pygame
import subprocess as sp
from ffplay_audio_previewer import FFPLAY_AudioPreviewer
import random

try:
    from moviepy import VideoFileClip
    print("moviepy imported successfully")
except ImportError as e:
    VideoFileClip = None
    messagebox.showerror("Import Error", f"Failed to import moviepy. Please ensure moviepy is installed. Error: {e}")
    print(f"Failed to import moviepy: {e}")

class PlaylistNameDialog(simpledialog.Dialog):
    def body(self, master):
        tk.Label(master, text="Enter playlist name:").grid(row=0)
        self.playlist_name_entry = tk.Entry(master)
        self.playlist_name_entry.grid(row=0, column=1)
        return self.playlist_name_entry

    def apply(self):
        self.playlist_name = self.playlist_name_entry.get()

class RadiantBeats:
    def __init__(self, root, connection):
        self.root = root
        self.connection = connection
        
        self.root = root
        self.root.title("Radiant Beats")
        self.root.geometry("600x600")

        self.music_service = MusicService()
        self.current_song_index = 0
        self.current_video = None
        self.audio_previewer = FFPLAY_AudioPreviewer()
        self.shuffle = False
        self.repeat = False
        self.paused = False

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

        self.pause_button = tk.Button(self.root, text="Pause", command=self.pause_song)
        self.pause_button.pack()

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

        self.playlist_var = tk.StringVar(self.root)
        self.playlist_var.set("All Songs")  # Default value
        self.playlist_dropdown = tk.OptionMenu(self.root, self.playlist_var, "All Songs", "Favorites")
        self.playlist_dropdown.pack()

        self.load_playlist_button = tk.Button(self.root, text="Load Playlist", command=self.load_selected_playlist)
        self.load_playlist_button.pack()

        self.update_playlist_dropdown()  # Update the dropdown with available playlists

        self.status_label = tk.Label(self.root, text="00:00")
        self.status_label.pack()

        self.position_slider = tk.Scale(self.root, from_=0, to=100, orient=tk.HORIZONTAL, command=self.set_position)
        self.position_slider.pack(fill=tk.X)

        self.shuffle_button = tk.Button(self.root, text="Shuffle", command=self.toggle_shuffle)
        self.shuffle_button.pack()

        self.repeat_button = tk.Button(self.root, text="Repeat", command=self.toggle_repeat)
        self.repeat_button.pack()

    def update_playlist_dropdown(self):
        menu = self.playlist_dropdown["menu"]
        menu.delete(0, "end")
        playlists = self.music_service.get_all_playlists()
        menu.add_command(label="All Songs", command=lambda: self.playlist_var.set("All Songs"))
        menu.add_command(label="Favorites", command=lambda: self.playlist_var.set("Favorites"))
        for playlist in playlists:
            menu.add_command(label=playlist.name, command=lambda name=playlist.name: self.playlist_var.set(name))

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
                self.paused = False
                self.update_status()
                self.set_slider_max(selected_song)
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

    def pause_song(self):
        if not self.paused:
            pygame.mixer.music.pause()
            self.paused = True
        else:
            pygame.mixer.music.unpause()
            self.paused = False

    def stop_song(self):
        pygame.mixer.music.stop()
        self.paused = False
        if self.current_video:
            self.current_video.close()
            self.current_video = None

    def add_to_playlist(self):
        selected_song = self.song_listbox.get(tk.ACTIVE)
        if selected_song:
            dialog = PlaylistNameDialog(self.root)
            playlist_name = dialog.playlist_name
            if playlist_name:
                self.music_service.create_playlist(playlist_name)
                self.music_service.add_song_to_playlist(playlist_name, selected_song)
                self.update_playlist_dropdown()  # Update the dropdown with the new playlist
            else:
                existing_playlist = self.playlist_var.get()
                if existing_playlist != "All Songs" and existing_playlist != "Favorites":
                    self.music_service.add_song_to_playlist(existing_playlist, selected_song)

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

    def load_selected_playlist(self):
        selected_playlist = self.playlist_var.get()
        if selected_playlist == "All Songs":
            self.refresh_songs()
        elif selected_playlist == "Favorites":
            self.load_favorites()
        else:
            self.load_playlist(selected_playlist)

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

    def update_status(self):
        if pygame.mixer.music.get_busy():
            current_time = pygame.mixer.music.get_pos() // 1000
            minutes = current_time // 60
            seconds = current_time % 60
            self.status_label.config(text=f"{minutes:02}:{seconds:02}")
            self.position_slider.set(current_time)
            self.root.after(500, self.update_status)  # Update every 500ms for better responsiveness
        else:
            if not self.paused:
                if self.repeat:
                    self.play_song()
                else:
                    self.play_next_song()

    def set_position(self, value):
        pygame.mixer.music.rewind()
        pygame.mixer.music.set_pos(int(value))

    def set_slider_max(self, song_path):
        song_length = pygame.mixer.Sound(song_path).get_length()
        self.position_slider.config(to=int(song_length))

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        self.shuffle_button.config(relief=tk.SUNKEN if self.shuffle else tk.RAISED)

    def toggle_repeat(self):
        self.repeat = not self.repeat
        self.repeat_button.config(relief=tk.SUNKEN if self.repeat else tk.RAISED)

    def play_next_song(self):
        if self.shuffle:
            self.current_song_index = random.randint(0, self.song_listbox.size() - 1)
        else:
            self.current_song_index = (self.current_song_index + 1) % self.song_listbox.size()
        self.song_listbox.select_clear(0, tk.END)
        self.song_listbox.select_set(self.current_song_index)
        self.song_listbox.event_generate("<<ListboxSelect>>")
        self.play_song()

if __name__ == "__main__":
    root = tk.Tk()
    connection = create_connection()  # Ensure the connection is created
    app = RadiantBeats(root, connection)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
