#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import sys
from collections import defaultdict
from email.policy import default
import json
import dateutil.parser
import datetime
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')


db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website_link = db.Column(db.String(120), nullable=True)
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean(), nullable=False, default=False)
    seeking_description = db.Column(db.String(120))
    created_ts = db.Column(db.String(120), nullable=False, default=datetime.now())
    shows = db.relationship("Show", backref="venue", lazy='dynamic')

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500), nullable=True)
    facebook_link = db.Column(db.String(120), nullable=True)
    website_link = db.Column(db.String(120), nullable=True)
    seeking_venue = db.Column(db.Boolean(), nullable=False, default=False)
    seeking_description = db.Column(db.String(120))
    created_ts = db.Column(db.String(120), nullable=False, default=datetime.now())
    shows = db.relationship("Show", backref="artist", lazy='dynamic')

class Show(db.Model):
  __tablename__ = 'show'

  id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
  start_time = db.Column(db.TIMESTAMP)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  
  venues = Venue.query.order_by(Venue.created_ts.desc()).limit(10).all()
  artists = Artist.query.order_by(Artist.created_ts.desc()).limit(10).all()
  return render_template('pages/home.html', venues=venues, artists=artists)

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  venues = Venue.query.all()

  # concatenate data. is there a better way using sql?
  venues_data = defaultdict(dict)
  for venue in venues:
    key = (venue.city, venue.state)
    if key not in venues_data:
      venues_data[key] = {
        'city': venue.city,
        'state': venue.state,
        'venues': [
          {
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': venue.shows.filter(Show.start_time > datetime.now()).count()
          }
          
        ]
      }
    else:
      venues_data[key]['venues'].append(
        {
          'id': venue.id,
          'name': venue.name,
          'num_upcoming_shows': venue.shows.filter(Show.start_time > datetime.now()).count()
        }
      )
      
  return render_template('pages/venues.html', areas=list(venues_data.values()))

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  response= {
    "count": 0, 
    "data": []
  }
  if search_term:
    query = Venue.query.filter(Venue.name.ilike(f'%{search_term}%'))

    response = {
      "count": query.count(),
      "data": [
        {
          "id": d.id,
          "name": d.name,
          "num_upcoming_shows": d.shows.filter(Show.start_time > datetime.now()).count()
        }
        for d in query.all()
      ]
    }

  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  
  def format_start_time(shows_list):
    res = []
    for show in shows_list:
      d = show.__dict__
      d['start_time'] = str(d['start_time'])
      d['artist_name'] = show.artist.name
      d['artist_image_link'] = show.artist.image_link
      res.append(d)
    return res

  venue_obj = Venue.query.get(venue_id)
  venue = venue_obj.__dict__
  venue['genres'] = venue['genres'].split(',')
  venue['upcoming_shows'] = format_start_time(venue_obj.shows.filter(Show.start_time > datetime.now()))
  venue['past_shows'] = format_start_time(venue_obj.shows.filter(Show.start_time < datetime.now()))
  venue['past_shows_count'] = len(venue['past_shows'])
  venue['upcoming_shows_count'] = len(venue['upcoming_shows'])

  return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form)
  form.genres.data = ','.join(form.genres.data)
  if Venue.query.filter(Venue.name==form.name.data).first():
    flash(f'Venue {form.name.data} already exists')
  else:
    try:
      venue = Venue(**form.data)
      db.session.add(venue)
      db.session.commit()
      flash(f'Venue {venue.name} was successfully listed!')
    except:
      print(sys.exc_info)
      flash(f'An error occurred. Venue {form.name.data} could not be listed.')
      db.session.rollback()
    finally:
      db.session.close()
  return redirect(url_for('index'))

@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.with_entities(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search = request.get_json()
  search_term = request.form.get('search_term', '')
  response = {
    "count": 0,
    "data": []
  }
  if search_term:
    query = Artist.query.filter(Artist.name.ilike(f'%{search_term}%'))
    data = query.all()
    response = {
      "count": query.count(),
      "data": [{
        "id": art.id,
        "name": art.name,
        "num_upcoming_shows": art.shows.filter(Show.start_time > datetime.now()).count()
      } for art in data]
    }
  
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  
  def format_start_time(shows_list):
    res = []
    for show in shows_list:
      d = show.__dict__
      d['start_time'] = str(d['start_time'])
      d['venue_name'] = show.venue.name
      d['venue_image_link'] = show.venue.image_link
      res.append(d)
    return res
  
    
  artist = Artist.query.get(artist_id)
  data = artist.__dict__
  data['genres'] = data['genres'].split(',')
  data['upcoming_shows'] = format_start_time(artist.shows.filter(Show.start_time > datetime.now()))
  data['past_shows'] = format_start_time(artist.shows.filter(Show.start_time < datetime.now()))
  data['past_shows_count'] = len(data['past_shows'])
  data['upcoming_shows_count'] = len(data['upcoming_shows'])

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)
  
  form.genres.data = artist.genres.split(',')
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    form = ArtistForm(request.form)
    form.genres.data = ','.join(form.genres.data)
    db.session.execute(db.update(Artist).where(Artist.id==artist_id).values(**form.data))
    db.session.commit()
    flash(f'Artist {form.name.data} successfully updated!')
  except:
    db.session.rollback()
    flash(f'An error occurred. Artist {form.name.data} could not be updated.')
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  data = venue.__dict__
  form.genres.data = data['genres'].split(',')
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    form = VenueForm(request.form)
    form.genres.data = ','.join(form.genres.data)
    db.session.execute(db.update(Venue).where(Venue.id==venue_id).values(**form.data))
    db.session.commit()
    flash(f'Venue {form.name.data} successfully updated!')
  except:
    db.session.rollback()
    flash(f'An error occurred. Venue {form.name.data} could not be updated.')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  form = ArtistForm(request.form)
  form.genres.data = ','.join(form.genres.data)

  if Artist.query.filter(Artist.name == form.name.data).all():
    flash(f'Artist {form.name.data} already exists.')
    redirect(url_for('index'))

  try:
    artist = Artist(**form.data)
   
    db.session.add(artist)
    db.session.commit()
    flash(f'Artist {form.name.data} was successfully listed!')
  except:
    db.session.rollback()
    flash(f'An error occurred. Artist {form.name.data} could not be listed.')
  return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
 
  res = []
  for sh in Show.query.all():
    d = sh.__dict__
    d['venue_name'] = sh.venue.name
    d['artist_name'] = sh.artist.name
    d['artist_image_link'] = sh.artist.image_link
    d['start_time'] = str(d['start_time'])
    res.append(d)
  return render_template('pages/shows.html', shows=res)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  try:
    data = request.form
    show = Show(
      artist_id=int(data['artist_id']),
      venue_id=int(data['venue_id']),
      start_time=datetime.strptime(data['start_time'], "%Y-%m-%d %H:%M:%S").isoformat()
      )
    db.session.add(show)
    db.session.commit()  
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    print(sys.exc_info())
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
