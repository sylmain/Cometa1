import re

from PyQt5.QtCore import QStringListModel, Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtWidgets import QWidget, QApplication, QAbstractItemView, QMessageBox, QPushButton, QInputDialog, QMenu, \
    QAction

from functions_pkg.db_functions import MySQLConnection
from rooms_pkg.ui_rooms import Ui_Form
import functions_pkg.functions as func


class RoomsWidget(QWidget):
    def __init__(self):
        super(RoomsWidget, self).__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.dep_dict = dict()
        self.worker_dict = dict()
        self.room_dict = dict()
        self.dep_rooms_dict = dict()
        self.room_deps_dict = dict()

        self.organization_name = func.get_organization_name()

        self.tree_view_model = QStandardItemModel(0, 1, parent=self)
        self.resp_person_model = QStringListModel()

        self._initialize()

        self.setWindowTitle("Метрологические помещения")

        # todo вставить иконку
        self.setWindowIcon(QIcon("D:/cometa/mainwindow_icon.png"))
        self.resize(870, 720)

    def _initialize(self):

        # присваиваем модели дереву и комбобоксам
        self.ui.treeView.setModel(self.tree_view_model)
        self.ui.comboBox_room_responsible_person.setModel(self.resp_person_model)

        # задаем индексы перехода по tab
        RoomsWidget.setTabOrder(self.ui.lineEdit_room_number, self.ui.plainTextEdit_room_name)
        RoomsWidget.setTabOrder(self.ui.plainTextEdit_room_name, self.ui.lineEdit_room_area)
        RoomsWidget.setTabOrder(self.ui.lineEdit_room_area, self.ui.plainTextEdit_room_purpose)
        RoomsWidget.setTabOrder(self.ui.plainTextEdit_room_purpose, self.ui.comboBox_room_responsible_person)
        RoomsWidget.setTabOrder(self.ui.comboBox_room_responsible_person, self.ui.plainTextEdit_room_requirements)
        RoomsWidget.setTabOrder(self.ui.plainTextEdit_room_requirements, self.ui.plainTextEdit_room_conditions)
        RoomsWidget.setTabOrder(self.ui.plainTextEdit_room_conditions, self.ui.plainTextEdit_room_equipment)
        RoomsWidget.setTabOrder(self.ui.plainTextEdit_room_equipment, self.ui.plainTextEdit_room_personal)
        RoomsWidget.setTabOrder(self.ui.plainTextEdit_room_personal, self.ui.plainTextEdit_room_info)

        self._create_tree_view_model()
        self._make_connects()
        self._draw_treeview()

    def _create_tree_view_model(self):

        self.ui.label_8.setStyleSheet("color: none")

        self.tree_view_model.clear()
        self._clear_room_area()
        self.tree_view_model.setHorizontalHeaderLabels([f"Отделы и помещения {self.organization_name}"])

        self.departments = func.get_departments()
        self.workers = func.get_workers()
        self.rooms = func.get_rooms()
        self.room_dep = func.get_room_deps()
        dep_workers = func.get_worker_deps()

        self.dep_dict = self.departments['dep_dict']

        self.worker_dict = self.workers['worker_dict']
        self.dep_workers_dict = dep_workers['dep_workers_dict']
        self.worker_deps_dict = dep_workers['worker_deps_dict']
        self.room_dict = self.rooms['room_dict']
        self.dep_rooms_dict = self.room_dep['dep_rooms_dict']
        self.room_deps_dict = self.room_dep['room_deps_dict']

        self._update_treeview()
        # разворачиваем все элементы
        self.ui.treeView.expandAll()

        self.ui.pushButton_delete.setDisabled(True)
        self.ui.pushButton_add_rooms.setDisabled(True)
        self.ui.pushButton_save.setDisabled(True)
        self.ui.lineEdit_room_number.setReadOnly(True)

    def _update_treeview(self):
        self._add_rooms_in_model()

    def _add_rooms_in_model(self):
        for dep in self.dep_dict:
            dep_name = self.dep_dict[dep]['name']
            item = QStandardItem(dep_name)
            self.tree_view_model.appendRow(item)
            if dep in self.dep_rooms_dict:
                for room in self.dep_rooms_dict[dep]:
                    item.appendRow([QStandardItem(self.room_dict[room]['number'])])

    def _draw_treeview(self):

        #   ставим автоматические переносы
        self.ui.treeView.setWordWrap(True)

        #   устанавливаем ширину первого столбца
        self.ui.treeView.setColumnWidth(0, 350)

        self.ui.treeView.setAnimated(True)
        self.ui.treeView.setSortingEnabled(True)
        self.ui.treeView.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.ui.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.treeView.customContextMenuRequested.connect(self._open_menu)

    def _make_connects(self):

        # выбор элемента в списке
        self.ui.treeView.selectionModel().selectionChanged.connect(self._on_selection_changed)

        # клик по кнопке "Добавить помещения"
        self.ui.pushButton_add_rooms.clicked.connect(self._add_rooms)

        # клик по кнопке "Удалить помещение"
        self.ui.pushButton_delete.clicked.connect(self._delete_room)

        # клик по кнопке "Сохранить"
        self.ui.pushButton_save.clicked.connect(self._save_room)

        # изменение текста в поле Владелец
        self.ui.plainTextEdit_rent.textChanged.connect(self._radio_switch)

    def _on_selection_changed(self):
        if not self.ui.treeView.selectedIndexes():
            return

        cur_index = self.ui.treeView.currentIndex()
        if not cur_index.isValid():
            return
        # щелчок по отделу
        if not cur_index.parent().isValid():
            self._clear_room_area()
            self.ui.pushButton_delete.setDisabled(True)
            self.ui.pushButton_add_rooms.setEnabled(True)
            self.ui.pushButton_save.setDisabled(True)
            self.ui.lineEdit_room_number.setReadOnly(True)
        # щелчок по комнате
        else:
            self._update_room_area(cur_index)
            self.ui.pushButton_delete.setEnabled(True)
            self.ui.pushButton_add_rooms.setDisabled(True)
            self.ui.pushButton_save.setEnabled(True)
            self.ui.lineEdit_room_number.setReadOnly(False)

    def _update_room_area(self, cur_index):
        room_id = func.get_room_id_from_number(cur_index.data(), self.room_dict)
        self.ui.lineEdit_room_id.setText(room_id)
        self.ui.lineEdit_room_number.setText(self.room_dict[room_id]['number'])
        self.ui.plainTextEdit_room_name.setPlainText(self.room_dict[room_id]['name'])
        self.ui.lineEdit_room_area.setText(self.room_dict[room_id]['area'])
        self.ui.plainTextEdit_room_purpose.setPlainText(self.room_dict[room_id]['purpose'])
        self.ui.plainTextEdit_room_requirements.setPlainText(self.room_dict[room_id]['requirements'])
        self.ui.plainTextEdit_room_conditions.setPlainText(self.room_dict[room_id]['conditions'])
        self.ui.plainTextEdit_room_equipment.setPlainText(self.room_dict[room_id]['equipment'])
        if self.room_dict[room_id]['owner'] == self.organization_name:
            self.ui.radioButton_own.setChecked(True)
        else:
            self.ui.radioButton_rent.setChecked(True)
            self.ui.plainTextEdit_rent.setPlainText(self.room_dict[room_id]['owner'])
        self.ui.plainTextEdit_room_personal.setPlainText(self.room_dict[room_id]['personal'])
        self.ui.plainTextEdit_room_info.setPlainText(self.room_dict[room_id]['info'])
        dep_name = cur_index.parent().data()

        dep_list = list()
        for dep_id in self.room_deps_dict[room_id]:
            dep_list.append(dep_id)
        worker_list = func.get_workers_list(dep_list, self.worker_dict, self.dep_workers_dict)['workers']
        worker_list.append("")
        self.resp_person_model.setStringList(worker_list)

        worker = func.get_worker_fio_from_id(self.room_dict[room_id]['resp_person'], self.worker_dict)
        if worker in worker_list:
            self.ui.comboBox_room_responsible_person.setCurrentText(worker)
        else:
            self.ui.comboBox_room_responsible_person.setCurrentText("")
        if self.ui.comboBox_room_responsible_person.currentText() == "":
            self.ui.label_8.setStyleSheet("color: Red")
        else:
            self.ui.label_8.setStyleSheet("color: none")

    def _clear_room_area(self):
        self.ui.lineEdit_room_id.setText("")
        self.ui.lineEdit_room_number.setText("")
        self.ui.plainTextEdit_room_name.setPlainText("")
        self.ui.lineEdit_room_area.setText("")
        self.ui.plainTextEdit_room_purpose.setPlainText("")
        self.ui.plainTextEdit_room_requirements.setPlainText("")
        self.ui.plainTextEdit_room_conditions.setPlainText("")
        self.ui.plainTextEdit_room_equipment.setPlainText("")
        self.ui.radioButton_own.setChecked(True)
        self.ui.plainTextEdit_room_personal.setPlainText("")
        self.ui.plainTextEdit_room_info.setPlainText("")
        self.ui.comboBox_room_responsible_person.clear()

    def _add_rooms(self):
        cur_index = self.ui.treeView.currentIndex()
        if cur_index.parent().isValid():
            dep_id = func.get_dep_id_from_name(cur_index.parent().data(), self.dep_dict)
        else:
            dep_id = func.get_dep_id_from_name(cur_index.data(), self.dep_dict)
        room_set = set()
        room_line = ""
        if not self.ui.lineEdit_room_number.text():
            dialog = QInputDialog(self)
            dialog.setInputMode(QInputDialog.TextInput)
            dialog.setWindowTitle("Номера помещений (лабораторий)")
            dialog.setLabelText(f"Добавление помещений в '{func.get_dep_name_from_id(dep_id, self.dep_dict)}'\n"
                                f"Введите номера помещений через запятую\n"
                                f"Можно вводить диапазоны через троеточие (1...4, 215-в, 9а, 10...15)")
            dialog.resize(500, 100)
            ok = dialog.exec()
            result = dialog.textValue()
            if ok and result:
                room_line = result
        else:
            room_line = self.ui.lineEdit_room_number.text()
        for room in room_line.split(","):
            if "..." in room.strip():
                try:
                    for i in range(int(room.split("...")[0]), int(room.split("...")[1]) + 1):
                        room_set.add(str(i))
                except:
                    print("Неверный диапазон")
                    return
            else:
                room_set.add(room.strip())

        if len(room_set) > 0:
            MySQLConnection.verify_connection()
            connection = MySQLConnection.create_connection()
            for room in room_set:
                if room != "":
                    insert_sql_1 = f"INSERT IGNORE INTO rooms (room_number) VALUES " \
                                   f"('{room}')"
                    room_id = MySQLConnection.execute_query(connection, insert_sql_1)[1]
                    if room_id != 0:
                        insert_sql_2 = f"INSERT IGNORE INTO rooms_departments VALUES " \
                                       f"({int(room_id)}, {int(dep_id)})"
                        MySQLConnection.execute_query(connection, insert_sql_2)
            connection.close()
            self._create_tree_view_model()

    def _save_room(self):

        room_id = self.ui.lineEdit_room_id.text()

        # проверка на совпадение номеров кабинетов. Если отличаются, подтверждение изменения номера
        room_number_old = self.ui.treeView.currentIndex().data()
        room_number_new = self.ui.lineEdit_room_number.text()
        if room_number_new != room_number_old:
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Подтверждение изменения номера")
            dialog.setText(f"Вы действительно хотите поменять номер помещения с \"{room_number_old}\"?\n"
                           f"на \"{room_number_new}\"?")
            dialog.setIcon(QMessageBox.Question)
            btn_yes = QPushButton("&Да")
            btn_no = QPushButton("&Нет")
            dialog.addButton(btn_yes, QMessageBox.AcceptRole)
            dialog.addButton(btn_no, QMessageBox.RejectRole)
            dialog.setDefaultButton(btn_no)
            dialog.setEscapeButton(btn_no)
            result = dialog.exec()
            if result != 0:
                self.ui.lineEdit_room_number.setText(room_number_old)
                return

        #  получение id ответственного за комнату из комбобокса
        resp_person_id = func.get_worker_id_from_fio(self.ui.comboBox_room_responsible_person.currentText(),
                                                     self.worker_dict)

        # проверка площади
        if not self.ui.lineEdit_room_area.text():
            room_area = "0"
        else:
            if re.fullmatch("^(\d+)[.,]*(\d*)$", self.ui.lineEdit_room_area.text()):
                room_area = func.dot_to_comma(self.ui.lineEdit_room_area.text())
            else:
                QMessageBox.warning(self, "Ошибка",
                                    f"Введенная площадь помещения \"{self.ui.lineEdit_room_area.text()}\" "
                                    f"не является числом. Единицы измерения вводить не нужно")
                return

        # получение владельца
        if self.ui.radioButton_own.isChecked():
            room_owner = self.organization_name
        else:
            room_owner = self.ui.plainTextEdit_rent.toPlainText()

        MySQLConnection.verify_connection()
        connection = MySQLConnection.create_connection()
        rooms_sql = f"UPDATE rooms " \
                    f"SET " \
                    f"room_number = '{self.ui.lineEdit_room_number.text()}', " \
                    f"room_name = '{self.ui.plainTextEdit_room_name.toPlainText()}', " \
                    f"room_area = '{room_area}', " \
                    f"room_responsible_person = {int(resp_person_id)}, " \
                    f"room_purpose = '{self.ui.plainTextEdit_room_purpose.toPlainText()}', " \
                    f"room_requirements = '{self.ui.plainTextEdit_room_requirements.toPlainText()}', " \
                    f"room_conditions = '{self.ui.plainTextEdit_room_conditions.toPlainText()}', " \
                    f"room_equipment = '{self.ui.plainTextEdit_room_equipment.toPlainText()}', " \
                    f"room_owner = '{room_owner}', " \
                    f"room_personal = '{self.ui.plainTextEdit_room_personal.toPlainText()}', " \
                    f"room_info = '{self.ui.plainTextEdit_room_info.toPlainText()}' " \
                    f"WHERE room_id = {int(room_id)};"
        MySQLConnection.execute_query(connection, rooms_sql)
        connection.close()
        self._create_tree_view_model()
        QMessageBox.information(self, "Сохранено", "Информация сохранена")

    def _delete_room(self):

        room_number = self.ui.treeView.currentIndex().data()
        room_id = self.ui.lineEdit_room_id.text()

        dialog = QMessageBox(self)
        dialog.setWindowTitle("Подтверждение удаления")
        dialog.setText(f"Вы действительно хотите удалить помещение \"{room_number}\"?\n"
                       f"Также будет удалена вся информация о помещении")
        dialog.setIcon(QMessageBox.Question)
        btn_yes = QPushButton("&Да")
        btn_no = QPushButton("&Нет")
        dialog.addButton(btn_yes, QMessageBox.AcceptRole)
        dialog.addButton(btn_no, QMessageBox.RejectRole)
        dialog.setDefaultButton(btn_no)
        dialog.setEscapeButton(btn_no)
        result = dialog.exec()
        if result == 0:
            delete_1 = f"DELETE FROM rooms WHERE " \
                       f"room_id = '{int(room_id)}'"

            delete_2 = f"DELETE FROM rooms_departments WHERE " \
                       f"RD_room_id = {int(room_id)}"

            MySQLConnection.verify_connection()
            connection = MySQLConnection.create_connection()
            MySQLConnection.execute_transaction_query(connection, delete_1, delete_2)
            connection.close()
            self._create_tree_view_model()

    # контекстное меню
    def _open_menu(self, position):

        inner_menu_1_text = "Передать в"
        inner_menu_2_text = "Совместное использование с"
        cur_index = self.ui.treeView.currentIndex()

        room_id = 0
        dep_id = 0
        if cur_index.parent().isValid():
            room_id = self.ui.lineEdit_room_id.text()
            dep_id = func.get_dep_id_from_name(cur_index.parent().data(), self.dep_dict)
        else:
            dep_id = func.get_dep_id_from_name(cur_index.data(), self.dep_dict)

        menu = QMenu()

        # вложенное меню передачи помещения в другой отдел
        inner_menu_1 = QMenu(inner_menu_1_text)
        for dep in self.dep_dict:
            if dep != dep_id and room_id in self.room_deps_dict and dep not in self.room_deps_dict[room_id]:
                inner_menu_1.addAction(self.dep_dict[dep]['name'])

        # вложенное меню добавления помещения в другой отдел
        inner_menu_2 = QMenu(inner_menu_2_text)
        for dep in self.dep_dict:
            if dep != dep_id and room_id in self.room_deps_dict and dep not in self.room_deps_dict[room_id]:
                inner_menu_2.addAction(self.dep_dict[dep]['name'])

        action_delete_room = QAction()
        action_delete_room.setText("Удалить помещение")
        action_delete_room.triggered.connect(self._delete_room)

        action_remove_from_dep = QAction()
        action_remove_from_dep.setText("Убрать из отдела")
        action_remove_from_dep.triggered.connect(lambda: self._remove_from_dep(room_id, dep_id))

        action_add_rooms = QAction()
        action_add_rooms.setText("Добавить помещения в этот отдел")
        action_add_rooms.triggered.connect(self._add_rooms)

        # правый клик на отделе
        if not cur_index.parent().isValid():
            menu.addAction(action_add_rooms)

        # правый клик на помещении
        else:
            menu.addMenu(inner_menu_1)
            menu.addMenu(inner_menu_2)
            menu.addSeparator()
            if len(self.room_deps_dict[room_id]) > 1:
                menu.addAction(action_remove_from_dep)
                menu.addSeparator()
            menu.addAction(action_delete_room)

        menu_selection = menu.exec_(self.ui.treeView.viewport().mapToGlobal(position))
        if menu_selection:
            if menu_selection.parent():
                # передача помещения в другой отдел
                if menu_selection.parent().title() == inner_menu_1_text:
                    dep_in = func.get_dep_id_from_name(menu_selection.text(), self.dep_dict)
                    self._transfer_to_dep(room_id, dep_id, dep_in)
                # добавление помещения в другой отдел
                if menu_selection.parent().title() == inner_menu_2_text:
                    dep_in = func.get_dep_id_from_name(menu_selection.text(), self.dep_dict)
                    self._add_to_dep(room_id, dep_in)

    def _remove_from_dep(self, room_id, dep_id):
        sql_update = f"DELETE FROM rooms_departments " \
                     f"WHERE RD_room_id = {int(room_id)} AND RD_dep_id = {int(dep_id)}"
        MySQLConnection.verify_connection()
        connection = MySQLConnection.create_connection()
        MySQLConnection.execute_query(connection, sql_update)
        connection.close()
        self._create_tree_view_model()
        self._choose_new_room_resp(room_id)
        self._create_tree_view_model()

    def _transfer_to_dep(self, room_id, old_dep_id, new_dep_id):
        sql_update = f"UPDATE rooms_departments " \
                     f"SET RD_room_id = {int(room_id)}, RD_dep_id = {int(new_dep_id)} " \
                     f"WHERE RD_room_id = {int(room_id)} AND RD_dep_id = {int(old_dep_id)}"
        MySQLConnection.verify_connection()
        connection = MySQLConnection.create_connection()
        MySQLConnection.execute_query(connection, sql_update)
        connection.close()
        self._create_tree_view_model()
        self._choose_new_room_resp(room_id)
        self._create_tree_view_model()

    def _add_to_dep(self, room_id, dep_id):
        sql_insert = f"INSERT INTO rooms_departments VALUES " \
                     f"({int(room_id)}, {int(dep_id)})"
        MySQLConnection.verify_connection()
        connection = MySQLConnection.create_connection()
        MySQLConnection.execute_query(connection, sql_insert)
        connection.close()
        self._create_tree_view_model()
        self._choose_new_room_resp(room_id)
        self._create_tree_view_model()

    # выбираем и записываем нового ответственного за помещения
    def _choose_new_room_resp(self, room_id):
        room_number = func.get_room_number_from_id(room_id, self.room_dict)

        dep_list = list()
        for dep_id in self.room_deps_dict[room_id]:
            dep_list.append(dep_id)
        new_resp_person_list = func.get_workers_list(dep_list, self.worker_dict, self.dep_workers_dict)['workers']
        new_resp_person_list.append("")
        if len(new_resp_person_list) == 1:
            QMessageBox.warning(self, "Предупреждение",
                                f"Ответственный за помещение \"{room_number}\" не назначен, "
                                f"т.к. в отделах {', '.join(self.room_deps_dict[room_id])} нет сотрудников")
            sql_update = f"UPDATE rooms SET " \
                         f"room_responsible_person = 0 " \
                         f"WHERE room_id = {int(room_id)}"
            MySQLConnection.verify_connection()
            connection = MySQLConnection.create_connection()
            MySQLConnection.execute_query(connection, sql_update)
            connection.close()
            return
        else:
            worker, ok = QInputDialog.getItem(self, "Выбор ответственного",
                                              f"Выберите нового ответственного за помещение",
                                              new_resp_person_list, current=0, editable=False)
            if ok:
                new_resp_person_id = func.get_worker_id_from_fio(worker, self.worker_dict)
            else:
                new_resp_person_id = "0"
            if new_resp_person_id == "0":
                QMessageBox.warning(self, "Предупреждение",
                                    f"Ответственный за помещение не назначен")
            sql_update = f"UPDATE rooms SET " \
                         f"room_responsible_person = {int(new_resp_person_id)} " \
                         f"WHERE room_id = {int(room_id)}"
            MySQLConnection.verify_connection()
            connection = MySQLConnection.create_connection()
            MySQLConnection.execute_query(connection, sql_update)
            connection.close()

    def _radio_switch(self):
        if not self.ui.plainTextEdit_rent.toPlainText():
            self.ui.radioButton_own.setChecked(True)
        else:
            self.ui.radioButton_rent.setChecked(True)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = RoomsWidget()
    window.resize(870, 720)
    window.show()
    sys.exit(app.exec())
