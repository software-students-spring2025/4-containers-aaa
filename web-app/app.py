from flask import Flask, render_template, request, send_file
import os
from datetime import datetime
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploaded_audio'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create')
def create():
    return render_template('create.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'audio' not in request.files:
        return 'No audio file', 400
    
    file = request.files['audio']
    if file.filename == '':
        return 'No selected file', 400
    
    #save the file to the uploads folder in the root directory
    if file:
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

    #get data from the form
    name = request.form['name']
    date = request.form['date']
    description = request.form['description']
    print(name, date, description)
        
    return 'File uploaded successfully', 200

if __name__ == '__main__':
    app.run(debug=True) 