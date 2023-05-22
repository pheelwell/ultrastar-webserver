import os
from flask import Flask, render_template, request, send_file
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import class_mapper
from dotenv import load_dotenv
import socket

# make sure to work inside the app context
load_dotenv()


QR_URL = os.getenv('QR_URL')
SONGFOLDER = os.getenv('SONGFOLDER')
SONG_DB = os.getenv('SONG_DB')
ULTRASTAR_DB = os.getenv('ULTRASTAR_DB')


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SONG_DB
app.config['SQLALCHEMY_BINDS'] = {
    'us_db': ULTRASTAR_DB
}
db = SQLAlchemy(app)

# Create a class for the songs table
class Song(db.Model):
    __tablename__ = 'songs'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    artist = db.Column(db.String(255))
    language = db.Column(db.String(255))
    year = db.Column(db.Integer)
    mp3_path = db.Column(db.String(255), unique=True)
    modify_date = db.Column(db.Integer)
    folder_path = db.Column(db.String(255))


# Create a class for the us_songs table
class USSong(db.Model):
    __bind_key__ = 'us_db'
    __tablename__ = 'us_songs'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    artist = db.Column(db.String(255))
    title = db.Column(db.String(255))
    TimesPlayed = db.Column(db.Integer)


def model_to_dict(model):
    """Converts a SQLAlchemy model object to a dictionary."""
    if isinstance(model, list):
        return [model_to_dict(m) for m in model]
    columns = [c.key for c in class_mapper(model.__class__).columns]
    return {c: getattr(model, c) for c in columns}


# Update the handle_song_request function
def handle_song_request(request):
    artist_filter = request.args.get('artist_filter')
    song_filter = request.args.get('song_filter')
    sort_by = request.args.get('sort_by', 'artist')  # Default sort by artist
    limit = request.args.get('limit', 1000)  # Default limit to 100 songs
    offset = request.args.get('offset', 0)  # Default offset to 0

    query = Song.query
    

    if artist_filter:
        query = query.filter(Song.artist.like(f"%{artist_filter}%"))

    if song_filter:
        query = query.filter(Song.title.like(f"%{song_filter}%"))

    if sort_by == 'artist':
        query = query.order_by(Song.artist)
    elif sort_by == 'title':
        query = query.order_by(Song.title)
    elif sort_by == 'year':
        query = query.order_by(Song.year)
    
    # if querrying for times played, dont limit the results
    if sort_by != 'times_played':
        query = query.limit(limit).offset(offset)
    

    songs = query.all()

    # Retrieve TimesPlayed from us_songs table
    query = USSong.query
    us_songs = query.all()
    us_songs = [model_to_dict(song) for song in us_songs]
    songs = [model_to_dict(song) for song in songs]

    for song in songs:
        match_found = False  # Flag variable to track if a match is found
        for us_song in us_songs:
            if us_song["artist"].rstrip('\x00') == song["artist"] and us_song["title"].rstrip('\x00') == song["title"]:
                print(f"match found for {song['artist']} - {song['title']}")
                song["times_played"] = us_song["TimesPlayed"]
                match_found = True
                break  # Break out of the inner loop
        if not match_found:
            song["times_played"] = 0
    
    if sort_by == 'times_played':
        # remove songs with 0 times played
        songs = [song for song in songs if song['times_played'] > 0]
        songs = sorted(songs, key=lambda k: k['times_played'], reverse=True)

    return songs



@app.route('/')
def index():
    songs = handle_song_request(request)
    artist_filter = request.args.get('artist_filter',default='')
    song_filter = request.args.get('song_filter',default='')
    sort_by = request.args.get('sort_by', 'artist')  # Default sort by artist
    # get local ip
    return render_template('index.html', songs=songs, artist_filter=artist_filter, song_filter=song_filter, sort_by=sort_by, local_ip=QR_URL)

@app.route('/api/songs')
def api_songs():
    songs = handle_song_request(request)
    
    return {'songs': songs}



@app.route('/api/mp3')
def api_mp3():
    #this holds the relative path to the mp3 file
    mp3_path = request.args.get('mp3_path')
    print(mp3_path)
    #concat the song path to the song folder
    mp3_path = os.path.join(SONGFOLDER, mp3_path)
    print(mp3_path)
    # prevent path traversal
    #return the song from the os
    return send_file(mp3_path, mimetype='audio/mp3')

# print test on startup of the server
@app.before_first_request
def before_first_request():
    print("Flask app is starting up...")

if __name__ == '__main__':
    print('start')
    app.run(debug=True)
