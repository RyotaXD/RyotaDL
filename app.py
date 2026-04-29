import os
import yt_dlp
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Konfigurasi YTDL diperkuat (Anti-Blokir & Direct Stream)
YTDL_CFG = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'default_search': 'ytsearch5',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'referer': 'https://www.google.com/'
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
            # Mencari 5 hasil sesuai logika you.py
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
        return jsonify({'error': str(e), 'results': []}), 500

@app.route('/get_stream_url', methods=['POST'])
def get_stream_url():
    video_url = request.json.get('url')
    try:
        # Mengambil link audio langsung (Direct Streaming)
        with yt_dlp.YoutubeDL(YTDL_CFG) as ydl:
            info = ydl.extract_info(video_url, download=False)
            stream_url = info.get('url') 
            return jsonify({
                'success': True,
                'stream_url': stream_url,
                'title': info.get('title')
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
