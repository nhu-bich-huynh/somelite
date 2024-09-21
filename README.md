# Somelite
Social media website made in the framework flask.
For the KU course DIS, Databases and Information Systems.

See Guide.md for further instructions on how the app is
accessed and used.

### Requirements
- python3 & pip
- npm & tailwind (only for updating the styling)
- You need to put your postgres password in app.py

### Building
##### Linux
```
git clone git@github.com:nhu-bich-huynh/somelite.git
cd somelite
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```
##### Windows
```
git clone git@github.com:nhu-bich-huynh/somelite.git
cd somelite
python3 -m venv .venv
./.venv/Scripts/activate
pip install -r requirements.txt
```
##### CSS (only for updating the styling)
```
npx tailwindcss -i ./src/static/css/input.css -o ./src/static/css/output.css --watch
```
### Running
```
flask --app src/app run
```
##### Debug
```
flask --debug --app src/app run
```
