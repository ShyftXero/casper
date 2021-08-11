#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template
from rich import print
import json
import toml

app = Flask(__name__)

STATS = dict()

OPS = []


@app.route("/beacon", methods=["GET", "POST"])
def beacon():
    incoming_data = None
    if request.method == "POST":
        incoming_data = request.get_json(force=True)
        print(incoming_data)
        STATS[incoming_data["uuid"]] = incoming_data

    return {"OPS": OPS}


@app.route("/stats")
@app.route("/")
def stats():
    resp = json.dumps(STATS, sort_keys = True, indent = 4, separators = (',', ': '))

    return f'<pre>{resp}</pre>'


@app.route("/newops", methods=["GET", "POST"])
def newops():
    global OPS
    if request.method == "POST":
        data = request.get_json(force=True)
        try:

            for task in data:
                OPS.append(task)  # this is the string the agents are supposed ingest
            print("ops", OPS)
        except BaseException as e:
            return {"msg": repr(e)}
        return {"msg": "ok"}
    return repr(OPS)

@app.route('/flushops')
def flushops():
    global OPS
    OPS = []
    print(OPS)
    return {"msg": "ok"}

@app.get("/hud")
def hud():
    return render_template('hud.html')

@app.get("/agent/<agent_id>")
def agent_id(agent_id):
    return render_template('hud.html', agent_data=STATS[agent_id])

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000)
