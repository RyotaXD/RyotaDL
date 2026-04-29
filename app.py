import os
import yt_dlp
from flask import Flask, render_template, request, jsonify, Response
from urllib.parse import unquote

app = Flask(__name__)
TEMP_FOLDER = "/tmp"

# Mengambil konfigurasi dari you.py dan menambah fitur anti-bot
YTDL_CFG = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch5',
    'nocheckcertificate': True,
    'extract_flat': True,
    'skip_download': True,
    # User-Agent sangat penting agar tidak muncul "Lagu tidak ditemukan"
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'results': []})
    
    try:
        with yt_dlp.YoutubeDL(YTDL_CFG) as ydl:
            # Mencari 5 hasil sesuai skrip you.py
            info = ydl.extract_info(f"ytsearch5:{query}", download=False)
            if not info or 'entries' not in info:
                return jsonify({'results': []})
                
            results = [{
                'title': e.get('title', 'Unknown'),
                'url': e.get('webpage_url') or f"https://www.youtube.com/watch?v={e.get('id')}",
                'id': e.get('id'),
                'thumbnail': f"https://img.youtube.com/vi/{e.get('id')}/mqdefault.jpg",
                'uploader': e.get('uploader', 'Unknown'),
                'duration': e.get('duration_string', '0:00')
            } for e in info['entries']]
            return jsonify({'results': results})
    except Exception as e:
        # Jika error, kirim pesan agar kita tahu penyebabnya di web
        return jsonify({'error': str(e), 'results': []}), 500

@app.route('/play', methods=['POST'])
def play():
    data = request.json
    url = data.get('url')
    outtmpl = os.path.join(TEMP_FOLDER, 'audio_%(id)s.%(ext)s')
    
    # Copy config pencarian untuk proses download
    play_opts = YTDL_CFG.copy()
    play_opts.update({
        'extract_flat': False,
        'skip_download': False,
        'outtmpl': outtmpl,
    })
    
    try:
        with yt_dlp.YoutubeDL(play_opts) as ydl:
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
        return "File Not Found", 404
    
    def generate():
        with open(filepath, 'rb') as f:
            while chunk := f.read(1024*512):
                yield chunk
    
    return Response(generate(), mimetype='audio/mpeg')

if __name__ == '__main__':
    app.run()
