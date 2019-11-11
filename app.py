from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
 

#setup and config Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'

#config SQLAlchemy
db = SQLAlchemy(app)

#DEFINING MODELS
class Blog(db.Model):
    id = db.Column(db.Integer, primary_key = True) 
    title = db.Column(db.String(200),nullable= False)
    body =  db.Column(db.String,nullable= False)
    author = db.Column(db.String,nullable = False)
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

db.create_all()

# add new blog
@app.route('/',methods=["GET","POST"])
def new_post():
    if request.method == "POST":
        new_blog =  Blog(
            title = request.form["title"],
            body = request.form["body"],
            author = request.form["author"]
        )
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('new_post'))
    posts = Blog.query.all()
    return render_template('/index.html',posts = posts )

# show all blog
# @app.route('/', methods=["GET"])
# def root():
#     arr = ['Po','Loi']
#     return render_template('/index.html',users=arr)


if __name__ == "__main__":
    app.run(debug = True, port=5001)