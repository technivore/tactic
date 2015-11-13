
import nltk
import sys
import copy
# I want nltk to only search here so that I can see
# what behavior on remote will be like.
nltk.data.path = ['./nltk_data/']
from nltk.corpus import wordnet as wn
from flask_login import current_user
from flask import url_for
from matplotlib_utilities import GraphList, ColorMapper, FigureCanvas

from tile_base import TileBase
from shared_dicts import mainwindow_instances, distribute_event
from shared_dicts import tile_classes, user_tiles, tokenizer_dict, weight_functions
from users import load_user
from tactic_app.clusterer_classes import CentroidClusterer, OptCentroidClusterer
import numpy

# Decorator function used to register runnable analyses in analysis_dict
def tile_class(tclass):
    tile_classes[tclass.__name__] = tclass
    return tclass

def weight_function(wfunc):
    weight_functions[wfunc.__name__] = wfunc
    return wfunc

def user_tile(tclass):
    uname = current_user.username
    if not (uname in user_tiles):
        user_tiles[uname] = {}
    user_tiles[uname][tclass.__name__] = tclass
    return tclass

def create_user_tiles(tile_code):
    try:
        exec tile_code in globals(), globals()
    except:
        return str(sys.exc_info()[0]) + " "  + str(sys.exc_info()[1])
    return "success"