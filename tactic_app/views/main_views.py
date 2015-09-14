__author__ = 'bls910'
from tactic_app import app, db, socketio
from flask import request, jsonify, render_template, send_file, url_for
from flask_login import current_user
from flask_socketio import join_room
from tactic_app.shared_dicts import tile_classes, user_tiles
from tactic_app.shared_dicts import mainwindow_instances
from tactic_app.main import distribute_event
from user_manage_views import render_project_list

# The main window should join a room associated with the user
@socketio.on('connect', namespace='/main')
def connected_msg():
    print"client connected"

@socketio.on('join', namespace='/main')
def on_join(data):
    room=data["room"]
    join_room(room)
    print "user joined room " + room

# Views for creating and saving a new project
# As well as for updating an existing project.

@app.route('/save_new_project', methods=['POST'])
def save_new_project():
    data_dict = request.json
    mainwindow_dict = mainwindow_instances[data_dict['main_id']].compile_save_dict()
    combined_dict = mainwindow_dict.copy()

    # It's important that data_dict is added on top of mainwindow dict
    # because it has the updated version of project_name
    combined_dict.update(data_dict)
    mainwindow_instances[data_dict['main_id']].project_name = data_dict["project_name"]
    db[current_user.project_collection_name].insert_one(combined_dict)
    socketio.emit('update-project-list', {"html": render_project_list()}, namespace='/user_manage', room=current_user.get_id())
    return jsonify({"project_name": data_dict["project_name"], "success": True, "message": "Project Successfully Saved"})

@app.route('/update_project', methods=['POST'])
def update_project():
    data_dict = request.json

    # Here's it's important that we do mainwindow before data_dict
    # bcause the new information is coming from data_dict (notably new header_struct and hidden_list)
    combined_dict = mainwindow_instances[data_dict['main_id']].compile_save_dict().copy()
    combined_dict.update(data_dict)
    db[current_user.project_collection_name].update_one({"project_name": combined_dict["project_name"]},
                                                        {'$set': combined_dict})
    return jsonify({"success": True, "message": "Project Successfully Saved"})

# Views for reading data from the database and
# passing back to the client.

@app.route('/grab_data/<main_id>/<doc_name>', methods=['get'])
def grab_data(main_id, doc_name):
    return jsonify({"doc_name": doc_name, "data_rows": mainwindow_instances[main_id].doc_dict[doc_name].data_rows})

@app.route('/grab_project_data/<main_id>/<doc_name>', methods=['get'])
def grab_project_data(main_id, doc_name):
    mw = mainwindow_instances[main_id]
    return jsonify({"doc_name": doc_name, "tile_ids": mw.tile_ids, "data_rows": mw.doc_dict[doc_name].data_rows, "tablespec_dict": mw.tablespec_dict()})

@app.route('/get_additional_params', methods=['GET'])
def get_additional_params():
    result = {"tile_types": tile_classes.keys(), "user_tile_types": user_tiles[current_user.username].keys()};
    return jsonify(result)

@app.route('/set_visible_doc/<main_id>/<doc_name>', methods=['get'])
def set_visible_doc(main_id, doc_name):
    mainwindow_instances[main_id].visible_doc_name = doc_name
    return jsonify({"success": True})

@app.route('/distribute_events/<event_name>', methods=['get', 'post'])
def distribute_events_stub(event_name):
    data_dict = request.json
    main_id = request.json["main_id"]
    if "tile_id" in request.json:
        tile_id = request.json["tile_id"]
    else:
        tile_id = None
    distribute_event(event_name, main_id, data_dict, tile_id)
    return jsonify({"success": True})

@app.route('/figure_source/<main_id>/<tile_id>/<figure_name>', methods=['GET','POST'])
def figure_source(main_id, tile_id, figure_name):
    img = mainwindow_instances[main_id].tile_instances[tile_id].images[figure_name]
    return send_file(img, mimetype='image/png')

@app.route('/create_tile_request/<tile_type>', methods=['GET','POST'])
def create_tile_request(tile_type):
    main_id = request.json["main_id"]
    tile_name = request.json["tile_name"]
    new_tile = mainwindow_instances[main_id].create_tile_instance_in_mainwindow(tile_type, tile_name)
    tile_id = new_tile.tile_id
    new_tile.figure_url = url_for("figure_source", main_id=main_id, tile_id=tile_id, figure_name="X")[:-1]
    form_html = new_tile.create_form_html()
    result = render_template("tile.html", tile_id=tile_id,
                           tile_name=new_tile.tile_name,
                           form_text=form_html)
    return jsonify({"html":result, "tile_id": tile_id})

@app.route('/create_tile_from_save_request/<tile_id>', methods=['GET','POST'])
def create_tile_from_save_request(tile_id):
    main_id = request.json["main_id"]
    tile_instance = mainwindow_instances[main_id].tile_instances[tile_id]
    tile_instance.figure_url = url_for("figure_source", main_id=main_id, tile_id=tile_id, figure_name="X")[:-1]
    form_html = tile_instance.create_form_html()
    result = render_template("tile.html", tile_id=tile_id,
                           tile_name=tile_instance.tile_name,
                           form_text=form_html)
    return jsonify({"html":result, "tile_id": tile_id})
