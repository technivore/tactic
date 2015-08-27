__author__ = 'bls910'

import Queue
import threading
import nltk
# I want nltk to only search here so that I can see
# what behavior on remote will be like.
nltk.data.path = ['./nltk_data/']
from nltk.corpus import wordnet as wn
from flask_login import current_user

from tactic_app import socketio
from shared_dicts import mainwindow_instances
from vector_space import Vocabulary
from shared_dicts import tile_classes, tokenizer_dict
from users import load_user


# Decorator function used to register runnable analyses in analysis_dict
def tile_class(tclass):
    tile_classes[tclass.__name__] = tclass
    return tclass

class TileBase(threading.Thread):
    options = []
    input_start_template = '<div class="form-group">' \
                     '<label>{0}</label>'
    basic_input_template = '<input type="{1}" class="form-control" id="{0}" placeholder="{2}">' \
                     '</div>'
    select_base_template = '<select class="form-control" id="{0}">'
    select_option_template = '<option value="{0}">{0}</option>'

    def __init__(self, main_id, tile_id):
        self._stopevent = threading.Event()
        self._sleepperiod = .2
        threading.Thread.__init__(self)
        global current_tile_id
        self.update_events = ["RefreshTile", "UpdateOptions", "ShowFront"]
        self.tile_id = tile_id
        self.main_id = main_id
        self._my_q = Queue.Queue(0)
        self.current_html = None
        self.tile_type = self.__class__.__name__
        return

    def run(self):
        while not self._stopevent.isSet( ):
            if (not self._my_q.empty()):
                q_item = self._my_q.get()
                if type(q_item) == dict:
                    self.handle_event(q_item["event_name"], q_item["data"])
                else:
                    self.handle_event(q_item)
            self._stopevent.wait(self._sleepperiod)

    def join(self, timeout=None):
        """ Stop the thread and wait for it to end. """
        self._stopevent.set( )
        threading.Thread.join(self, timeout)

    def post_event(self, item):
        self._my_q.put(item)

    def spin_and_refresh(self):
        self.post_event("StartSpinner")
        self.post_event("RefreshTile")
        self.post_event("StopSpinner")


    def handle_event(self, event_name, data=None):
        if event_name == "RefreshTile":
            self.push_direct_update()
        elif event_name == "RefreshTileFromSave":
            self.push_direct_update(self.current_html)
        elif event_name == "UpdateOptions":
            self.update_options(data)
        elif event_name =="ShowFront":
            self.show_front()
        elif event_name=="StartSpinner":
            self.start_spinner()
        elif event_name=="StopSpinner":
            self.stop_spinner()
        return

    def update_data(self, data):
        print "update data not implemented"
        return

    def update_options(self, form_data):
        return

    def show_front(self):
        socketio.emit("tile-message",
                      {"tile_id": str(self.tile_id), "message": "showFront"},
                      namespace='/main', room=self.main_id)

    def push_direct_update(self, new_html=None):
        if new_html == None:
            new_html = self.render_content()
        self.current_html = new_html
        socketio.emit("tile-message",
                      {"tile_id": str(self.tile_id), "message": "displayTileContent", "html": new_html},
                      namespace='/main', room=self.main_id)

    def start_spinner(self):
        # socketio.emit("start-spinner", {"tile_id": str(self.tile_id)}, namespace='/main', room=self.main_id)
        socketio.emit("tile-message",
                      {"tile_id": str(self.tile_id), "message": "startSpinner"},
                      namespace='/main', room=self.main_id)

    def stop_spinner(self):
        # socketio.emit("stop-spinner", {"tile_id": str(self.tile_id)}, namespace='/main', room=self.main_id)
        socketio.emit("tile-message",
              {"tile_id": str(self.tile_id), "message": "stopSpinner"},
              namespace='/main', room=self.main_id)

    def render_content(self):
        print "not implemented"

    def compile_save_dict(self):
        result = {}
        for (attr, val) in self.__dict__.items():
            if not ((attr.startswith("_")) or (attr == "additionalInfo") or (str(type(val)) == "<type 'instance'>")):
                result[attr] = val
        result["tile_type"] = type(self).__name__
        result.update(self.cache_dicts())
        return result

    def cache_dicts(self):
        return {}

    # Not currently used
    # def initiate_update(self):
    #     socketio.emit("tile-message",
    #           {"tile_id": str(self.tile_id), "message": "initiateTileRefresh"},
    #           namespace='/main', room=self.main_id)

    @property
    def current_user(self):
        user_id = mainwindow_instances[self.main_id].user_id
        current_user = load_user(user_id)
        return current_user

    def get_user_list(self, the_list):
        return self.current_user.get_list(the_list)

    def create_form_html(self):
        form_html = ""
        for option in self.options:
            if option["type"] == "column_select":
                the_template = self.input_start_template + self.select_base_template
                form_html += the_template.format(option["name"])
                for choice in mainwindow_instances[self.main_id].ordered_sig_dict.keys():
                    form_html += self.select_option_template.format(choice)
                form_html += '</select></div>'
            elif option["type"] == "tokenizer_select":
                the_template = self.input_start_template + self.select_base_template
                form_html += the_template.format(option["name"])
                for choice in tokenizer_dict.keys():
                    form_html += self.select_option_template.format(choice)
                form_html += '</select></div>'
            elif option["type"] == "list_select":
                the_template = self.input_start_template + self.select_base_template
                form_html += the_template.format(option["name"])
                for choice in current_user.list_names:
                    form_html += self.select_option_template.format(choice)
                form_html += '</select></div>'
            else:
                the_template = self.input_start_template + self.basic_input_template
                form_html += the_template.format(option["name"], option["type"], option["placeholder"])
        return form_html

