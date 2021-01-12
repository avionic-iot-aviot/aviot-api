from . import webapp
from flask import render_template


@webapp.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')