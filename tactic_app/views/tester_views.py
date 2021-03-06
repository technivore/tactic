from flask import render_template, redirect, request, url_for, flash, jsonify
from flask.ext.login import login_user, login_required, logout_user
from flask_login import current_user

from tactic_app.users import User
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Regexp, EqualTo
from tactic_app.shared_dicts import user_tiles, loaded_user_modules
from tactic_app import app, socketio, csrf

@app.route('/direct_user_manage/<username>/<password>', methods=['GET', 'POST'])
def direct_user_manage(username, password):
    user = User.get_user_by_username(username)
    if user is not None and user.verify_password(password):
        login_user(user, remember=False)
    return redirect(url_for("user_manage"))

@app.route('/direct_project/<project_name>/<username>/<password>', methods=['GET', 'POST'])
def direct_project(project_name, username, password):
    user = User.get_user_by_username(username)
    if user is not None and user.verify_password(password):
        login_user(user, remember=False)
    return redirect(url_for("main_project", project_name=project_name))

@app.route('/direct_collection/<collection_name>/<username>/<password>', methods=['GET', 'POST'])
def direct_collection(collection_name, username, password):
    user = User.get_user_by_username(username)
    if user is not None and user.verify_password(password):
        login_user(user, remember=False)
    return redirect(url_for("main", collection_name=collection_name))