#app.py

from flask import Flask, request #import main Flask class and request object

app = Flask(__name__) #create the Flask app

@app.route('/', methods=['POST'])
def slash_response():        
    user_id = request.form.get('user_id')
    response = '{"text": "Hi there, <@' + user_id + '>"}'
    return response, 200, {'content-type': 'application/json'}

if __name__ == '__main__':
    app.run(debug=True, port=5000) #run app in debug mode on port 5000
