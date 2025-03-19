import tkinter as tk
from infrastructure.database import create_connection  # Update the import to reflect the correct path
from presentation.app import RadiantBeats

if __name__ == "__main__":
    connection = create_connection()  # Call the create_connection function
    root = tk.Tk()
    app = RadiantBeats(root, connection)  # Pass the connection to RadiantBeats
    root.protocol("WM_DELETE_WINDOW", app.on_closing)  # Ensure connection is closed on exit
    root.mainloop()