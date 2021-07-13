from PyQt5.QtCore import QStringListModel, QDate, Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtWidgets import QWidget, QApplication, QAbstractItemView, QMessageBox, QPushButton, QMenu, QAction, \
    QInputDialog

from functions_pkg.db_functions import MySQLConnection
from workers_pkg.ui_workers import Ui_Form
import functions_pkg.functions as func


class WorkersWidget(QWidget):
    def __init__(self, parent=None):
        super(WorkersWidget, self).__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.worker_dict = dict()
        self.dep_dict = dict()
        self.dep_workers_dict = dict()
        self.worker_deps_dict = dict()
        self.room_dict = dict()

        self.organization_name = func.get_organization_name()

        self.tree_view_model = QStandardItemModel(0, 1, parent=self)

        self._initialize()

        self.setWindowTitle("Сотрудники метрологических подразделений")

        # todo вставить иконку
        self.setWindowIcon(QIcon("D:/cometa/mainwindow_icon.png"))
        self.resize(1000, 600)

    def _initialize(self):
        self.reserve_name = "Резерв"

        self.ui.treeView.setModel(self.tree_view_model)

        # задаем индексы перехода по tab
        WorkersWidget.setTabOrder(self.ui.lineEdit_worker_surname, self.ui.lineEdit_worker_name)
        WorkersWidget.setTabOrder(self.ui.lineEdit_worker_name, self.ui.lineEdit_worker_patronymic)
        WorkersWidget.setTabOrder(self.ui.lineEdit_worker_patronymic, self.ui.lineEdit_worker_tab_number)
        WorkersWidget.setTabOrder(self.ui.lineEdit_worker_tab_number, self.ui.lineEdit_worker_post)
        WorkersWidget.setTabOrder(self.ui.lineEdit_worker_post, self.ui.lineEdit_worker_phone)
        WorkersWidget.setTabOrder(self.ui.lineEdit_worker_phone, self.ui.lineEdit_worker_email)
        WorkersWidget.setTabOrder(self.ui.lineEdit_worker_email, self.ui.dateEdit_worker_birthday)
        WorkersWidget.setTabOrder(self.ui.dateEdit_worker_birthday, self.ui.plainTextEdit_worker_birthplace)
        WorkersWidget.setTabOrder(self.ui.plainTextEdit_worker_birthplace, self.ui.plainTextEdit_worker_education)
        WorkersWidget.setTabOrder(self.ui.plainTextEdit_worker_education, self.ui.lineEdit_worker_snils)
        WorkersWidget.setTabOrder(self.ui.lineEdit_worker_snils, self.ui.dateEdit_worker_startjob_date)
        WorkersWidget.setTabOrder(self.ui.dateEdit_worker_startjob_date, self.ui.plainTextEdit_worker_contract_info)
        WorkersWidget.setTabOrder(self.ui.plainTextEdit_worker_contract_info, self.ui.plainTextEdit_worker_attestations)
        WorkersWidget.setTabOrder(self.ui.plainTextEdit_worker_attestations, self.ui.plainTextEdit_worker_info)

        self._create_tree_view_model()
        self._make_connects()
        self._draw_treeview()

    def _create_tree_view_model(self):

        self.tree_view_model.clear()
        self.tree_view_model.setHorizontalHeaderLabels([f"Отделы и сотрудники {self.organization_name}"])

        departments = func.get_departments()
        workers = func.get_workers()
        dep_workers = func.get_worker_deps()

        self.worker_dict = workers['worker_dict']
        self.dep_workers_dict = dep_workers['dep_workers_dict']
        self.worker_deps_dict = dep_workers['worker_deps_dict']
        self.dep_dict = departments['dep_dict']
        self.room_dict = func.get_rooms()['room_dict']

        self._update_treeview()
        # разворачиваем все элементы
        self.ui.treeView.expandAll()

        self.ui.pushButton_delete.setDisabled(True)
        self.ui.pushButton_add.setDisabled(True)

    def _update_treeview(self):
        self._add_workers_in_model()

        self.ui.dateEdit_worker_startjob_date.setDate(QDate.currentDate())

        self._clear_worker_area()

    def _add_workers_in_model(self):
        for dep_id in sorted(self.dep_workers_dict):
            if dep_id != "-1":
                item = QStandardItem(self.dep_dict[dep_id]['name'])
                # print(item.text())
                self.tree_view_model.appendRow(item)
                for worker_id in self.dep_workers_dict[dep_id]:
                    fio = func.get_worker_fio_and_number_from_id(worker_id, self.worker_dict)
                    if worker_id == self.dep_dict[dep_id]['boss']:
                        item.insertRow(0, [QStandardItem(f"нач. {fio}")])
                    elif worker_id == self.dep_dict[dep_id]['boss_assistant']:
                        if item.rowCount() == 0 or "нач. " not in item.child(0).text():
                            item.insertRow(0, [QStandardItem(f"зам. {fio}")])
                        else:
                            item.insertRow(1, [QStandardItem(f"зам. {fio}")])
                    else:
                        item.appendRow([QStandardItem(fio)])

        for dep_id in self.dep_dict:
            if dep_id not in self.dep_workers_dict:
                item = QStandardItem(self.dep_dict[dep_id]['name'])
                self.tree_view_model.appendRow(item)

        item = QStandardItem(self.reserve_name)
        self.tree_view_model.appendRow(item)
        if "-1" in self.dep_workers_dict:
            for worker_id in self.dep_workers_dict['-1']:
                fio = func.get_worker_fio_and_number_from_id(worker_id, self.worker_dict)
                item.appendRow([QStandardItem(fio)])

    def _draw_treeview(self):

        self.ui.treeView.setWordWrap(True)
        self.ui.treeView.setColumnWidth(0, 350)

        self.ui.treeView.setAnimated(True)
        self.ui.treeView.setSortingEnabled(True)
        self.ui.treeView.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.ui.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.treeView.customContextMenuRequested.connect(self._open_menu)

    def _make_connects(self):

        # выбор элемента в списке
        self.ui.treeView.selectionModel().selectionChanged.connect(self._on_selection_changed)

        # клик по кнопке "Добавить сотрудника"
        self.ui.pushButton_add.clicked.connect(self._add_worker)

        # клик по кнопке "Уволить сотрудника"
        self.ui.pushButton_delete.clicked.connect(self._delete_worker)

        # клик по кнопке "Сохранить информацию"
        self.ui.pushButton_save.clicked.connect(self._save_worker_info)

        # клик по кнопке "Сотрудники"
        # self.ui.pushButton_workers.clicked.connect(self.delete_dep_list(self.itemModel.itemFromIndex(self.ui.treeView.selectionModel().currentIndex())))

    def _on_selection_changed(self):
        if not self.ui.treeView.selectedIndexes():
            return

        cur_index = self.ui.treeView.currentIndex()
        if not cur_index.isValid():
            return
        if cur_index.parent().isValid():
            self._update_worker_area(cur_index.data())
            self.ui.pushButton_delete.setEnabled(True)
            self.ui.pushButton_add.setDisabled(True)
            # self._update_worker_area(re.sub("\s\(\w*\)", "", cur_index.data()))
        else:
            self._clear_worker_area()
            self.ui.pushButton_delete.setDisabled(True)
            self.ui.pushButton_add.setEnabled(True)

    def _update_worker_area(self, fio):
        worker_id = str(func.get_worker_id_from_fio(fio, self.worker_dict))
        self.ui.lineEdit_worker_id.setText(worker_id)
        self.ui.lineEdit_worker_tab_number.setText(self.worker_dict[worker_id]['tab_number'])
        self.ui.lineEdit_worker_surname.setText(self.worker_dict[worker_id]['surname'])
        self.ui.lineEdit_worker_name.setText(self.worker_dict[worker_id]['name'])
        self.ui.lineEdit_worker_patronymic.setText(self.worker_dict[worker_id]['patronymic'])

        self.ui.lineEdit_worker_post.setText(self.worker_dict[worker_id]['post'])
        self.ui.lineEdit_worker_snils.setText(self.worker_dict[worker_id]['snils'])
        self.ui.dateEdit_worker_birthday.setDate(self.worker_dict[worker_id]['birthday'])
        self.ui.plainTextEdit_worker_birthplace.setPlainText(self.worker_dict[worker_id]['birthplace'])
        self.ui.plainTextEdit_worker_contract_info.setPlainText(self.worker_dict[worker_id]['contract_info'])
        self.ui.dateEdit_worker_startjob_date.setDate(self.worker_dict[worker_id]['startjob_date'])
        self.ui.plainTextEdit_worker_attestations.setPlainText(self.worker_dict[worker_id]['attestations'])
        self.ui.plainTextEdit_worker_education.setPlainText(self.worker_dict[worker_id]['education'])
        self.ui.lineEdit_worker_email.setText(self.worker_dict[worker_id]['email'])
        self.ui.plainTextEdit_worker_info.setPlainText(self.worker_dict[worker_id]['info'])
        self.ui.lineEdit_worker_phone.setText(self.worker_dict[worker_id]['phone'])

    def _clear_worker_area(self):
        self.ui.lineEdit_worker_id.setText('')
        self.ui.lineEdit_worker_tab_number.setText('')
        self.ui.lineEdit_worker_surname.setText('')
        self.ui.lineEdit_worker_name.setText('')
        self.ui.lineEdit_worker_patronymic.setText('')
        self.ui.lineEdit_worker_post.setText('')
        self.ui.lineEdit_worker_snils.setText('')
        self.ui.dateEdit_worker_birthday.setDate(QDate(1980, 1, 1))
        self.ui.plainTextEdit_worker_birthplace.setPlainText('')
        self.ui.plainTextEdit_worker_contract_info.setPlainText('')
        self.ui.dateEdit_worker_startjob_date.setDate(QDate.currentDate())
        self.ui.plainTextEdit_worker_attestations.setPlainText('')
        self.ui.plainTextEdit_worker_education.setPlainText('')
        self.ui.lineEdit_worker_email.setText('')
        self.ui.plainTextEdit_worker_info.setPlainText('')
        self.ui.lineEdit_worker_phone.setText('+')

    def _add_worker(self):
        cur_index = self.ui.treeView.currentIndex()
        if not cur_index:
            return
        if not cur_index.parent().isValid():
            self.ui.lineEdit_worker_surname.setFocus()
        else:
            self._clear_worker_area()
            self.ui.lineEdit_worker_surname.setFocus()

    def _save_worker_info(self):

        dep_id = func.get_dep_id_from_name(self.ui.treeView.currentIndex().data(), self.dep_dict)

        # если фамилия не введена - ошибка
        if not self.ui.lineEdit_worker_surname.text():
            QMessageBox.warning(self, "Ошибка сохранения", "Необходимо ввести фамилию сотрудника")
            return

        # форматируем даты
        birthday = self.ui.dateEdit_worker_birthday.date().toString("yyyy-MM-dd")
        startjob_date = self.ui.dateEdit_worker_startjob_date.date().toString("yyyy-MM-dd")

        # если сотрудник новый, то id = NULL
        if self.ui.lineEdit_worker_id.text():
            worker_id = f"'{self.ui.lineEdit_worker_id.text()}'"
        else:
            worker_id = "NULL"

        if self.ui.lineEdit_worker_phone.text() == "+":
            phone = ""
        else:
            phone = self.ui.lineEdit_worker_phone.text()

        MySQLConnection.verify_connection()
        connection = MySQLConnection.create_connection()
        sql_replace = f"REPLACE INTO workers " \
                      f"VALUES (" \
                      f"{worker_id}, " \
                      f"'{self.ui.lineEdit_worker_tab_number.text()}', " \
                      f"'{self.ui.lineEdit_worker_surname.text()}', " \
                      f"'{self.ui.lineEdit_worker_name.text()}', " \
                      f"'{self.ui.lineEdit_worker_patronymic.text()}', " \
                      f"'{self.ui.lineEdit_worker_post.text()}', " \
                      f"'{self.ui.lineEdit_worker_snils.text()}', " \
                      f"'{birthday}', " \
                      f"'{self.ui.plainTextEdit_worker_birthplace.toPlainText()}', " \
                      f"'{self.ui.plainTextEdit_worker_contract_info.toPlainText()}', " \
                      f"'{startjob_date}', " \
                      f"'{self.ui.plainTextEdit_worker_attestations.toPlainText()}', " \
                      f"'{self.ui.plainTextEdit_worker_education.toPlainText()}', " \
                      f"'{self.ui.lineEdit_worker_email.text()}', " \
                      f"'{self.ui.plainTextEdit_worker_info.toPlainText()}', " \
                      f"'{phone}');"
        new_worker_id = MySQLConnection.execute_query(connection, sql_replace)[1]
        if worker_id == "NULL" and dep_id != "0":
            sql_insert = f"INSERT INTO workers_departments VALUES (" \
                         f"{int(new_worker_id)}, " \
                         f"{int(dep_id)})"
            MySQLConnection.execute_query(connection, sql_insert)
        connection.close()
        self._clear_worker_area()
        self._create_tree_view_model()
        QMessageBox.information(self, "Сохранено", "Информация сохранена")

    def _delete_worker(self):
        worker_id = self.ui.lineEdit_worker_id.text()
        worker_name = func.get_worker_fio_and_number_from_id(worker_id, self.worker_dict)
        dep_name = self.ui.treeView.currentIndex().parent().data()
        if dep_name == self.reserve_name:
            dep_id = "-1"
        else:
            dep_id = func.get_dep_id_from_name(dep_name, self.dep_dict)

        dialog = QMessageBox(self)
        dialog.setWindowTitle("Подтверждение удаления")
        if dep_name != self.reserve_name:
            if len(self.dep_workers_dict[dep_id]) < 2:
                dialog.setText(f"Вы действительно хотите уволить {self.worker_dict[worker_id]['post']} "
                               f"{worker_name} из \"{dep_name}\"?\n"
                               f"Информация о сотруднике также удалится из всех справочников.\n"
                               f"В подразделении не останется сотрудников")
            else:
                dialog.setText(f"Вы действительно хотите уволить {self.worker_dict[worker_id]['post']} "
                               f"{worker_name} из \"{dep_name}\"?\n"
                               f"Информация о сотруднике также удалится из всех справочников.")
        else:
            dialog.setText(f"Вы действительно хотите уволить {self.worker_dict[worker_id]['post']} "
                           f"{worker_name} из \"{dep_name}\"?\n"
                           f"Информация о сотруднике также удалится из всех справочников.")
        dialog.setIcon(QMessageBox.Question)
        btn_yes = QPushButton("&Да")
        btn_no = QPushButton("&Нет")
        dialog.addButton(btn_yes, QMessageBox.AcceptRole)
        dialog.addButton(btn_no, QMessageBox.RejectRole)
        dialog.setDefaultButton(btn_no)
        dialog.setEscapeButton(btn_no)
        result = dialog.exec()

        if result == 0:
            if dep_name != self.reserve_name:
                if self.dep_dict[dep_id]['boss'] == worker_id or self.dep_dict[dep_id]['boss_assistant'] == worker_id:
                    self._choose_new_boss(dep_id, worker_id)
                if func.get_worker_rooms_list(worker_id, self.room_dict):
                    self._choose_new_room_resp(worker_id)

            sql_delete_1 = f"DELETE FROM workers " \
                           f"WHERE worker_id = {int(worker_id)}"

            sql_delete_2 = f"DELETE FROM workers_departments " \
                           f"WHERE WD_worker_id = {int(worker_id)}"

            MySQLConnection.verify_connection()
            connection = MySQLConnection.create_connection()
            MySQLConnection.execute_transaction_query(connection, sql_delete_1, sql_delete_2)
            print(sql_delete_1)
            print(sql_delete_2)
            connection.close()
            self._clear_worker_area()
            self._create_tree_view_model()

    # перевести сотрудника в другой отдел
    def _transfer_to_dep(self, worker_id, dep_id):
        cur_dep_name = self.ui.treeView.currentIndex().parent().data()
        cur_dep_id = func.get_dep_id_from_name(cur_dep_name, self.dep_dict)
        MySQLConnection.verify_connection()
        connection = MySQLConnection.create_connection()

        if cur_dep_name == self.reserve_name:
            sql_update = f"UPDATE workers_departments SET " \
                         f"WD_dep_id = {int(dep_id)} " \
                         f"WHERE WD_worker_id = {int(worker_id)} " \
                         f"AND WD_dep_id = -1"
            MySQLConnection.execute_query(connection, sql_update)

        else:
            if func.get_worker_rooms_list(worker_id, self.room_dict):
                self._choose_new_room_resp(worker_id)
            if dep_id == "-1":
                for dep in self.dep_dict:
                    if (self.dep_dict[dep]['boss'] == worker_id or
                            self.dep_dict[dep]['boss_assistant'] == worker_id):
                        self._choose_new_boss(dep, worker_id)
                sql_delete = f"DELETE FROM workers_departments WHERE " \
                             f"WD_worker_id = {int(worker_id)}"
                sql_insert = f"INSERT INTO workers_departments VALUES " \
                             f"({int(worker_id)}, -1)"
                # sql_update_1 = f"UPDATE departments SET " \
                #                f"dep_boss = 0 WHERE " \
                #                f"dep_boss = {int(worker_id)}"
                # sql_update_2 = f"UPDATE departments SET " \
                #                f"dep_boss_assistant = 0 WHERE " \
                #                f"dep_boss_assistant = {int(worker_id)}"
                MySQLConnection.execute_transaction_query(connection, sql_delete, sql_insert)
            else:
                if (self.dep_dict[cur_dep_id]['boss'] == worker_id or
                        self.dep_dict[cur_dep_id]['boss_assistant'] == worker_id):
                    self._choose_new_boss(cur_dep_id, worker_id)
                sql_update_1 = f"UPDATE workers_departments SET " \
                               f"WD_dep_id = {int(dep_id)} " \
                               f"WHERE WD_worker_id = {int(worker_id)} " \
                               f"AND WD_dep_id = {int(cur_dep_id)}"
                # sql_update_2 = f"UPDATE departments SET " \
                #                f"dep_boss = 0 WHERE " \
                #                f"dep_id = {int(dep_id)} AND " \
                #                f"dep_boss = {int(worker_id)}"
                # sql_update_3 = f"UPDATE departments SET " \
                #                f"dep_boss_assistant = 0 WHERE " \
                #                f"dep_id = {int(dep_id)} AND " \
                #                f"dep_boss_assistant = {int(worker_id)}"
                MySQLConnection.execute_transaction_query(connection, sql_update_1)
        connection.close()
        self._clear_worker_area()
        self._create_tree_view_model()

    # добавить этого сотрудника в другой отдел
    def _add_to_dep(self, worker_id, dep_id):

        MySQLConnection.verify_connection()
        connection = MySQLConnection.create_connection()
        sql_insert = f"INSERT INTO workers_departments VALUES " \
                     f"({int(worker_id)}, " \
                     f"{int(dep_id)})"
        MySQLConnection.execute_query(connection, sql_insert)
        connection.close()
        self._clear_worker_area()
        self._create_tree_view_model()

    # убрать из отдела
    def _remove_from_dep(self, worker_id, dep_id):

        if len(self.worker_deps_dict[worker_id]) > 1:
            if (self.dep_dict[dep_id]['boss'] == worker_id or
                    self.dep_dict[dep_id]['boss_assistant'] == worker_id):
                self._choose_new_boss(dep_id, worker_id)

            sql_delete = f"DELETE FROM workers_departments WHERE " \
                         f"WD_worker_id = {int(worker_id)} AND " \
                         f"WD_dep_id = {int(dep_id)}"
            MySQLConnection.verify_connection()
            connection = MySQLConnection.create_connection()
            MySQLConnection.execute_transaction_query(connection, sql_delete)
            connection.close()
        else:
            self._transfer_to_dep(worker_id, "-1")
        self._clear_worker_area()
        self._create_tree_view_model()

    # выбираем и записываем нового начальника
    def _choose_new_boss(self, dep_id, worker_id):

        dep_name = func.get_dep_name_from_id(dep_id, self.dep_dict)
        boss_name = func.get_worker_fio_from_id(self.dep_dict[dep_id]['boss'], self.worker_dict)

        worker_list = func.get_workers_list([dep_id], self.worker_dict, self.dep_workers_dict)['workers']
        worker_list.remove(func.get_worker_fio_from_id(worker_id, self.worker_dict))

        if boss_name in worker_list:
            worker_list.remove(boss_name)

        worker_list.append("")
        # если сотрудников не осталось
        if len(worker_list) == 1:
            QMessageBox.warning(self, "Предупреждение",
                                f"Руководители \"{dep_name}\" не назначены, т.к. в отделе не осталось сотрудников")
            sql_update = f"UPDATE departments SET " \
                         f"dep_boss = 0, dep_boss_assistant = 0 " \
                         f"WHERE dep_id = {int(dep_id)}"
            print(sql_update)
            MySQLConnection.verify_connection()
            connection = MySQLConnection.create_connection()
            MySQLConnection.execute_query(connection, sql_update)
            connection.close()
            return

        if self.dep_dict[dep_id]['boss'] == worker_id:
            worker, ok = QInputDialog.getItem(self, "Выбор начальника",
                                              f"Выберите нового начальника в \n\"{dep_name}\"",
                                              worker_list, current=0, editable=False)
            if ok:
                new_boss_id = func.get_worker_id_from_fio(worker, self.worker_dict)
            else:
                new_boss_id = "0"
            if new_boss_id == "0":
                QMessageBox.warning(self, "Предупреждение", f"Начальник в \"{dep_name}\" не назначен")
            sql_update_1 = f"UPDATE departments SET " \
                           f"dep_boss = {int(new_boss_id)} " \
                           f"WHERE dep_id = {int(dep_id)}"
            sql_update_2 = f"UPDATE departments SET " \
                           f"dep_boss_assistant = 0 " \
                           f"WHERE dep_id = {int(dep_id)} AND " \
                           f"dep_boss_assistant = {int(new_boss_id)}"
            print(sql_update_1, sql_update_2)
            MySQLConnection.verify_connection()
            connection = MySQLConnection.create_connection()
            MySQLConnection.execute_transaction_query(connection, sql_update_1, sql_update_2)
            connection.close()
        if self.dep_dict[dep_id]['boss_assistant'] == worker_id:
            worker, ok = QInputDialog.getItem(self, "Выбор заместителя начальника",
                                              f"Выберите нового заместителя начальника в \n\"{dep_name}\"",
                                              worker_list, current=0, editable=False)
            if ok:
                new_boss_assistant_id = func.get_worker_id_from_fio(worker, self.worker_dict)
            else:
                new_boss_assistant_id = "0"
            if new_boss_assistant_id == "0":
                QMessageBox.warning(self, "Предупреждение",
                                    f"Заместитель начальника в \"{dep_name}\" не назначен")
            sql_update = f"UPDATE departments SET " \
                         f"dep_boss_assistant = {int(new_boss_assistant_id)} " \
                         f"WHERE dep_id = {int(dep_id)}"
            print(sql_update)
            MySQLConnection.verify_connection()
            connection = MySQLConnection.create_connection()
            MySQLConnection.execute_query(connection, sql_update)
            connection.close()

    # выбираем и записываем нового ответственного за помещения
    def _choose_new_room_resp(self, worker_id):

        dep_list = list()
        room_number_list = list()
        worker_fio = func.get_worker_fio_from_id(worker_id, self.worker_dict)
        room_deps_dict = func.get_room_deps()['room_deps_dict']

        for room_id in self.room_dict:
            if self.room_dict[room_id]['resp_person'] == worker_id:
                room_number_list.append(self.room_dict[room_id]['number'])
                for dep in room_deps_dict[room_id]:
                    dep_list.append(dep)
        new_resp_person_list = func.get_workers_list(dep_list, self.worker_dict, self.dep_workers_dict)['workers']
        if worker_fio in new_resp_person_list:
            new_resp_person_list.remove(worker_fio)
        new_resp_person_list.append("")
        if len(new_resp_person_list) == 1:
            QMessageBox.warning(self, "Предупреждение",
                                f"Ответственный за помещения {', '.join(room_number_list)} не назначен, "
                                f"т.к. в отделах не осталось сотрудников")
            sql_update = f"UPDATE rooms SET " \
                         f"room_responsible_person = 0 " \
                         f"WHERE room_responsible_person = {int(worker_id)}"
            print(sql_update)
            MySQLConnection.verify_connection()
            connection = MySQLConnection.create_connection()
            MySQLConnection.execute_query(connection, sql_update)
            connection.close()
            return
        else:
            worker, ok = QInputDialog.getItem(self, "Выбор ответственного",
                                              f"Выберите нового ответственного за помещения "
                                              f"{', '.join(room_number_list)}",
                                              new_resp_person_list, current=0, editable=False)
            if ok:
                new_resp_person_id = func.get_worker_id_from_fio(worker, self.worker_dict)
            else:
                new_resp_person_id = "0"
            if new_resp_person_id == "0":
                QMessageBox.warning(self, "Предупреждение",
                                    f"Ответственный за помещения {', '.join(room_number_list)} не назначен")
            sql_update = f"UPDATE rooms SET " \
                         f"room_responsible_person = {int(new_resp_person_id)} " \
                         f"WHERE room_responsible_person = {int(worker_id)}"
            print(sql_update)
            MySQLConnection.verify_connection()
            connection = MySQLConnection.create_connection()
            MySQLConnection.execute_query(connection, sql_update)
            connection.close()

    # контекстное меню
    def _open_menu(self, position):
        cur_index = self.ui.treeView.currentIndex()
        cur_name = cur_index.data()

        worker_id = 0
        dep_id = 0
        if cur_index.parent().isValid():
            worker_id = self.ui.lineEdit_worker_id.text()
            dep_id = func.get_dep_id_from_name(cur_index.parent().data(), self.dep_dict)
        else:
            dep_id = func.get_dep_id_from_name(cur_index.data(), self.dep_dict)

        menu = QMenu()

        # вложенное меню перевода сотрудника в другой отдел
        inner_menu_1 = QMenu("Перевести в отдел")
        for dep in self.dep_dict:
            if worker_id in self.worker_deps_dict and dep not in self.worker_deps_dict[worker_id]:
                inner_menu_1.addAction(self.dep_dict[dep]['name'])

        # вложенное меню добавление сотрудника в другой отдел
        inner_menu_2 = QMenu("Добавить в отдел")
        for dep in self.dep_dict:
            if worker_id in self.worker_deps_dict and dep not in self.worker_deps_dict[worker_id]:
                inner_menu_2.addAction(self.dep_dict[dep]['name'])

        action_hire_worker = QAction()
        action_hire_worker.setText("Уволить сотрудника")
        action_hire_worker.triggered.connect(self._delete_worker)

        action_make_employee = QAction()
        action_make_employee.setText("Снять с должности")
        action_make_employee.triggered.connect(lambda: self._transfer_to_dep(worker_id, dep_id))

        action_make_boss = QAction()
        action_make_boss.setText("Назначить начальником")
        action_make_boss.triggered.connect(lambda: self._make_boss(worker_id, dep_id))

        action_make_boss_assistant = QAction()
        action_make_boss_assistant.setText("Назначить заместителем начальника")
        action_make_boss_assistant.triggered.connect(lambda: self._make_boss_assistant(worker_id, dep_id))

        action_add_worker = QAction()
        action_add_worker.setText("Добавить сотрудника в этот отдел")
        action_add_worker.triggered.connect(self._add_worker)

        action_transfer_to_reserve = QAction()
        action_transfer_to_reserve.setText("Отправить в резерв")
        action_transfer_to_reserve.triggered.connect(lambda: self._transfer_to_dep(worker_id, "-1"))

        action_remove_from_dep = QAction()
        action_remove_from_dep.setText("Убрать из отдела")
        action_remove_from_dep.triggered.connect(lambda: self._remove_from_dep(worker_id, dep_id))

        # правый клик на отделе
        if not cur_index.parent().isValid():
            if cur_index.data() != "Резерв":
                menu.addAction(action_add_worker)
            else:
                pass

        # правый клик на сотруднике
        else:
            # клик не по резерву
            if cur_index.parent().data() != self.reserve_name:
                # клик по начальнику
                if "нач. " in cur_name:
                    menu.addAction(action_make_employee)
                    menu.addAction(action_make_boss_assistant)

                #  клик по заму
                elif "зам. " in cur_name:
                    menu.addAction(action_make_employee)
                    menu.addAction(action_make_boss)

                # клик по простому сотруднику
                else:
                    menu.addAction(action_make_boss)
                    menu.addAction(action_make_boss_assistant)

                menu.addSeparator()
                menu.addMenu(inner_menu_1)
                menu.addMenu(inner_menu_2)
                if worker_id in self.worker_deps_dict[worker_id] and len(self.worker_deps_dict[worker_id]) > 1:
                    menu.addAction(action_remove_from_dep)
                menu.addSeparator()
                menu.addAction(action_transfer_to_reserve)
                menu.addAction(action_hire_worker)
            # клик по резерву
            else:
                menu.addMenu(inner_menu_1)
                menu.addSeparator()
                menu.addAction(action_hire_worker)

        menu_selection = menu.exec_(self.ui.treeView.viewport().mapToGlobal(position))
        if menu_selection:
            if menu_selection.parent():
                if menu_selection.parent().title() == "Перевести в отдел":
                    dep_in = func.get_dep_id_from_name(menu_selection.text(), self.dep_dict)
                    self._transfer_to_dep(worker_id, dep_in)
                elif menu_selection.parent().title() == "Добавить в отдел":
                    dep_in = func.get_dep_id_from_name(menu_selection.text(), self.dep_dict)
                    self._add_to_dep(worker_id, dep_in)

    def _make_boss(self, new_boss_id, dep_id):
        old_boss_id = self.dep_dict[dep_id]['boss']
        old_boss_assistant_id = self.dep_dict[dep_id]['boss_assistant']

        if old_boss_id == new_boss_id:
            return
        elif old_boss_assistant_id == new_boss_id:
            sql_update_deps = f"UPDATE departments SET " \
                              f"dep_boss = {int(new_boss_id)}, " \
                              f"dep_boss_assistant = 0 " \
                              f"WHERE dep_id = {int(dep_id)}"
        else:
            sql_update_deps = f"UPDATE departments SET " \
                              f"dep_boss = {int(new_boss_id)} " \
                              f"WHERE dep_id = {int(dep_id)}"

        MySQLConnection.verify_connection()
        connection = MySQLConnection.create_connection()
        MySQLConnection.execute_query(connection, sql_update_deps)
        connection.close()
        self._clear_worker_area()
        self._create_tree_view_model()

    def _make_boss_assistant(self, new_boss_assistant_id, dep_id):
        old_boss_id = self.dep_dict[dep_id]['boss']
        old_boss_assistant_id = self.dep_dict[dep_id]['boss_assistant']

        if old_boss_assistant_id == new_boss_assistant_id:
            return
        elif old_boss_id == new_boss_assistant_id:
            sql_update_deps = f"UPDATE departments SET " \
                              f"dep_boss = 0, " \
                              f"dep_boss_assistant = {int(new_boss_assistant_id)} WHERE " \
                              f"dep_id = {int(dep_id)}"
        else:
            sql_update_deps = f"UPDATE departments SET " \
                              f"dep_boss_assistant = {int(new_boss_assistant_id)} WHERE " \
                              f"dep_id = {int(dep_id)}"

        MySQLConnection.verify_connection()
        connection = MySQLConnection.create_connection()
        MySQLConnection.execute_query(connection, sql_update_deps)
        connection.close()
        self._clear_worker_area()
        self._create_tree_view_model()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = WorkersWidget()
    window.resize(1000, 600)
    window.setWindowTitle("Сотрудники")
    window.show()
    sys.exit(app.exec())
