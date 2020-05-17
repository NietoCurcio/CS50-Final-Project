from functools import wraps
from flask import session, request, url_for, redirect

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function
# https://flask.palletsprojects.com/en/1.0.x/patterns/viewdecorators/