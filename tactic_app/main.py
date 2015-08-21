__author__ = 'bls910'

import Queue
import threading
from tactic_app import db
from flask_login import current_user
import copy

from collections import OrderedDict
from shared_dicts import mainwindow_instances
from shared_dicts import tile_classes
current_main_id = 0

def create_new_mainwindow(user_id, collection_name):
    mw = mainWindow(user_id, collection_name)
    mainwindow_instances[mw.main_id] = mw
    mw.start()
    return mw.main_id

def create_new_mainwindow_from_project(project_dict):
    mw = mainWindow(project_dict["user_id"], project_dict["collection_name"])
    for (key, val) in project_dict.items():
        if not(key == "tile_instances"):
            mw.__dict__[key] = val
    tile_dict = project_dict["tile_instances"]
    for (handle, tile_instance) in tile_dict.items():
        mw.create_tile_from_save(tile_instance, handle)
    mainwindow_instances[mw.main_id] = mw
    mw.start()
    return mw.main_id

class mainWindow(threading.Thread):
    def __init__(self, user_id, collection_name):
        global current_main_id
        self._stopevent = threading.Event()
        self._sleepperiod = .2
        threading.Thread.__init__(self)
        self._my_q = Queue.Queue(0)
        self.update_events = ["CellChange"]
        self.tile_instances = {}
        self.current_tile_id = 0
        self.collection_name = collection_name # This isn't used yet.
        self.main_id = str(current_main_id)
        self.user_id = user_id
        (self.data_dict, self.id_list) = self.build_data_dict()

        self.signature_list = self.build_signature_list()
        self.ordered_sig_dict = OrderedDict()
        for it in self.signature_list:
            if type(it) == str or type(it) == unicode:
                the_key = it
            else:
                the_key = "-".join(it)
            self.ordered_sig_dict[the_key] = it
        current_main_id += 1
        self.change_list = []

    def run(self):
        while not self._stopevent.isSet( ):
            if (not self._my_q.empty()):
                q_item = self._my_q.get()
                if type(q_item) == dict:
                    self.handle_event(q_item["event_name"], q_item["data"])
                else:
                    self.handle_event(q_item)
            self._stopevent.wait(self._sleepperiod)

    def add_blank_column(self, column_name):
        for doc in self.data_dict["the_rows"]:
            doc[column_name] = ""

    def compile_save_dict(self):
        result = {}
        for (attr, val) in mainwindow_instances['0'].__dict__.items():
            if not ((attr.startswith("_")) or (attr == "tile_instances") or (str(type(val)) == "<type 'instance'>")):
                result[attr] = val
        tile_instance_saves = {}
        for (tile_handle, tile_instance) in self.tile_instances.items():
            tile_instance_saves[tile_handle] = tile_instance.compile_save_dict()
        result["tile_instances"] = tile_instance_saves
        return result

    def join(self, timeout=None):
        """ Stop the thread and wait for it to end. """
        self._stopevent.set()
        threading.Thread.join(self, timeout)

    def handle_event(self, event_name, data=None):
        if event_name == "CellChange":
            self.set_row_column_data(data["row_index"], data["signature"], data["new_content"])
            self.change_list.append(data["row_index"])
        elif event_name == "RemoveTile":
            del self.tile_instances[data]
        return

    def post_event(self, item):
        self._my_q.put(item)

    def create_tile(self, tile_type):
        new_id = "tile_id_" + str(self.current_tile_id)
        new_tile = tile_classes[tile_type](self.main_id, new_id)
        self.tile_instances[new_id] = new_tile
        new_tile.start()
        self.current_tile_id += 1
        return new_tile

    def create_tile_from_save(self, tile_save, id):
        new_tile = tile_classes[tile_save["tile_type"]](self.main_id, id)
        for (key, val) in tile_save.items():
            new_tile.__dict__[key] = val
        self.tile_instances[id] = new_tile
        new_tile.start()

    def build_signature_list(self):
        ddict = self.data_dict["the_rows"][0]
        result = []
        for (the_key, the_item) in ddict.items():
            if type(the_item) != dict:
                result.append(the_key)
            else:
                result += self.build_sig_step(the_item, [the_key])
        return result

    def build_sig_step(self, ddict, sofar):
        result = []
        for (the_key, the_item) in ddict.items():
            newsofar = copy.deepcopy(sofar)
            newsofar.append(the_key)
            if type(the_item) == dict:
                newsofar.append(self.build_sig_step(the_item, newsofar))
            result.append(newsofar)
        return result

    def build_data_dict(self):
        row_list = []
        id_list = []
        result = {}
        the_collection = db[self.collection_name]
        for r in the_collection.find():
            id_list.append(r["_id"])
            del r["_id"]
            row_list.append(r)
        result["the_rows"] = row_list
        result["collection_name"] = self.collection_name
        return (result, id_list)

    def get_data_for_signature(self, row, signature):
        result = row
        for field in signature:
            result = result[field]
        return result

    def set_row_column_data(self, row_index, sig, new_content):
        the_row = self.data_dict["the_rows"][row_index]
        result = the_row
        for field in sig[1:-1]:
            result = result[field[0]]
        result[sig[-1][0]] = new_content

    def get_column_data(self, signature):
        the_rows = self.data_dict["the_rows"]
        result = []
        for the_row in the_rows:
            result.append(self.get_data_for_signature(the_row, self.ordered_sig_dict[signature]))
        return result