from flask import Flask, render_template, jsonify
import threading
import gesture_control
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_presentation():
    try:
        # Create and start the thread for file selection and gesture control
        thread = threading.Thread(target=select_file_and_start)
        thread.daemon = True
        thread.start()
        return jsonify({"status": "success", "message": "Starting file selection..."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def select_file_and_start():
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # Create a new Tkinter window
        root = tk.Tk()
        root.withdraw()
        
        # Force the window to the foreground
        root.lift()
        root.attributes('-topmost', True)
        
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select PowerPoint Presentation",
            filetypes=[
                ("PowerPoint files", "*.ppt;*.pptx"),
                ("All files", "*.*")
            ]
        )
        
        # Clean up
        root.destroy()
        
        if file_path:
            print(f"Selected file: {file_path}")
            gesture_control.main(file_path)
        else:
            print("No file selected")
            
    except Exception as e:
        print(f"Error in file selection: {e}")

if __name__ == '__main__':
    app.run(debug=False)  # Set debug to False for production
