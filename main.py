from flask import Flask, render_template, request, redirect, url_for, send_from_directory, abort, flash
import yt_dlp
import os
import subprocess
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for flashing messages

DOWNLOAD_FOLDER = 'downloads' # The folder where the webm and mp3 files will be downloaded (after conversion)
FILES_LIST = 'downloaded_files.json' # The json file where the names of the downloaded files are saved, so you will have a history of what you downloaded
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
downloaded_files = []

# Function to save downloaded files list to a JSON file
def save_downloaded_files():
    with open(FILES_LIST, 'w') as f:
        json.dump(downloaded_files, f)

# Function to load downloaded files list from a JSON file
def load_downloaded_files():
    global downloaded_files
    if os.path.exists(FILES_LIST):
        with open(FILES_LIST, 'r') as f:
            downloaded_files = json.load(f)

# Function to delete all downloaded files
def delete_all_files():
    global downloaded_files
    for filename in downloaded_files:
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    downloaded_files = []
    save_downloaded_files()
    # Delete the downloaded_files.json file
    if os.path.exists(FILES_LIST):
        os.remove(FILES_LIST)

@app.route('/')
def index():
    load_downloaded_files()
    return render_template('index.html', files=downloaded_files)

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    convert_to_mp3 = 'convert' in request.form

    if not url:
        return redirect(url_for('index'))

    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(url, download=True)
        
        if 'entries' in result:
            # It's a playlist
            for entry in result['entries']:
                filename = ydl.prepare_filename(entry)
                downloaded_files.append(os.path.basename(filename))
                if convert_to_mp3:
                    mp3_filename = os.path.splitext(filename)[0] + '.mp3'
                    subprocess.run([
                        'ffmpeg', '-i', filename, '-b:a', '320k', mp3_filename
                    ])
                    downloaded_files.append(os.path.basename(mp3_filename))
                    os.remove(filename)  # Delete the original file
                    downloaded_files.remove(os.path.basename(filename))  # Remove the file from the list
        else:
            # It's a single video
            filename = ydl.prepare_filename(result)
            downloaded_files.append(os.path.basename(filename))
            if convert_to_mp3:
                mp3_filename = os.path.splitext(filename)[0] + '.mp3'
                subprocess.run([
                    'ffmpeg', '-i', filename, '-b:a', '320k', mp3_filename
                ])
                downloaded_files.append(os.path.basename(mp3_filename))
                os.remove(filename)  # Delete the original file
                downloaded_files.remove(os.path.basename(filename))  # Remove the file from the list

    save_downloaded_files()  # Save the list after downloading
    return redirect(url_for('index'))

@app.route('/delete_files', methods=['POST'])
def delete_files():
    delete_all_files()
    flash('Files deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/files/<path:filename>')
def files(filename):
    try:
        # Using safe_join to ensure the path is within the directory
        safe_path = os.path.join(DOWNLOAD_FOLDER, filename)
        if not os.path.isfile(safe_path):
            print(f"File not found: {safe_path}")
            abort(404)
        return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)
    except Exception as e:
        print(f"Error: {e}")
        abort(404)

if __name__ == '__main__':
    load_downloaded_files()  # Load the list when the app starts
    app.run(host='0.0.0.0', port = 5000, debug=True) #here you set the host and port on which you can access the web page, set 0.0.0.0, if the script is installed on a server in the LAN network, if the script is installed on a PC / laptop then set the host 127.0.0.1, and for the port, set what you want or what port you have, unused
