from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])
def hello():
    # return jsonify({'message': 'Hello, World!'})
    return "hello world my name is yagnesh"

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)