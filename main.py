from flask import Flask, flash, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.secret_key = "muiz"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blogs.db'

UPLOADS_FOLDER = 'static/uploads'
app.config['UPLOADS_FOLDER'] = UPLOADS_FOLDER

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# ✅ User model added
class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    posts = db.relationship("Blogs", backref='author', lazy=True, cascade='all,delete-orphan')

class Blogs(db.Model):
    _id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(100), unique=True)
    content = db.Column(db.String(100), unique=True)
    image = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm-password']

        if password != confirm:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('register'))

        # ✅ Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered!", "danger")
            return redirect(url_for('register'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(name=name, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash("Registered successfully! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for('dashboard'))  # ✅ Go to dashboard after login
        else:
            flash("Invalid email or password!", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for('home'))


@app.route('/')
def home():
    blogs=Blogs.query.all()
    print("blogs",blogs)
    return render_template('home.html',blogs=blogs)


@app.route('/dashboard')
@login_required
def dashboard():
    blogs = Blogs.query.all()
    return render_template('dashboard.html', blogs=current_user.posts)


@app.route("/addblog", methods=['GET', 'POST'])
@login_required
def Add_Blog():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        file = request.files['image']

        if file.filename == '':
            return 'No selected file'

        if file:
            filepath = os.path.join(app.config['UPLOADS_FOLDER'], file.filename)
            file.save(filepath)

        blog_data = Blogs(title=title, content=content, image=file.filename,user_id=current_user.id)
        # post = Post(title=title, content=content, user_id=current_user.id)
        db.session.add(blog_data)
        db.session.commit()
        flash("Blog added successfully!", "success")
        return redirect(url_for("dashboard"))
    else:
        return render_template("addblog.html")


@app.route('/viewblog/<title>')
def viewblog(title):
    blog = Blogs.query.filter_by(title=title).first()
    return render_template('view_blog.html', blog=blog)  # ✅ Removed wrong flash


@app.route('/delete/<id>')
@login_required
def deleteuser(id):
    blog = Blogs.query.get(id)
    if blog:
        db.session.delete(blog)
        db.session.commit()
        flash("Blog deleted successfully!", "success")
    return redirect(url_for('dashboard'))


@app.route("/updateblog/<id>", methods=['GET', 'POST'])
@login_required
def updateblog(id):
    blog = Blogs.query.get(id)

    if not blog:
        return "Blog not found", 404

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()

        if not title or not content:
            error = "Title and content cannot be empty."
            return render_template("updateblog.html", blog=blog, error=error)

        blog.title = title
        blog.content = content

        file = request.files.get('image')
        if file and file.filename != '':
            filename = file.filename
            file.save(os.path.join(app.config['UPLOADS_FOLDER'], filename))
            blog.image = filename

        try:
            db.session.commit()
            flash("Blog updated successfully!", "success")
            return redirect(url_for('viewblog', title=blog.title))
        except Exception as e:
            db.session.rollback()
            error = "Something went wrong. Please try again."
            return render_template("updateblog.html", blog=blog, error=error)

    return render_template("updateblog.html", blog=blog)


with app.app_context():
    db.drop_all()
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)