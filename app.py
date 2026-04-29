import os
import yt_dlp
from flask import Flask, render_template, request, jsonify, Response
from urllib.parse import unquote

app = Flask(__name__)

# Gunakan folder /tmp karena Render memberikan izin tulis di sini
TEMP_FOLDER = "/tmp"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'results': []})
    
    ydl_opts = {'quiet': True, 'extract_flat': True, 'skip_download': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch10:{query}", download=False)
            results = [{
                'title': e.get('title', 'Unknown'),
                'url': f"https://www.youtube.com/watch?v={e['id']}",
                'id': e['id'],
                'thumbnail': f"https://img.youtube.com/vi/{e['id']}/mqdefault.jpg",
                'uploader': e.get('uploader', 'Unknown')
            } for e in info['entries']]
            return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/play', methods=['POST'])
def play():
    data = request.json
    url = data.get('url')
    # Nama file menggunakan ID video agar unik
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
            # Ambil hanya nama filenya saja, bukan path lengkapnya
            basename = os.path.basename(filename)
            return jsonify({
                'success': True,
                'filename': basename,
                'title': info.get('title')
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stream/<filename>')
def stream(filename):
    # Cari file di folder /tmp
    filepath = os.path.join(TEMP_FOLDER, unquote(filename))
    
    if not os.path.exists(filepath):
        return "File tidak ditemukan", 404
    
    def generate():
        with open(filepath, 'rb') as f:
            while chunk := f.read(1024*512):
                yield chunk
    
    # Tentukan tipe konten (mimetype)
    mimetype = 'audio/mpeg'
    if filename.endswith('.m4a'): mimetype = 'audio/mp4'
    elif filename.endswith('.webm'): mimetype = 'audio/webm'
    
    return Response(generate(), mimetype=mimetype)

if __name__ == '__main__':
    app.run()
