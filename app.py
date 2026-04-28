from flask import Flask, render_template, request, jsonify, Response
import yt_dlp
import os
import time
from urllib.parse import unquote

app = Flask(__name__)

# Buat folder temp jika belum ada
TEMP_FOLDER = "temp_audio"
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

class MusicPlayer:
    def __init__(self):
        self.current_info = {}
    
    def search_youtube(self, query, max_results=10):
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'skip_download': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Menambahkan 'ytsearch' untuk hasil pencarian yang lebih baik
                info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
                return [{
                    'title': entry.get('title', 'Unknown'),
                    'id': entry['id'],
                    'duration': entry.get('duration', 0),
                    'uploader': entry.get('uploader', 'Unknown'),
                    'url': f"https://www.youtube.com/watch?v={entry['id']}",
                    'thumbnail': f"https://img.youtube.com/vi/{entry['id']}/mqdefault.jpg"
                } for entry in info['entries']]
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def get_audio_path(self, video_url):
        """Mengambil info dan mendownload audio tanpa FFmpeg"""
        timestamp = int(time.time())
        # Simpan di folder temp dengan nama yang aman
        outtmpl = os.path.join(TEMP_FOLDER, f'audio_{timestamp}.%(ext)s')
        
        ydl_opts = {
            'format': 'bestaudio/best', # Ambil format terbaik (biasanya m4a/webm)
            'outtmpl': outtmpl,
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                filename = ydl.prepare_filename(info)
                return True, info.get('title', 'Unknown'), filename
        except Exception as e:
            return False, str(e), None

player = MusicPlayer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'error': 'Masukkan judul lagu!'})
    results = player.search_youtube(query)
    return jsonify({'results': results})

@app.route('/play', methods=['POST'])
def play():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL tidak valid'}), 400
    
    # Pembersihan file lama (hapus file yang umurnya lebih dari 5 menit)
    now = time.time()
    for f in os.listdir(TEMP_FOLDER):
        fpath = os.path.join(TEMP_FOLDER, f)
        if os.stat(fpath).st_mtime < now - 300:
            try:
                os.remove(fpath)
            except:
                pass

    success, title, filepath = player.get_audio_path(url)
    
    if success:
        return jsonify({
            'success': True,
            'title': title,
            'filename': os.path.basename(filepath)
        })
    else:
        return jsonify({'error': "Gagal mengunduh audio: " + filepath}), 400

@app.route('/stream/<filename>')
def stream_audio(filename):
    filename = unquote(filename)
    filepath = os.path.join(TEMP_FOLDER, filename)
    
    if not os.path.exists(filepath):
        return "File not found", 404

    def generate():
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(1024 * 512) # 512KB chunks
                if not chunk:
                    break
                yield chunk
    
    # Mendeteksi mimetype berdasarkan ekstensi file
    mimetype = 'audio/mpeg'
    if filename.endswith('.m4a'): mimetype = 'audio/mp4'
    elif filename.endswith('.webm'): mimetype = 'audio/webm'

    return Response(
        generate(),
        mimetype=mimetype,
        headers={
            'Accept-Ranges': 'bytes',
            'Cache-Control': 'no-cache',
        }
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)                pass
    
    success, title, filename = player.download_audio(url)
    
    if success:
        return jsonify({
            'success': True,
            'title': title,
            'filename': os.path.basename(filename),
            'filepath': filename  # Send full path for streaming
        })
    else:
        return jsonify({'error': title}), 400

@app.route('/stream/<filename>')
def stream_audio(filename):
    """Stream audio file"""
    filename = unquote(filename)
    
    def generate():
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                while True:
                    data = f.read(1024 * 1024)  # 1MB chunks
                    if not data:
                        break
                    yield data
    
    return Response(
        generate(),
        mimetype='audio/mpeg',
        headers={
            'Content-Disposition': 'inline',
            'Accept-Ranges': 'bytes',
            'Cache-Control': 'no-cache',
        }
    )

@app.route('/status')
def status():
    return jsonify(player.current_info)

@app.route('/stop')
def stop():
    player.current_info = {}
    return jsonify({'status': 'stopped'})

@app.route('/cleanup')
def cleanup():
    count = 0
    for f in glob.glob('audio_*.mp3') + glob.glob('audio_*.m4a'):
        if os.path.exists(f):
            os.unlink(f)
            count += 1
    return jsonify({'cleaned': count})

if __name__ == '__main__':
    # Initial cleanup
    for f in glob.glob('audio_*'):
        if os.path.exists(f):
            os.unlink(f)
    print("🎵 Music Player Ready! http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
