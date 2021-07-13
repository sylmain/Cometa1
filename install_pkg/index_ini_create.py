from PyQt5.QtCore import QSettings


class SettingsIni(QSettings):
    CONFIG_FILE_NAME = "settings/index.ini"
    settings = QSettings(CONFIG_FILE_NAME, QSettings.IniFormat)

    def __init__(self):
        QSettings.__init__(self)

    def write(self, key, value):
        # self.settings.clear()
        self.settings.setValue(key, value)
        self.settings.sync()

    def read(self, key):
        return self.settings.value(key)


ap = SettingsIni()
ap.sync()
ap.write("key", "value")
ap.clear()
ap.write("keys/key1", "value1")
ap.write("keys/key2", "value2")
ap.write("keys/key3", "value3")
