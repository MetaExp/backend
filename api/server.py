from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from util.config import REACT_PORT, API_PORT
from util.meta_path_loader import MetaPathLoaderDispatcher
from active_learning.meta_path_selector import RandomMetaPathSelector
import json

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:{}".format(REACT_PORT)}})


def run(port, hostname, debug_mode):
    app.run(host=hostname, port=port, debug=debug_mode)


# TODO: If meta-paths for A and B will be written in Java, they will need this information in Java
@app.route("/node-sets", methods=["POST"])
def receive_node_sets():
    # TODO: Check if necessary information is in request object
    if not request.json:
        abort(400)


@app.route("/node-sets", methods=["GET"])
def send_node_sets():
    # TODO: Call fitting method in active_learning
    return jsonify("Hello world")


# TODO: If meta-paths for A and B will be written in Java, they will need this information in Java
@app.route("/types", methods=["POST"])
def receive_edge_node_types():
    # TODO: Check if necessary information is in request object
    if not request.json:
        abort(400)


mock_id = 1
@app.route("/next-meta-paths", methods=["GET"])
def send_next_metapaths_to_rate():
    global mock_id
    batch_size = 5
    meta_path_loader = MetaPathLoaderDispatcher().get_loader("Rotten Tomato")
    meta_paths = meta_path_loader.load_meta_paths()
    next_batch = RandomMetaPathSelector(meta_paths=meta_paths).get_next(size=batch_size)
    paths = [{'id': id,
              'meta_path': meta_path,
              'rating': 0.5} for id, meta_path in zip(range(mock_id, mock_id + batch_size), next_batch)]
    mock_id += batch_size
    return jsonify(paths)

@app.route("/get-available-datasets", methods=["GET"])
def get_available_datasets():
    return MetaPathLoaderDispatcher().get_available_datasets()

# TODO: Maybe post each rated meta-path
@app.route("/rate-meta-paths", methods=["POST"])
def receive_rated_metapaths():
    if not request.is_json:
        abort(400)
    rated_metapaths = request.get_json()
    if not all(key in rated_metapaths for key in ['id', 'meta_path', 'rating']):
        abort(400)
    # TODO: the filename should be unique
    json.dump('rated_data.json', rated_metapaths)
    return 'OK'


@app.route("/results", methods=["GET"])
def send_results():
    # TODO: Call fitting method in explanation
    return jsonify("Hello world")


if __name__ == '__main__':
    app.run(port=API_PORT)