class SelectionTile(TileBase):
    def __init__(self, main_id, tile_id):
        TileBase.__init__(self, main_id, tile_id)
        self.update_events.append("text_select")
        self.selected_text = ""
        self.tile_type = self.__class__.__name__
        return

    def update_data(self, data):
        self.selected_text = data["selected_text"]
        return

    def handle_event(self, event_name, data=None):
        if event_name == "text_select":
            self.update_data(data);
            self.push_direct_update()
        TileBase.handle_event(self, event_name, data)

    def render_content(self):
        return self.selected_text

@tile_class
class SimpleSelectionTile(SelectionTile):
    options = [{
        "name": "extra_text",
        "type": "text",
        "placeholder":"no selection"
    }]
    def __init__(self, main_id, tile_id):
        SelectionTile.__init__(self, main_id, tile_id)
        self.extra_text = "placeholder text"
        self.selected_text = "no selection"
        self.tile_type = self.__class__.__name__

    def render_content(self):
        return "{} {}".format(self.extra_text, self.selected_text)

    def update_options(self, form_data):
        self.extra_text = form_data["extra_text"]
        self.spin_and_refresh()

@tile_class
class WordnetSelectionTile(SelectionTile):
    options = [{
        "name": "number_to_show",
        "type": "text",
        "placeholder": "5"}]
    def __init__(self, main_id, tile_id):
        SelectionTile.__init__(self, main_id, tile_id)
        self.selected_text = "no selection"
        self.to_show = 5
        self.tile_type = self.__class__.__name__

    def render_content(self):
        res = wn.synsets(self.selected_text)[:self.to_show]
        return "<div>Synsets are:</div><div>{}</div>".format(res)

    def update_options(self, form_data):
        self.to_show = int(form_data["number_to_show"])
        self.post_event("ShowFront")
        self.spin_and_refresh()
        return

@tile_class
class ColumnSourceTile(TileBase):
    options=[{
        "name": "column_source",
        "type": "column_select",
        "placeholder": ""
    }]

    def __init__(self, main_id, tile_id):
        TileBase.__init__(self, main_id, tile_id)
        self.column_source = None
        self.update_events = ["RefreshTile", "UpdateOptions", "ColumnChange"]
        self.tile_type = self.__class__.__name__

    def render_content(self):
        return "Column selected is {}".format(self.column_source)

    def update_options(self, form_data):
        self.column_source = form_data["column_source"]
        self.post_event("ShowFront")
        self.spin_and_refresh()
        # self.push_direct_update()

@tile_class
class VocabularyDisplayTile(ColumnSourceTile):
    options = ColumnSourceTile.options + [
        {"name": "tokenizer", "type": "tokenizer_select", "placeholder": ""},
        {"name": "stop_list", "type": "list_select", "placeholder": ""}]

    def __init__(self, main_id, tile_id):
        ColumnSourceTile.__init__(self, main_id, tile_id)
        self.update_events.append("CellChange")
        self.tokenizer_func = None
        self._vocab = None
        self.stop_list = None
        self.tile_type = self.__class__.__name__

    def tokenize_rows(self, the_rows, the_tokenizer):
        tokenized_rows = []
        for raw_row in the_rows:
            if raw_row != None:
                tokenized_rows.append(tokenizer_dict[the_tokenizer](raw_row))
        return tokenized_rows

    def build_html_table_from_data_list(self, data_list):
        the_html = "<table><thead><tr>"
        for c in data_list[0]:
            the_html += "<th>{0}</th>".format(c)
        the_html += "</tr><tbody>"
        for r in data_list[1:]:
            the_html += "<tr>"
            for c in r:
                the_html += "<td>{0}</td>".format(c)
            the_html += "</tr>"
        the_html += "</tbody></table>"
        return the_html

    def handle_event(self, event_name, data=None):
        if event_name == "CellChange":
            # data will have the keys row_index, column_idex, signature, old_content, new_content
            if self._vocab is None:
                if self.column_source == None:
                    self.push_direct_update("No column source selected.")
                    return
                raw_rows = self.load_raw_column(self.column_source)
                raw_rows[data["row_index"]] = data["new_content"]
                tokenized_rows = self.tokenize_rows(raw_rows, self.tokenizer_func)
                self._vocab = Vocabulary(tokenized_rows, self.stop_list)
                self.vdata_table = self._vocab.vocab_data_table()
                the_html = self.build_html_table_from_data_list(self.vdata_table)
                return self.push_direct_update(the_html)
            else:
                old_tokenized = tokenizer_dict[self.tokenizer_func](data["old_content"])
                new_tokenized = tokenizer_dict[self.tokenizer_func](data["new_content"])
                self._vocab.update_vocabulary(old_tokenized, new_tokenized)
                self.vdata_table = self._vocab.vocab_data_table()
                the_html = self.build_html_table_from_data_list(self.vdata_table)
                self.push_direct_update(the_html)
                return
        else:
            ColumnSourceTile.handle_event(self, event_name, data)

    def render_content(self):
        if self.column_source == None:
            return "No column source selected."
        raw_rows = self.load_raw_column(self.column_source)
        tokenized_rows = self.tokenize_rows(raw_rows, self.tokenizer_func)
        self._vocab = Vocabulary(tokenized_rows, self.stop_list)
        self.vdata_table = self._vocab.vocab_data_table()
        the_html = self.build_html_table_from_data_list(self.vdata_table)
        return the_html

    def load_raw_column(self, column_signature):
        return mainwindow_instances[self.main_id].get_column_data(column_signature)

    def update_options(self, form_data):
        self.column_source = form_data["column_source"];
        self.tokenizer_func = form_data["tokenizer"];
        self.stop_list = self.get_user_list(form_data["stop_list"])
        self.post_event("ShowFront");
        self.spin_and_refresh()