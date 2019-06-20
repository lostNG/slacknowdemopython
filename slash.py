#app.py

from flask import Flask, request #import main Flask class and request object

app = Flask(__name__) #create the Flask app

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return Response("%s<h1>Flask on Now 2.0</h1><p>You are viewing a Flask application written in Python running on Now 2.0.</p><p>Visit the <a href='./about'>about</a> page or view the <a href='%s'>source code</a>.</p>" % (css, source), mimetype='text/html')


if __name__ == '__main__':
    app.run(debug=True, port=5000) #run app in debug mode on port 5000