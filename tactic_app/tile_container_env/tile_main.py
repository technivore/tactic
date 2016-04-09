from flask import Flask, jsonify, request
import sys
import copy
import tile_env
from tile_env import exec_tile_code

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


@app.route('/get_tile_exports', methods=["get", "post"])
def get_tile_exports():
    export_dict = tile_instance.exports
    result_dict = {"success": True, "exports": export_dict}
    return jsonify(result_dict)


@app.route('/post_event', methods=["get", "post"])
def post_event():
    data_dict = request.json
    event_name = data_dict["event_name"]
    tile_instance.post_event(event_name, data_dict)
    result_dict = {"success": True}
    return jsonify(result_dict)


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
    tile_instance.host_address = data["host_address"]
    tile_instance.user_id = data["user_id"]
    tile_instance.main_address = data["main_address"]
    tile_instance.app = app
    tile_instance.start()
    form_html = tile_instance.create_form_html()
    data["form_html"] = form_html
    return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)