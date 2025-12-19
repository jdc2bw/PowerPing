import serial.tools.list_ports
import sys
import glob
from time import sleep
from datetime import datetime
import sqlite3

    
def main():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')
    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    print("Available Ports:")
    for p in result:
        print(p)
    port = input("Select Port: COM")
    
    serialInst = serial.Serial() #create new serial instance
    serialInst.baudrate = 9600 #set baudrate
    serialInst.port = "COM" + port #set port
    serialInst.open()  #open port
    sleep(2)
    
    try:
        db = sqlite3.connect("batteries.db")
        cursor = db.cursor()
    except:
        print("Database error")
        
    while True:
        serialInst.write('R'.encode())  #request data
        while serialInst.in_waiting: #if there is data available to read
            packet = serialInst.readline()
            data=packet.decode('utf-8').strip()
            #print(f"data: {data}") #debug print
            data=data.split()
            #print(data) #Debug print
            id = int(data[0]) #get ID
            voltage = float(data[1]) #get Voltage
            rssi = int(data[2]) #get RSSI
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") #get current timestamp
            warning = data[3] #get warning level
            #print(f"ID: {id}, Voltage: {voltage}, RSSI: {rssi}, Time: {timestamp}")
            if warning == "D":
                cursor.execute("UPDATE batteries SET Voltage = ?, Warnings = 2 WHERE ID = ?", (voltage, rssi, timestamp, id))
            elif warning == "W":
                cursor.execute("UPDATE batteries SET Voltage = ?, RSSI = ?, Time = ?, Warnings = 1 WHERE ID = ?", (voltage, rssi, timestamp, id))
            else:
                cursor.execute("UPDATE batteries SET Voltage = ?, RSSI = ?, Time = ?, Warnings = 0 WHERE ID = ?", (voltage, rssi, timestamp, id))
            db.commit()
            sleep(0.1)
        sleep(1)  #wait before next read
        
if __name__ == "__main__":
    main()