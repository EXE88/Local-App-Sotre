import os
from flask import Flask, render_template, send_from_directory, url_for, request, redirect, flash, session, abort
import hashlib

app = Flask(__name__)
app.secret_key = 'CHANGEME-SET-A-STRONG-SECRET'

DOWNLOAD_FOLDER = 'downloadable'
ICON_FOLDER = 'downloadable_icon'
DEFAULT_ICON = 'icons/file.png'
ALLOWED_EXTENSIONS = {'.apk', '.exe', '.jpg', '.jpeg', '.png', '.zip', '.pdf', '.txt', '.mp3', '.mp4'}
ADMIN_PASSWORD = os.environ.get('ADMIN_UPLOAD_PASS', 'mystrongpassword')

IMAGE_EXTS = {'.jpg', '.jpeg', '.png'}

def allowed_file(filename):
    return '.' in filename and os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

@app.route('/')
def index():
    files = []
    for filename in os.listdir(DOWNLOAD_FOLDER):
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.isfile(filepath):
            size = os.path.getsize(filepath)
            name, ext = os.path.splitext(filename)
            ext = ext.lower()
            icon_url = None
            icon_size = 190
            if ext in IMAGE_EXTS:
                icon_url = url_for('downloadable', filename=filename)
                icon_size = 512
            else:
                for ext_icon in ['.png', '.jpg', '.jpeg']:
                    icon_path = f"{name}{ext_icon}"
                    full_icon_path = os.path.join(ICON_FOLDER, icon_path)
                    if os.path.isfile(full_icon_path):
                        icon_url = url_for('downloadable_icon', filename=icon_path)
                        break
                if not icon_url:
                    ext_icon_map = {
                        '.apk': 'icons/apk.png',
                        '.exe': 'icons/exe.png',
                        '.jpg': 'icons/image.png',
                        '.jpeg': 'icons/image.png',
                        '.png': 'icons/image.png',
                        '.zip': 'icons/zip.png',
                        '.pdf': 'icons/pdf.png',
                        '.txt': 'icons/txt.png',
                        '.mp3': 'icons/mp3.png',
                        '.mp4': 'icons/mp4.png',
                    }
                    icon_url = url_for('static', filename=ext_icon_map.get(ext, DEFAULT_ICON))
            files.append({
                'name': filename,
                'size': size,
                'url': url_for('downloadable', filename=filename),
                'icon': icon_url,
                'icon_size': icon_size
            })
    files.sort(key=lambda x: os.path.getctime(os.path.join(DOWNLOAD_FOLDER, x['name'])), reverse=True)
    return render_template('index.html', files=files)

@app.route('/downloadable/<path:filename>')
def downloadable(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

@app.route('/downloadable_icon/<path:filename>')
def downloadable_icon(filename):
    return send_from_directory(ICON_FOLDER, filename)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'admin_logged_in' not in session:
        if request.method == 'POST':
            password = request.form.get('password')            
            if hash_password(password) == hash_password(ADMIN_PASSWORD):
                session['admin_logged_in'] = True
                return redirect(url_for('upload'))
            else:
                flash('!Wrong Password', 'danger')
        return render_template('login.html')
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No File Choosed', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No File Choosed', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = file.filename
            save_path = os.path.join(DOWNLOAD_FOLDER, filename)
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(save_path):
                filename = f"{base}_{counter}{ext}"
                save_path = os.path.join(DOWNLOAD_FOLDER, filename)
                counter += 1
            file.save(save_path)
            flash('File Uploaded Successfully', 'success')
            return redirect(url_for('upload'))
        else:
            flash('File Type Not Allowed', 'danger')
    return render_template('upload.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('!You Are Logged Out', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True,host="127.0.0.1",port=5000)
