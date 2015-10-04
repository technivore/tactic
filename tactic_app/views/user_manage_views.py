__author__ = 'bls910'

import os
import pymongo
from flask import render_template, request, make_response, redirect, url_for, jsonify
from tactic_app import app, db, socketio
from tactic_app.file_handling import read_xml_file_to_dict_list, read_csv_file_to_dict_list, read_txt_file_to_dict_list, load_a_list;
from tactic_app.main import create_new_mainwindow, create_new_mainwindow_from_project, mainwindow_instances
from tactic_app.users import put_docs_in_collection, build_data_collection_name
from tactic_app.tiles import create_user_tiles
from tactic_app.shared_dicts import user_tiles, loaded_user_modules
from flask_login import current_user
from flask_socketio import join_room

@app.route('/user_manage')
def user_manage():
    if current_user.username in user_tiles:
        user_tile_name_list = user_tiles[current_user.username].keys()
    else:
        user_tile_name_list = []
    return render_template('user_manage/user_manage.html', user_tile_name_list=user_tile_name_list)

@app.route('/main/<collection_name>', methods=['get'])
def main(collection_name):
    cname=build_data_collection_name(collection_name)
    main_id = create_new_mainwindow(current_user.get_id(), collection_name=cname)
    doc_names = mainwindow_instances[main_id].doc_names
    short_collection_name = mainwindow_instances[main_id].short_collection_name
    if current_user.username not in loaded_user_modules:
        loaded_user_modules[current_user.username] = set([])

    # the loaded_modules must be a list to be easily saved to pymongo
    mainwindow_instances[main_id].loaded_modules = list(loaded_user_modules[current_user.username])
    return render_template("main.html",
                           collection_name=cname,
                           project_name='',
                           main_id=main_id,
                           doc_names=doc_names,
                           short_collection_name=short_collection_name)

@app.route('/main_project/<project_name>', methods=['get'])
def main_project(project_name):
    project_dict = db[current_user.project_collection_name].find_one({"project_name": project_name})
    if current_user.username not in loaded_user_modules:
        loaded_user_modules[current_user.username] = set([])
    for module in project_dict["loaded_modules"]:
        if module not in loaded_user_modules[current_user.username]:
            load_tile_module(module)
    main_id = create_new_mainwindow_from_project(project_dict)
    doc_names = mainwindow_instances[main_id].doc_names
    short_collection_name = mainwindow_instances[main_id].short_collection_name

    # We want to do this in case there were some additional modules loaded


    # the loaded_modules must be a list to be easily saved to pymongo
    mainwindow_instances[main_id].loaded_modules = list(loaded_user_modules[current_user.username])
    return render_template("main.html",
                           collection_name=project_dict["collection_name"],
                           project_name=project_name,
                           main_id=main_id,
                           doc_names=doc_names,
                           short_collection_name=short_collection_name)

@app.route('/view_list/<list_name>', methods=['get'])
def view_list(list_name):
    the_list = current_user.get_list(list_name)
    return render_template("user_manage/list_viewer.html",
                           list_name=list_name,
                           the_list=the_list)

@app.route('/view_module/<module_name>', methods=['get'])
def view_module(module_name):
    # the_list = current_user.get_list(list_name)
    module_code = current_user.get_tile_module(module_name)
    return render_template("user_manage/module_viewer.html",
                           module_name=module_name,
                           module_code=module_code)


@app.route('/load_tile_module/<tile_module_name>', methods=['get', 'post'])
def load_tile_module(tile_module_name):
    tile_module = current_user.get_tile_module(tile_module_name)
    create_user_tiles(tile_module)
    if current_user.username not in loaded_user_modules:
        loaded_user_modules[current_user.username] = set([])
    loaded_user_modules[current_user.username].add(tile_module_name)
    socketio.emit('update-loaded-tile-list', {"html": render_loaded_tile_list(),
                                            "user_tile_name_list": user_tiles[current_user.username].keys()},
                                         namespace='/user_manage', room=current_user.get_id())
    socketio.emit('update-loaded-tile-list', {"html": render_loaded_tile_list(),
                                        "user_tile_name_list": user_tiles[current_user.username].keys()},
                                     namespace='/main', room=current_user.get_id())
    return make_response("", 204)


def render_loaded_tile_list():
    return render_template("user_manage/loaded_tile_list.html", user_tile_name_list=user_tiles[current_user.username].keys())

def render_project_list():
    return render_template("user_manage/project_list.html")

def render_collection_list():
    return render_template("user_manage/collection_list.html")

def render_list_list():
    return render_template("user_manage/list_list.html")

def render_tile_module_list():
    return render_template("user_manage/tile_module_list.html")

@app.route('/create_duplicate_list', methods=['post'])
def create_duplicate_list():
    list_to_copy = request.json['list_to_copy']
    new_list_name = request.json['new_list_name']
    old_list_dict = db[current_user.list_collection_name].find_one({"list_name": list_to_copy})
    new_list_dict = {"list_name": new_list_name, "the_list": old_list_dict["the_list"]}
    db[current_user.list_collection_name].insert_one(new_list_dict)
    socketio.emit('update-list-list', {"html": render_list_list()}, namespace='/user_manage', room=current_user.get_id())
    return jsonify({"success": True})

@app.route('/add_list', methods=['POST', 'GET'])
def add_list():
    file = request.files['file']
    the_list = load_a_list(file)
    data_dict = {"list_name": file.filename, "the_list": the_list}
    db[current_user.list_collection_name].insert_one(data_dict)
    socketio.emit('update-list-list', {"html": render_list_list()}, namespace='/user_manage', room=current_user.get_id())
    return make_response("", 204)

