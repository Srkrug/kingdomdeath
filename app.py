# imports
from flask import Flask, request, flash, redirect, session
from flask import render_template
from flask_bootstrap import Bootstrap
from werkzeug.contrib.fixers import ProxyFix
from sqlobject import *
import uuid


class BossDatabase(SQLObject):
    """connect to mysql database"""

    _connection = connectionForURI("mysql://root:Avodaq1234*@localhost/kingdomdeath")
    name = StringCol(length=255, unique=True)
    strength = IntCol()
    speed = IntCol()
    accuracy = IntCol()
    toughness = IntCol()
    evasion = IntCol()


class UserDatabase(SQLObject):
    """connect to mysql database"""

    _connection = connectionForURI("mysql://root:Avodaq1234*@localhost/kingdomdeath")
    name = StringCol(length=255, unique=True)
    password = StringCol(length=255)
    secret_key = StringCol()


class CharDatabase(SQLObject):
    """connect to mysql database"""

    _connection = connectionForURI("mysql://root:Avodaq1234*@localhost/kingdomdeath")
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

# setup flask app
app = Flask(__name__)
Bootstrap(app)
app.wsgi_app = ProxyFix(app.wsgi_app)

# create tables if necessary
BossDatabase.createTable(ifNotExists=True)
CharDatabase.createTable(ifNotExists=True)
UserDatabase.createTable(ifNotExists=True)

# create default entry if necessary
try:
    app.secret_key = UserDatabase.selectBy(name="default")[0].secret_key
except:
    UserDatabase(name="default", password="default", secret_key=str(uuid.uuid4()))
    app.secret_key = UserDatabase.selectBy(name="default")[0].secret_key


# create lists of columns
boss_columns = sorted(BossDatabase.sqlmeta.columns.keys())
char_columns = sorted(CharDatabase.sqlmeta.columns.keys())


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

            user = UserDatabase.selectBy(name=request.form["name"],password=request.form["password"])[0].name
            session['user'] = user
            flash("Login successfull")
            return redirect("/char_sheet.html")
        except:
            flash("Wrong credentials")


    # logout user
    if request.method == "POST" and request.form["submit"] == "Logout":
        session.pop('user', None)
        flash("Logout successfull")

    return render_template("/login.html")


@app.route("/boss_editor.html", methods=['GET', 'POST'])
def boss_editor():
    """render boss"""

    # check if logged in
    if not 'user' in session:
        flash("Please login")
        return redirect("login.html")

    # save  to database if post
    if request.method == "POST" and request.form["submit"] == "Save":
        try:
            f = ""
            for column in boss_columns:

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
                for column in boss_columns:
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
                           boss_list={'boss': [eval(str(row.sqlmeta.asDict()).replace("L","")) for row in BossDatabase.select()]},
                           boss_columns=boss_columns)


@app.route("/char_sheet.html", methods=['GET', 'POST'])
def char_sheet():
    """render char_sheet"""

    # check if logged in
    if not 'user' in session:
        flash("Please login")
        return redirect("login.html")

    # save  to database if post
    if request.method == "POST" and request.form["submit"] == "Save":
        try:
            f = ""
            for column in char_columns:

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
                for column in char_columns:
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
                           char_list={'char': [eval(str(row.sqlmeta.asDict()).replace("L","")) for row in CharDatabase.select()]},
                           boss_list={'boss': [eval(str(row.sqlmeta.asDict()).replace("L","")) for row in BossDatabase.select()]},
                           char_columns=char_columns)


if __name__ == '__main__':
    app.run()