import sys

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QSettings, QDir
from PyQt5.QtWidgets import QWizardPage, QLabel, QVBoxLayout, QComboBox, QSpacerItem, QHBoxLayout, QWizard, QLineEdit, \
    QFormLayout

from functions_pkg.db_functions import MySQLConnection


class Page_1(QWizardPage):
    def __init__(self, parent=None):
        QWizardPage.__init__(self, parent)
        self.setTitle("Начало")

        self.label = QLabel("Этот мастер поможет вам правильно настроить приложение")
        self.label.setWordWrap(True)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)


class Page_2(QWizardPage):
    def __init__(self, parent=None):
        QWizardPage.__init__(self, parent)
        self.setTitle("Выбор расположения базы данных")
        self.setSubTitle("Пожалуйста, выберите диск для установки необходимых файлов\n"
                         "Диск не должен быть сетевым")

        self.diskLabel = QLabel("Диск:")
        self.combobox = QComboBox()
        self.spacer = QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        self.label = QLabel(
            "На выбранном диске будет создана папка 'Cometa', которая содержит все необходимые файлы, "
            "а также файлы пользователя\n"
            "Туда же необходимо переместить запущенный файл \'Cometa.exe\' после окончания процедуры настройки")
        self.label.setWordWrap(True)

        for drive in QDir.drives():
            self.combobox.addItem(drive.path())

        self.hlayout = QHBoxLayout()
        self.hlayout.addWidget(self.diskLabel)
        self.hlayout.addWidget(self.combobox)
        self.hlayout.addItem(self.spacer)
        self.vlayout = QVBoxLayout()
        self.vlayout.addLayout(self.hlayout)
        self.vlayout.addWidget(self.label)
        self.setLayout(self.vlayout)

        self.registerField("drive", self.combobox)


class Page_3(QWizardPage):
    def __init__(self, parent=None):
        QWizardPage.__init__(self, parent)
        self.setTitle("Параметры подключения к MySQL")
        self.setSubTitle("Заполните данные для подключения к MySQL серверу")

        self.pageLayout = QFormLayout()

        self.hostLabel = QLabel("Имя сетевого &устройства")
        self.portLabel = QLabel("Номер &порта")
        self.userLabel = QLabel("&Имя пользователя")
        self.pwdLabel = QLabel("Паро&ль")

        self.hostLine = QLineEdit("192.168.1.71")
        self.portLine = QLineEdit("3306")
        self.userLine = QLineEdit("sylmain")
        self.pwdLine = QLineEdit("03091981")

        self.hostLabel.setBuddy(self.hostLine)
        self.portLabel.setBuddy(self.portLine)
        self.userLabel.setBuddy(self.userLine)
        self.pwdLabel.setBuddy(self.pwdLine)

        self.hostLine.setToolTip("IP-адрес сервера MySQL или \'localhost\'")
        self.portLine.setToolTip("Порт MySQL. По умолчанию \'3306\'")
        self.userLine.setToolTip("Имя пользователя, которому создана учетная запись MySQL")
        self.pwdLine.setToolTip("Пароль пользовател в MySQL")

        self.hostLine.setPlaceholderText("IP-адрес или \'localhost\'")
        self.portLine.setPlaceholderText("По умолчанию номер порта MySQL \'3306\'")
        self.userLine.setPlaceholderText("Учетное имя пользователя в MySQL")
        self.pwdLine.setPlaceholderText("Пароль пользователя в MySQL")
        self.pwdLine.setEchoMode(QLineEdit.Password)

        self.pageLayout.setWidget(0, QFormLayout.LabelRole, self.hostLabel)
        self.pageLayout.setWidget(0, QFormLayout.FieldRole, self.hostLine)
        self.pageLayout.setWidget(1, QFormLayout.LabelRole, self.portLabel)
        self.pageLayout.setWidget(1, QFormLayout.FieldRole, self.portLine)
        self.pageLayout.setWidget(2, QFormLayout.LabelRole, self.userLabel)
        self.pageLayout.setWidget(2, QFormLayout.FieldRole, self.userLine)
        self.pageLayout.setWidget(3, QFormLayout.LabelRole, self.pwdLabel)
        self.pageLayout.setWidget(3, QFormLayout.FieldRole, self.pwdLine)

        self.setLayout(self.pageLayout)

        self.registerField("host", self.hostLine)
        self.registerField("port", self.portLine)
        self.registerField("user", self.userLine)
        self.registerField("pwd", self.pwdLine)

    def validatePage(self) -> bool:
        host = self.field("host")
        port = self.field("port")
        user = self.field("user")
        pwd = self.field("pwd")
        if MySQLConnection.verify_connection_with_args(host, port, user, pwd):
            dialog = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information,
                                           "Выполнено",
                                           "Подключение к MySQL выполнено успешно",
                                           buttons=QtWidgets.QMessageBox.Ok)
            dialog.exec()
            return True
        elif not MySQLConnection.verify_connection_with_args(host, port, user, pwd):
            # print("no connection")
            dialog = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical,
                                           "Подключение не выполнено",
                                           "Невозможно подключиться к серверу. Проверьте настройки соединения",
                                           buttons=QtWidgets.QMessageBox.Ok)
            dialog.exec()
            return False


