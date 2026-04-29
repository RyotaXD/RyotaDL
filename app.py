import os
import yt_dlp
from flask import Flask, render_template, request, jsonify, Response
from urllib.parse import unquote

app = Flask(__name__)
TEMP_FOLDER = "/tmp"

# Konfigurasi YTDL yang mirip dengan skrip you.py
YTDL_CFG = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch5', # Sesuai dengan you.py
    'nocheckcertificate': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query', '').strip()
    try:
        with yt_dlp.YoutubeDL(YTDL_CFG) as ydl:
            # Mengambil 5 hasil seperti di skrip you.py
            info = ydl.extract_info(f"ytsearch5:{query}", download=False)
            results = [{
                'title': e.get('title', 'Unknown'),
                'url': e.get('webpage_url'),
                'id': e.get('id'),
                'thumbnail': f"https://img.youtube.com/vi/{e.get('id')}/mqdefault.jpg",
                'uploader': e.get('uploader', 'Unknown'),
                'duration': e.get('duration_string', '0:00')
            } for e in info['entries']]
            return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/play', methods=['POST'])
def play():
    data = request.json
    url = data.get('url')
    # Path folder /tmp untuk Render
    outtmpl = os.path.join(TEMP_FOLDER, 'audio_%(id)s.%(ext)s')
    
    opts = YTDL_CFG.copy()
    opts['outtmpl'] = outtmpl

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return jsonify({
                'success': True,
                'filename': os.path.basename(filename),
                'title': info.get('title')
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stream/<filename>')
def stream(filename):
    filepath = os.path.join(TEMP_FOLDER, unquote(filename))
    if not os.path.exists(filepath):
        return "Not Found", 404
    
    def generate():
        with open(filepath, 'rb') as f:
            while chunk := f.read(1024*512):
                yield chunk
    
    return Response(generate(), mimetype='audio/mpeg')

if __name__ == '__main__':
    app.run()
