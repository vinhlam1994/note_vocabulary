# app.py
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from gtts import gTTS
import pandas as pd
from flask import Response
import os
import string

app = Flask(__name__)
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///vocab.db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/audio'

from extensions import db
db.init_app(app)
with app.app_context():
    db.create_all()
from models import Vocabulary

# Ensure audio folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    search = request.args.get('search', '')
    filter_tag = request.args.get('tag', '')
    filter_letter = request.args.get('letter', '')

    words = Vocabulary.query

    if search:
        words = words.filter(Vocabulary.word.contains(search))
    if filter_tag:
        words = words.filter(Vocabulary.tag == filter_tag)
    if filter_letter:
        words = words.filter(Vocabulary.word.startswith(filter_letter))

    words = words.order_by(Vocabulary.word).all()
    tags = db.session.query(Vocabulary.tag).distinct().all()

    return render_template('index.html', words=words, tags=tags, search=search, filter_tag=filter_tag, filter_letter=filter_letter, letters=list(string.ascii_uppercase))

@app.route('/add', methods=['GET', 'POST'])
def add_word():
    if request.method == 'POST':
        word = request.form['word'].strip()
        word_type = request.form['word_type']
        phonetic = request.form['phonetic']
        meaning_vi = request.form['meaning_vi']
        meaning_en = request.form['meaning_en']
        note = request.form['note']
        tag = request.form['tag']

        if word and word_type and meaning_vi:
            vocab = Vocabulary(word=word, word_type=word_type, phonetic=phonetic,
                               meaning_vi=meaning_vi, meaning_en=meaning_en,
                               note=note, tag=tag)
            db.session.add(vocab)
            db.session.commit()

            # Generate pronunciation
            tts = gTTS(word)
            tts.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{vocab.id}.mp3"))

            return redirect(url_for('index'))
    return render_template('add_word.html')

@app.route('/edit/<int:word_id>', methods=['GET', 'POST'])
def edit_word(word_id):
    vocab = Vocabulary.query.get_or_404(word_id)
    if request.method == 'POST':
        vocab.word = request.form['word']
        vocab.word_type = request.form['word_type']
        vocab.phonetic = request.form['phonetic']
        vocab.meaning_vi = request.form['meaning_vi']
        vocab.meaning_en = request.form['meaning_en']
        vocab.note = request.form['note']
        vocab.tag = request.form['tag']
        db.session.commit()

        # Regenerate pronunciation
        tts = gTTS(vocab.word)
        tts.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{vocab.id}.mp3"))

        return redirect(url_for('index'))
    return render_template('edit_word.html', vocab=vocab)

@app.route('/delete/<int:word_id>')
def delete_word(word_id):
    vocab = Vocabulary.query.get_or_404(word_id)
    db.session.delete(vocab)
    db.session.commit()

    # Delete audio file
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{vocab.id}.mp3")
    if os.path.exists(audio_path):
        os.remove(audio_path)

    return redirect(url_for('index'))

@app.route('/audio/<int:word_id>')
def audio(word_id):
    return send_from_directory(app.config['UPLOAD_FOLDER'], f"{word_id}.mp3")

@app.route('/export/csv')
def export_csv():
    data = Vocabulary.query.all()
    df = pd.DataFrame([{
        'Word': v.word,
        'Type': v.word_type,
        'Phonetic': v.phonetic,
        'Meaning_VI': v.meaning_vi,
        'Meaning_EN': v.meaning_en,
        'Note': v.note,
        'Tag': v.tag
    } for v in data])
    csv_data = df.to_csv(index=False, encoding='utf-8-sig')
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=vocab.csv"}
    )

@app.route('/export/excel')
def export_excel():
    data = Vocabulary.query.all()
    df = pd.DataFrame([{
        'Word': v.word,
        'Type': v.word_type,
        'Phonetic': v.phonetic,
        'Meaning_VI': v.meaning_vi,
        'Meaning_EN': v.meaning_en,
        'Note': v.note,
        'Tag': v.tag
    } for v in data])
    output = pd.ExcelWriter('vocab.xlsx', engine='openpyxl')
    df.to_excel(output, index=False, sheet_name='Vocabulary')
    output.close()
    return send_from_directory('.', 'vocab.xlsx', as_attachment=True)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
