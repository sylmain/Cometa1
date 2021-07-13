import mysql.connector
from PyQt5.QtCore import QStorageInfo, QDir
from mysql.connector import Error

from global_vars import Globals

glob = Globals()

# print(glob.getSett())
# print("ggood")

# def verify_connection(host_name, port_name, user_name, user_password):
try:
    connection = mysql.connector.connect(
        host='localhost',
        port='3306',
        user='root',
        passwd='03091981',
        database='cometa'
    )
    connection.close()
    print("good")
    # return {"connect": True}
except Error as e:
    print(e)
    # return {"connect": False, "error": e}
