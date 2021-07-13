import mysql.connector
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QMessageBox, QPushButton
from mysql.connector import Error

from global_vars import Globals


class MySQLConnection:

    @staticmethod
    def create_connection():
        connection = None
        if MySQLConnection.is_settings_file_exists():
            settings = QSettings(Globals.settings_path_string, QSettings.IniFormat)
            host = settings.value("connect/host")
            port = settings.value("connect/port")
            user = settings.value("connect/user")
            pwd = settings.value("connect/pwd")
            db_name = 'cometa'
            try:
                connection = mysql.connector.connect(
                    host=host,
                    port=port,
                    user=user,
                    passwd=pwd,
                    database=db_name
                )
                # print("good")
                return connection
            except Error as e:
                print(f"The error '{e}' occurred")
        return connection

    @staticmethod
    def is_db_connected():
        if MySQLConnection.is_settings_file_exists():
            settings = QSettings(Globals.settings_path_string, QSettings.IniFormat)
            host = settings.value("connect/host")
            port = settings.value("connect/port")
            user = settings.value("connect/user")
            pwd = settings.value("connect/pwd")
            db_name = "cometa"
            try:
                connection = mysql.connector.connect(
                    host=host,
                    port=port,
                    user=user,
                    passwd=pwd,
                    database=db_name
                )
                connection.close()
                return True
            except Error as e:
                return False
        else:
            return False

    @staticmethod
    def verify_connection_with_args(host, port, user, pwd):
        try:
            connection = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                passwd=pwd,
            )
            connection.close()
            return True
        except Error as e:
            return False

    @staticmethod
    def execute_query(connection, query):
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            connection.commit()
            # print("Query executed successfully")
            return True, cursor.lastrowid
        except Error as e:
            print(f"The error '{e}' occurred")
            return False, e.errno

    @staticmethod
    def execute_transaction_query(connection, *query):
        try:
            cursor = connection.cursor()
            connection.start_transaction()
            for sql in query:
                cursor.execute(sql)
            connection.commit()
            # print("Transaction executed successfully")
            return True, "OK"
        except Error as e:
            connection.rollback()
            print(f"The error '{e}' occurred")
            return False, e.errno

    @staticmethod
    def execute_read_query(connection, query):
        cursor = connection.cursor()
        result = []
        try:
            cursor.execute(query)
            # print("Query executed successfully")
            for item in cursor:
                result.append(item)
        except Error as e:
            print(f"The error '{e}' occurred")
        return result

    @staticmethod
    def verify_connection():
        if not MySQLConnection.is_db_connected():
            dialog = QMessageBox()
            dialog.setWindowTitle("Отсутствует связь")
            dialog.setText(f"Отсутствует связь с сервером базы данных\n"
                           f"Работа в форме невозможна")
            dialog.setIcon(QMessageBox.Information)
            btn_close = QPushButton("&Закрыть")
            dialog.addButton(btn_close, QMessageBox.AcceptRole)
            dialog.setDefaultButton(btn_close)
            dialog.exec()
            exit()

    @staticmethod
    def is_settings_file_exists():
        settings_dir = Globals.settings_dir
        if not settings_dir.exists("index.ini"):
            return False
        else:
            return True