@app.route('/add_tile_module', methods=['POST', 'GET'])
def add_tile_module():
    f = request.files['file']
    the_module = f.read()
    data_dict = {"tile_module_name": f.filename, "tile_module": the_module}
    db[current_user.tile_collection_name].insert_one(data_dict)
    socketio.emit('update-tile-module-list', {"html": render_tile_module_list()}, namespace='/user_manage', room=current_user.get_id())
    return make_response("", 204)

# @app.route('/load_single_file', methods=['POST', 'GET'])
# def load_single_file():
#     file = request.files['file']
#     filename, file_extension = os.path.splitext(file.filename)
#     if file_extension == ".xml":
#         (collection_name, dict_list) = read_xml_file_to_dict_list(file)
#     elif file_extension == ".csv":
#         (collection_name, dict_list) = read_csv_file_to_dict_list(file)
#     else:
#         return jsonify({"message": "Not a valid file extension", "alert_type": "alert-danger"})
#     if collection_name is None: # then dict_list contains an error object
#         e = dict_list # For clarity
#         return jsonify({"message": e.message, "alert_type": "alert-danger"})
#     try:
#         put_docs_in_collection(build_data_collection_name(collection_name), dict_list)
#         socketio.emit('update-collection-list', {"html": render_collection_list()}, namespace='/user_manage', room=current_user.get_id())
#     except pymongo.errors.InvalidStringData:
#         print "Strings in documents must be valid UTF-8"
#     # current_user.add_collection(collection_name)
#     return jsonify({"message":"File successfully loaded", "alert_type": "alert-success"})

@app.route('/load_files/<collection_name>', methods=['POST', 'GET'])
def load_files(collection_name):
    file_list = request.files.getlist("file")
    full_collection_name = build_data_collection_name(collection_name)

    for file in file_list:
        filename, file_extension = os.path.splitext(file.filename)
        if file_extension == ".xml":
            (success, dict_list) = read_xml_file_to_dict_list(file)
            header_list = []
        elif file_extension == ".csv":
            (success, dict_list, header_list) = read_csv_file_to_dict_list(file)
        elif file_extension ==".txt":
            (success, dict_list, header_list) = read_txt_file_to_dict_list(file)
        else:
            return jsonify({"message": "Not a valid file extension " + file_extension, "alert_type": "alert-danger"})
        if not success: # then dict_list contains an error object
            e = dict_list # For clarity
            return jsonify({"message": e.message, "alert_type": "alert-danger"})

        try:
            db[full_collection_name].insert_one({"name": filename, "data_rows": dict_list, "header_list": header_list})
        except pymongo.errors.InvalidStringData:
            print "Strings in documents must be valid UTF-8"

    socketio.emit('update-collection-list', {"html": render_collection_list()}, namespace='/user_manage', room=current_user.get_id())
    return jsonify({"message":"Collection successfully loaded", "alert_type": "alert-success"})

@app.route('/delete_project/<project_name>', methods=['post'])
def delete_project(project_name):
    db[current_user.project_collection_name].delete_one({"project_name": project_name})
    socketio.emit('update-project-list', {"html": render_project_list()}, namespace='/user_manage', room=current_user.get_id())
    return
    # return render_template("project_list.html")

@app.route('/delete_list/<list_name>', methods=['post'])
def delete_list(list_name):
    db[current_user.list_collection_name].delete_one({"list_name": list_name})
    socketio.emit('update-list-list', {"html": render_list_list()}, namespace='/user_manage', room=current_user.get_id())
    return jsonify({"success": True})

@app.route('/delete_tile_module/<tile_module_name>', methods=['post'])
def delete_tile_module(tile_module_name):
    db[current_user.tile_collection_name].delete_one({"tile_module_name": tile_module_name})
    socketio.emit('update-tile-module-list', {"html": render_tile_module_list()}, namespace='/user_manage', room=current_user.get_id())
    return jsonify({"success": True})

@app.route('/delete_collection/<collection_name>', methods=['post'])
def delete_collection(collection_name):
    db.drop_collection(current_user.full_collection_name(collection_name))
    socketio.emit('update-collection-list', {"html": render_collection_list()}, namespace='/user_manage', room=current_user.get_id())
    return jsonify({"success": True})

@app.route('/duplicate_collection', methods=['post'])
def duplicate_collection():
    collection_to_copy = current_user.full_collection_name(request.json['collection_to_copy'])
    new_collection_name = current_user.full_collection_name(request.json['new_collection_name'])
    for doc in db[collection_to_copy].find():
        db[new_collection_name].insert_one(doc)
    socketio.emit('update-collection-list', {"html": render_collection_list()}, namespace='/user_manage', room=current_user.get_id())
    return jsonify({"success": True})

@app.route('/update_module', methods=['post'])
def update_module():
    data_dict = request.json
    module_name = data_dict["module_name"]
    module_code = data_dict["new_code"]
    db[current_user.tile_collection_name].update_one({"tile_module_name": module_name},
                                                        {'$set': {"tile_module": module_code}})
    return jsonify({"success": True, "message": "Module Successfully Saved", "alert_type": "alert-success"})

@socketio.on('connect', namespace='/user_manage')
def connected_msg():
    print"client connected"

@socketio.on('join', namespace='/user_manage')
def on_join(data):
    room=data["user_id"]
    join_room(room)
    print "user joined room " + room