class Page_4(QWizardPage):
    def __init__(self, parent=None):
        QWizardPage.__init__(self)
        self.setTitle("Завершение установки")
        self.label = QLabel()
        self.label.setTextFormat(QtCore.Qt.RichText)
        self.label.setWordWrap(True)
        self.font = QtGui.QFont()
        self.font.setPointSize(9)
        self.label.setFont(self.font)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def initializePage(self) -> None:
        user = self.field("user")
        ini_path = QDir.drives()[self.field("drive")].path()
        self.label.setText("<b>Внимательно прочитайте следующую информацию!</b><br><br>"
                           "Сохранены настройки подключения для пользователя \'"
                           + user +
                           "\'.<br> "
                           "Настройки действительны <b>только для данного компьютера</b>.<br>"
                           "Запуск программы по сети с другого рабочего места невозможен.<br>"
                           "Настройки подключения к MySQL можно поменять в меню \'Настройки\'.<br><br>"
                           "<b>Для завершения установки нажмите \'Завершить\' и переместите программу "
                           "(файл \'Cometa.exe\') в папку \'Сometa\' на диске "
                           + ini_path +
                           ".</b><br>"
                           "В дальнейшем запускайте программу из этой папки или создайте ярлык на рабочем столе.")


class Wizard(QWizard):
    def __init__(self):
        QWizard.__init__(self)
        self.setWindowTitle("Мастер настройки")
        self.resize(500, 325)
        self.addPage(Page_1())
        self.addPage(Page_2())
        self.addPage(Page_3())
        self.addPage(Page_4())

        self.setButtonText(QWizard.FinishButton, "Завершить")
        self.setButtonText(QWizard.CancelButton, "Отмена")
        self.setButtonText(QWizard.NextButton, "Далее")

        # при нажатии Cancel выход из программы
        self.cancel_btn = self.button(QWizard.CancelButton)
        self.cancel_btn.clicked.connect(lambda: sys.exit())

        # при нажатии Finish запись параметров и выход из программы
        self.finish_btn = self.button(QWizard.FinishButton)
        self.finish_btn.clicked.connect(self.finish_validate)


    @QtCore.pyqtSlot()
    def finish_validate(self):

        # путь к файлу index.ini
        ini_path = QDir.drives()[self.field("drive")].path() + "Cometa/settings/index.ini"
        settings = QSettings(ini_path, QSettings.IniFormat)
        settings.setValue("paths/ini_path", ini_path)
        settings.setValue("paths/cometa_path", QDir.drives()[self.field("drive")].path() + "Cometa")
        settings.setValue("connect/host", self.field("host"))
        settings.setValue("connect/port", self.field("port"))
        settings.setValue("connect/user", self.field("user"))
        settings.setValue("connect/pwd", self.field("pwd"))
        settings.sync()
        sys.exit()
