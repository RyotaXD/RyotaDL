import os
import yt_dlp
from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__)

# Konfigurasi YTDL untuk mengambil link stream saja
YTDL_CFG = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query', '').strip()
    try:
        with yt_dlp.YoutubeDL(YTDL_CFG) as ydl:
            # Mencari 5 hasil seperti di skrip you.py
            info = ydl.extract_info(f"ytsearch5:{query}", download=False)
            results = [{
                'title': e.get('title'),
                'url': e.get('webpage_url'),
                'id': e.get('id'),
                'thumbnail': f"https://img.youtube.com/vi/{e.get('id')}/mqdefault.jpg",
                'uploader': e.get('uploader'),
                'duration': e.get('duration_string')
            } for e in info['entries']]
            return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_stream_url', methods=['POST'])
def get_stream_url():
    video_url = request.json.get('url')
    try:
        with yt_dlp.YoutubeDL(YTDL_CFG) as ydl:
            # Hanya ekstrak info, JANGAN download
            info = ydl.extract_info(video_url, download=False)
            # Ambil URL stream audio mentah
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
