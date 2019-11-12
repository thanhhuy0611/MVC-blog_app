from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

#setup and config Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SECRET_KEY'] = "KHOA OC-CHO"

#config SQLAlchemy
db = SQLAlchemy(app)
login_manager = LoginManager(app)


#DEFINING MODELS
class Blog(db.Model):
    id = db.Column(db.Integer, primary_key = True) 
    title = db.Column(db.String(200),nullable= False)
    body =  db.Column(db.String,nullable= False)
    author = db.Column(db.String,nullable = False)
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
class Users(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key = True) 
    email = db.Column(db.String,nullable= False,unique = True)
    password = db.Column(db.String,nullable = False,unique = False)
    user_name =  db.Column(db.String,nullable= False)
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password,password)

db.create_all()

@login_manager.user_loader
def load_user(id):
    return Users.query.get(id)

# add new blog
@app.route('/',methods=["GET","POST"])
def new_post():
    user = "hard code here"
    if not user:
        return redirect(url_for('login'))
    if request.method == "POST":
        new_blog =  Blog(
            title = request.form["title"],
            body = request.form["body"],
            author = request.form["author"]
        )
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('new_post'))
    # show all blog
    posts = Blog.query.all()
    return render_template('/index.html',posts = posts )

# delete a blog
@app.route('/blog/<b>', methods=["GET","POST","DELETE"])
def delete_blog(b):
    if request.method =="POST":
        post = Blog.query.filter_by(id = b).first()
        if not post:
            return "there is no such post"
        db.session.delete(post)
        db.session.commit()
        return redirect(url_for('new_post'))

# check account login
@app.route('/login', methods=["GET","POST"])
def login():
    if not current_user.is_anonymous:
        return redirect(url_for('new_post'))

    if request.method == "POST":
        user = Users.query.filter_by(email = request.form["email"]).first()
        if not user:
            flash('Email or password incorrect!','danger')
        if user:
            if user.check_password(request.form['password']):
                login_user(user)
                flash(f'Welcome back, {user.user_name}','success')
                return redirect(url_for('new_post'))
    return render_template('/login.html')

# sign up account
@app.route('/signup', methods=["GET","POST"])
def sign_up():
    if request.method == "POST":
        #check email unique
        is_email_exits = Users.query.filter_by(email = request.form["email"]).first()
        print("checkemail",is_email_exits)
        if is_email_exits:
            flash('Email is exits. Please try again!','danger')
        if not is_email_exits:
            new_user =  Users(
                email = request.form["email"],        
                user_name = request.form["user_name"]
            )
            new_user.set_password(request.form["password"])
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('new_post'))
    return render_template('/signup.html')

if __name__ == "__main__":
    app.run(debug = True, port=5001)