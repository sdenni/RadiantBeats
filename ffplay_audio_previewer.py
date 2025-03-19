import logging
import subprocess
import numpy as np

class FFPLAY_AudioPreviewer:
    def __init__(self):
        self.logfile = 'ffplay_audio_previewer.log'
        logging.basicConfig(filename=self.logfile, level=logging.ERROR)

    def preview_clip(self, clip):
        try:
            clip_path = clip.get_file_path()
            self.proc = subprocess.Popen(['ffplay', '-autoexit', clip_path], stdin=subprocess.PIPE)
            self.proc.wait()
        except Exception as e:
            logging.error(f"Error previewing clip: {e}")
            raise

    def get_frames_array(self, clip_path):
        return np.zeros((100, 100, 3), dtype=np.uint8)