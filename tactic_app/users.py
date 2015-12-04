
# This module contains the User class machinery required by flask-login

import re
from flask.ext.login import UserMixin
from flask_login import current_user
from tactic_app import login_manager, db
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

def build_data_collection_name(collection_name):
    return '{}.data_collection.{}'.format(current_user.username, collection_name)

def put_docs_in_collection(collection_name, dict_list):
    return db[collection_name].insert_many(dict_list)


@login_manager.user_loader
def load_user(userid):
    # This expects that userid will be a string
    # If it's an ObjectId, rather than a string, I get an error likely having to do with login_manager
    result = db.user_collection.find_one({"_id": ObjectId(userid)})

    if result is None:
        return None
    else:
        return User(result)

class User(UserMixin):
    def __init__(self, user_dict):
        self.username = user_dict["username"]
        self.password_hash = user_dict["password_hash"]

    @staticmethod
    def get_user_by_username(username):
        result = db.user_collection.find_one({"username": username})
        if result is None:
            return None
        else:
            return User(result)

    def create_collection_meta_data(self, collection_type):
        result = {
            "username": self.username,
            "user_id": self.get_id(),
            "collection_type": collection_type
        }
        return result

    @staticmethod
    def create_new(user_dict):
        username = user_dict["username"]
        if len(username) < 4:
            return {"success": False, "message": "Usernames must be at least 4 characters.", "username": username}
        if "." in username:
            return {"success": False, "message": "Usernames cannot contain a period.", "username": username}
        password = user_dict["password"]
        if len(password) < 4:
            return {"success": False, "message": "Passwords must be at least 4 characters.", "username": username}
        if db.user_collection.find_one({"username": username}) is not None:
            return {"success": False, "message": "That username is taken.", "username": username}
        password_hash = generate_password_hash(password)
        new_user_dict = {"username": username, "password_hash": password_hash}
        db.user_collection.insert_one(new_user_dict)
        return {"success": True, "message": "", "username": username}

    # get_id is required by login_manager
    def get_id(self):
        # Note that I have to convert this to a string for login_manager to be happy.
        return str(db.user_collection.find_one({"username": self.username})["_id"])

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_user_dict(self):
        return {"username": self.username, "password_hash": self.password_hash}

    @property
    def project_collection_name(self):
        return '{}.projects'.format(self.username)

    @property
    def list_collection_name(self):
        return '{}.lists'.format(self.username)

    @property
    def tile_collection_name(self):
        return '{}.tiles'.format(self.username)

    @property
    def my_record(self):
        return db.user_collection.find_one({"username": self.username})

    @property
    def data_collections(self):
        cnames = db.collection_names()
        string_start =self.username + ".data_collection."
        my_collection_names = []
        for cname in cnames:
            m = re.search(string_start + "(.*)", cname)
            if m:
                my_collection_names.append(m.group(1))
        return sorted([str(t) for t in my_collection_names], key=str.lower)

    def full_collection_name(self, cname):
        return self.username + ".data_collection." + cname

    @property
    def project_names(self):
        if self.project_collection_name not in db.collection_names():
            db.create_collection(self.project_collection_name)
            return []
        my_project_names = []
        for doc in db[self.project_collection_name].find():
            my_project_names.append(doc["project_name"])
        return sorted([str(t) for t in my_project_names], key=str.lower)

    @property
    def list_names(self):
        if self.list_collection_name not in db.collection_names():
            db.create_collection(self.list_collection_name)
            return []
        my_list_names = []
        for doc in db[self.list_collection_name].find():
            my_list_names.append(doc["list_name"])
        return sorted([str(t) for t in my_list_names], key=str.lower)

    def get_resource_names(self, res_type, tag_filter=None, search_filter=None):
        if res_type == "collection":
            dcollections = self.data_collections
            res_names = []
            for dcol in dcollections:
                cname=build_data_collection_name(dcol)
                mdata = db[cname].find_one({"name": "__metadata__"})
                if tag_filter is not None:
                    if mdata is not None and "tags" in mdata:
                        if tag_filter in mdata["tags"]:
                            res_names.append(dcol)
                elif search_filter is not None:
                    if search_filter in dcol:
                        res_names.append(dcol)
                else:
                    res_names.append(dcol)
        else:
            cnames = {"tile": self.tile_collection_name, "list": self.list_collection_name, "project": self.project_collection_name}
            name_keys = {"tile": "tile_module_name", "list": "list_name", "project": "project_name"}
            cname = cnames[res_type]
            name_key = name_keys[res_type]
            if cname not in db.collection_names():
                db.create_collection(cname)
                return []
            res_names = []
            for doc in db[cname].find():
                if tag_filter is not None:
                    if "metadata" in doc:
                        if "tags" in doc["metadata"]:
                            if tag_filter in doc["metadata"]["tags"]:
                                res_names.append(doc[name_key])
                elif search_filter is not None:
                    if search_filter in doc[name_key]:
                        res_names.append(doc[name_key])
                else:
                    res_names.append(doc[name_key])
        return sorted([str(t) for t in res_names], key=str.lower)

    @property
    def tile_module_names(self,):
        if self.tile_collection_name not in db.collection_names():
            db.create_collection(self.tile_collection_name)
            return []
        my_tile_names = []
        for doc in db[self.tile_collection_name].find():
            my_tile_names.append(doc["tile_module_name"])
        return sorted([str(t) for t in my_tile_names], key=str.lower)

    def get_list(self, list_name):
        list_dict = db[self.list_collection_name].find_one({"list_name": list_name})
        return list_dict["the_list"]

    def get_tile_module(self, tile_module_name):
        tile_dict = db[self.tile_collection_name].find_one({"tile_module_name": tile_module_name})
        return tile_dict["tile_module"]
