import typing

import mysql.connector
import sys
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QMessageBox, QPushButton
from mysql.connector import Error

from GLOBAL_VARS import *


class MySQLConnection:

    @staticmethod
    def get_connection() -> typing.Any:
        try:
            connection = mysql.connector.connect(
                host=HOST,
                port=PORT,
                user=USER,
                passwd=PWD,
                database=DB_NAME
            )
        except Error as e:
            dialog = QMessageBox()
            dialog.setWindowTitle("Ошибка подключения")
            dialog.setText(f"Отсутствует связь с базой данных. Проверьте подключение\n"
                           f"Код ошибки:\n{e}")
            dialog.setIcon(QMessageBox.Critical)
            btn_close = QPushButton("&Закрыть")
            dialog.addButton(btn_close, QMessageBox.AcceptRole)
            dialog.setDefaultButton(btn_close)
            dialog.exec()
            return None
            # sys.exit(f"Невозможно подключиться к базе данных\n{e}")
        else:
            return connection

    @staticmethod
    def execute_query(sql: str) -> int:
        connection = MySQLConnection.get_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(sql)
                connection.commit()
            except Error as e:
                dialog = QMessageBox()
                dialog.setWindowTitle("Ошибка сохранения")
                dialog.setText(f"Внимание! Данные не сохранены!\n"
                               f"Код ошибки:\n{e}")
                dialog.setIcon(QMessageBox.Warning)
                btn_close = QPushButton("&Закрыть")
                dialog.addButton(btn_close, QMessageBox.AcceptRole)
                dialog.setDefaultButton(btn_close)
                dialog.exec()
                return 0
            else:
                return cursor.lastrowid
            finally:
                connection.close()
                print("Запрос на изменение выполнен, соединение закрыто")

    @staticmethod
    def execute_transaction_query(*sql: str) -> bool:
        connection = MySQLConnection.get_connection()
        if connection:
            cursor = connection.cursor()
            connection.start_transaction()
            try:
                for sql_item in sql:
                    cursor.execute(sql_item)
                connection.commit()
            except Error as e:
                dialog = QMessageBox()
                dialog.setWindowTitle("Ошибка транзакции")
                dialog.setText(f"Внимание! Данные не сохранены!\n"
                               f"Код ошибки:\n{e}")
                dialog.setIcon(QMessageBox.Critical)
                btn_close = QPushButton("&Закрыть")
                dialog.addButton(btn_close, QMessageBox.AcceptRole)
                dialog.setDefaultButton(btn_close)
                dialog.exec()
                return False
            else:
                return True
            finally:
                connection.close()
                print("Транзакция выполнена, соединение закрыто")

    @staticmethod
    def execute_read_query(sql: str):
        connection = MySQLConnection.get_connection()
        result = []
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(sql)
            except Error as e:
                dialog = QMessageBox()
                dialog.setWindowTitle("Ошибка выполнения запроса")
                dialog.setText(f"Внимание! Данные не получены!\n"
                               f"Код ошибки:\n{e}")
                dialog.setIcon(QMessageBox.Warning)
                btn_close = QPushButton("&Закрыть")
                dialog.addButton(btn_close, QMessageBox.AcceptRole)
                dialog.setDefaultButton(btn_close)
                dialog.exec()
            else:
                for item in cursor:
                    result.append(item)
            finally:
                connection.close()
        return result

    @staticmethod
    def is_db_connected():
        if MySQLConnection.is_settings_file_exists():
            # settings = QSettings(Globals.settings_path_string, QSettings.IniFormat)
            print("helo")
            host = SETTINGS.value("connect/host")
            port = SETTINGS.value("connect/port")
            user = SETTINGS.value("connect/user")
            pwd = SETTINGS.value("connect/pwd")
            db_name = "cometa"
            print(host)
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
        print("connection verified")

    @staticmethod
    def is_settings_file_exists():
        # settings_dir = Globals.settings_dir
        if not SETTINGS_DIR.exists("index.ini"):
            return False
        else:
            return True
