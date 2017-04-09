# imports
from flask import Flask, request, flash
from flask import render_template
from flask_bootstrap import Bootstrap
from collections import OrderedDict
from sqlobject import *
import os


class BossDatabase(SQLObject):
    """connect to mysql database"""

    _connection = connectionForURI("mysql://root:cisco@localhost/kingdomdeath")
    name = StringCol(length=255, unique=True)
    strength = IntCol()
    speed = IntCol()
    accuracy = IntCol()
    toughness = IntCol()
    evasion = IntCol()


class CharDatabase(SQLObject):
    """connect to mysql database"""

    _connection = connectionForURI("mysql://root:cisco@localhost/kingdomdeath")
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
app.secret_key = os.urandom(24)

# create tables if necessary
BossDatabase.createTable(ifNotExists=True)
CharDatabase.createTable(ifNotExists=True)

# create lists of columns
boss_columns = sorted(BossDatabase.sqlmeta.columns.keys())
char_columns = sorted(CharDatabase.sqlmeta.columns.keys())

@app.route("/", methods=['GET', 'POST'])
def default():
    """redirect to default"""

    return boss_editor()


@app.route("/boss_editor.html", methods=['GET', 'POST'])
def boss_editor():
    """render boss"""

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
                           boss_list={'boss': [row.sqlmeta.asDict() for row in BossDatabase.select()]},
                           boss_columns=boss_columns)


@app.route("/char_sheet.html", methods=['GET', 'POST'])
def char_sheet():
    """render char_sheet"""

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
                           char_list={'char': [row.sqlmeta.asDict() for row in CharDatabase.select()]},
                           boss_list={'boss': [row.sqlmeta.asDict() for row in BossDatabase.select()]},
                           char_columns=char_columns)


app.run(host='0.0.0.0')
