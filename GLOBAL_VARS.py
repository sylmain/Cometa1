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

URL_START = "https://fgis.gost.ru/fundmetrology/eapi"
