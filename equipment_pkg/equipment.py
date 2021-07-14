import json
from json.decoder import JSONDecodeError

from PyQt5.QtCore import QRegExp, QThread, pyqtSignal, Qt, QStringListModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog, QDialog, QMessageBox, QProgressDialog, \
    QAbstractItemView, QPushButton

from equipment_pkg.ui_equipment import Ui_MainWindow
from functions_pkg.db_functions import MySQLConnection
from functions_pkg.send_get_request import GetRequest
import functions_pkg.functions as func

url_start = "https://fgis.gost.ru/fundmetrology/eapi"
status = ["СИ", "СИ в качестве эталона", "Эталон единицы величины"]


class SearchThread(QThread):
    msg_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.url = ""
        self.is_running = True

    def run(self):
        if self.is_running:
            self.sleep(1)
            print("thread running")
            print(self.url)
            resp = GetRequest.getRequest(self.url)
            print(resp)
            print("thread stopped")
            self.msg_signal.emit(resp)


class EquipmentWidget(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super(EquipmentWidget, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.search_thread = SearchThread()
        self._add_connects()

        self.eq_type = ""
        self.get_type = ""
        self.vri_numbers = list()

        self.mit_search = dict()
        self.mit = dict()

        self.vri_search = dict()
        self.vri = dict()

        self.mieta_search = dict()
        self.mieta = dict()

        self.vri_info_dict = dict()

        self.measure_codes_dict = func.get_measure_codes()['measure_codes_dict']
        # self.mis_dict = func.get_mis()['mis_dict']
        self.departments = func.get_departments()
        self.workers = func.get_workers()
        self.worker_deps = func.get_worker_deps()
        self.rooms = func.get_rooms()
        self.room_deps = func.get_room_deps()
        self.mi_deps = func.get_mi_deps()

        self.tbl_verif_model = QStandardItemModel(0, 5, parent=self)
        self.tbl_equip_model = QStandardItemModel(0, 5, parent=self)
        self.lv_dep_model = QStringListModel(parent=self)
        self.cb_worker_model = QStringListModel(parent=self)
        self.cb_room_model = QStringListModel(parent=self)

        self.ui.tableView_equip_list.setModel(self.tbl_equip_model)
        self.ui.tableView_verification_info.setModel(self.tbl_verif_model)
        self.ui.listView_departments.setModel(self.lv_dep_model)
        self.ui.comboBox_responsiblePerson.setModel(self.cb_worker_model)
        self.ui.comboBox_room.setModel(self.cb_room_model)

        self._add_measure_codes()
        self.ui.comboBox_status.addItems(status)

        self.org_name = func.get_organization_name()

        self._clear_all()
        self._update_equip_table()
        self._update_verification_table()

    def _add_measure_codes(self):
        code_names = list()
        for code in self.measure_codes_dict:
            code_names.append(f"{self.measure_codes_dict[code]['code']} {self.measure_codes_dict[code]['name']}")
        self.ui.comboBox_measure_code.addItems(sorted(code_names))

    def _add_connects(self):
        self.ui.toolButton_equip_add.clicked.connect(self._on_add_equip_arshin)
        self.ui.pushButton_equip_save.clicked.connect(self._on_save_equip)
        self.search_thread.msg_signal.connect(self._on_getting_resp, Qt.QueuedConnection)
        self.ui.tableView_equip_list.clicked.connect(self._update_info)
        self.ui.tableView_equip_list.activated.connect(self._update_info)
        self.ui.tableView_verification_info.clicked.connect(self._update_vri_info)
        self.ui.tableView_verification_info.activated.connect(self._update_vri_info)
        self.ui.pushButton_add_dep.clicked.connect(self._on_add_dep)
        self.ui.pushButton_remove_dep.clicked.connect(self._on_remove_dep)
        self.ui.pushButton_clear.clicked.connect(self._clear_all)
        self.ui.pushButton_delete_mi.clicked.connect(self._on_delete_mi)
        self.ui.comboBox_status.currentTextChanged.connect(self._on_status_changed)

    # -------------------------------------ИЗМЕНЕНИЕ СТАТУСА СИ (ЭТАЛОН, СИ...)-----------------------------------------

    def _on_status_changed(self, new_status):
        if new_status == "СИ":
            self.ui.groupBox_uve_info.hide()
            self.ui.groupBox_mieta_info.hide()
            # self.ui.tab_etalon.setDisabled(True)
        elif new_status == "СИ в качестве эталона":
            # self.ui.tab_etalon.setEnabled(True)
            self.ui.groupBox_uve_info.hide()
            self.ui.groupBox_mieta_info.show()
        elif new_status == "Эталон единицы величины":
            # self.ui.tab_etalon.setEnabled(True)
            self.ui.groupBox_mieta_info.hide()
            self.ui.groupBox_uve_info.show()

    # -------------------------------------КЛИК ПО КНОПКЕ "УДАЛИТЬ ОБОРУДОВАНИЕ"----------------------------------------

    def _on_delete_mi(self):
        mi_id = self.ui.lineEdit_equip_id.text()
        if mi_id:
            sql_delete_1 = f"DELETE FROM mis WHERE mi_id = {int(mi_id)}"
            sql_delete_2 = f"DELETE FROM mis_departments WHERE MD_mi_id = {int(mi_id)}"

            dialog = QMessageBox(self)
            dialog.setWindowTitle("Подтверждение удаления")
            dialog.setText(f"Вы действительно хотите удалить оборудование?\n"
                           f"Также удалится вся сопутствующая информация.")
            dialog.setIcon(QMessageBox.Question)
            btn_yes = QPushButton("&Да")
            btn_no = QPushButton("&Нет")
            dialog.addButton(btn_yes, QMessageBox.AcceptRole)
            dialog.addButton(btn_no, QMessageBox.RejectRole)
            dialog.setDefaultButton(btn_no)
            dialog.setEscapeButton(btn_no)
            result = dialog.exec()
            if result == 0:
                MySQLConnection.verify_connection()
                connection = MySQLConnection.create_connection()
                MySQLConnection.execute_transaction_query(connection, sql_delete_1, sql_delete_2)
                connection.close()

                self._update_equip_table()
                self._update_verification_table()
                self._clear_all()

    # -------------------------------------КЛИК ПО КНОПКЕ "ДОБАВИТЬ ОТДЕЛ"---------------------------------------------

    def _on_add_dep(self):
        dep_list = func.get_departments()['dep_name_list']
        cur_dep_list = self.lv_dep_model.stringList()
        choose_list = sorted(list(set(dep_list) - set(cur_dep_list)))
        if choose_list:
            dep_name, ok = QInputDialog.getItem(self, "Выбор отдела",
                                                "Выберите отдел, который использует данное оборудование",
                                                choose_list, current=0, editable=False)
            if ok and dep_name:
                cur_dep_list.append(dep_name)
                self.lv_dep_model.setStringList(sorted(cur_dep_list))
                dep_id = func.get_dep_id_from_name(dep_name, self.departments['dep_dict'])
                # добавляем сотрудников
                cur_worker_list = self.cb_worker_model.stringList()
                cur_worker_list += \
                    func.get_workers_list([dep_id], self.workers['worker_dict'], self.worker_deps['dep_workers_dict'])[
                        'workers']
                self.cb_worker_model.setStringList(sorted(set(cur_worker_list)))
                # добавляем помещения
                cur_room_list = self.cb_room_model.stringList()
                cur_room_list += \
                    func.get_rooms_list([dep_id], self.rooms['room_dict'], self.room_deps['dep_rooms_dict'])['rooms']
                self.cb_room_model.setStringList(sorted(set(cur_room_list)))
        else:
            QMessageBox.information(self, "Выбора нет", f"Все подразделения включены в список")

    # ----------------------------------КЛИК ПО КНОПКЕ "УДАЛИТЬ ОТДЕЛ"-------------------------------------------------

    def _on_remove_dep(self):
        if not self.ui.listView_departments.selectedIndexes():
            return
        dep_name = self.ui.listView_departments.currentIndex().data()
        cur_dep_list = self.lv_dep_model.stringList()
        cur_dep_list.remove(dep_name)
        self.lv_dep_model.setStringList(cur_dep_list)
        dep_list = list()
        for dep in cur_dep_list:
            dep_id = func.get_dep_id_from_name(dep, self.departments['dep_dict'])
            dep_list.append(dep_id)
        worker_list = func.get_workers_list(dep_list, self.workers['worker_dict'],
                                            self.worker_deps['dep_workers_dict'])['workers']
        room_list = func.get_rooms_list(dep_list, self.rooms['room_dict'], self.room_deps['dep_rooms_dict'])['rooms']
        self.cb_worker_model.setStringList(worker_list)
        self.cb_room_model.setStringList(room_list)

    def _update_info(self, index):
        self._clear_all()
        row = self.tbl_equip_model.itemFromIndex(index).row()
        card_number = self.tbl_equip_model.index(row, 0).data()
        mi_id = func.get_mis_id_from_card_number(card_number, self.mis_dict)
        self.ui.lineEdit_equip_id.setText(mi_id)
        self.ui.lineEdit_reg_card_number.setText(self.mis_dict[mi_id]['reg_card_number'])
        self.ui.comboBox_measure_code.setCurrentText(
            func.get_measure_code_name_from_id(self.mis_dict[mi_id]['measure_code'], self.measure_codes_dict))
        self.ui.comboBox_status.setCurrentText(self.mis_dict[mi_id]['status'])
        self.ui.lineEdit_reestr.setText(self.mis_dict[mi_id]['reestr'])
        self.ui.plainTextEdit_title.setPlainText(self.mis_dict[mi_id]['title'])
        self.ui.plainTextEdit_type.setPlainText(self.mis_dict[mi_id]['type'])
        self.ui.lineEdit_modification.setText(self.mis_dict[mi_id]['modification'])
        self.ui.lineEdit_number.setText(self.mis_dict[mi_id]['number'])
        self.ui.lineEdit_inv_number.setText(self.mis_dict[mi_id]['inv_number'])
        self.ui.plainTextEdit_manufacturer.setPlainText(self.mis_dict[mi_id]['manufacturer'])
        self.ui.lineEdit_manuf_year.setText(self.mis_dict[mi_id]['manuf_year'])
        self.ui.lineEdit_expl_year.setText(self.mis_dict[mi_id]['expl_year'])
        self.ui.lineEdit_diapazon.setText(self.mis_dict[mi_id]['diapazon'])
        self.ui.lineEdit_PG.setText(self.mis_dict[mi_id]['PG'])
        self.ui.lineEdit_KT.setText(self.mis_dict[mi_id]['KT'])
        self.ui.plainTextEdit_other_characteristics.setPlainText(self.mis_dict[mi_id]['other_characteristics'])
        self.ui.lineEdit_MPI.setText(self.mis_dict[mi_id]['MPI'])
        self.ui.plainTextEdit_purpose.setPlainText(self.mis_dict[mi_id]['purpose'])
        self.ui.comboBox_responsiblePerson.setCurrentText(
            func.get_worker_fio_from_id(self.mis_dict[mi_id]['responsible_person'], self.workers['worker_dict']))
        self.ui.plainTextEdit_personal.setPlainText(self.mis_dict[mi_id]['personal'])
        # self.ui.comboBox_room.setPlainText(func.get_room_number_from_id(self.mis_dict[mis_id]['room'], self.room_dict))
        self.ui.plainTextEdit_software_inner.setPlainText(self.mis_dict[mi_id]['software_inner'])
        self.ui.plainTextEdit_software_outer.setPlainText(self.mis_dict[mi_id]['software_outer'])
        self.ui.plainTextEdit_owner.setPlainText(self.mis_dict[mi_id]['owner'])
        self.ui.plainTextEdit_owner_contract.setPlainText(self.mis_dict[mi_id]['owner_contract'])

        if self.mis_dict[mi_id]['RE'] != "0":
            self.ui.checkBox_has_manual.setChecked(True)
        else:
            self.ui.checkBox_has_manual.setChecked(False)
        if self.mis_dict[mi_id]['pasport'] != "0":
            self.ui.checkBox_has_pasport.setChecked(True)
        else:
            self.ui.checkBox_has_pasport.setChecked(False)
        if self.mis_dict[mi_id]['MP'] != "0":
            self.ui.checkBox_has_verif_method.setChecked(True)
        else:
            self.ui.checkBox_has_verif_method.setChecked(False)
        self.ui.lineEdit_period_TO.setText(self.mis_dict[mi_id]['TO_period'])

        self._update_owner_info()

        self._update_verification_table()

    def _update_owner_info(self):
        self.mi_deps = func.get_mi_deps()
        mi_id = self.ui.lineEdit_equip_id.text()
        if mi_id:
            dep_name_list = list()
            if mi_id in self.mi_deps['mi_deps_dict']:
                for dep_id in self.mi_deps['mi_deps_dict'][mi_id]:
                    dep_name_list.append(func.get_dep_name_from_id(dep_id, self.departments['dep_dict']))
            self.lv_dep_model.setStringList(sorted(dep_name_list))

            dep_list = list()
            for dep in dep_name_list:
                dep_id = func.get_dep_id_from_name(dep, self.departments['dep_dict'])
                dep_list.append(dep_id)
            worker_list = func.get_workers_list(dep_list, self.workers['worker_dict'],
                                                self.worker_deps['dep_workers_dict'])['workers']
            room_list = func.get_rooms_list(dep_list, self.rooms['room_dict'], self.room_deps['dep_rooms_dict'])[
                'rooms']
            worker_list.insert(0, "")
            room_list.insert(0, "")
            self.cb_worker_model.setStringList(worker_list)
            self.cb_room_model.setStringList(room_list)

            self.ui.comboBox_responsiblePerson.setCurrentText(
                func.get_worker_fio_from_id(self.mis_dict[mi_id]['responsible_person'], self.workers['worker_dict']))

            self.ui.comboBox_room.setCurrentText(
                func.get_room_number_from_id(self.mis_dict[mi_id]['room'], self.rooms['room_dict']))

    def _on_getting_resp(self, resp):
        if not resp or resp.startswith("Error") or resp.startswith("<!DOCTYPE html>"):
            QMessageBox.critical(self, "Ошибка", f"Возникла ошибка получения сведений из ФГИС \"АРШИН\".\n{resp}")
            self.dialog.close()
            return
        else:
            try:
                self.resp_json = json.loads(resp)
            except JSONDecodeError as err:
                QMessageBox.critical(self, "Ошибка", f"Невозможно распознать ответ ФГИС \"АРШИН\".\n{resp}")
                self.dialog.close()
                return
            if self.resp_json:
                if self.get_type == "mieta_vri":
                    self.vri = self.resp_json
                    self._fill_vri_info()
                elif "mit" in self.search_thread.url:
                    self._get_mit()
                elif "vri" in self.search_thread.url:
                    self._get_vri()
                elif "mieta" in self.search_thread.url:
                    self._get_mieta()

                else:
                    self.dialog.close()

    def _input_verify(self, dialog):
        if not dialog.textValue():
            dialog.setLabelText("Введите один из номеров:\n"
                                "- номер в реестре;\n"
                                "- номер эталона единиц величин;\n"
                                "- номер в перечне СИ, применяемых в качестве эталона;\n"
                                "- номер свидетельства формата 2021 года.")
            return
        rx_mit = QRegExp("^[1-9][0-9]{0,5}-[0-9]{2}$")
        rx_npe = QRegExp("^гэт[1-9][0-9]{0,2}-(([0-9]{2})|([0-9]{4}))$")
        rx_uve = QRegExp("^[1-3]\.[0-9]\.\S{3}\.\d{4}\.20[0-4]\d$")
        rx_mieta = QRegExp("^[1-9]\d{0,5}\.\d{2}\.(0Р|1Р|2Р|3Р|4Р|5Р|РЭ|ВЭ|СИ)\.\d+$")
        rx_svid = QRegExp("^(С|И)\-\S{1,3}\/[0-3][0-9]\-[0-1][0-9]\-20[2-5][0-9]\/\d{8,10}$")
        rx_vri_id = QRegExp("^([1-2]\-)*\d{6,10}$")
        rx_mit.setCaseSensitivity(False)
        rx_npe.setCaseSensitivity(False)
        rx_uve.setCaseSensitivity(False)
        rx_mieta.setCaseSensitivity(False)
        rx_svid.setCaseSensitivity(False)
        rx_vri_id.setCaseSensitivity(False)
        if rx_mit.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер реестра СИ")
            self.eq_type = "mit"
            self.get_type = "mit"
        elif rx_npe.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Государственный первичный эталон")
        elif rx_uve.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер эталона единицы величины")
        elif rx_mieta.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер в перечне СИ, применяемых в качестве эталонов")
            self.eq_type = "mieta"
            self.get_type = "mieta"
        elif rx_svid.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер свидетельства о поверке")
            self.eq_type = "vri"
            self.get_type = "vri"
        elif rx_vri_id.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"ID свидетельства о поверке")
            self.eq_type = "vri_id"
            self.get_type = "vri_id"
        else:
            self.eq_type = ""
            self.get_type = ""
            dialog.setLabelText("Введенный номер не определяется. Проверьте правильность ввода")

    # СИ по номеру реестра
    def _get_mit(self):

        # получаем self.mit_search
        if "search" in self.search_thread.url \
                and 'result' in self.resp_json \
                and 'count' in self.resp_json['result']:

            # если ищем по номеру в реестре
            if self.eq_type == "mit":
                if self.resp_json['result']['count'] == 0:
                    self.dialog.close()
                    QMessageBox.critical(self, "Ошибка",
                                         f"Очевидно, вы пытались ввести номер реестра СИ, но ФГИС "
                                         f"\"АРШИН\" не содержит такой записи.\n"
                                         f"Перепроверьте правильность введенного номера")
                    return
                elif self.resp_json['result']['count'] == 1:
                    self.mit_search = self.resp_json
                    self._update_progressbar(50, "Поиск информации в реестре утвержденных типов СИ")
                    url = f"{url_start}/mit/{self.resp_json['result']['items'][0]['mit_id']}"
                    self.search_thread.url = url
                    self.search_thread.start()
                elif self.resp_json['result']['count'] < 50:
                    items_list = list()
                    for item in self.resp_json['result']['items']:
                        item_name_list = list()
                        if 'number' in item:
                            item_name_list.append(item['number'])
                        if 'title' in item:
                            item_name_list.append(item['title'])
                        if 'notation' in item:
                            item_name_list.append(item['notation'])
                        if 'manufactorer' in item:
                            item_name_list.append(item['manufactorer'])
                        item_name = " ".join(item_name_list)
                        if len(item_name) > 150:
                            items_list.append(f"{item_name[:150]}...")
                        else:
                            items_list.append(item_name)

                    s, ok = QInputDialog.getItem(self, "Выбор реестра", "Выберите необходимый реестр", items_list,
                                                 current=0, editable=False)
                    if ok and s:
                        self.mit_search = self.resp_json
                        self._update_progressbar(50, "Поиск информации в реестре утвержденных типов СИ")
                        url = f"{url_start}/mit/{self.resp_json['result']['items'][items_list.index(s)]['mit_id']}"
                        self.search_thread.url = url
                        self.search_thread.start()
                else:
                    QMessageBox.critical(self, "Ошибка", "Слишком много результатов поиска. Уточните номер")
                    # self._stop_search()
                    return

            # если ищем по номеру свидетельства

            elif self.eq_type == "vri" or self.eq_type == "mieta" or self.eq_type == "vri_id":
                if self.resp_json['result']['count'] == 0:
                    QMessageBox.critical(self, "Ошибка", f"Невозможно найти номер в реестре")
                else:
                    self.mit_search = self.resp_json
                    self._update_progressbar(85, "Поиск информации в реестре утвержденных типов СИ")
                    url = f"{url_start}/mit/{self.resp_json['result']['items'][0]['mit_id']}"
                    self.search_thread.url = url
                    self.search_thread.start()

        # получаем self.mit
        elif "mit/" in self.search_thread.url:
            self.mit = self.resp_json

            if self.eq_type == "mit":
                self._fill_mit()
                self._stop_search()

            elif self.eq_type == "vri" or self.eq_type == "mieta" or self.eq_type == "vri_id":
                self._fill_vri()
                self._fill_mit()
                self._fill_vri_info()
            # self._stop_search()

    # номер свидетельства
    def _get_vri(self):

        # получаем self.vri_search
        if "search" in self.search_thread.url and 'result' in self.resp_json and 'count' in self.resp_json[
            'result']:
            if self.resp_json['result']['count'] == 0:
                self.dialog.close()
                QMessageBox.critical(self, "Ошибка",
                                     f"Очевидно, вы пытались ввести номер свидетельства образца 2021 года, "
                                     f"но ФГИС \"АРШИН\" не содержит такой записи.\n"
                                     f"Перепроверьте раскладку клавиатуры и правильность введенного номера.\n"
                                     f"Напоминаем, что буквы должны вводиться в русской раскладке.\n"
                                     f"После внесения исправлений запустите поиск заново.")
                return
            elif self.resp_json['result']['count'] == 1:
                self.vri_search = self.resp_json
                self._update_progressbar(20, "Поиск информации о результатах поверки СИ")
                url = f"{url_start}/vri/{self.resp_json['result']['items'][0]['vri_id']}"
                self.search_thread.url = url
                self.search_thread.start()
            else:
                QMessageBox.critical(self, "Ошибка", "Слишком много результатов поиска. Уточните номер свидетельства")
                self.dialog.close()
                return

        # получаем self.vri
        elif "vri/" in self.search_thread.url:
            self.vri = self.resp_json
            mitypeNumber = ""
            mitypeTitle = ""
            if self.eq_type == "mieta":
                if 'result' in self.mieta:
                    if 'mitype_num' in self.mieta['result']:  # номер реестра
                        mitypeNumber = self.mieta['result']['mitype_num']
                    if 'mitype' in self.mieta['result']:  # наименование
                        mitypeTitle = self.mieta['result']['mitype']

                    if mitypeNumber and mitypeTitle:
                        self._update_progressbar(70, "Поиск номера в реестре утвержденных типов СИ")
                        url = f"{url_start}/mit?rows=100&search={mitypeNumber}%20{mitypeTitle.replace(' ', '%20')}"
                        self.search_thread.url = url
                        self.search_thread.start()

            else:
                if 'miInfo' in self.vri['result']:
                    if 'etaMI' in self.vri['result']['miInfo']:
                        miInfo = self.vri['result']['miInfo']['etaMI']
                        if self.eq_type == "vri" or self.eq_type == "vri_id":
                            if 'regNumber' in miInfo:
                                regNumber = miInfo['regNumber']
                                self._update_progressbar(40, "Поиск номера эталона")
                                url = f"{url_start}/mieta?rows=100&search={regNumber}"
                                self.search_thread.url = url
                                self.search_thread.start()
                    elif 'singleMI' in self.vri['result']['miInfo'] or self.eq_type == "mieta":
                        miInfo = self.vri['result']['miInfo']['singleMI']

                        if 'mitypeNumber' in miInfo:  # номер реестра
                            mitypeNumber = miInfo['mitypeNumber']
                        if 'mitypeTitle' in miInfo:  # наименование
                            mitypeTitle = miInfo['mitypeTitle']

                        if self.eq_type == "vri_id":
                            self.vri_numbers.append([f"1-{self.number}",
                                                     self.vri['result']['vriInfo']['organization']])
                        else:
                            self.vri_numbers.append([self.vri_search['result']['items'][0]['vri_id'],
                                                     self.vri_search['result']['items'][0]['org_title']])

                        if mitypeNumber and mitypeTitle:
                            self._update_progressbar(50, "Поиск номера в реестре утвержденных типов СИ")
                            url = f"{url_start}/mit?rows=100&search={mitypeNumber}%20{mitypeTitle.replace(' ', '%20')}"
                            self.search_thread.url = url
                            self.search_thread.start()
                        else:
                            self._fill_vri()
                            self._fill_vri_info()
                    elif 'partyMI' in self.vri['result']['miInfo']:
                        miInfo = self.vri['result']['miInfo']['partyMI']

    # СИ как эталон
    def _get_mieta(self):

        # получаем self.mieta_search
        if 'result' in self.resp_json and 'count' in self.resp_json['result']:
            if self.resp_json['result']['count'] == 0:
                self.dialog.close()
                QMessageBox.critical(self, "Ошибка",
                                     f"Очевидно, вы пытались ввести номер СИ, применяемого в качестве эталона, "
                                     f"но ФГИС \"АРШИН\" не содержит такой записи.\n"
                                     f"Перепроверьте раскладку клавиатуры и правильность введенного номера.")

            elif self.resp_json['result']['count'] == 1:
                self.mieta_search = self.resp_json
                if 'items' in self.resp_json['result'] and 'rmieta_id' in self.resp_json['result']['items'][0]:
                    mieta_id = self.resp_json['result']['items'][0]['rmieta_id']
                    if self.eq_type == "vri" or self.eq_type == "vri_id":
                        self._update_progressbar(50, "Поиск информации об эталоне")
                    else:
                        self._update_progressbar(25, "Поиск информации об эталоне")
                    url = f"{url_start}/mieta/{mieta_id}"
                    self.search_thread.url = url
                    self.search_thread.start()
            else:
                self.dialog.close()
                QMessageBox.critical(self, "Ошибка", "Слишком много результатов поиска. Уточните номер эталона")
                return

        # получаем self.mieta
        elif 'result' in self.resp_json and 'cresults' in self.resp_json['result']:
            self.mieta = self.resp_json
            result = self.resp_json['result']
            if 'number' in result:
                self.ui.lineEdit_mieta_number.setText(result['number'])
            if 'rankcode' in result:
                self.ui.comboBox_mieta_rank.setCurrentText(result['rankcode'])
            if 'rankclass' in result:
                self.ui.lineEdit_mieta_rank_title.setText(result['rankclass'])
            if 'npenumber' in result:
                self.ui.lineEdit_mieta_npenumber.setText(result['npenumber'])
            if 'schematype' in result:
                self.ui.lineEdit_mieta_schematype.setText(result['schematype'])
            if 'schematitle' in result:
                self.ui.plainTextEdit_mieta_schematitle.setPlainText(result['schematitle'])

            self.ui.comboBox_status.setCurrentText("СИ в качестве эталона")

            for cresult in result['cresults']:
                if 'vri_id' in cresult and 'org_title' in cresult:
                    self.vri_numbers.append([cresult['vri_id'], cresult['org_title']])

            if self.eq_type == "vri" or self.eq_type == "vri_id":
                if 'mitype_num' in result and 'mitype' in result:  # номер реестра
                    self._update_progressbar(75, "Поиск номера в реестре утвержденных типов СИ")
                    url = f"{url_start}/mit?rows=100&search={result['mitype_num']}%20{result['mitype'].replace(' ', '%20')}"
                    self.search_thread.url = url
                    self.search_thread.start()
                else:
                    self._fill_vri()
                    self._fill_vri_info()

            elif self.eq_type == "mieta":
                self._update_progressbar(50, "Поиск информации о результатах поверки СИ")
                url = f"{url_start}/vri/{self.vri_numbers[0][0]}"
                self.search_thread.url = url
                self.search_thread.start()

    # ______________________ЗАПОЛНЕНИЕ ИНФОРМАЦИИ С РЕЕСТРА__________________________
    def _fill_mit(self):
        if 'general' in self.mit:
            general = self.mit['general']
            # записываем номер реестра, наименование, тип
            if 'number' in general:
                self.ui.lineEdit_reestr.setText(general['number'])
            if 'title' in general:
                self.ui.plainTextEdit_title.setPlainText(general['title'])
            if 'notation' in general:
                self.ui.plainTextEdit_type.setPlainText(" ,".join(general['notation']))
        if 'manufacturer' in self.mit:
            manufacturer = self.mit['manufacturer']
            # записываем производителя
            manufacturer_list = list()
            if 'title' in manufacturer[0]:
                manufacturer_list.append(manufacturer[0]['title'])
            if 'country' in manufacturer[0]:
                manufacturer_list.append(manufacturer[0]['country'])
            if 'locality' in manufacturer[0]:
                manufacturer_list.append(manufacturer[0]['locality'])
            self.ui.plainTextEdit_manufacturer.setPlainText(", ".join(manufacturer_list))
        if 'mit' in self.mit:
            mit = self.mit['mit']
            if 'interval' in mit:
                for word in mit['interval'].split(" "):
                    if word.isdigit():
                        if "мес" in mit['interval']:
                            self.ui.lineEdit_MPI.setText(str(int(word)))
                        else:
                            self.ui.lineEdit_MPI.setText(str(int(word) * 12))

            if 'period' in mit and (mit['period'] == "Да" or mit['period'] == "да"):
                self.ui.radioButton_MPI_yes.setChecked(True)
            else:
                self.ui.radioButton_MPI_no.setChecked(True)
                self.ui.lineEdit_MPI.setText("")

    def _update_progressbar(self, val, text):
        if self.dialog.isActiveWindow():
            self.dialog.setLabelText(text)
            self.dialog.setValue(val)
        else:
            self.search_thread.is_running = False
            self._clear_all()

    # ______________ЗАПОЛНЕНИЕ ИНФОРМАЦИИ С НОМЕРА СВИДЕТЕЛЬСТВА_____________________
    def _fill_vri(self):

        if 'result' in self.vri:

            if 'miInfo' in self.vri['result']:
                miInfo = self.vri['result']['miInfo']
                if 'etaMI' in miInfo:
                    miInfo = miInfo['etaMI']
                elif 'singleMI' in miInfo:
                    miInfo = miInfo['singleMI']
                elif 'partyMI' in miInfo:
                    miInfo = miInfo['partyMI']

                if 'modification' in miInfo:  # модификация
                    self.ui.lineEdit_modification.setText(miInfo['modification'])
                if 'manufactureNum' in miInfo:  # заводской номер
                    self.ui.lineEdit_number.setText(miInfo['manufactureNum'])
                if 'inventoryNum' in miInfo:  # инвентарный номер
                    self.ui.lineEdit_inv_number.setText(miInfo['inventoryNum'])
                if 'manufactureYear' in miInfo:  # год выпуска
                    self.ui.lineEdit_manuf_year.setText(str(miInfo['manufactureYear']))

                # СИ НЕ В РЕЕСТРЕ
                mitypeNumber = ""
                if 'mitypeNumber' in miInfo:  # номер реестра
                    mitypeNumber = miInfo['mitypeNumber']
                if not mitypeNumber:
                    self.ui.plainTextEdit_title.setPlainText(miInfo['mitypeTitle'])
                    self.ui.plainTextEdit_type.setPlainText(miInfo['modification'])
                    self.ui.lineEdit_modification.setText(miInfo['modification'])
                    if 'vriInfo' in self.vri['result']:
                        vriInfo = self.vri['result']['vriInfo']
                        if 'vrfDate' in vriInfo and 'validDate' in vriInfo:
                            start_date = vriInfo['vrfDate']
                            end_date = vriInfo['validDate']
                            self.ui.lineEdit_MPI.setText(str((int(end_date[-4:]) - int(start_date[-4:])) * 12))
                            self.ui.radioButton_MPI_yes.setChecked(True)
                        self._stop_search()

    def _fill_vri_info(self):

        self.get_type = "mieta_vri"

        if 'result' in self.vri and 'vriInfo' in self.vri['result']:
            row = list()
            cert_num = ""
            organization = ""
            signCipher = ""
            miOwner = ""
            vrfDate = ""
            validDate = ""
            vriType = "2"
            docTitle = ""
            applicable = 1
            stickerNum = ""
            signPass = 0
            signMi = 0
            structure = ""
            briefIndicator = 0
            briefCharacteristics = ""
            ranges = ""
            values = ""
            channels = ""
            blocks = ""
            additional_info = ""

            # список поверок для таблицы: дата поверки, годен до или бессрочно, номер свид-ва, результат, поверитель
            vriInfo = self.vri['result']['vriInfo']
            row.append(QStandardItem(vriInfo['vrfDate']))
            if 'applicable' in vriInfo and 'certNum' in vriInfo['applicable']:
                if 'validDate' in vriInfo:
                    row.append(QStandardItem(vriInfo['validDate']))
                else:
                    row.append(QStandardItem("Бессрочно"))
                cert_num = vriInfo['applicable']['certNum']
                row.append(QStandardItem(cert_num))
                row.append(QStandardItem("ГОДЕН"))
            elif 'inapplicable' in vriInfo and 'noticeNum' in vriInfo['inapplicable']:
                row.append(QStandardItem("-"))
                cert_num = vriInfo['inapplicable']['noticeNum']
                row.append(QStandardItem(cert_num))
                row.append(QStandardItem("БРАК"))
            if 'organization' in vriInfo:
                row.append(QStandardItem(self.vri_numbers[0][1]))
            self.tbl_verif_model.appendRow(row)

            if 'organization' in vriInfo:
                organization = vriInfo['organization']
            if 'signCipher' in vriInfo:
                signCipher = vriInfo['signCipher']
            if 'miOwner' in vriInfo:
                miOwner = vriInfo['miOwner']
            if 'vrfDate' in vriInfo:
                vrfDate = vriInfo['vrfDate']
            if 'validDate' in vriInfo:
                validDate = vriInfo['validDate']
            if 'vriType' in vriInfo:
                vriType = vriInfo['vriType']
            if 'docTitle' in vriInfo:
                docTitle = vriInfo['docTitle']
            if 'applicable' in vriInfo:
                applicable = 1
                if 'stickerNum' in vriInfo['applicable']:
                    stickerNum = vriInfo['applicable']['stickerNum']
                if 'signPass' in vriInfo['applicable'] and vriInfo['applicable']['signPass']:
                    signPass = 1
                if 'signMi' in vriInfo['applicable'] and vriInfo['applicable']['signMi']:
                    signMi = 1
            if 'inapplicable' in vriInfo:
                applicable = 0

            if 'info' in self.vri['result']:
                info = self.vri['result']['info']
                if 'structure' in info:
                    structure = info['structure']
                if 'briefIndicator' in info and info['briefIndicator']:
                    briefIndicator = 1
                if 'briefCharacteristics' in info:
                    briefCharacteristics = info['briefCharacteristics']
                if 'ranges' in info:
                    ranges = info['ranges']
                if 'values' in info:
                    values = info['values']
                if 'channels' in info:
                    channels = info['channels']
                if 'blocks' in info:
                    blocks = info['blocks']
                if 'additional_info' in info:
                    additional_info = info['additional_info']

            if cert_num:
                self.vri_info_dict[cert_num] = {'organization': organization,
                                                'signCipher': signCipher,
                                                'miOwner': miOwner,
                                                'vrfDate': vrfDate,
                                                'validDate': validDate,
                                                'vriType': vriType,
                                                'docTitle': docTitle,
                                                'applicable': applicable,
                                                'stickerNum': stickerNum,
                                                'signPass': signPass,
                                                'signMi': signMi,
                                                'structure': structure,
                                                'briefIndicator': briefIndicator,
                                                'briefCharacteristics': briefCharacteristics,
                                                'ranges': ranges,
                                                'values': values,
                                                'channels': channels,
                                                'blocks': blocks,
                                                'additional_info': additional_info}
            print(self.vri_info_dict)
            self._update_vri_info(self.tbl_verif_model.item(0, 2).index())

            # ЕСЛИ ИЩЕМ ПО НОМЕРУ ЭТАЛОНА, ТО УДАЛЯЕМ ПЕРВУЮ ПОВЕРКУ И ИЩЕМ СЛЕДУЮЩУЮ
            if self.eq_type == "mieta":
                del self.vri_numbers[0]
                if len(self.vri_numbers) > 0:
                    self._update_progressbar(95, "Поиск информации о поверках")
                    url = f"{url_start}/vri/{self.vri_numbers[0][0]}"
                    self.search_thread.url = url
                    self.search_thread.start()
                    return
            else:
                # ЕСЛИ ИЩЕМ ПО НОМЕРУ СВИДЕТЕЛЬСТВА И ОДНА ПОВЕРКА, ОЧИЩАЕМ СПИСОК
                if len(self.vri_numbers) == 1:
                    self.vri_numbers.clear()
                # ЕСЛИ БОЛЬШЕ ОДНОЙ ПОВЕРКИ, ТО УДАЛЯЕМ ЗАПИСАННУЮ И ИЩЕМ СЛЕДУЮЩУЮ
                for vri in self.vri_numbers:
                    if self.vri_search['result']['items'][0]['vri_id'] in vri:
                        self.vri_numbers.remove(vri)
                if len(self.vri_numbers) > 0:
                    self._update_progressbar(95, "Поиск информации о поверках")
                    url = f"{url_start}/vri/{self.vri_numbers[0][0]}"
                    self.search_thread.url = url
                    self.search_thread.start()
                    return
            self._stop_search()

    def _update_vri_info(self, index):
        row = self.tbl_verif_model.itemFromIndex(index).row()
        cert_num = self.tbl_verif_model.index(row, 2).data()
        if cert_num in self.vri_info_dict:
            self.ui.plainTextEdit_vri_organization.setPlainText(self.vri_info_dict[cert_num]['organization'])
            self.ui.plainTextEdit_vri_miOwner.setPlainText(self.vri_info_dict[cert_num]['miOwner'])
            self.ui.lineEdit_vrfDate.setText(self.vri_info_dict[cert_num]['vrfDate'])
            self.ui.lineEdit_vri_validDate.setText(self.vri_info_dict[cert_num]['validDate'])
            if self.vri_info_dict[cert_num]['vriType'] == "2":
                self.ui.lineEdit_vri_vriType.setText("периодическая")
            elif self.vri_info_dict[cert_num]['vriType'] == "1":
                self.ui.lineEdit_vri_vriType.setText("первичная")
            self.ui.plainTextEdit_vri_docTitle.setPlainText(self.vri_info_dict[cert_num]['docTitle'])
            if self.vri_info_dict[cert_num]['applicable'] == 1:
                self.ui.groupBox_inapplicable.hide()
                self.ui.groupBox_applicable.show()
                self.ui.lineEdit_vri_certNum.setText(cert_num)
                self.ui.lineEdit_vri_signCipher.setText(self.vri_info_dict[cert_num]['signCipher'])
                self.ui.lineEdit_vri_stickerNum.setText(self.vri_info_dict[cert_num]['stickerNum'])
                self.ui.checkBox_vri_signPass.setChecked(self.vri_info_dict[cert_num]['signPass'])
                self.ui.checkBox_vri_signMi.setChecked(self.vri_info_dict[cert_num]['signMi'])
            else:
                self.ui.groupBox_applicable.hide()
                self.ui.groupBox_inapplicable.show()
                self.ui.lineEdit_vri_noticeNum.setText(cert_num)
            self.ui.plainTextEdit_vri_structure.setPlainText(self.vri_info_dict[cert_num]['structure'])
            self.ui.checkBox_vri_briefIndicator.setChecked(self.vri_info_dict[cert_num]['briefIndicator'])
            self.ui.plainTextEdit_vri_briefCharacteristics.setPlainText(self.vri_info_dict[cert_num]['briefCharacteristics'])
            self.ui.plainTextEdit_vri_ranges.setPlainText(self.vri_info_dict[cert_num]['ranges'])
            self.ui.plainTextEdit_vri_values.setPlainText(self.vri_info_dict[cert_num]['values'])
            self.ui.plainTextEdit_vri_channels.setPlainText(self.vri_info_dict[cert_num]['channels'])
            self.ui.plainTextEdit_vri_blocks.setPlainText(self.vri_info_dict[cert_num]['blocks'])
            self.ui.plainTextEdit_vri_additional_info.setPlainText(self.vri_info_dict[cert_num]['additional_info'])

    def _stop_search(self):
        self.dialog.setLabelText("Поиск завершен. Данные внесены в форму.")
        self.dialog.setValue(100)
        self.dialog.setCancelButtonText("Готово")
        self._update_verification_table()

    def _clear_all(self):

        # очищаем списки отделов, комнат и работников
        self.lv_dep_model.setStringList([])
        self.cb_worker_model.setStringList([])
        self.cb_room_model.setStringList([])


        self.mit_search.clear()
        self.mit.clear()
        self.vri_search.clear()
        self.vri.clear()
        self.mieta_search.clear()
        self.mieta.clear()
        self.vri_numbers.clear()

        self.ui.lineEdit_equip_id.setText("")
        self.ui.comboBox_status.setCurrentIndex(0)
        self.ui.comboBox_measure_code.setCurrentIndex(0)
        self.ui.lineEdit_reg_card_number.setText("")
        self.ui.lineEdit_reestr.setText("")
        self.ui.lineEdit_MPI.setText("12")
        self.ui.radioButton_MPI_yes.setChecked(True)
        self.ui.plainTextEdit_title.setPlainText("")
        self.ui.plainTextEdit_type.setPlainText("")
        self.ui.lineEdit_modification.setText("")
        self.ui.plainTextEdit_manufacturer.setPlainText("")
        self.ui.lineEdit_manuf_year.setText("")
        self.ui.lineEdit_expl_year.setText("")
        self.ui.lineEdit_number.setText("")
        self.ui.lineEdit_inv_number.setText("")
        self.ui.lineEdit_diapazon.setText("")
        self.ui.lineEdit_PG.setText("")
        self.ui.lineEdit_KT.setText("")
        self.ui.plainTextEdit_other_characteristics.setPlainText("")
        self.ui.plainTextEdit_software_inner.setPlainText("")
        self.ui.plainTextEdit_software_outer.setPlainText("")
        self.ui.lineEdit_period_TO.setText("")

        self.ui.plainTextEdit_purpose.setPlainText("")
        self.ui.plainTextEdit_personal.setPlainText("")
        self.ui.plainTextEdit_owner.setPlainText("")
        self.ui.plainTextEdit_owner_contract.setPlainText("")
        self.ui.checkBox_has_manual.setChecked(False)
        self.ui.checkBox_has_verif_method.setChecked(False)
        self.ui.checkBox_has_pasport.setChecked(False)

        # ---------------------------------ОЧИСТКА ИНФОРМАЦИИ О ПОВЕРКАХ------------------------------------------------
        self.tbl_verif_model.clear()
        self.ui.plainTextEdit_vri_organization.setPlainText("")
        self.ui.plainTextEdit_vri_miOwner.setPlainText("")
        self.ui.lineEdit_vrfDate.setText("")
        self.ui.lineEdit_vri_validDate.setText("")
        self.ui.lineEdit_vri_vriType.setText("")
        self.ui.plainTextEdit_vri_docTitle.setPlainText("")
        self.ui.groupBox_inapplicable.show()
        self.ui.groupBox_applicable.show()
        self.ui.lineEdit_vri_certNum.setText("")
        self.ui.lineEdit_vri_signCipher.setText("")
        self.ui.lineEdit_vri_stickerNum.setText("")
        self.ui.checkBox_vri_signPass.setChecked(False)
        self.ui.checkBox_vri_signMi.setChecked(False)
        self.ui.lineEdit_vri_noticeNum.setText("")
        self.ui.plainTextEdit_vri_structure.setPlainText("")
        self.ui.checkBox_vri_briefIndicator.setChecked(False)
        self.ui.plainTextEdit_vri_briefCharacteristics.setPlainText("")
        self.ui.plainTextEdit_vri_ranges.setPlainText("")
        self.ui.plainTextEdit_vri_values.setPlainText("")
        self.ui.plainTextEdit_vri_channels.setPlainText("")
        self.ui.plainTextEdit_vri_blocks.setPlainText("")
        self.ui.plainTextEdit_vri_additional_info.setPlainText("")

        # ---------------------------------ОЧИСТКА ИНФОРМАЦИИ ОБ ЭТАЛОНАХ---------------------------------------------
        self.ui.lineEdit_mieta_number.setText("")
        self.ui.lineEdit_mieta_rank_title.setText("")
        self.ui.lineEdit_mieta_npenumber.setText("")
        self.ui.lineEdit_mieta_schematype.setText("")
        self.ui.plainTextEdit_mieta_schematitle.setPlainText("")
        self.ui.comboBox_mieta_rank.setCurrentIndex(0)

    def _update_equip_table(self):
        self.tbl_equip_model.clear()
        self.mis_dict = func.get_mis()['mis_dict']

        self.tbl_equip_model.setHorizontalHeaderLabels(
            ["Номер карточки", "Код измерений", "Наименование", "Тип", "Заводской номер"])
        self.ui.tableView_equip_list.setColumnWidth(0, 110)
        self.ui.tableView_equip_list.setColumnWidth(1, 100)
        self.ui.tableView_equip_list.setColumnWidth(2, 200)
        self.ui.tableView_equip_list.setColumnWidth(3, 100)
        self.ui.tableView_equip_list.setColumnWidth(4, 110)
        for mi_id in self.mis_dict:
            row = []
            row.append(QStandardItem(self.mis_dict[mi_id]['reg_card_number']))
            row.append(QStandardItem(
                func.get_measure_code_from_id(self.mis_dict[mi_id]['measure_code'], self.measure_codes_dict)))
            row.append(QStandardItem(self.mis_dict[mi_id]['title']))
            row.append(QStandardItem(self.mis_dict[mi_id]['modification']))
            row.append(QStandardItem(self.mis_dict[mi_id]['number']))
            self.tbl_equip_model.appendRow(row)
        self.ui.tableView_equip_list.resizeRowsToContents()
        self._clear_all()

    def _update_verification_table(self):
        # self.tbl_verif_model.clear()
        self.tbl_verif_model.setHorizontalHeaderLabels(
            ["Дата поверки", "Годен до", "Номер свидетельства", "Результат", "Организация-поверитель"])
        self.ui.tableView_verification_info.setColumnWidth(0, 85)
        self.ui.tableView_verification_info.setColumnWidth(1, 65)
        self.ui.tableView_verification_info.setColumnWidth(2, 170)
        self.ui.tableView_verification_info.setColumnWidth(3, 70)
        self.ui.tableView_verification_info.setColumnWidth(4, 280)
        self.ui.tableView_verification_info.resizeRowsToContents()

    def _on_save_equip(self):

        # ЕСЛИ ПОЛЕ ID НЕ ЗАПОЛНЕНО, ТО NULL

        if not self.ui.lineEdit_reg_card_number.text():
            QMessageBox.warning(self, "Ошибка сохранения", "Необходимо ввести номер регистрационной карточки")
            return

        mi_id = self.ui.lineEdit_equip_id.text()
        if not mi_id:
            mi_id = "NULL"

        measure_code_id = func.get_measure_code_id_from_name(self.ui.comboBox_measure_code.currentText(),
                                                             self.measure_codes_dict)
        resp_person_id = func.get_worker_id_from_fio(self.ui.comboBox_responsiblePerson.currentText(),
                                                     self.workers['worker_dict'])

        room_id = func.get_room_id_from_number(self.ui.comboBox_room.currentText(), self.rooms['room_dict'])

        card_number = self.ui.lineEdit_reg_card_number.text()

        sql_replace = f"REPLACE INTO mis VALUES (" \
                      f"{mi_id}, " \
                      f"'{self.ui.lineEdit_reg_card_number.text()}', " \
                      f"{int(measure_code_id)}, " \
                      f"'{self.ui.comboBox_status.currentText()}', " \
                      f"'{self.ui.lineEdit_reestr.text()}', " \
                      f"'{self.ui.plainTextEdit_title.toPlainText()}', " \
                      f"'{self.ui.plainTextEdit_type.toPlainText()}', " \
                      f"'{self.ui.lineEdit_modification.text()}', " \
                      f"'{self.ui.lineEdit_number.text()}', " \
                      f"'{self.ui.lineEdit_inv_number.text()}', " \
                      f"'{self.ui.plainTextEdit_manufacturer.toPlainText()}', " \
                      f"'{self.ui.lineEdit_manuf_year.text()}', " \
                      f"'{self.ui.lineEdit_expl_year.text()}', " \
                      f"'{self.ui.lineEdit_diapazon.text()}', " \
                      f"'{self.ui.lineEdit_PG.text()}', " \
                      f"'{self.ui.lineEdit_KT.text()}', " \
                      f"'{self.ui.plainTextEdit_other_characteristics.toPlainText()}', " \
                      f"'{self.ui.lineEdit_MPI.text()}', " \
                      f"'{self.ui.plainTextEdit_purpose.toPlainText()}', " \
                      f"{int(resp_person_id)}, " \
                      f"'{self.ui.plainTextEdit_personal.toPlainText()}', " \
                      f"{int(room_id)}, " \
                      f"'{self.ui.plainTextEdit_software_inner.toPlainText()}', " \
                      f"'{self.ui.plainTextEdit_software_outer.toPlainText()}', " \
                      f"{int(self.ui.checkBox_has_manual.checkState())}, " \
                      f"{int(self.ui.checkBox_has_pasport.checkState())}, " \
                      f"{int(self.ui.checkBox_has_verif_method.checkState())}, " \
                      f"'{self.ui.lineEdit_period_TO.text()}', " \
                      f"'{self.ui.plainTextEdit_owner.toPlainText()}', " \
                      f"'{self.ui.plainTextEdit_owner_contract.toPlainText()}');"

        MySQLConnection.verify_connection()
        connection = MySQLConnection.create_connection()
        result = MySQLConnection.execute_query(connection, sql_replace)

        if result[0]:
            mi_id = str(result[1])
        else:
            connection.close()
            return

        sql_replace = f"REPLACE INTO mis_vri_info VALUES (" \
                      f"{mi_id}, " \
                      f"'{self.ui.lineEdit_reg_card_number.text()}', " \
                      f"{int(measure_code_id)}, " \
                      f"'{self.ui.comboBox_status.currentText()}', " \
                      f"'{self.ui.lineEdit_reestr.text()}', " \
                      f"'{self.ui.plainTextEdit_title.toPlainText()}', " \
                      f"'{self.ui.plainTextEdit_type.toPlainText()}', " \
                      f"'{self.ui.lineEdit_modification.text()}', " \
                      f"'{self.ui.lineEdit_number.text()}', " \
                      f"'{self.ui.lineEdit_inv_number.text()}', " \
                      f"'{self.ui.plainTextEdit_manufacturer.toPlainText()}', " \
                      f"'{self.ui.lineEdit_manuf_year.text()}', " \
                      f"'{self.ui.lineEdit_expl_year.text()}', " \
                      f"'{self.ui.lineEdit_diapazon.text()}', " \
                      f"'{self.ui.lineEdit_PG.text()}', " \
                      f"'{self.ui.lineEdit_KT.text()}', " \
                      f"'{self.ui.plainTextEdit_other_characteristics.toPlainText()}', " \
                      f"'{self.ui.lineEdit_MPI.text()}', " \
                      f"'{self.ui.plainTextEdit_purpose.toPlainText()}', " \
                      f"{int(resp_person_id)}, " \
                      f"'{self.ui.plainTextEdit_personal.toPlainText()}', " \
                      f"{int(room_id)}, " \
                      f"'{self.ui.plainTextEdit_software_inner.toPlainText()}', " \
                      f"'{self.ui.plainTextEdit_software_outer.toPlainText()}', " \
                      f"{int(self.ui.checkBox_has_manual.checkState())}, " \
                      f"{int(self.ui.checkBox_has_pasport.checkState())}, " \
                      f"{int(self.ui.checkBox_has_verif_method.checkState())}, " \
                      f"'{self.ui.lineEdit_period_TO.text()}', " \
                      f"'{self.ui.plainTextEdit_owner.toPlainText()}', " \
                      f"'{self.ui.plainTextEdit_owner_contract.toPlainText()}');"

        old_deps = set()
        if mi_id in self.mi_deps['mi_deps_dict']:
            old_deps = set(self.mi_deps['mi_deps_dict'][mi_id])

        new_deps = set()
        for dep in self.lv_dep_model.stringList():
            dep_id = func.get_dep_id_from_name(dep, self.departments['dep_dict'])
            new_deps.add(dep_id)

        insert_list = new_deps - old_deps
        if insert_list:
            sql_insert = f"INSERT IGNORE INTO mis_departments VALUES ({mi_id}, " \
                         f"{f'), ({mi_id}, '.join(insert_list)});"
        else:
            sql_insert = None

        delete_list = old_deps - new_deps
        if delete_list:
            sql_delete = f"DELETE FROM mis_departments WHERE (MD_mi_id = {mi_id} AND MD_dep_id IN ({' ,'.join(delete_list)}));"
        else:
            sql_delete = None
        MySQLConnection.execute_transaction_query(connection, sql_insert, sql_delete)
        connection.close()

        self._update_equip_table()
        self._update_info(self.tbl_equip_model.indexFromItem(self.tbl_equip_model.findItems(card_number, column=0)[0]))

        self.ui.tableView_equip_list.setCurrentIndex(
            self.tbl_equip_model.indexFromItem(self.tbl_equip_model.findItems(card_number, column=0)[0]))

        self.ui.tableView_equip_list.scrollTo(self.ui.tableView_equip_list.currentIndex())

        QMessageBox.information(self, "Сохранено", "Информация сохранена")

    def _on_add_equip_arshin(self):
        self._clear_all()

        dialog = QInputDialog(self)
        dialog.setInputMode(QInputDialog.TextInput)
        dialog.setWindowTitle("Поиск эталона в ФГИС \"Аршин\"")
        dialog.setLabelText("Введите один из номеров:\n"
                            "- номер в реестре;\n"
                            "- номер эталона единиц величин;\n"
                            "- номер в перечне СИ, применяемых в качестве эталона;\n"
                            "- номер свидетельства формата 2021 года;\n"
                            "- id поверки.")
        dialog.textValueChanged.connect(lambda: self._input_verify(dialog))
        result = dialog.exec()
        if result == QDialog.Accepted:
            self.number = dialog.textValue()
            if self.eq_type == "":
                QMessageBox.warning(self, "Предупреждение", "Введите корректный номер")
                return

            self.dialog = QProgressDialog(self)
            self.dialog.setAutoClose(False)
            self.dialog.setAutoReset(False)
            self.dialog.setWindowTitle("Поиск информации в ФГИС \"Аршин\"")
            self.dialog.setCancelButtonText("Прервать")
            self.dialog.canceled.connect(lambda: print("hey"))
            self.dialog.setRange(0, 100)
            self.dialog.setWindowModality(Qt.WindowModal)
            if self.eq_type == "mit":
                self._update_progressbar(0, "Поиск номера реестра")
            elif self.eq_type == "vri":
                self._update_progressbar(0, "Поиск номера свидетельства")
            elif self.eq_type == "mieta":
                self._update_progressbar(0, "Поиск номера в перечне СИ, применяемых в качестве эталонов")
            elif self.eq_type == "vri_id":
                self._update_progressbar(0, "Получение данных из свидетельства")

            self.dialog.resize(350, 100)
            self.dialog.show()

            self.search_thread.is_running = True

            self.ui.plainTextEdit_owner.setPlainText(self.org_name)

            if self.eq_type == "vri_id":
                if "-" in self.number:
                    url = f"{url_start}/vri/{self.number}"
                else:
                    url = f"{url_start}/vri/1-{self.number}"
                self.search_thread.url = url
                self.search_thread.start()
            else:
                url = f"{url_start}/{self.eq_type}?rows=100&search={self.number}"
                self.search_thread.url = url
                self.search_thread.start()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = EquipmentWidget()

    window.showMaximized()
    sys.exit(app.exec_())
