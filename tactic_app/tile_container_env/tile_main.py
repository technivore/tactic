from flask import Flask, jsonify, request
import sys
import copy
import tile_env
from tile_env import exec_tile_code
import cPickle
from bson.binary import Binary

app = Flask(__name__)

tile_instance = None


@app.route('/')
def hello():
    return 'This is the provider communicating'


@app.route('/load_source', methods=["get", "post"])
def load_source():
    app.logger.debug("entering load_source")
    data_dict = request.json
    # app.logger.debug("data_dict is " + str(data_dict))
    tile_code = data_dict["tile_code"]
    result = exec_tile_code(tile_code)
    return jsonify(result)


@app.route("/recreate_from_save", methods=["get", "post"])
def recreate_from_save():
    app.logger.debug("entering recreate_from_save")
    global tile_instance
    from tile_env import tile_class
    data = copy.copy(request.json)
    app.logger.debug("creating tile instance")
    tile_instance = tile_class(data["main_id"], data["tile_id"],
                               data["tile_name"])
    app.logger.debug("tile instance is complete")
    tile_instance.base_figure_url = data["base_figure_url"]
    tile_instance.app = app
    tile_instance.recreate_from_save(data)
    tile_instance.app = app
    tile_instance.start()
    return jsonify({"is_shrunk": tile_instance.is_shrunk,
                    "saved_size": tile_instance.full_tile_height,
                    "exports": tile_instance.exports,
                    "tile_name": tile_instance.tile_name})


@app.route("/render_tile", methods=["get", "post"])
def render_tile():
    return jsonify({"tile_html": tile_instance.render_me()})


@app.route('/get_save_dict', methods=["get", "post"])
def get_save_dict():
    save_dict = tile_instance.compile_save_dict()
    return jsonify(save_dict)


@app.route('/get_property/<property_name>', methods=["get", "post"])
def get_property(property_name):
    val = getattr(tile_instance, property_name)
    return jsonify({"val": val})


@app.route('/transfer_pipe_value', methods=["get", "post"])
def transfer_pipe_value():
    export_name = request.json["export_name"]
    encoded_val = Binary(cPickle.dumps(getattr(tile_instance, export_name)))
    return jsonify({"encoded_val": encoded_val})


@app.route('/get_tile_exports', methods=["get", "post"])
def get_tile_exports():
    export_dict = tile_instance.exports
    result_dict = {"success": True, "exports": export_dict}
    return jsonify(result_dict)


@app.route('/post_event', methods=["get", "post"])
def post_event():
    app.logger.debug("entering post_event in tile_main")
    data_dict = request.json
    event_name = data_dict["event_name"]
    tile_instance.post_event(event_name, data_dict)
    result_dict = {"success": True}
    app.logger.debug("leaving post_event in tile_main")
    return jsonify(result_dict)


@app.route('/get_image/<figure_name>', methods=["get", "post"])
def get_image(figure_name):
    encoded_img = Binary(cPickle.dumps(tile_instance.img_dict[figure_name]))
    return jsonify({"img": encoded_img})


@app.route('/instantiate_tile_class', methods=["get", "post"])
def instantiate_tile_class():
    app.logger.debug("entering instantiate_tile_class")
    global tile_instance
    from tile_env import tile_class
    data = copy.copy(request.json)
    app.logger.debug("creating tile instance")
    tile_instance = tile_class(data["main_id"], data["tile_id"],
                               data["tile_name"])
    app.logger.debug("tile instance is complete")
    tile_instance.user_id = data["user_id"]
    tile_instance.base_figure_url = data["base_figure_url"]
    tile_instance.app = app
    tile_instance.start()
    app.logger.debug("about to create form html")
    form_html = tile_instance.create_form_html()
    data["form_html"] = form_html
    app.logger.debug("leaving instantiate_tile_class")
    return jsonify(data)


@app.route('/reinstantiate_tile', methods=["get", "post"])
def reinstantiate_tile():
    app.logger.debug("entering reinstantiate_tile_class")
    global tile_instance
    from tile_env import tile_class
    reload_dict = copy.copy(request.json)
    app.logger.debug("creating tile instance")
    # tile_instance.kill()
    tile_instance = tile_class(reload_dict["main_id"], reload_dict["tile_id"],
                               reload_dict["tile_name"])
    for (attr, val) in reload_dict.items():
        setattr(tile_instance, attr, val)
    tile_instance.app = app
    tile_instance.start()
    app.logger.debug("about to create form html")
    form_html = tile_instance.create_form_html()
    app.logger.debug("leaving reinstantiate_tile_class")
    return jsonify({"success": True, "form_html": form_html})


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)