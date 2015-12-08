__author__ = 'bls910'


import datetime

mainwindow_instances = {}
tile_classes = {}
user_tiles = {}
tokenizer_dict = {}
loaded_user_modules = {}
weight_functions = {}

def distribute_event(event_name, main_id, data_dict=None, tile_id=None):
    try:
        mwindow = mainwindow_instances[main_id]
        if tile_id is not None:
            tile_instance = mwindow.tile_instances[tile_id]
            tile_instance.post_event(event_name, data_dict)
        else:
            for tile_id, tile_instance in mwindow.tile_instances.items():
                tile_instance.post_event(event_name, data_dict)
        if event_name in mwindow.update_events:
            mwindow.post_event(event_name, data_dict)
        return True
    except:
        mwindow.handle_exception("Error distributing event " + event_name)
        return False

def get_tile_class(username, tile_type):
    if username in user_tiles:
        for (category, dict) in user_tiles[username].items():
            if tile_type in dict:
                return dict[tile_type]
    for (category, dict) in tile_classes.items():
        if tile_type in dict:
            return dict[tile_type]
    return None


def create_initial_metadata():
    mdata = {"datetime": datetime.datetime.today(),
             "tags": "",
             "notes": ""}
    return mdata