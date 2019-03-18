from flask import Flask, render_template
import pdb
import time
import os

app = Flask(__name__)


@app.route("/")
def hello():
    buffer: str = r''
    filename = 'graph.json'
    with open(filename, 'r') as file:
        for line in file.readlines():
            buffer += line
    last_modified = time.strftime('%Y-%m-%d %H:%M:%S',
                                  time.localtime(os.path.getctime(filename)))
    return render_template(
        'index.html.j2', graph=buffer, last_modified=last_modified)


if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True, port=5000)
