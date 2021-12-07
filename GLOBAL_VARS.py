from PyQt5.QtCore import QDir, QSettings


# путь к файлу настроек settings.ini в формате QDir
SETTINGS_PATH = QDir("D:\cometa\settings\index.ini")
# SETTINGS_PATH = QDir(QDir.currentPath() + "\settings\index.ini")

# текстовый путь к файлу настроек settings.ini
SETTINGS_PATH_STRING = QDir.absolutePath(SETTINGS_PATH)

# путь к папке настроек settings в формате QDir
SETTINGS_DIR = QDir("D:\cometa\settings")

# текстовый путь к папке настроек settings в формате QDir
SETTINGS_DIR_STRING = QDir.absolutePath(SETTINGS_DIR)

SETTINGS = QSettings(SETTINGS_PATH_STRING, QSettings.IniFormat)
SETTINGS.setIniCodec("UTF-8")

HOST = SETTINGS.value("connect/hosp")
PORT = SETTINGS.value("connect/port")
USER = SETTINGS.value("connect/user")
PWD = SETTINGS.value("connect/pwd")
DB_NAME = 'cometa'

URL_START = "https://fgis.gost.ru/fundmetrology/eapi"
MI_STATUS_LIST = ["СИ", "СИ в качестве эталона"]
VRI_TYPE_LIST = ["периодическая", "первичная"]

COLOR_OF_CHANGED_FIELDS = "#1854A8"
