from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import InputRequired, Length, Email, EqualTo
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    age = db.Column(db.Integer)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(200))


class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True)
    bio = db.Column(db.Text, default="Artist bio will appear here.")
    image = db.Column(db.String(200), default="default_artist.jpg")


class Music(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    genre = db.Column(db.String(100))
    preview = db.Column(db.String(500))     # audio url
    musiclink = db.Column(db.String(500))   # audio url
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))
    artist = db.relationship('Artist', backref='songs')


class CommunityPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='posts')




class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=3)])
    age = IntegerField(validators=[InputRequired()])
    email = StringField(validators=[InputRequired(), Email()])
    password = PasswordField(validators=[InputRequired()])
    confirm = PasswordField(validators=[InputRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField(validators=[InputRequired(), Email()])
    password = PasswordField(validators=[InputRequired()])
    submit = SubmitField('Login')


class CommunityForm(FlaskForm):
    content = StringField(validators=[InputRequired()])
    submit = SubmitField('Post')



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



@app.route('/')
def home():
    return redirect(url_for('catalog'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            age=form.age.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created")
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('catalog'))
        flash("Invalid credentials")
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/catalog')
@login_required
def catalog():
    musics = Music.query.all()
    return render_template('catalog.html', musics=musics)


@app.route('/artist/<int:artist_id>')
@login_required
def artist_profile(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    return render_template('artist_profile.html', artist=artist)



@app.route('/community', methods=['GET', 'POST'])
@login_required
def community():
    form = CommunityForm()
    posts = CommunityPost.query.order_by(CommunityPost.id.desc()).all()

    if form.validate_on_submit():
        post = CommunityPost(content=form.content.data, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('community'))

    return render_template('community.html', posts=posts, form=form)


@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = CommunityPost.query.get_or_404(post_id)

    if post.user_id != current_user.id:
        flash("You cannot delete this post")
        return redirect(url_for('community'))

    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('community'))



def load_jamendo_music():
    if Music.query.first():
        return

    CLIENT_ID = "43d6901f"
    URL = "https://api.jamendo.com/v3.0/tracks/"

    params = {
        "client_id": CLIENT_ID,
        "format": "json",
        "limit": 25,
        "include": "musicinfo"
    }

    data = requests.get(URL, params=params).json()

    for track in data.get("results", []):
        title = track.get("name")
        artist_name = track.get("artist_name")
        audio = track.get("audio")

        if not title or not artist_name or not audio:
            continue

        artist = Artist.query.filter_by(name=artist_name).first()
        if not artist:
            artist = Artist(name=artist_name)
            db.session.add(artist)
            db.session.commit()

        tags = track.get("musicinfo", {}).get("tags", [])
        genre = ", ".join(tags) if tags else "Unknown"

        song = Music(
            title=title,
            genre=genre,
            preview=audio,
            musiclink=audio,
            artist_id=artist.id
        )

        db.session.add(song)

    db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        load_jamendo_music()

    app.run
