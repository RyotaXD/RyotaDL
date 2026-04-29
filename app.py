import os
import uuid
import yt_dlp
import subprocess
from flask import Flask, render_template, request, jsonify, url_for
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = Flask(__name__)
console = Console()

# Path penyimpanan di Termux
VAULT = 'static/downloads'
if not os.path.exists(VAULT): os.makedirs(VAULT)

def ryota_engine(url):
    uid = str(uuid.uuid4())[:6]
    filename = f'Ryee_{uid}.mp4'
    path_template = os.path.join(VAULT, filename)
    if "facebook.com/share/" in url:
        try:
            import requests
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            url = res.url
        except: pass

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
        'outtmpl': path_template,
        'nocheckcertificate': True,
        'external_downloader': 'aria2c',
        'external_downloader_args': ['-x', '16', '-s', '16', '-k', '1M'],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Referer': 'https://www.facebook.com/',
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown Title')
            table = Table(title="[bold green]Download Berhasil[/bold green]")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            table.add_row("Judul", title[:40])
            table.add_row("File", filename)
            console.print(table)
            return filename
    except Exception as e:
        console.print(f"[bold red]!! FUSION ERROR: {e}[/bold red]")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        console.print(f"[bold #a78bfa][*] Web Request Link:[/bold #a78bfa] [dim]{url}[/dim]\n")
        filename = ryota_engine(url)
        if filename:
            return jsonify({
                'success': True,
                'video_url': url_for('static', filename=f'downloads/{filename}')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Gagal! FB Memblokir Akses. Coba Mode Pesawat! ðŸ˜ˆ'
            })
    return render_template('index.html')

if __name__ == '__main__':
    app.run()
    
