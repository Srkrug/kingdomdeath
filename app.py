# imports
import MySQLdb
import uuid

from flask import Flask, request, flash, redirect, session
from flask import render_template
from flask_bootstrap import Bootstrap
from flask_recaptcha import ReCaptcha
from sqlobject import *
from werkzeug.contrib.fixers import ProxyFix


class UserDatabase(SQLObject):
    """connect to mysql database"""

    name = StringCol(length=255, unique=True)
    password = StringCol(length=255)


class ConfigDatabase(SQLObject):
    """connect to mysql database"""

    name = StringCol(length=255, unique=True)
    secret_key = StringCol(length=255)
    recaptcha_secret_key = StringCol(length=255)
    recaptcha_site_key = StringCol(length=255)


class BossDatabase(SQLObject):
    """connect to mysql database"""

    name = StringCol(length=255, unique=True)
    strength = IntCol()
    speed = IntCol()
    accuracy = IntCol()
    toughness = IntCol()
    evasion = IntCol()


class CharDatabase(SQLObject):
    """connect to mysql database"""

    name = StringCol(length=255, unique=True)

    stat_survival = IntCol()
    stat_movement = IntCol()
    stat_accuracy = IntCol()
    stat_strength = IntCol()
    stat_evasion = IntCol()
    stat_luck = IntCol()
    stat_speed = IntCol()

    defense_insanity = IntCol()
    defense_head = IntCol()
    defense_arms = IntCol()
    defense_body = IntCol()
    defense_waist = IntCol()
    defense_legs = IntCol()

    weapon_speed = IntCol()
    weapon_accuracy = IntCol()
    weapon_strength = IntCol()


# setup mysql credentials
mysql_user = "root"
mysql_password = "Avodaq1234*"
mysql_host = "localhost"

# setup flask app
app = Flask(__name__)
Bootstrap(app)
app.wsgi_app = ProxyFix(app.wsgi_app)

# create database if necessary
db = MySQLdb.connect(host=mysql_host, user=mysql_user, passwd=mysql_password)
c = db.cursor()
c.execute("create database if not exists system")
db.close()

# create database if necessary
UserDatabase._connection = connectionForURI(
    "mysql://" + mysql_user + ":" + mysql_password + "@" + mysql_host + "/system")
ConfigDatabase._connection = connectionForURI(
    "mysql://" + mysql_user + ":" + mysql_password + "@" + mysql_host + "/system")

# create tables if necessary
UserDatabase.createTable(ifNotExists=True)
ConfigDatabase.createTable(ifNotExists=True)

# create default entry if necessary
try:
    app.secret_key = ConfigDatabase.selectBy(name="default")[0].secret_key
except:
    ConfigDatabase(name="default", secret_key=str(uuid.uuid4()), recaptcha_secret_key="PLEASECHANGE",
                   recaptcha_site_key="PLEASECHANGE")
    app.secret_key = ConfigDatabase.selectBy(name="default")[0].secret_key

# create global variables
BOSS_COLUMNS = []
CHAR_COLUMNS = []

# create recaptcha
recaptcha = ReCaptcha(app=app)
recaptcha.secret_key = ConfigDatabase.selectBy(name="default")[0].recaptcha_secret_key
recaptcha.site_key = ConfigDatabase.selectBy(name="default")[0].recaptcha_site_key
recaptcha.theme = "light"
recaptcha.type = "image"
recaptcha.size = "normal"
recaptcha.tabindex = 10
recaptcha.is_enabled = True


@app.route("/", methods=['GET', 'POST'])
def default():
    """redirect to default"""

    return redirect("/login.html")


@app.route("/login.html", methods=['GET', 'POST'])
def login():
    """login mask"""

    # login user
    if request.method == "POST" and request.form["submit"] == "Login":

        # check if credentials are correct
        try:
            if request.form["name"] == "default":
                raise Exception

            # create session
            name = UserDatabase.selectBy(name=request.form["name"], password=request.form["password"])[0].name
            session['name'] = name

            # create database if necessary
            db = MySQLdb.connect(host=mysql_host, user=mysql_user, passwd=mysql_password)
            c = db.cursor()
            c.execute("create database if not exists " + name)
            db.close()

            BossDatabase._connection = connectionForURI(
                "mysql://" + mysql_user + ":" + mysql_password + "@" + mysql_host + "/" + session["name"])
            CharDatabase._connection = connectionForURI(
                "mysql://" + mysql_user + ":" + mysql_password + "@" + mysql_host + "/" + session["name"])

            # create tables if necessary
            BossDatabase.createTable(ifNotExists=True)
            CharDatabase.createTable(ifNotExists=True)

            # create lists of columns
            global BOSS_COLUMNS
            global CHAR_COLUMNS
            BOSS_COLUMNS = sorted(BossDatabase.sqlmeta.columns.keys())
            CHAR_COLUMNS = sorted(CharDatabase.sqlmeta.columns.keys())

            flash("Login successfull")
            return redirect("/char_sheet.html")
        except:
            flash("Wrong credentials")

    return render_template("/login.html")


