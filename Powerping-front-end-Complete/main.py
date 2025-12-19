import sqlite3
from flask import Flask, session, render_template, request, g, redirect, url_for, jsonify
from werkzeug.exceptions import HTTPException
from time import sleep

app = Flask(__name__)
app.secret_key = "POWERPINGSECRETKEY"

@app.route('/')

def home():
    warnings=0
    voltage=0
    id=0

    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect("batteries.db")
    cursor = db.cursor()
    if (voltage is not None) and (voltage != 0): #valid data read
        if int(voltage) < 3.3: #voltage warning level 2
            warnings = 2
        elif int(voltage) < 3.5: #voltage warning level 1
            warnings = 1
        else: 
            warnings = 0 #no warnings
    if (id is not None) and (id != 0): #valid data read
        #print(f"Updating database for ID={id} with Voltage={voltage} and Warnings={warnings}")
        cursor.execute("UPDATE batteries SET Voltage = ?, Warnings = ? WHERE ID = ?", (float(voltage), int(warnings), int(id))) #update database
        db.commit()
        sleep(1)
    cursor.execute("SELECT * FROM batteries ORDER by Warnings DESC") #get all batteries ordered by warnings
    batteries = cursor.fetchall()
    cursor.close()
    return render_template('index.html', batteries=batteries)

@app.route('/Register', methods=['GET', 'POST']) #Battery registration
def register():
    if request.method == 'POST': 
        # Handle form submission
        id = request.form['ID'] #get battery ID from form
        name = request.form['Name'] #get battery name from form
        try:
            int(id)
        except ValueError:
            return render_template('Register.html', error="ID must be an integer.")
        
        # Input validation
        if not id or not name:
            return render_template('Register.html', error="Please fill in all fields.")
        if int(id) < 0:
            return render_template('Register.html', error="ID must be a non-negative integer.")
        if int(id) > 100000:
            return render_template('Register.html', error="ID must be less than 256.")
        
        db = g._database = sqlite3.connect("batteries.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM batteries WHERE ID = ?", (id,))
        batteries = cursor.fetchall()
        cursor.close()
        # Check for duplicate ID
        if int(id) in [row[0] for row in batteries]:
            return render_template('Register.html', error="ID already exists. Please choose a different ID.")
        cursor = db.cursor()
        cursor.execute("INSERT INTO batteries (ID, Name) VALUES (?, ?)", (id, name))
        db.commit()
        cursor.close()
        return render_template('Register.html', error="Battery registered successfully.")

    return render_template('Register.html')

@app.route('/Remove', methods=['POST'])
def remove(): #Battery removal
    #print(request.form)
    # Get form data
    idRemove = request.form['idRemove'] if 'idRemove' in request.form else None
    if idRemove == None: #no form data
        return render_template('Register.html', error="No form data submitted.")
    try:
        int(idRemove) #validate integer
    except ValueError: #invalid integer
        return render_template('Register.html', error="ID must be an integer.")
    if int(idRemove) < 0:
        return render_template('Register.html', error="ID must be a non-negative integer.")
    if int(idRemove) > 100000:
        return render_template('Register.html', error="ID must be less than 256.")
    db = g._database = sqlite3.connect("batteries.db")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM batteries WHERE ID = ?", (idRemove,))
    batteries = cursor.fetchall()
    cursor.close()
    if int(idRemove) not in [row[0] for row in batteries]:
        return render_template('Register.html', error="Battery ID does not exist.")
    # Handle battery removal
    id_remove = request.form['idRemove']
    db = g._database = sqlite3.connect("batteries.db")
    cursor = db.cursor()
    cursor.execute("DELETE FROM batteries WHERE ID = ?", (id_remove,))
    db.commit()
    cursor.close()
    return render_template('Register.html', error="Battery removed successfully.")

@app.route('/get_db_values')
def get_batteries():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect("batteries.db", check_same_thread=False, timeout=5.0)
    cursor = db.cursor()
    cursor.execute("SELECT * FROM batteries ORDER BY Warnings DESC")
    batteries = cursor.fetchall()
    cursor.close()
    
    #convert database value into JSON object
    battery_list = []
    for row in batteries:
        battery_list.append({
            "ID": row[0],
            "Name": row[1],
            "Warnings": row[2],
            "Voltage": row[3],
            "Time": row[4],
            "RSSI": row[5]

        })
    return jsonify(battery_list)

@app.errorhandler(HTTPException) #HTTP error handler
def http_error_handler(error):
    return redirect(url_for('home'))
    
    
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
    
        
if __name__ == '__main__':
    app.run(debug=False)