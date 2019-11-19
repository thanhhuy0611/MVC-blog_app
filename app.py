from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from flask_wtf import FlaskForm
from flask_migrate import Migrate
from wtforms import StringField, validators, PasswordField, SubmitField
import os 

#setup and config Flask app
app = Flask(__name__)
print(os.environ.get('DATABASE_URL'))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_POSTGRES')
app.config['SECRET_KEY'] = "anything"

#config SQLAlchemy
db = SQLAlchemy(app)

#set up Flask
migrate = Migrate(app, db)

# set up flask-login
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = "login"


#DEFINING MODELS
class Blog(db.Model):
    id = db.Column(db.Integer, primary_key = True) 
    title = db.Column(db.String(200),nullable= False)
    body =  db.Column(db.String,nullable= False)
    author = db.Column(db.String,nullable = False)
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
    user_id = db.Column(db.String,nullable = False)
    view_count = db.Column(db.Integer, default=0)


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

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    body =  db.Column(db.String,nullable= False)  
    user_id = db.Column(db.Integer,nullable = False)
    blog_id = db.Column(db.Integer,nullable = False)
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())


db.create_all()

## My awesome forms
class RegisterForm(FlaskForm):
    username = StringField(
        "User name", validators=[
            validators.DataRequired(), 
            validators.Length(min=3,max=20,message="Need to be in between 3 and 20")
    ])
    email = StringField(
        "Email", validators=[
            validators.DataRequired(), 
            validators.Length(min=3,max=200,message="Need to be in between 3 and 20"), 
            validators.Email("Please enter correct email!")
    ])
    password = PasswordField(
        'Password', validators=[
            validators.DataRequired(),
            validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Confirm password', validators=[validators.DataRequired()])
    submit = SubmitField('Sign up')

# sign up account
@app.route('/signup', methods=["GET","POST"])
def sign_up():
    form = RegisterForm()
    if not current_user.is_anonymous:
        return redirect(url_for('home'))
    if request.method == "POST":
        if form.validate_on_submit():
        #check email unique
            is_email_exits = Users.query.filter_by(email = form.email.data).first()
            print("emailcheck",is_email_exits)
            if is_email_exits:
                flash('Email is exits. Please try again!','danger')
            if not is_email_exits:
                new_user =  Users(
                    email = form.email.data,        
                    user_name = form.username.data
                )
                new_user.set_password(form.password.data)
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                return redirect(url_for('home'))
        print(form.errors.items())
    return render_template('/signup.html', form = form)

# set current_user
@login_manager.user_loader
def load_user(b):
    return Users.query.filter_by(id = b).first()

# comment
@app.route('/posts/<id>/comments', methods=['GET','POST'])
def create_comment(id):
    ref = request.args.get('ref')
    print(ref)
    if request.method == "POST":
        comment = Comment(
            body = request.form["body"],
            user_id = current_user.id,
            blog_id = id
        )
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for(ref, id= id))

# delete comment
@app.route('/posts/<id>/comments/<id_comment>', methods=['GET','POST'])
def delete_comment(id,id_comment):
    ref = request.args.get('ref')
    print('ref',ref)
    comment = Comment.query.filter_by(id = id_comment).first()
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for(ref, id= id))

# show all blog
@app.route('/',methods=["GET","POST"])
def home():
    posts = Blog.query.all()
    filter = request.args.get('filter')
    for post in posts:
        post.comments = Comment.query.filter_by(blog_id = post.id).all()
    if filter == 'most-recently':
        posts = Blog.query.order_by(Blog.created_on.desc()).all()
    if filter == 'top-viewed':
        posts = Blog.query.order_by(Blog.view_count.desc()).all()
    return render_template('/index.html',posts = posts, ref = 'home')




# add new blog
@app.route('/newpost',methods=["GET","POST"])
def new_post():
    if request.method == "POST":
        new_blog =  Blog(
            title = request.form["title"],
            body = request.form["body"],
            author = current_user.user_name,
            user_id = current_user.id
        )
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('home'))

#view a blog
@app.route('/posts/<id>',methods=["GET","POST"])
def view_post(id):
    post = Blog.query.get(id)
    post.view_count +=1
    db.session.commit() 
    post.comments = Comment.query.filter_by(blog_id = id).all()
    return render_template('/post.html',post = post, ref = 'view_post')

#Edit a blog
@app.route('/posts/<id>/edit',methods=['GET','POST'])
def edit_post(id):
    post = Blog.query.get(id)
    if request.method == "POST":
        post.title = request.form['title']
        post.body = request.form['body']
        db.session.commit()
        return redirect(url_for('view_post',id = id))
    return render_template('/editpost.html',post = post)

# delete a blog
@app.route('/blog/<b>', methods=["GET","POST","DELETE"])
@login_required
def delete_blog(b):
    if request.method =="POST":
        post = Blog.query.filter_by(id = b).first()
        if not post:
            return "there is no such post"
        db.session.delete(post)
        db.session.commit()
        return redirect(url_for('home'))

# check account login
@app.route('/login', methods=["GET","POST"])
def login():
    if not current_user.is_anonymous:
        return redirect(url_for('home'))

    if request.method == "POST":
        user = Users.query.filter_by(email = request.form["email"]).first()
        if not user:
            flash('Email incorrect!','danger')
        if user:
            if user.check_password(request.form['password']):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash('Password incorrect!','danger')
    return render_template('/login.html')

# logout 
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug = True, port=5001)