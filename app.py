import os
import yt_dlp
from flask import Flask, render_template, request, jsonify, Response
from urllib.parse import unquote

app = Flask(__name__)

# Menggunakan folder /tmp karena Render mengizinkan penulisan file di sini
TEMP_FOLDER = "/tmp"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'error': 'Masukkan judul lagu!'})
    
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Mencari 10 hasil dari YouTube
            info = ydl.extract_info(f"ytsearch10:{query}", download=False)
            results = [{
                'title': entry.get('title', 'Unknown'),
                'id': entry['id'],
                'uploader': entry.get('uploader', 'Unknown'),
                'url': f"https://www.youtube.com/watch?v={entry['id']}",
                'thumbnail': f"https://img.youtube.com/vi/{entry['id']}/mqdefault.jpg"
            } for entry in info['entries']]
            return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/play', methods=['POST'])
def play():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL tidak valid'}), 400
    
    # Simpan dengan ID video agar tidak bentrok
    outtmpl = os.path.join(TEMP_FOLDER, 'audio_%(id)s.%(ext)s')
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': outtmpl,
        'quiet': True,
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return jsonify({
                'success': True,
                'title': info.get('title', 'Unknown'),
                'filename': os.path.basename(filename)
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stream/<filename>')
def stream_audio(filename):
    filename = unquote(filename)
    filepath = os.path.join(TEMP_FOLDER, filename)
    
    if not os.path.exists(filepath):
        return "File tidak ditemukan", 404

    def generate():
        with open(filepath, 'rb') as f:
            while True:
                data = f.read(1024 * 512) # Kirim dalam potongan 512KB
                if not data:
                    break
                yield data
    
    return Response(
        generate(),
        mimetype='audio/mpeg',
        headers={
            'Accept-Ranges': 'bytes',
            'Cache-Control': 'no-cache',
        }
    )

if __name__ == '__main__':
    app.run()
