from PyQt5.QtCore import QStringListModel, Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtWidgets import QWidget, QApplication, QInputDialog, QMessageBox, QPushButton, QAbstractItemView, QMenu, \
    QAction

from departments_pkg.ui_departments import Ui_Form
from functions_pkg.db_functions import MySQLConnection
import functions_pkg.functions as func


class DepartmentsWidget(QWidget):

    def __init__(self, parent=None):
        super(DepartmentsWidget, self).__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.dep_dict = dict()
        self.worker_dict = dict()

        # список id отделов на удаление
        self.delete_id_list = list()

        # текущий список отделов дерева для drag&drop обновления
        self.current_treeview_list = list()

        self.organization_name = func.get_organization_name()
        self.director_name = func.get_director_name()

        self.tree_view_model = QStandardItemModel(0, 1, parent=self)
        self.boss_model = QStringListModel()
        self.boss_assistant_model = QStringListModel()

        self._initialize()

        self.setWindowTitle(f"Метрологические подразделения {self.organization_name}")

        # todo вставить иконку
        self.setWindowIcon(QIcon("D:/cometa/mainwindow_icon.png"))
        self.resize(900, 700)

    def _initialize(self):
        # присваиваем модели дереву и комбобоксам
        self.ui.treeView.setModel(self.tree_view_model)
        self.ui.comboBox_dep_boss.setModel(self.boss_model)
        self.ui.comboBox_dep_boss_assistant.setModel(self.boss_assistant_model)

        self._create_tree_view_model()
        self._make_connects()
        self._draw_treeview()

    def _create_tree_view_model(self):

        self.ui.label_4.setStyleSheet("color: none")

        self.tree_view_model.clear()
        self.tree_view_model.setHorizontalHeaderLabels([f"Организационная структура {self.organization_name}"])

        self.dep_dict = func.get_departments()['dep_dict']
        self.worker_dict = func.get_workers()['worker_dict']
        self.dep_workers_dict = func.get_worker_deps()['dep_workers_dict']

        self._update_treeview()
        # разворачиваем все элементы
        self.ui.treeView.expandAll()

    def _update_treeview(self):

        # добавляем в дерево отделы без родителей
        for dep in self.dep_dict:
            if self.dep_dict[dep]['parent'] == "0":
                self.tree_view_model.appendRow([QStandardItem(self.dep_dict[dep]['name'])])

        # создаем иерархию отделов рекурсивным поиском
        self._add_deps_in_model(self.tree_view_model.invisibleRootItem())

        # очищаем правую сторону
        self._clear_dep_area()

    def _draw_treeview(self):

        #   ставим автоматические переносы
        self.ui.treeView.setWordWrap(True)

        #   устанавливаем ширину первого столбца
        self.ui.treeView.setColumnWidth(0, 350)

        self.ui.treeView.setDragEnabled(True)
        self.ui.treeView.setDragDropMode(QAbstractItemView.InternalMove)
        self.ui.treeView.setDropIndicatorShown(True)
        self.ui.treeView.setAutoScroll(True)
        self.ui.treeView.setAnimated(True)
        self.ui.treeView.setSortingEnabled(True)
        self.ui.treeView.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.ui.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.treeView.customContextMenuRequested.connect(self._open_menu)

    def _add_deps_in_model(self, item):
        if not item.hasChildren():
            return
        for i in range(item.rowCount()):
            for dep in self.dep_dict:
                parent_name = ""
                if self.dep_dict[dep]['parent'] != "0":
                    parent_name = self.dep_dict[self.dep_dict[dep]['parent']]['name']
                if parent_name == item.child(i).text():
                    item.child(i).appendRow([QStandardItem(self.dep_dict[dep]['name'])])
            self._add_deps_in_model(item.child(i))

    def _delete_dep_list(self, item):
        if not item.hasChildren():
            return
        for i in range(item.rowCount()):
            dep_name = item.child(i).text()
            self.delete_id_list.append(int(func.get_dep_id_from_name(dep_name, self.dep_dict)))
            self._delete_dep_list(item.child(i))

    def _make_connects(self):

        # выбор элемента в списке
        self.ui.treeView.selectionModel().selectionChanged.connect(self._on_selection_changed)

        # клик по кнопке "Сохранить структуру"
        self.ui.pushButton_save_tree.clicked.connect(self._save_tree)

        # клик по кнопке "Новый отдел"
        self.ui.pushButton_new_dep.clicked.connect(lambda: self._add_department(0))

        # клик по кнопке "Удалить отдел"
        self.ui.pushButton_remove_dep.clicked.connect(self._delete_department)

        # клик по кнопке "Сохранить информацию"
        self.ui.pushButton_save_dep.clicked.connect(self._save_department)

        # изменение текущего начальника отдела
        self.ui.comboBox_dep_boss.currentTextChanged.connect(self._delete_boss_from_assistants)

        # кнопка Развернуть все
        self.ui.pushButton_expand_all.clicked.connect(lambda: self.ui.treeView.expandAll())

        # кнопка Свернуть все
        self.ui.pushButton_collapse_all.clicked.connect(lambda: self.ui.treeView.collapseAll())

    def _make_current_treeview_list(self, item):
        if not item.hasChildren():
            return
        for i in range(item.rowCount()):
            parent_name = item.text()
            child_name = item.child(i).text()
            parent_id = func.get_dep_id_from_name(parent_name, self.dep_dict)
            child_id = func.get_dep_id_from_name(child_name, self.dep_dict)
            self.current_treeview_list.append((child_id, child_name, parent_id))
            self._make_current_treeview_list(item.child(i))

    def _save_tree(self):
        self.current_treeview_list.clear()
        self._make_current_treeview_list(self.tree_view_model.invisibleRootItem())

        MySQLConnection.verify_connection()
        connection = MySQLConnection.get_connection()
        for dep in self.current_treeview_list:
            update_sql = f"UPDATE departments SET " \
                         f"dep_parent = {int(dep[2])} " \
                         f"WHERE dep_id = {int(dep[0])};"
            MySQLConnection.execute_query(connection, update_sql)
        connection.close()
        QMessageBox.information(self, "Сохранено", "Структура сохранена")

    def _on_selection_changed(self):

        if not self.ui.treeView.selectedIndexes():
            return

        if not self.ui.treeView.currentIndex().isValid():
            return

        self._update_dep_area()

    def _update_dep_area(self):

        cur_dep_id = func.get_dep_id_from_name(self.ui.treeView.currentIndex().data(), self.dep_dict)

        self.ui.lineEdit_dep_id.setText(cur_dep_id)
        self.ui.textEdit_dep_name.setText(self.dep_dict[cur_dep_id]['name'])
        self.ui.lineEdit_dep_abbr.setText(self.dep_dict[cur_dep_id]['abbr'])
        self.ui.lineEdit_dep_number.setText(self.dep_dict[cur_dep_id]['number'])
        self.ui.textEdit_dep_info.setText(self.dep_dict[cur_dep_id]['info'])
        self.ui.lineEdit_boss_post.setText(self.dep_dict[cur_dep_id]['boss_post'])
        self.ui.lineEdit_boss_assistant_post.setText(self.dep_dict[cur_dep_id]['boss_assistant_post'])

        dep_workers_list = func.get_workers_list([cur_dep_id], self.worker_dict, self.dep_workers_dict)[
            'worker_and_numbers']
        boss_name = func.get_worker_fio_and_number_from_id(self.dep_dict[cur_dep_id]['boss'], self.worker_dict)
        boss_assistant_name = func.get_worker_fio_and_number_from_id(self.dep_dict[cur_dep_id]['boss_assistant'],
                                                                     self.worker_dict)
        dep_workers_list.append("")
        self.boss_model.setStringList(dep_workers_list)
        if boss_name:
            self.ui.comboBox_dep_boss.setCurrentIndex(
                self.ui.comboBox_dep_boss.findText(boss_name, flags=Qt.MatchStartsWith))
        else:
            self.ui.comboBox_dep_boss.setCurrentText('')

        self.boss_assistant_model.setStringList(dep_workers_list)
        if self.ui.comboBox_dep_boss.currentText() != "":
            self.ui.comboBox_dep_boss_assistant.removeItem(
                self.ui.comboBox_dep_boss_assistant.findText(boss_name, flags=Qt.MatchStartsWith))

        if boss_assistant_name:
            self.ui.comboBox_dep_boss_assistant.setCurrentIndex(
                self.ui.comboBox_dep_boss_assistant.findText(boss_assistant_name, flags=Qt.MatchStartsWith))
        else:
            self.ui.comboBox_dep_boss_assistant.setCurrentText('')

        if self.ui.comboBox_dep_boss.currentText() == "":
            self.ui.label_4.setStyleSheet("color: red")
        else:
            self.ui.label_4.setStyleSheet("color: none")

    def _clear_dep_area(self):

        self.ui.treeView.clearSelection()
        self.ui.lineEdit_dep_id.setText("")
        self.ui.textEdit_dep_name.setText("")
        self.ui.lineEdit_dep_abbr.setText("")
        self.ui.lineEdit_dep_number.setText("")
        self.ui.lineEdit_boss_post.setText("")
        self.ui.lineEdit_boss_assistant_post.setText("")
        self.ui.textEdit_dep_info.setText("")

        self.boss_model.setStringList([])
        self.boss_assistant_model.setStringList([])

    def _delete_boss_from_assistants(self):
        dep_id = self.ui.lineEdit_dep_id.text()
        cur_boss_assistant = self.ui.comboBox_dep_boss_assistant.currentText()
        dep_workers_list = func.get_workers_list([dep_id], self.worker_dict, self.dep_workers_dict)[
            'worker_and_numbers']
        boss = self.ui.comboBox_dep_boss.currentText()
        if boss:
            dep_workers_list.remove(boss)
        dep_workers_list.append('')
        self.boss_assistant_model.setStringList(dep_workers_list)
        self.ui.comboBox_dep_boss_assistant.setCurrentText(cur_boss_assistant)

    def _add_department(self, dep_parent_id):

        dialog = QInputDialog(self)
        dialog.setInputMode(QInputDialog.TextInput)
        dialog.setWindowTitle("Создание отдела")
        dialog.setLabelText("Введите название отдела")
        dialog.resize(500, 100)
        ok = dialog.exec()
        result = dialog.textValue()
        if ok and result:
            dep_name = result
            MySQLConnection.verify_connection()
            connection = MySQLConnection.get_connection()
            create_dep = f"INSERT INTO departments (dep_id, dep_name, dep_parent) VALUES " \
                         f"(NULL, '{dep_name}', {int(dep_parent_id)});"

            resp = MySQLConnection.execute_query(connection, create_dep)
            connection.close()
            if resp[0]:
                self._create_tree_view_model()
            elif resp[1] == 1062:
                dialog = QMessageBox(self)
                dialog.setWindowTitle("Дублирование наименования отдела")
                dialog.setText(f"Отдел с таким именем \"{dep_name}\" существует.\n"
                               f"Дублирование невозможно.")
                dialog.setIcon(QMessageBox.Information)
                btn_close = QPushButton("&Закрыть")
                dialog.addButton(btn_close, QMessageBox.AcceptRole)
                dialog.setDefaultButton(btn_close)
                dialog.exec()

    def _delete_department(self):
        if not self.ui.treeView.selectedIndexes():
            return
        dep_name = self.ui.treeView.currentIndex().data()
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Подтверждение удаления")
        dialog.setText(f"Вы действительно хотите удалить \"{dep_name}\"?\n"
                       f"Также удалятся все подотделы и информация о работающих в отделах сотрудниках.\n"
                       f"Cотрудники отдела переместятся в \"Резерв\" соответствующего справочника.")
        dialog.setIcon(QMessageBox.Question)
        btn_yes = QPushButton("&Да")
        btn_no = QPushButton("&Нет")
        dialog.addButton(btn_yes, QMessageBox.AcceptRole)
        dialog.addButton(btn_no, QMessageBox.RejectRole)
        dialog.setDefaultButton(btn_no)
        dialog.setEscapeButton(btn_no)
        result = dialog.exec()
        if result == 0:
            self.delete_id_list.append(int(func.get_dep_id_from_name(dep_name, self.dep_dict)))
            self._delete_dep_list(
                self.tree_view_model.itemFromIndex(self.ui.treeView.currentIndex()))
            MySQLConnection.verify_connection()
            connection = MySQLConnection.get_connection()
            for dep_id in self.delete_id_list:
                delete_sql = f"DELETE FROM departments WHERE dep_id = {dep_id};"

                update_sql = f"UPDATE workers_departments SET " \
                             f"WD_dep_id = -1 " \
                             f"WHERE WD_dep_id = '{int(dep_id)}';"
                MySQLConnection.execute_transaction_query(connection, delete_sql, update_sql)

            connection.close()
            self.delete_id_list.clear()
            self._create_tree_view_model()

    def _open_menu(self, position):

        menu = QMenu()

        action_add_dep = QAction()
        action_add_dep.setText("Добавить подчиненный отдел")
        dep_parent_id = func.get_dep_id_from_name(self.ui.treeView.currentIndex().data(), self.dep_dict)
        action_add_dep.triggered.connect(lambda: self._add_department(dep_parent_id))

        action_del_dep = QAction()
        action_del_dep.setText("Удалить отдел")
        action_del_dep.triggered.connect(self._delete_department)

        menu.addAction(action_add_dep)
        menu.addAction(action_del_dep)

        menu.exec_(self.ui.treeView.viewport().mapToGlobal(position))

    def _is_child(self, child_name, parent_name):
        is_child = False
        child_id = func.get_dep_id_from_name(child_name, self.dep_dict)
        parent_id = func.get_dep_id_from_name(parent_name, self.dep_dict)

        while child_id != "0" and not is_child:
            for dep_id in self.dep_dict:
                if dep_id == child_id:
                    if self.dep_dict[dep_id]['parent'] == parent_id:
                        is_child = True
                    else:
                        child_id = self.dep_dict[dep_id]['parent']
        return is_child

    def _save_department(self):
        if not self.ui.treeView.selectedIndexes():
            return
        dep_id = func.get_dep_id_from_name(self.ui.treeView.currentIndex().data(), self.dep_dict)
        boss_id = func.get_worker_id_from_fio(self.ui.comboBox_dep_boss.currentText(), self.worker_dict)
        boss_assistant_id = func.get_worker_id_from_fio(self.ui.comboBox_dep_boss_assistant.currentText(),
                                                        self.worker_dict)
        MySQLConnection.verify_connection()
        connection = MySQLConnection.get_connection()
        sql_update_deps = f"UPDATE departments SET " \
                          f"dep_name = '{self.ui.textEdit_dep_name.toPlainText()}', " \
                          f"dep_abbr = '{self.ui.lineEdit_dep_abbr.text()}', " \
                          f"dep_number = '{self.ui.lineEdit_dep_number.text()}', " \
                          f"dep_boss = {boss_id}, " \
                          f"dep_boss_assistant = {boss_assistant_id}, " \
                          f"dep_info = '{self.ui.textEdit_dep_info.toPlainText()}', " \
                          f"dep_boss_post = '{self.ui.lineEdit_boss_post.text()}', " \
                          f"dep_boss_assistant_post = '{self.ui.lineEdit_boss_assistant_post.text()}' " \
                          f"WHERE dep_id = {int(self.ui.lineEdit_dep_id.text())};"
        MySQLConnection.execute_query(connection, sql_update_deps)
        connection.close()
        QMessageBox.information(self, "Сохранено", "Информация сохранена")
        self._create_tree_view_model()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = DepartmentsWidget()
    window.show()
    sys.exit(app.exec_())
