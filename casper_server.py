from flask import Flask, request, jsonify
from rich import print
import json
import toml
app = Flask(__name__)

STATS = dict()

OPS = ""

@app.route('/beacon',methods=['GET','POST'])
def beacon():
    data = None
    if request.method == 'POST':
        data = request.get_json(force=True)
        print(data)
        STATS[data['uuid']] = data
    return f'cool... data={data}'

@app.route('/stats')
@app.route('/')
def stats():
    return jsonify(STATS)

@app.route('/newops', methods=['GET', 'POST'])
def newops():
    if request.method == 'POST':
        data = request.get_json(force=True)
        try:
            toml.loads(data.get('ops','')) # if this works, it's at least a valid toml file...
            OPS = data.get('ops') # this is the string the agents are supposed ingest
        except BaseException as e:
            return e
        return "ok"
    return OPS



if __name__ == '__main__':
    app.run(debug=True, port=5000)
