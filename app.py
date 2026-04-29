import os
from flask import Flask, render_template, request, jsonify, Response
import yt_dlp
from urllib.parse import unquote

app = Flask(__name__)

# Gunakan folder /tmp agar aman di Render
TEMP_FOLDER = "/tmp"
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query', '')
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
    outtmpl = os.path.join(TEMP_FOLDER, 'audio.%(ext)s')
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': outtmpl,
        'quiet': True,
        'noplaylist': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return jsonify({'success': True, 'filename': os.path.basename(filename), 'title': info.get('title')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stream/<filename>')
def stream(filename):
    filepath = os.path.join(TEMP_FOLDER, filename)
    if not os.path.exists(filepath):
        return "Not Found", 404
    
    def generate():
        with open(filepath, 'rb') as f:
            while chunk := f.read(1024*512):
                yield chunk
    return Response(generate(), mimetype='audio/mpeg')

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
    app.run()
