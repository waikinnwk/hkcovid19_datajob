from flask import Flask
import os

app = Flask(__name__)
on_heroku = os.environ.get('ON_HEROKU')
if __name__ == "__main__":
    if on_heroku == True:
        app.run()
    else:
        app.run(host='127.0.0.1', port=8081)