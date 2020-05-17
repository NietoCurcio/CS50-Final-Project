from flask import flash, Flask, render_template, request, url_for, session, redirect
from login import login_required
from sqlalchemy import create_engine, Table, MetaData
from werkzeug.security import check_password_hash, generate_password_hash
# https://flask.palletsprojects.com/en/1.1.x/patterns/sqlalchemy/
# https://docs.sqlalchemy.org/en/13/core/connections.html?highlight=resultproxy#sqlalchemy.engine.ResultProxy
# https://docs.sqlalchemy.org/en/13/core/tutorial.html#coretutorial-selecting
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from werkzeug.utils import secure_filename
import os
# https://flask-wtf.readthedocs.io/en/stable/form.html#module-flask_wtf.file
# flask-wtf for the forms and upload
# pip install flask-wtf

app = Flask(__name__)
app.secret_key = b'l\xddD\xc0t\x1d=\xd4&q\xd5.\x14\xef\xb8\xb0'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
# app.uploaded_imaegs_dest = "./static/images/"

# images = UploadSet('images', IMAGES)
# configure_uploads(app, images)

class formUploadImage(FlaskForm):
    # create a field
    image = FileField(validators=[FileAllowed(['jpg', 'png'], 'Images only!')])

db = create_engine('sqlite:///dogscats.db')
metadata = MetaData(bind=db)
users = Table('users', metadata, autoload=True)
cases = Table('cases', metadata, autoload=True)
######### store table test in users #########

# con = db.connect()
######### make a connection with db, but looks that is not necessary #########

# db.execute(users.insert(), id='2')
# db.execute("INSERT INTO")
######### two methods of INSERT VALUES IN TABLE #########

# rows = db.execute("SELECT * FROM test") #-> ResultProxy
# linha = users.select(users.columns.id).execute().first() # ->RowProxy
# rows = db.execute() engine (db.execute) or connection (con.execute)
######### TWO METHODS OF SELECT VALUES using engine or connection #########

######### TESTS #########
# print("INICIO FELIPAO")
# print(type(rows)) ResultProxy
# print(type(linha)) .first do this to be a RowProxy
# print(rows)
# print(linha)
# for row in rows:
#     print(type(row))
#     print(row['id'])
# # print(rows['id']) 'ResultProxy' object is not subscriptable without for loop
# print(linha['id']) is a RowProxy, this works
# rows = rows.fetchall() return all rows in a List
# Thus I can use print(rows[0]['id']) :)
# print("FIM teste ")

@app.after_request
def after_request(response):
    response.headers["Cache-Control"]="no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response
    # Do you know that bug in css files? this is for this, reset Cache in browser
    
@app.route("/")
@login_required
def index():
    user = session["user_id"]
    rowsMy = db.execute("SELECT * FROM cases WHERE person_id = :user", user=user)
    rowsMy = rowsMy.fetchall() #transform to a list of dicts

    rowsSelected = db.execute("SELECT * FROM cases WHERE id_case IN (SELECT id_case FROM selectedCases WHERE person_id = :user)", user=user)
    rowsSelected = rowsSelected.fetchall()
    name=db.execute("SELECT username FROM users WHERE id = :id",id=user)
    name=name.fetchall()
    return render_template("index.html", rowsMy=rowsMy, rowsSelected=rowsSelected, name=name[0]['username'])

@app.route("/delete/<string:filename>", methods=['POST', 'GET'])
@login_required
def delete(filename):
    print(filename)
    rows = db.execute("SELECT * FROM cases WHERE filename = :name", name=filename)
    rows=rows.fetchall() #transform ResultProxy to all RowProxy List
    if rows[0]['person_id'] == session['user_id']:
        rows=rows[0]['id_case']
        db.execute("DELETE FROM cases WHERE id_case = :idcase", idcase=rows)
        if filename != "default.jpg":
            os.remove(os.path.join("static/images/users", filename))
    return redirect("/")

