from PyQt5.QtCore import QSettings
from PyQt5.QtCore import QStorageInfo

for drive in QStorageInfo.mountedVolumes():
    print(drive.rootPath())

INDEX_INI_PATH = "C:\\Comet\\index.ini"
settings = QSettings(INDEX_INI_PATH, QSettings.IniFormat)
settings.setValue("index1.ini_path", INDEX_INI_PATH + " 05 ")
settings.sync()
print(settings.contains(INDEX_INI_PATH))
class Install:
    def __init__(self):
        pass
        # print(?getcwd())  # текущий рабочий каталог
        # print(INDEX_INI_PATH)


test = Install()
