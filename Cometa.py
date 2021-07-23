from PyQt5.QtCore import QSettings, QDir, Qt, QFile
from PyQt5 import QtWinExtras
from PyQt5.QtGui import QPixmap
import pickle
from PyQt5.QtGui import QKeySequence, QIcon
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QMdiArea, QMdiSubWindow, QAction, QPushButton, \
    QTabWidget, QWidget

from install_pkg.WinWizard import Wizard
from functions_pkg.db_functions import MySQLConnection
from ui_mainwindow import Ui_MainWindow
from workers_pkg.workers import WorkersWidget
from rooms_pkg.rooms import RoomsWidget
from departments_pkg.departments import DepartmentsWidget
from organization_pkg.organization import OrganizationWidget
from equipment_pkg.equipment import EquipmentWidget


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.get_settings_from_ini()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)

        # self.mdi.setViewMode(QMdiArea.TabbedView)
        # self.mdi.setTabPosition(QTabWidget.South)
        # self.mdi.setTabsMovable(True)
        # self.mdi.setTabsClosable(True)

        self.setWindowTitle("Комплекс метрологический автоматизированный \"Комета\"")

        self.setWindowIcon(QIcon("mainwindow_icon.png"))

        self.open_subs = dict()

        self.create_menus()

    def create_menus(self):
        self.ui.settings.setStatusTip("Это вход в настройки")
        self.ui.action_19.triggered.connect(self.open_workers)
        self.ui.action_19.setStatusTip("Список сотрудников метрологических подразделений")

        self.ui.action_17.triggered.connect(self.open_departments)
        self.ui.action_17.setStatusTip("Список метрологических подразделений")

        self.ui.action_18.triggered.connect(self.open_rooms)
        self.ui.action_18.setStatusTip("Список помещений")

        self.ui.action_9.triggered.connect(self.open_org_info)
        self.ui.action_9.setStatusTip("Общая информация о предприятии")

        self.ui.action_11.triggered.connect(self.open_equipment)
        self.ui.action_11.setStatusTip("Используемое оборудование")

    def open_workers(self):
        if "workers" in self.open_subs and self.open_subs["workers"] in self.mdi.subWindowList():
            self.mdi.setActiveSubWindow(self.open_subs["workers"])
        else:
            sub = QMdiSubWindow()
            sub.setWidget(WorkersWidget())
            self.mdi.addSubWindow(sub)
            sub.setAttribute(Qt.WA_DeleteOnClose)
            sub.show()
            self.open_subs["workers"] = sub

    def open_equipment(self):
        if "equipment" in self.open_subs and self.open_subs["equipment"] in self.mdi.subWindowList():
            self.mdi.setActiveSubWindow(self.open_subs["equipment"])
        else:
            sub = QMdiSubWindow()
            sub.setWidget(EquipmentWidget())
            self.mdi.addSubWindow(sub)
            sub.setAttribute(Qt.WA_DeleteOnClose)
            sub.show()
            self.open_subs["equipment"] = sub

    def open_departments(self):
        if "departments" in self.open_subs and self.open_subs["departments"] in self.mdi.subWindowList():
            self.mdi.setActiveSubWindow(self.open_subs["departments"])
        else:
            sub = QMdiSubWindow()
            sub.setWidget(DepartmentsWidget())
            self.mdi.addSubWindow(sub)
            sub.setAttribute(Qt.WA_DeleteOnClose)
            sub.show()
            self.open_subs["departments"] = sub

    def open_rooms(self):
        if "rooms" in self.open_subs and self.open_subs["rooms"] in self.mdi.subWindowList():
            self.mdi.setActiveSubWindow(self.open_subs["rooms"])
        else:
            sub = QMdiSubWindow()
            sub.setWidget(RoomsWidget())
            self.mdi.addSubWindow(sub)
            sub.setAttribute(Qt.WA_DeleteOnClose)
            sub.show()
            self.open_subs["rooms"] = sub


    def open_org_info(self):
        if "organization" in self.open_subs and self.open_subs["organization"] in self.mdi.subWindowList():
            self.mdi.setActiveSubWindow(self.open_subs["organization"])
        else:
            sub = QMdiSubWindow()
            sub.setWidget(OrganizationWidget())
            self.mdi.addSubWindow(sub)
            sub.setAttribute(Qt.WA_DeleteOnClose)
            sub.resize(520, 730)
            sub.show()
            self.open_subs["organization"] = sub


    def is_settings_file_exists(self):
        dir = QDir(QDir.currentPath() + "\settings")
        if not dir.exists("index.ini"):
            return False
        else:
            return True

    def get_settings_from_ini(self):
        if self.is_settings_file_exists():
            dir = QDir(QDir.currentPath() + "\settings\index.ini")
            settings_path = QDir.absolutePath(dir)
            settings = QSettings(settings_path, QSettings.IniFormat)
            host = settings.value("connect/host")
            port = settings.value("connect/port")
            user = settings.value("connect/user")
            pwd = settings.value("connect/pwd")
            if MySQLConnection.verify_connection_with_args(host, port, user, pwd):
                print("Подключение выполнено")
            elif not MySQLConnection.verify_connection_with_args(host, port, user, pwd):
                print("Не подключено")
        else:
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Первый запуск программы?")
            dialog.setText(f"Если запуск производится впервые, нажмите \"Да\" и следуйте "
                           f"инструкциям мастера.\nВ противном случае нажмите \"Нет\" и убедитесь, "
                           f"что запускаемый файл находится в каталоге \'Cometa\' на соответствующем диске")
            dialog.setIcon(QMessageBox.Question)
            btn_yes = QPushButton("&Да")
            btn_no = QPushButton("&Нет")
            dialog.addButton(btn_yes, QMessageBox.AcceptRole)
            dialog.addButton(btn_no, QMessageBox.RejectRole)
            dialog.setEscapeButton(btn_no)
            result = dialog.exec()
            if result == 0:
                wizard = Wizard()
                wizard.exec()
            else:
                sys.exit()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.showMaximized()
    sys.exit(app.exec_())
