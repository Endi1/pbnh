import io
import re

from flask import request, send_file, render_template, Response
from sqlalchemy import exc
from werkzeug.datastructures import FileStorage
from datetime import datetime, timezone, timedelta

from pbnh import conf
from pbnh.db import paste
from pbnh.app import app
from pbnh.app import util

config = conf.get_config().get('database')

@app.route("/", methods=["GET"])
def hello():
    return render_template('index.html')

@app.route("/test", methods=["GET"])
def testing():
    return render_template('test.html')


@app.route("/", methods=["POST"])
def post_paste():
    addr = request.remote_addr
    sunsetstr = request.form.get('sunset')
    mimestr = request.form.get('mime')
    sunset = util.getSunsetFromStr(sunsetstr)
    inputstr = request.form.get('content')
    if not inputstr:
        inputstr = request.form.get('c')
    # we got string data
    if inputstr and isinstance(inputstr, str):
        return util.stringData(inputstr, addr=addr, sunset=sunset, mime=mimestr)
    files = request.files.get('content')
    if not files:
        files = request.files.get('c')
    # we got file data
    if files and isinstance(files, FileStorage):
        return util.fileData(files, addr=addr, sunset=sunset, mimestr=mimestr)
    return fourohfour()


@app.route("/<string:paste_id>", methods=["GET"])
def view_paste(paste_id):
    """
    If there are no extensions or slashes check if the mimetype is text, if it
    is text attempt to highlight it. If not return the data and set the mimetype
    so the browser can attempt to render it.
    """
    query = util.getPaste(paste_id)
    if not query:
        return fourohfour()
    mime = query.get('mime')
    data = query.get('data')
    if mime.split('/')[0] == 'text':
        return render_template('paste.html', paste=data.decode('utf-8'),
                mime=mime)
    else:
        data = io.BytesIO(query.get('data'))
        return send_file(data, mimetype=mime)
    return fourohfour()

@app.route("/<int:paste_id>.<string:filetype>")
def view_paste_with_extension(paste_id, filetype):
    query = util.getPaste(paste_id)
    if not query:
        return fourohfour()
    data = query.get('data')
    mime = util.getMime(mimestr=filetype)
    data = io.BytesIO(query.get('data'))
    return Response(data, mimetype=mime)

@app.route("/<string:paste_id>/<string:filetype>")
def view_paste_with_highlighting(paste_id, filetype):
    query = util.getPaste(paste_id)
    if not query:
        return fourohfour()
    data = query.get('data')
    mime = util.getMime(mimestr=filetype)
    return render_template('paste.html', paste=data.decode('utf-8'),
            mime=mime)

@app.route("/error")
def fourohfour():
    return render_template('404.html')