@app.route("/login", methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == "GET":
        return render_template("login.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        error = None
        rows = db.execute("SELECT * FROM users WHERE username = :user", user=username)
        rows = rows.fetchall()

        # print(rows[0]['id'])
        # print(len(rows))
        # print(type(rows))

        if not rows:
            error = "Incorrent username"
            flash(error)
            return render_template("login.html")
        elif not check_password_hash(rows[0]['hash'], password):
            error = "Password incorrect"
            flash(error)
            return render_template("login.html")

        if error is None:
            session.clear()
            session["user_id"] = rows[0]['id']
            return redirect("/") 
        

@app.route("/logout")
def logout():
    session.clear()
    return redirect("login")
    # https://flask.palletsprojects.com/en/1.1.x/tutorial/views/?highlight=check_password_hash#logout
    # https://flask.palletsprojects.com/en/1.1.x/quickstart/?highlight=session%20pop

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        error = None
        user = request.form.get("username")
        name = users.select(users.columns.username == user).execute()
        name = name.fetchall()
        if name != [] and name[0]['username'] == user:
            error = "Username already exist!"
        
        em = request.form.get("email")

        password = request.form.get("password")
        password = generate_password_hash(password)

        passConf = request.form.get("passConf")

        if not check_password_hash(password, passConf):
            error = "Password don't match"

        if error is None:
            db.execute("INSERT INTO users (username, email, hash) VALUES (:user, :em, :h)", user=user, em=em, h=password)
            row = db.execute("SELECT id FROM users WHERE username = :user", user=user)
            print("FELIAP")
            print(row)
            row = row.fetchall()
            print(row)
            session["user_id"] = row[0]['id']
            return redirect("/")
        if error != None:
            flash(error)
    return redirect('/register')

@app.route("/MyDonation", methods=['GET', 'POST'])
@login_required
def registerDonation():
    form = formUploadImage()
    if request.method == "POST":
        # if form.validate_on_submit() other check if its is a post request
        f = (form.image.data)
        # print(f) #with file is FilesTORAGE: 'DOGCAT.JPG', void is None

        adress = request.form.get("adress")
        desc = request.form.get("description")
        reason = request.form.get("reason")

        user=session["user_id"]
        email = db.execute("SELECT email FROM users WHERE id = :user", user=user)
        email = email.fetchall()
        email = email[0]['email']
        
        if f != None:
            filename = secure_filename(f.filename)
            name = cases.select(cases.columns.filename == filename).execute()
            name = name.fetchall()
            # print("feliap")
            # print(filename)
            print(name)
            if name != []:
                # is the same folder for all users, so in this way, I will able to avoid overwrite images
                error = "Filename already exist! Must be different, please rename the file (e.g, name_something)"
                flash(error)
                return redirect("/MyDonation")
            # print(type(filename)) str
            f.save(os.path.join(f"static/images/users/", filename))

            db.execute("INSERT INTO cases (person_id, adress, email, description, reason, filename) VALUES (:person, :ad, :em, :des, :rea, :file)",
            person=user, ad=adress, em=email, des=desc, rea=reason, file=filename)

            return redirect("/")
        else:
            filename = "default.jpg"
            db.execute("INSERT INTO cases (person_id, adress, email, description, reason, filename) VALUES (:person, :ad, :em, :des, :rea, :file)",
            person=user, ad=adress, em=email, des=desc, rea=reason, file=filename)
            return redirect("/")
    else:
        return render_template("recordsDonation.html", form=form)

@app.route("/adopt")
@login_required
def adopt():
    user = session['user_id']
    allrows = db.execute("SELECT * FROM cases")
    allrows = allrows.fetchall() # ResultPorxy to list of RowPorxy thank god I find this in docmentation
    return render_template("adopt.html", allrows=allrows, user=user, len=len(allrows))


@app.route("/rec/<string:id>", methods=['POST', 'GET'])
@login_required
def recordAdopt(id):
    print(id)
    user = session["user_id"]
    db.execute("INSERT INTO selectedCases (id_case, person_id) VALUES (:idcase, :idperson)",
    idcase=id, idperson=user)
    return redirect("/")