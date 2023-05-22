import os
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
SONGFOLDER = os.getenv('SONGFOLDER')

# Configure the SQLAlchemy engine
engine = create_engine('sqlite:///F://webserver//songs.db')

# Create a session factory
Session = sessionmaker(bind=engine)

# Create a base class for declarative models
Base = declarative_base()

# Create the database tables
Base.metadata.create_all(engine)

class Song(Base):
    __tablename__ = 'songs'
    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    artist = Column(String(255))
    language = Column(String(255))
    year = Column(Integer)
    mp3_path = Column(String(255), unique=True)
    modify_date = Column(Integer)
    folder_path = Column(String(255))



# Create a session
session = Session()

def index_songs():
    # Create db
    Base.metadata.create_all(engine)
    batch = 500
    count = 0
    edited = 0
    added = 0
    for root, dirs, files in os.walk(SONGFOLDER):
        for file in files:
            if file.endswith('.mp3'):
                batch -= 1
                # get relative path for api route later
                mp3_path = os.path.join(root, file).replace(SONGFOLDER, '')
                # get metadata
                # search for txt in same folder
                # the name of the txt file is NOT the same as the mp3 file, so replacing the extension is not enough
                # get folder name
                for folder_file in os.listdir(root):
                    if folder_file.endswith('.txt'):
                        txt_path = os.path.join(root, folder_file)
                        # open file
                        with open(txt_path, 'r', encoding='ISO-8859-1') as txt_file:
                            # read lines
                            lines = txt_file.readlines()
                            # search for metadata (probably in the first 20 lines)
                            for line in lines[:20]:
                                if line.startswith('#TITLE:'):
                                    title = line.replace('#TITLE:', '').strip()
                                elif line.startswith('#ARTIST:'):
                                    artist = line.replace('#ARTIST:', '').strip()
                                elif line.startswith('#LANGUAGE:'):
                                    language = line.replace('#LANGUAGE:', '').strip()
                                elif line.startswith('#YEAR:'):
                                    year = line.replace('#YEAR:', '').strip()
                        # checj if song is already in database
                        # get modify date of folder
                        # this is the date the song was added to the database
                        modify_date = os.path.getmtime(root)
                        
                        # create song object
                        song = Song(title=title, artist=artist, language=language, year=year, mp3_path=mp3_path, modify_date=modify_date)
                        # add folder path
                        song.folder_path = root.replace(SONGFOLDER, '')
                        # go back one folder
                        song.folder_path = os.path.dirname(song.folder_path)
                        
                        if session.query(Song).filter_by(mp3_path=mp3_path).first():
                            # update song in database
                            edited += 1
                            session.query(Song).filter_by(mp3_path=mp3_path).update({'title': title, 'artist': artist, 'language': language, 'year': year, 'modify_date': modify_date, 'folder_path': song.folder_path})
                        else:
                            # add to database
                            session.add(song)
                            added += 1
                        count += 1
                if batch == 0:
                    print(f"processed {count} songs...")
                    batch = 500
                    session.commit()
    session.commit()
    print(f"processed {count} songs...")
    print(f"added {added} songs...")
    print(f"edited {edited} songs...")
    print("done")

index_songs()