@app.route("/register.html", methods=['GET', 'POST'])
def register():
    """register mask"""

    # register user
    if request.method == "POST" and request.form["submit"] == "Register":

        # check if fields are empty
        if request.form["name"] == "" or request.form["password"] == "":
            flash("Please insert a name and a password.")
            return redirect("/register.html")

        # check if user exists
        try:
            if recaptcha.verify():
                # create user
                UserDatabase(name=request.form["name"], password=request.form["password"])

                flash("User created. Please login.")
                return redirect("/login.html")
            else:
                flash("Please identify yourself as a human.")
        except:
            flash("User already exists")

    return render_template("/register.html", recaptcha=recaptcha)


@app.route("/account.html", methods=['GET', 'POST'])
def account():
    """account mask"""

    # check if logged in
    if not 'name' in session:
        flash("Please login")
        return redirect("login.html")

    # logout user
    if request.method == "POST" and request.form["submit"] == "Logout":
        session.pop("name", None)
        flash("Logout successfull")
        return redirect("/login.html")

    # delete user
    if request.method == "POST" and request.form["submit"] == "Delete":
        # delete user
        UserDatabase.deleteBy(name=session["name"])

        # delete database
        db = MySQLdb.connect(host=mysql_host, user=mysql_user, passwd=mysql_password)
        c = db.cursor()
        c.execute("drop database " + session["name"])
        db.close()

        # remove session
        session.pop("name", None)
        flash("Delete successfull")
        return redirect("/login.html")

    return render_template("/account.html")


@app.route("/boss_editor.html", methods=['GET', 'POST'])
def boss_editor():
    """render boss"""

    # check if logged in
    if not "name" in session:
        flash("Please login")
        return redirect("login.html")

    # save  to database if post
    if request.method == "POST" and request.form["submit"] == "Save":
        try:
            f = ""
            for column in BOSS_COLUMNS:

                # convert int if possible
                try:
                    int(request.form[column])
                    f += column + "=" + request.form[column] + ", "
                except:
                    f += column + "='" + request.form[column] + "', "

            # add a new entry
            eval("BossDatabase(" + f + ")")

            load_boss = request.form["name"]
        except:
            try:
                # update existing entry
                selected_boss = BossDatabase.selectBy(name=request.form["name"])[0]
                for column in BOSS_COLUMNS:
                    try:
                        setattr(selected_boss, column, int(request.form[column]))
                    except:
                        setattr(selected_boss, column, request.form[column])

                # load this boss
                load_boss = request.form["name"]
            except Exception as e:
                flash("Update was not possible. The following error occured: " + str(e))
                load_boss = "none"

    elif request.method == "POST" and request.form["submit"] == "Delete":

        # delete existing entry
        try:
            BossDatabase.deleteBy(name=request.form["name"])
            load_boss = "none"

        except Exception as e:
            flash("Delete was not possible. The following error occured: " + str(e))
            load_boss = "none"
    else:
        load_boss = "none"

    return render_template("boss_editor.html", load_boss=load_boss,
                           boss_list={'boss': [eval(str(row.sqlmeta.asDict()).replace("L", "")) for row in
                                               BossDatabase.select()]},
                           boss_columns=BOSS_COLUMNS)


@app.route("/char_sheet.html", methods=['GET', 'POST'])
def char_sheet():
    """render char_sheet"""

    # check if logged in
    if not "name" in session:
        flash("Please login")
        return redirect("login.html")

    # save  to database if post
    if request.method == "POST" and request.form["submit"] == "Save":
        try:
            f = ""
            for column in CHAR_COLUMNS:

                # convert int if possible
                try:
                    int(request.form[column])
                    f += column + "=" + request.form[column] + ", "
                except:
                    f += column + "='" + request.form[column] + "', "

            # add a new entry
            eval("CharDatabase(" + f + ")")

            # add a new entry
            load_char = request.form["name"]
        except:
            try:
                # update existing entry
                selected_char = CharDatabase.selectBy(name=request.form["name"])[0]
                for column in CHAR_COLUMNS:
                    try:
                        setattr(selected_char, column, int(request.form[column]))
                    except:
                        setattr(selected_char, column, request.form[column])

                # load this char
                load_char = request.form["name"]

            except Exception as e:
                flash("Update was not possible. The following error occured: " + str(e))
                load_char = "none"

    elif request.method == "POST" and request.form["submit"] == "Delete":

        # delete existing entry
        try:
            CharDatabase.deleteBy(name=request.form["name"])
            load_char = "none"
        except Exception as e:
            flash("Delete was not possible. The following error occured: " + str(e))
            load_char = "none"
    else:
        load_char = "none"

    return render_template("char_sheet.html", load_char=load_char,
                           char_list={'char': [eval(str(row.sqlmeta.asDict()).replace("L", "")) for row in
                                               CharDatabase.select()]},
                           boss_list={'boss': [eval(str(row.sqlmeta.asDict()).replace("L", "")) for row in
                                               BossDatabase.select()]},
                           char_columns=CHAR_COLUMNS)


if __name__ == '__main__':
    app.run()
