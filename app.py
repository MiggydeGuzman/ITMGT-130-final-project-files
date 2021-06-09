from flask import Flask, render_template, url_for, redirect, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, RadioField, IntegerField
from wtforms.validators import InputRequired, Email, Length, NumberRange
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
 

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))


# config
app.config["DEBUG"] = True
app.config["SECRET_KEY"] = b's@g@d@c0ff33!'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, 'database.db')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
Bootstrap(app)
db = SQLAlchemy(app) # Init DB
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Association Table
enrolled_classes = db.Table('enrolled_classes',
    db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
    db.Column("class_id", db.Integer, db.ForeignKey("classes.id")),
    db.PrimaryKeyConstraint('user_id', 'class_id')
    )


class Users(UserMixin, db.Model):
    """Table Users in database to hold user data"""
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(80))
    gender = db.Column(db.String)
    payment_method = db.Column(db.String)
    enrolled = db.relationship("Classes", secondary=enrolled_classes, backref=db.backref('enrolled', lazy="dynamic"))


class Classes(db.Model):
    """Classes table to hold all available classes"""
    id = db.Column(db.Integer, primary_key=True)
    class_code = db.Column(db.String(10), unique=True)
    class_category = db.Column(db.String(50))
    class_name = db.Column(db.String(50))
    instructor = db.Column(db.String(50))
    class_time = db.Column(db.String(50))
    price = db.Column(db.Integer)
    slots_available = db.Column(db.Integer)


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


class LoginForm(FlaskForm):
    """ Flask form for login"""
    username = StringField('Email', validators=[InputRequired(), Email(message="Invalid Email"), Length(min=5, max=50)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=5, max=80)])


class SignupForm(FlaskForm):
    """ Flask form for registration"""
    first_name = StringField('First Name', validators=[InputRequired(), Length(min=3, max=20)])
    last_name = StringField('Last Name', validators=[InputRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[InputRequired(), Email(message="Invalid Email"), Length(max=40)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=5, max=80)])
    gender = RadioField('Gender', choices=["male", "female"])
    payment_method = RadioField('Payment Method', choices=[("credit card", "credit card"), ("cash", "cash")])


class AddClasses(FlaskForm):
    """Form to be able to add classes to the DB""" 
    class_code = StringField("Class Code", validators=[InputRequired(), Length(max=10)])
    class_category = StringField("Class Category", validators=[InputRequired(), Length(min=5, max=50)])
    class_name = StringField("Class Name", validators=[InputRequired(), Length(min=5, max=50)])
    instructor = StringField("Instructor", validators=[InputRequired(), Length(min=5, max=50)])
    class_time = StringField("Class Time", validators=[InputRequired(), Length(min=5, max=50)])
    price = IntegerField("Price", validators=[InputRequired(), NumberRange(min=0)])
    slots_available = IntegerField("Slots Available", validators=[InputRequired(), NumberRange(max=20)])


class ChangePassword(FlaskForm):
    """Form to allow user to update information"""
    old_password = PasswordField('Old Password', validators=[InputRequired(), Length(min=5, max=80)])
    new_password1 = PasswordField('New Password', validators=[InputRequired(), Length(min=5, max=80)])
    new_password2 = PasswordField('Retype New Password', validators=[InputRequired(), Length(min=5, max=80)])


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/contactus1")
def contactus1():
    return render_template("contactus1.html")

@app.route("/contactus2")
def contactus2():
    return render_template("contactus2.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.username.data).first()
        if user: 
            if form.password.data == user.password:
                login_user(user)
                return redirect(url_for('homepage'))
            else:
                flash("Invalid username or password. Please try again.")
        else:
            flash("Check credentials again!")
    return render_template("login.html", form=form)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        new_user = Users(first_name=form.first_name.data, last_name=form.last_name.data, email=form.email.data, password=form.password.data, gender=form.gender.data, payment_method=form.payment_method.data)
        db.session.add(new_user)
        db.session.commit()
        flash("Account Created!")
        return redirect("signup")
    return render_template("signup.html", form=form)


@app.route("/enlistclass", methods=["GET", "POST"])
@login_required
def enlist_class():
    class_code = request.args.get('code', '')
    chosen_class = Classes.query.filter_by(class_code=class_code).first()
    if chosen_class:
        try:
            chosen_class.enrolled.append(current_user)
            chosen_class.slots_available -= 1
            db.session.commit()
            flash("Successfully Enlisted!")
        except:
            flash("Already Enlisted in this class!")
    return redirect("homepage")


@app.route("/enrolledclasses", methods=["GET", "POST"])
@login_required
def user_enrolled():
    enrolled_classes = current_user.enrolled
    payment_total = 0
    if not enrolled_classes:
        flash("No Classes Enrolled!")
    else:
        for classs in enrolled_classes:
            payment_total += int(classs.price) 

    return render_template("userenrolled.html", enrolled_classes=enrolled_classes, payment_total=payment_total)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Successfully Logged out!")
    return redirect(url_for("index"))


@app.route("/homepage")
@login_required
def homepage():
    return render_template("homepage.html", name=current_user.first_name.title())


@app.route('/myaccount')
@login_required
def myaccount():
    return render_template("myaccount.html", user_details=current_user)


@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    form = ChangePassword()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=current_user.email).first()
        if form.old_password.data == user.password:
            if form.new_password1.data == form.new_password2.data:
                user.password = form.new_password2.data
                db.session.commit()
                flash("Password successfully updated!")
            else: 
                flash("Passwords do not match")
        else: 
            flash("Incorrect Password")

    return render_template("changepassword.html", form=form)


@app.route('/adminclasses', methods=["GET", "POST"])
def admin_classes():
    form = AddClasses()
    if form.validate_on_submit():
        new_class = Classes(class_code= form.class_code.data, class_name=form.class_name.data, class_category=form.class_category.data, instructor=form.instructor.data, class_time=form.class_time.data, price=form.price.data, slots_available=form.slots_available.data)
        db.session.add(new_class)
        db.session.commit()
        flash("Class Successfully Added")

    return render_template("addclass.html", form=form)


@app.route("/rowingclasses")
@login_required
def rowing():
    classes = Classes.query.filter_by(class_category="Rowing")
    return render_template("rowing.html", classes=classes)


@app.route("/cyclingclasses")
@login_required
def cycling():
    classes = Classes.query.filter_by(class_category="Cycling")
    return render_template("cycling.html", classes=classes)


@app.route("/strengthclasses")
@login_required
def strength():
    classes = Classes.query.filter_by(class_category="Strength")
    return render_template("strength.html", classes=classes)


@app.route("/enduranceclasses")
@login_required
def endurance():
    classes = Classes.query.filter_by(class_category="Endurance")
    return render_template("endurance.html", classes=classes)


if __name__ == "__main__":
    app.run(debug=True)

