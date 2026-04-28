from flask import Flask, render_template, request, jsonify, Response, send_file
import yt_dlp
import os
import glob
import time
from urllib.parse import unquote

app = Flask(__name__)

class MusicPlayer:
    def __init__(self):
        self.current_info = {}
        self.temp_files = []
    
    def search_youtube(self, query, max_results=10):
        """Cari lagu di YouTube"""
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
                return [{
                    'title': entry.get('title', 'Unknown'),
                    'id': entry['id'],
                    'duration': entry.get('duration', 0),
                    'uploader': entry.get('uploader', 'Unknown'),
                    'url': f"https://www.youtube.com/watch?v={entry['id']}",
                    'thumbnail': f"https://img.youtube.com/vi/{entry['id']}/mqdefault.jpg"
                } for entry in info['entries']]
        except:
            return []
    
    def download_audio(self, url):
        """Download audio dengan nama file sederhana"""
        timestamp = int(time.time())
        output_file = f"audio_{timestamp}.%(ext)s"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_file,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Unknown')
                
                # Cari file yang baru dibuat
                files = glob.glob(f"audio_{timestamp}.*")
                if files:
                    audio_file = files[0]
                    self.current_info = {
                        'title': title,
                        'file': audio_file,
                        'url': url
                    }
                    self.temp_files.append(audio_file)
                    return True, title, audio_file
                return False, "File not found", None
        except Exception as e:
            print(f"Download error: {e}")
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
    
    # Cleanup lama
    for f in player.temp_files[:5]:  # Keep last 5
        if os.path.exists(f):
            try:
                os.unlink(f)
                player.temp_files.remove(f)
            except:
                pass
    
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
