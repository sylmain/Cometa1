from PyQt5.QtCore import QDir

class Globals:

    def getSett(self):
        return Globals.settings_path_string


    # путь к файлу настроек settings.ini в формате QDir
    settings_path = QDir("D:\cometa\settings\index.ini")
    # settings_path = QDir(QDir.currentPath() + "\settings\index.ini")

    # текстовый путь к файлу настроек settings.ini
    settings_path_string = QDir.absolutePath(settings_path)

    # путь к папке настроек settings в формате QDir
    settings_dir = QDir("D:\cometa\settings")

    # текстовый путь к папке настроек settings в формате QDir
    settings_dir_string = QDir.absolutePath(settings_dir)

    # print(settings_path_string)
    #
    # print(QDir.currentPath())
    # print(settings_dir.canonicalPath())
    # print(settings_path_string)
    # print(settings_dir_string)