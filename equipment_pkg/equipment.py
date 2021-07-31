import json
from json.decoder import JSONDecodeError

from PyQt5.QtCore import QRegExp, QThread, pyqtSignal, Qt, QStringListModel, QEvent, QDate, QSortFilterProxyModel, \
    QItemSelectionModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QCloseEvent
from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog, QDialog, QMessageBox, QProgressDialog, \
    QAbstractItemView, QPushButton
from functions_pkg.send_get_request import GetRequest
from equipment_pkg.ui_equipment import Ui_MainWindow
from functions_pkg.db_functions import MySQLConnection
import functions_pkg.functions as func

STATUS_LIST = ["СИ", "СИ в качестве эталона", "Эталон единицы величины"]
URL_START = "https://fgis.gost.ru/fundmetrology/eapi"
ORG_NAME = func.get_organization_name()


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
        else:
            self.msg_signal.emit("stop")


class EquipmentWidget(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super(EquipmentWidget, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.search_thread = SearchThread()

        self._add_connects()
        # self._create_dicts()

        self.departments = func.get_departments()
        self.workers = func.get_workers()
        self.worker_deps = func.get_worker_deps()
        self.rooms = func.get_rooms()
        self.room_deps = func.get_room_deps()

        self.mietas_dict = func.get_mietas()['mietas_dict']

        self.measure_codes_dict = dict()
        self.mis_dict = dict()
        self.mi_deps = dict()
        self.mis_vri_dict = dict()
        self.temp_vri_dict = dict()

        self.mit_search = dict()
        self.mit = dict()

        self.vri_search = dict()
        self.vri = dict()
        self.vri_numbers = list()

        self.mieta_search = dict()
        self.mieta = dict()

        self.tbl_vri_model = QStandardItemModel(0, 7, parent=self)
        self.tbl_mi_model = QStandardItemModel(0, 6, parent=self)
        self.lv_dep_model = QStringListModel(parent=self)
        self.cb_worker_model = QStringListModel(parent=self)
        self.cb_room_model = QStringListModel(parent=self)

        self.tbl_vri_proxy_model = CustomSortingModel()
        self.tbl_vri_proxy_model.setSourceModel(self.tbl_vri_model)

        self.ui.tableView_mi_list.setModel(self.tbl_mi_model)
        self.ui.tableView_vri_list.setModel(self.tbl_vri_proxy_model)
        self.ui.listView_departments.setModel(self.lv_dep_model)
        self.ui.comboBox_responsiblePerson.setModel(self.cb_worker_model)
        self.ui.comboBox_room.setModel(self.cb_room_model)

        self._add_measure_codes()
        self.ui.comboBox_status.addItems(STATUS_LIST)

        self._clear_all()
        self._update_mi_table()
        self._update_vri_table()

        self.ui.tabWidget.setCurrentIndex(0)

    def _add_measure_codes(self):
        self.measure_codes_dict = func.get_measure_codes()['measure_codes_dict']
        code_names = list()
        for code in self.measure_codes_dict:
            code_names.append(f"{self.measure_codes_dict[code]['code']} {self.measure_codes_dict[code]['name']}")
        self.ui.comboBox_measure_code.addItems(sorted(code_names))

    def _add_connects(self):
        self.ui.toolButton_equip_add.clicked.connect(self._on_start_search)
        self.search_thread.msg_signal.connect(self._on_getting_resp, Qt.QueuedConnection)
        self.ui.pushButton_equip_save.clicked.connect(self._on_save_all)
        self.ui.tableView_mi_list.clicked.connect(self._update_mi_tab)
        self.ui.tableView_mi_list.activated.connect(self._update_mi_tab)
        self.ui.tableView_vri_list.clicked.connect(self._on_vri_select)
        self.ui.tableView_vri_list.activated.connect(self._on_vri_select)
        self.ui.pushButton_save_vri.clicked.connect(self._on_save_vri)
        self.ui.pushButton_save_mieta.clicked.connect(self._on_save_mieta)
        self.ui.pushButton_add_vri.clicked.connect(self._test)
        self.ui.pushButton_clear_vri.clicked.connect(self._clear_vri_tab)
        self.ui.pushButton_add_dep.clicked.connect(self._on_add_dep)
        self.ui.pushButton_remove_dep.clicked.connect(self._on_remove_dep)
        self.ui.pushButton_clear.clicked.connect(self._clear_all)
        self.ui.pushButton_delete_mi.clicked.connect(self._on_delete_mi)
        self.ui.comboBox_status.currentTextChanged.connect(self._on_status_changed)
        self.ui.radioButton_applicable.toggled.connect(self._on_applicable_toggle)
        self.ui.tabWidget.currentChanged.connect(self._on_tab_changed)

    # -----------------------------------ВИДИМОСТЬ КНОПОК ПРИ ПЕРЕКЛЮЧЕНИИ ВКЛАДОК-------------------------------------
    def _on_tab_changed(self, tab_index):
        self.ui.frame_vri_buttons.hide()
        self.ui.frame_mieta_buttons.hide()
        if tab_index == 2:
            self.ui.frame_vri_buttons.show()
        elif tab_index == 1:
            self.ui.frame_mieta_buttons.show()

    def _test(self):
        for i in range(0, self.tbl_mi_model.rowCount()):
            print(self.tbl_mi_model.index(i, 2).data())

    # -------------------------------------ВИДИМОСТЬ БРАК/ГОДЕН ПРИ ПЕРЕКЛЮЧЕНИИ---------------------------------------
    def _on_applicable_toggle(self, choisen):
        if choisen:
            self.ui.groupBox_applicable.show()
            self.ui.groupBox_inapplicable.hide()
        else:
            self.ui.groupBox_applicable.hide()
            self.ui.groupBox_inapplicable.show()

    # --------------------------------------ИЗМЕНЕНИЕ СТАТУСА СИ (ЭТАЛОН, СИ...)---------------------------------------
    def _on_status_changed(self, new_status):
        self.ui.tabWidget.setTabEnabled(1, False)
        self.ui.groupBox_mieta_info.hide()
        self.ui.groupBox_uve_info.hide()
        if new_status == "СИ в качестве эталона":
            self.ui.tabWidget.setTabEnabled(1, True)
            self.ui.groupBox_mieta_info.show()
        elif new_status == "Эталон единицы величины":
            self.ui.tabWidget.setTabEnabled(1, True)
            self.ui.groupBox_uve_info.show()

    # ------------------------------------ОБНОВЛЕНИЕ ТАБЛИЦЫ ОБОРУДОВАНИЯ----------------------------------------------
    def _update_mi_table(self):
        self.tbl_mi_model.clear()
        self.mis_dict = func.get_mis()['mis_dict']
        self.mi_deps = func.get_mi_deps()['mi_deps_dict']

        self.tbl_mi_model.setHorizontalHeaderLabels(
            ["Номер карточки", "Код измерений", "Наименование", "Тип", "Заводской номер", "id"])
        self.ui.tableView_mi_list.setColumnWidth(0, 110)
        self.ui.tableView_mi_list.setColumnWidth(1, 100)
        self.ui.tableView_mi_list.setColumnWidth(2, 200)
        self.ui.tableView_mi_list.setColumnWidth(3, 100)
        self.ui.tableView_mi_list.setColumnWidth(4, 110)
        self.ui.tableView_mi_list.setColumnWidth(5, 0)
        for mi_id in self.mis_dict:
            row = []
            row.append(QStandardItem(self.mis_dict[mi_id]['reg_card_number']))
            row.append(QStandardItem(
                func.get_measure_code_from_id(self.mis_dict[mi_id]['measure_code'], self.measure_codes_dict)))
            row.append(QStandardItem(self.mis_dict[mi_id]['title']))
            row.append(QStandardItem(self.mis_dict[mi_id]['modification']))
            row.append(QStandardItem(self.mis_dict[mi_id]['number']))
            row.append(QStandardItem(mi_id))
            self.tbl_mi_model.appendRow(row)
        self.ui.tableView_mi_list.resizeRowsToContents()
        self.ui.tableView_mi_list.selectionModel().clearSelection()
        self._clear_all()

    # -----------------------------------------ОБНОВЛЕНИЕ ТАБЛИЦЫ ПОВЕРОК----------------------------------------------
    def _update_vri_table(self):
        self.mis_vri_dict = func.get_mis_vri_info()['mis_vri_dict']
        mi_id = self.ui.lineEdit_equip_id.text()
        if mi_id and mi_id in self.mis_vri_dict:
            self.tbl_vri_model.clear()
            for vri_id in self.mis_vri_dict[mi_id]:
                row = list()
                row.append(QStandardItem(self.mis_vri_dict[mi_id][vri_id]['vrfDate']))
                if self.mis_vri_dict[mi_id][vri_id]['applicable'] == "1":
                    if self.mis_vri_dict[mi_id][vri_id]['validDate']:
                        row.append(QStandardItem(self.mis_vri_dict[mi_id][vri_id]['validDate']))
                    else:
                        row.append(QStandardItem("Бессрочно"))
                    row.append(QStandardItem(self.mis_vri_dict[mi_id][vri_id]['certNum']))
                    row.append(QStandardItem("ГОДЕН"))
                else:
                    row.append(QStandardItem("-"))
                    row.append(QStandardItem(self.mis_vri_dict[mi_id][vri_id]['certNum']))
                    row.append(QStandardItem("БРАК"))

                row.append(QStandardItem(self.mis_vri_dict[mi_id][vri_id]['organization']))

                if vri_id in self.mietas_dict:
                    rankTitle = self.mietas_dict[vri_id]['rankclass']
                    schemaTitle = self.mietas_dict[vri_id]['schematitle']
                    schematype = self.mietas_dict[vri_id]['schematype']
                    regNumber = self.mietas_dict[vri_id]['number']
                    if rankTitle and schemaTitle and regNumber and schematype:
                        row.append(QStandardItem(f"{regNumber}: {rankTitle.lower()}\n{schematype}: {schemaTitle}"))
                    elif rankTitle and schemaTitle and regNumber:
                        row.append(QStandardItem(f"{regNumber}: {rankTitle.lower()}\n{schemaTitle}"))
                else:
                    row.append(QStandardItem("-"))
                row.append(QStandardItem(vri_id))
                self.tbl_vri_model.appendRow(row)

        self.tbl_vri_model.setHorizontalHeaderLabels(
            ["Дата поверки", "Годен до", "Номер свидетельства", "Результат", "Организация-поверитель", "Эталон", "id"])
        self.ui.tableView_vri_list.setColumnWidth(0, 85)
        self.ui.tableView_vri_list.setColumnWidth(1, 65)
        self.ui.tableView_vri_list.setColumnWidth(2, 180)
        self.ui.tableView_vri_list.setColumnWidth(3, 70)
        self.ui.tableView_vri_list.setColumnWidth(4, 210)
        self.ui.tableView_vri_list.setColumnWidth(5, 280)
        self.ui.tableView_vri_list.setColumnWidth(6, 0)
        self.ui.tableView_vri_list.resizeRowsToContents()
        self.ui.tableView_vri_list.sortByColumn(0, Qt.DescendingOrder)

    # ---------------------------------------ОБНОВЛЕНИЕ ВКЛАДКИ ОБ ОБОРУДОВАНИИ----------------------------------------
    def _update_mi_tab(self, index):
        self._clear_all()
        row = index.row()
        mi_id = self.tbl_mi_model.index(row, 5).data()

        if not mi_id or mi_id not in self.mis_dict:
            return

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
        self.ui.plainTextEdit_personal.setPlainText(self.mis_dict[mi_id]['personal'])
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
        self._update_vri_table()

        if self.tbl_vri_model.rowCount() > 0:
            self.ui.tableView_vri_list.selectionModel().setCurrentIndex(self.tbl_vri_model.item(0, 2).index(),
                                                                        QItemSelectionModel.SelectCurrent)
            self._on_vri_select(self.tbl_vri_model.item(0, 2).index())

    # ---------------------------------------ОБНОВЛЕНИЕ ВКЛАДКИ О ПОВЕРКЕ----------------------------------------------
    def _update_vri_tab(self, vri_dict):
        self.ui.plainTextEdit_vri_organization.setPlainText(vri_dict['organization'])
        self.ui.lineEdit_vri_signCipher.setText(vri_dict['signCipher'])
        self.ui.plainTextEdit_vri_miOwner.setPlainText(vri_dict['miOwner'])
        self.ui.lineEdit_vrfDate.setText(vri_dict['vrfDate'])
        self.ui.lineEdit_vri_validDate.setText(vri_dict['validDate'])
        self.ui.lineEdit_vri_vriType.setText(vri_dict['vriType'])
        self.ui.plainTextEdit_vri_docTitle.setPlainText(vri_dict['docTitle'])
        if int(vri_dict['applicable']):
            self.ui.radioButton_applicable.setChecked(True)
            self.ui.lineEdit_vri_certNum.setText(vri_dict['certNum'])
            self.ui.lineEdit_vri_stickerNum.setText(vri_dict['stickerNum'])
            self.ui.checkBox_vri_signPass.setChecked(int(vri_dict['signPass']))
            self.ui.checkBox_vri_signMi.setChecked(int(vri_dict['signMi']))
        else:
            self.ui.radioButton_inapplicable.setChecked(True)
            self.ui.lineEdit_vri_noticeNum.setText(vri_dict['certNum'])
        self.ui.plainTextEdit_vri_structure.setPlainText(vri_dict['structure'])
        self.ui.checkBox_vri_briefIndicator.setChecked(int(vri_dict['briefIndicator']))
        self.ui.plainTextEdit_vri_briefCharacteristics.setPlainText(
            vri_dict['briefCharacteristics'])
        self.ui.plainTextEdit_vri_ranges.setPlainText(vri_dict['ranges'])
        self.ui.plainTextEdit_vri_values.setPlainText(vri_dict['values'])
        self.ui.plainTextEdit_vri_channels.setPlainText(vri_dict['channels'])
        self.ui.plainTextEdit_vri_blocks.setPlainText(vri_dict['blocks'])
        self.ui.plainTextEdit_vri_additional_info.setPlainText(vri_dict['additional_info'])

    # ----------------------------------ОБНОВЛЕНИЕ ВКЛАДКИ ОБ ЭТАЛОНЕ--------------------------------------------------
    def _update_mieta_tab(self, row):
        self._clear_mieta_tab()
        vri_id = self.tbl_vri_model.index(row, 6).data()
        if vri_id and vri_id in self.mietas_dict:
            self.ui.lineEdit_mieta_id.setText(self.mietas_dict[vri_id]['mieta_id'])
            self.ui.lineEdit_mieta_number.setText(self.mietas_dict[vri_id]['number'])
            self.ui.comboBox_mieta_rank.setCurrentText(self.mietas_dict[vri_id]['rankcode'])
            self.ui.lineEdit_mieta_rank_title.setText(self.mietas_dict[vri_id]['rankclass'])
            self.ui.lineEdit_mieta_npenumber.setText(self.mietas_dict[vri_id]['npenumber'])
            self.ui.lineEdit_mieta_schematype.setText(self.mietas_dict[vri_id]['schematype'])
            self.ui.plainTextEdit_mieta_schematitle.setPlainText(self.mietas_dict[vri_id]['schematitle'])
        elif self.temp_vri_dict:
            cert_num = self.tbl_vri_model.index(row, 2).data()
            if cert_num in self.temp_vri_dict:
                self.ui.lineEdit_mieta_number.setText(self.temp_vri_dict[cert_num]['regNumber'])
                self.ui.comboBox_mieta_rank.setCurrentText(self.temp_vri_dict[cert_num]['rankСоdе'])
                self.ui.lineEdit_mieta_rank_title.setText(self.temp_vri_dict[cert_num]['rankTitle'])
                self.ui.lineEdit_mieta_npenumber.setText(self.temp_vri_dict[cert_num]['npenumber'])
                self.ui.lineEdit_mieta_schematype.setText(self.temp_vri_dict[cert_num]['schematype'])
                self.ui.plainTextEdit_mieta_schematitle.setPlainText(self.temp_vri_dict[cert_num]['schemaTitle'])

    # --------------------------------ОБНОВЛЕНИЕ ПОЛЕЙ ОТДЕЛА, СОТРУДНИКОВ И КОМНАТ------------------------------------
    def _update_owner_info(self):
        # self.mi_deps = func.get_mi_deps()
        mi_id = self.ui.lineEdit_equip_id.text()
        if mi_id:
            dep_name_list = list()
            if mi_id in self.mi_deps:
                for dep_id in self.mi_deps[mi_id]:
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

    # -------------------ОБНОВЛЕНИЕ ИНФОРМАЦИИ ПОЛЕЙ ПРИ ВЫБОРЕ ПОВЕРКИ В ТАБЛИЦЕ ПОВЕРОК------------------------------
    def _on_vri_select(self, index):
        row = index.row()

        if self.temp_vri_dict:
            cert_num = self.tbl_vri_model.index(row, 2).data()
            if cert_num in self.temp_vri_dict:
                self._update_vri_tab(self.temp_vri_dict[cert_num])
                self._update_mieta_tab(row)
        else:
            mi_id = self.ui.lineEdit_equip_id.text()
            vri_id = self.tbl_vri_model.index(row, 6).data()
            if vri_id and mi_id:
                self.ui.lineEdit_vri_id.setText(vri_id)
                self._update_vri_tab(self.mis_vri_dict[mi_id][vri_id])
                self._update_mieta_tab(row)

    # ------------------------------------------ОЧИСТКА ВСЕГО----------------------------------------------------------
    def _clear_all(self):
        self.mis_vri_dict.clear()
        self.tbl_vri_model.clear()

        self._clear_mi_tab()
        self._clear_mieta_tab()
        self._clear_vri_tab()

    # ---------------------------------ОЧИСТКА ВКЛАДКИ ОБОРУДОВАНИЯ----------------------------------------------------
    def _clear_mi_tab(self):

        # очищаем списки отделов, комнат и работников
        self.lv_dep_model.setStringList([])
        self.cb_worker_model.setStringList([])
        self.cb_room_model.setStringList([])

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

    # ---------------------------------ОЧИСТКА ВКЛАДКИ ЭТАЛОНов--------------------------------------------------------
    def _clear_mieta_tab(self):
        self.ui.lineEdit_mieta_id.setText("")
        self.ui.lineEdit_mieta_number.setText("")
        self.ui.comboBox_mieta_rank.setCurrentIndex(0)
        self.ui.lineEdit_mieta_rank_title.setText("")
        self.ui.lineEdit_mieta_npenumber.setText("")
        self.ui.lineEdit_mieta_schematype.setText("")
        self.ui.plainTextEdit_mieta_schematitle.setPlainText("")

    # --------------------------------------ОЧИСТКА ВКЛАДКИ ПОВЕРОК----------------------------------------------------
    def _clear_vri_tab(self):
        self.temp_vri_dict.clear()
        self.ui.lineEdit_vri_id.setText("")
        self.ui.plainTextEdit_vri_organization.setPlainText("")
        self.ui.plainTextEdit_vri_miOwner.setPlainText("")
        self.ui.lineEdit_vrfDate.setText("")
        self.ui.lineEdit_vri_validDate.setText("")
        self.ui.lineEdit_vri_vriType.setText("")
        self.ui.plainTextEdit_vri_docTitle.setPlainText("")
        self.ui.radioButton_applicable.setChecked(True)
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

    # -------------------------------------------НАЖАТИЕ КНОПКИ СОХРАНИТЬ----------------------------------------------
    def _on_save_all(self):

        # todo добавить удаление эталонов если оборудование переводится в разряд обычного СИ

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

        # если сохраняем результаты поиска
        if self.temp_vri_dict:
            for cert_num in self.temp_vri_dict:
                sql_insert = f"INSERT INTO mis_vri_info VALUES (" \
                             f"NULL, " \
                             f"{mi_id}, " \
                             f"'{self.temp_vri_dict[cert_num]['organization']}', " \
                             f"'{self.temp_vri_dict[cert_num]['signCipher']}', " \
                             f"'{self.temp_vri_dict[cert_num]['miOwner']}', " \
                             f"'{self.temp_vri_dict[cert_num]['vrfDate']}', " \
                             f"'{self.temp_vri_dict[cert_num]['validDate']}', " \
                             f"'{self.temp_vri_dict[cert_num]['vriType']}', " \
                             f"'{self.temp_vri_dict[cert_num]['docTitle']}', " \
                             f"{int(self.temp_vri_dict[cert_num]['applicable'])}, " \
                             f"'{self.temp_vri_dict[cert_num]['certNum']}', " \
                             f"'{self.temp_vri_dict[cert_num]['stickerNum']}', " \
                             f"{int(self.temp_vri_dict[cert_num]['signPass'])}, " \
                             f"{int(self.temp_vri_dict[cert_num]['signMi'])}, " \
                             f"'{self.temp_vri_dict[cert_num]['inapplicable_reason']}', " \
                             f"'{self.temp_vri_dict[cert_num]['structure']}', " \
                             f"{int(self.temp_vri_dict[cert_num]['briefIndicator'])}, " \
                             f"'{self.temp_vri_dict[cert_num]['briefCharacteristics']}', " \
                             f"'{self.temp_vri_dict[cert_num]['ranges']}', " \
                             f"'{self.temp_vri_dict[cert_num]['values']}', " \
                             f"'{self.temp_vri_dict[cert_num]['channels']}', " \
                             f"'{self.temp_vri_dict[cert_num]['blocks']}', " \
                             f"'{self.temp_vri_dict[cert_num]['additional_info']}', " \
                             f"'{self.temp_vri_dict[cert_num]['info']}');"
                result = MySQLConnection.execute_query(connection, sql_insert)

                if result[0]:
                    vri_id = str(result[1])
                else:
                    connection.close()
                    return
                if self.temp_vri_dict[cert_num]['regNumber']:
                    sql_insert = f"INSERT INTO mietas VALUES (" \
                                 f"NULL, " \
                                 f"{mi_id}, " \
                                 f"{vri_id}, " \
                                 f"'{self.temp_vri_dict[cert_num]['regNumber']}', " \
                                 f"'{self.temp_vri_dict[cert_num]['rankСоdе']}', " \
                                 f"'{self.temp_vri_dict[cert_num]['npenumber']}', " \
                                 f"'{self.temp_vri_dict[cert_num]['schematype']}', " \
                                 f"'{self.temp_vri_dict[cert_num]['schemaTitle']}', " \
                                 f"'{self.temp_vri_dict[cert_num]['rankTitle']}');"
                    MySQLConnection.execute_query(connection, sql_insert)

        # если сохраняем изменения
        else:
            vri_id = self.ui.lineEdit_vri_id.text()
            if not vri_id:
                vri_id = "NULL"

            signPass = 0
            signMi = 0
            briefIndicator = 0

            if self.ui.radioButton_applicable.isChecked():
                applicable = 1
                cert_num = self.ui.lineEdit_vri_certNum.text()
                if self.ui.checkBox_vri_signPass.isChecked():
                    signPass = 1
                if self.ui.checkBox_vri_signMi.isChecked():
                    signMi = 1
            else:
                applicable = 0
                cert_num = self.ui.lineEdit_vri_noticeNum.text()

            if self.ui.checkBox_vri_briefIndicator.isChecked():
                briefIndicator = 1

            sql_replace = f"REPLACE INTO mis_vri_info VALUES (" \
                          f"{vri_id}, " \
                          f"{mi_id}, " \
                          f"'{self.ui.plainTextEdit_vri_organization.toPlainText()}', " \
                          f"'{self.ui.lineEdit_vri_signCipher.text()}', " \
                          f"'{self.ui.plainTextEdit_vri_miOwner.toPlainText()}', " \
                          f"'{self.ui.lineEdit_vrfDate.text()}', " \
                          f"'{self.ui.lineEdit_vri_validDate.text()}', " \
                          f"'{self.ui.lineEdit_vri_vriType.text()}', " \
                          f"'{self.ui.plainTextEdit_vri_docTitle.toPlainText()}', " \
                          f"{applicable}, " \
                          f"'{cert_num}', " \
                          f"'{self.ui.lineEdit_vri_stickerNum.text()}', " \
                          f"{signPass}, " \
                          f"{signMi}, " \
                          f"'{self.ui.plainTextEdit_vri_inapplicable_reason.toPlainText()}', " \
                          f"'{self.ui.plainTextEdit_vri_structure.toPlainText()}', " \
                          f"{briefIndicator}, " \
                          f"'{self.ui.plainTextEdit_vri_briefCharacteristics.toPlainText()}', " \
                          f"'{self.ui.plainTextEdit_vri_ranges.toPlainText()}', " \
                          f"'{self.ui.plainTextEdit_vri_values.toPlainText()}', " \
                          f"'{self.ui.plainTextEdit_vri_channels.toPlainText()}', " \
                          f"'{self.ui.plainTextEdit_vri_blocks.toPlainText()}', " \
                          f"'{self.ui.plainTextEdit_vri_additional_info.toPlainText()}', " \
                          f"'');"
            MySQLConnection.execute_query(connection, sql_replace)

        # mieta_id = self.ui.lineEdit_mieta_id.text()
        # if not mieta_id:
        #     mieta_id = "NULL"
        #
        # sql_replace = f"REPLACE INTO mietas VALUES (" \
        #               f"{mieta_id}, " \
        #               f"{mi_id}, " \
        #               f"'{self.ui.lineEdit_mieta_number.text()}', " \
        #               f"'{self.ui.comboBox_mieta_rank.currentText()}', " \
        #               f"'{self.ui.lineEdit_mieta_npenumber.text()}', " \
        #               f"'{self.ui.lineEdit_mieta_schematype.text()}', " \
        #               f"'{self.ui.plainTextEdit_mieta_schematitle.toPlainText()}', " \
        #               f"'{self.ui.lineEdit_mieta_rank_title.text()}');"
        # MySQLConnection.execute_query(connection, sql_replace)

        old_deps = set()
        if mi_id in self.mi_deps:
            old_deps = set(self.mi_deps[mi_id])

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

        self._update_mi_table()

        row = self.tbl_mi_model.indexFromItem(self.tbl_mi_model.findItems(mi_id, column=5)[0]).row()
        index = self.tbl_mi_model.index(row, 0)
        self._update_mi_tab(index)
        self.ui.tableView_mi_list.setCurrentIndex(index)
        self.ui.tableView_mi_list.scrollTo(index)

        QMessageBox.information(self, "Сохранено", "Информация сохранена")

    # -------------------------------------КЛИК ПО КНОПКЕ "СОХРАНИТЬ ПОВЕРКУ"----------------------------------------
    def _on_save_vri(self):

        mi_id = self.ui.lineEdit_equip_id.text()
        if not mi_id:
            QMessageBox.critical(self, "Ошибка", "Сначала выполните сохранение оборудования")
            return

        vri_id = self.ui.lineEdit_vri_id.text()
        if not vri_id:
            vri_id = "NULL"

        signPass = 0
        signMi = 0
        briefIndicator = 0

        if self.ui.radioButton_applicable.isChecked():
            applicable = 1
            cert_num = self.ui.lineEdit_vri_certNum.text()
            if self.ui.checkBox_vri_signPass.isChecked():
                signPass = 1
            if self.ui.checkBox_vri_signMi.isChecked():
                signMi = 1
        else:
            applicable = 0
            cert_num = self.ui.lineEdit_vri_noticeNum.text()

        if self.ui.checkBox_vri_briefIndicator.isChecked():
            briefIndicator = 1

        sql_replace = f"REPLACE INTO mis_vri_info VALUES (" \
                      f"{vri_id}, " \
                      f"{int(mi_id)}, " \
                      f"'{self.ui.plainTextEdit_vri_organization.toPlainText()}', " \
                      f"'{self.ui.lineEdit_vri_signCipher.text()}', " \
                      f"'{self.ui.plainTextEdit_vri_miOwner.toPlainText()}', " \
                      f"'{self.ui.lineEdit_vrfDate.text()}', " \
                      f"'{self.ui.lineEdit_vri_validDate.text()}', " \
                      f"'{self.ui.lineEdit_vri_vriType.text()}', " \
                      f"'{self.ui.plainTextEdit_vri_docTitle.toPlainText()}', " \
                      f"{applicable}, " \
                      f"'{cert_num}', " \
                      f"'{self.ui.lineEdit_vri_stickerNum.text()}', " \
                      f"{signPass}, " \
                      f"{signMi}, " \
                      f"'{self.ui.plainTextEdit_vri_inapplicable_reason.toPlainText()}', " \
                      f"'{self.ui.plainTextEdit_vri_structure.toPlainText()}', " \
                      f"{briefIndicator}, " \
                      f"'{self.ui.plainTextEdit_vri_briefCharacteristics.toPlainText()}', " \
                      f"'{self.ui.plainTextEdit_vri_ranges.toPlainText()}', " \
                      f"'{self.ui.plainTextEdit_vri_values.toPlainText()}', " \
                      f"'{self.ui.plainTextEdit_vri_channels.toPlainText()}', " \
                      f"'{self.ui.plainTextEdit_vri_blocks.toPlainText()}', " \
                      f"'{self.ui.plainTextEdit_vri_additional_info.toPlainText()}', " \
                      f"'');"
        MySQLConnection.verify_connection()
        connection = MySQLConnection.create_connection()
        MySQLConnection.execute_query(connection, sql_replace)
        connection.close()

    # ---------------------------------------КЛИК ПО КНОПКЕ "СОХРАНИТЬ ЭТАЛОН"-----------------------------------------
    def _on_save_mieta(self):
        row = self.ui.tableView_vri_list.currentIndex().row()
        mieta_id = self.ui.lineEdit_mieta_id.text()
        mi_id = self.ui.lineEdit_equip_id.text()
        vri_id = self.ui.lineEdit_vri_id.text()

        if not mi_id or not vri_id:
            QMessageBox.critical(self, "Ошибка", "Сначала выполните сохранение оборудования и (или) поверки")
            return
        if not mieta_id:
            mieta_id = "NULL"

        sql_replace = f"REPLACE INTO mietas VALUES (" \
                      f"{mieta_id}, " \
                      f"{int(mi_id)}, " \
                      f"{int(vri_id)}, " \
                      f"'{self.ui.lineEdit_mieta_number.text()}', " \
                      f"'{self.ui.comboBox_mieta_rank.currentText()}', " \
                      f"'{self.ui.lineEdit_mieta_npenumber.text()}', " \
                      f"'{self.ui.lineEdit_mieta_schematype.text()}', " \
                      f"'{self.ui.plainTextEdit_mieta_schematitle.toPlainText()}', " \
                      f"'{self.ui.lineEdit_mieta_rank_title.text()}');"
        MySQLConnection.verify_connection()
        connection = MySQLConnection.create_connection()
        MySQLConnection.execute_query(connection, sql_replace)
        connection.close()

        self.mietas_dict = func.get_mietas()['mietas_dict']
        self._update_mieta_tab(row)

        if vri_id in self.mietas_dict:
            rankTitle = self.mietas_dict[vri_id]['rankclass']
            schemaTitle = self.mietas_dict[vri_id]['schematitle']
            schematype = self.mietas_dict[vri_id]['schematype']
            regNumber = self.mietas_dict[vri_id]['number']
            if rankTitle and schemaTitle and regNumber and schematype:
                self.tbl_vri_model.setItem(row, 5, QStandardItem(
                    f"{regNumber}: {rankTitle.lower()}\n{schematype}: {schemaTitle}"))
            elif rankTitle and schemaTitle and regNumber:
                self.tbl_vri_model.setItem(row, 5, QStandardItem(f"{regNumber}: {rankTitle.lower()}\n{schemaTitle}"))
            else:
                self.tbl_vri_model.setItem(row, 5, QStandardItem("-"))

        QMessageBox.information(self, "Сохранено", "Информация сохранена")

    # -------------------------------------КЛИК ПО КНОПКЕ "УДАЛИТЬ ОБОРУДОВАНИЕ"---------------------------------------
    def _on_delete_mi(self):
        mi_id = self.ui.lineEdit_equip_id.text()
        if mi_id:
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Подтверждение удаления")
            dialog.setText(f"Вы действительно хотите удалить оборудование?\n"
                           f"Также удалится вся сопутствующая информация.")
            dialog.setIcon(QMessageBox.Warning)
            btn_yes = QPushButton("&Да")
            btn_no = QPushButton("&Нет")
            dialog.addButton(btn_yes, QMessageBox.AcceptRole)
            dialog.addButton(btn_no, QMessageBox.RejectRole)
            dialog.setDefaultButton(btn_no)
            dialog.setEscapeButton(btn_no)
            result = dialog.exec()
            if result == 0:
                sql_delete_1 = f"DELETE FROM mis WHERE mi_id = {int(mi_id)}"
                sql_delete_2 = f"DELETE FROM mis_departments WHERE MD_mi_id = {int(mi_id)}"
                sql_delete_3 = f"DELETE FROM mis_vri_info WHERE vri_mi_id = {int(mi_id)}"
                sql_delete_4 = f"DELETE FROM mietas WHERE mieta_mi_id = {int(mi_id)}"
                MySQLConnection.verify_connection()
                connection = MySQLConnection.create_connection()
                MySQLConnection.execute_transaction_query(connection, sql_delete_1, sql_delete_2, sql_delete_3,
                                                          sql_delete_4)
                connection.close()

                self._update_mi_table()
                self._update_vri_table()
                self._clear_all()

    # -------------------------------------КЛИК ПО КНОПКЕ "ДОБАВИТЬ ОТДЕЛ"---------------------------------------------
    def _on_add_dep(self):
        cur_dep_list = self.lv_dep_model.stringList()
        full_dep_list = self.departments['dep_name_list']
        choose_list = sorted(list(set(full_dep_list) - set(cur_dep_list)))
        mi_id = self.ui.lineEdit_equip_id.text()
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
                if "" not in cur_worker_list:
                    cur_worker_list.insert(0, "")
                self.cb_worker_model.setStringList(sorted(set(cur_worker_list)))

                # добавляем помещения
                cur_room_list = self.cb_room_model.stringList()
                cur_room_list += \
                    func.get_rooms_list([dep_id], self.rooms['room_dict'], self.room_deps['dep_rooms_dict'])['rooms']
                if "" not in cur_room_list:
                    cur_room_list.insert(0, "")
                self.cb_room_model.setStringList(sorted(set(cur_room_list)))

                if mi_id:
                    self.ui.comboBox_responsiblePerson.setCurrentText(
                        func.get_worker_fio_from_id(self.mis_dict[mi_id]['responsible_person'],
                                                    self.workers['worker_dict']))
                    self.ui.comboBox_room.setCurrentText(
                        func.get_room_number_from_id(self.mis_dict[mi_id]['room'], self.rooms['room_dict']))
        else:
            QMessageBox.information(self, "Выбора нет", "Все подразделения включены в список")

    # ----------------------------------КЛИК ПО КНОПКЕ "УДАЛИТЬ ОТДЕЛ"-------------------------------------------------
    def _on_remove_dep(self):
        if not self.ui.listView_departments.selectedIndexes():
            return
        dep_name = self.ui.listView_departments.currentIndex().data()
        cur_dep_list = self.lv_dep_model.stringList()
        cur_dep_list.remove(dep_name)
        mi_id = self.ui.lineEdit_equip_id.text()

        self.lv_dep_model.setStringList(cur_dep_list)
        dep_list = list()

        for dep in cur_dep_list:
            dep_id = func.get_dep_id_from_name(dep, self.departments['dep_dict'])
            dep_list.append(dep_id)

        worker_list = func.get_workers_list(dep_list, self.workers['worker_dict'],
                                            self.worker_deps['dep_workers_dict'])['workers']
        room_list = func.get_rooms_list(dep_list, self.rooms['room_dict'], self.room_deps['dep_rooms_dict'])['rooms']
        if "" not in worker_list:
            worker_list.insert(0, "")
        if "" not in room_list:
            room_list.insert(0, "")
        self.cb_worker_model.setStringList(worker_list)
        self.cb_room_model.setStringList(room_list)

        if mi_id:
            self.ui.comboBox_responsiblePerson.setCurrentText(
                func.get_worker_fio_from_id(self.mis_dict[mi_id]['responsible_person'],
                                            self.workers['worker_dict']))
            self.ui.comboBox_room.setCurrentText(
                func.get_room_number_from_id(self.mis_dict[mi_id]['room'], self.rooms['room_dict']))

    # -------------------НАЖАТИЕ КНОПКИ ПОИСКА ОБОРУДОВАНИЯ ИЗ АРШИНА--------------------------------------------------
    def _on_start_search(self):
        self._clear_all()
        self.ui.tableView_mi_list.selectionModel().clearSelection()
        self.mit_search.clear()
        self.mit.clear()
        self.vri_search.clear()
        self.vri.clear()
        self.mieta_search.clear()
        self.mieta.clear()
        self.vri_numbers.clear()

        dialog = QInputDialog()
        dialog.setInputMode(QInputDialog.TextInput)
        dialog.setWindowTitle("Поиск эталона в ФГИС \"Аршин\"")
        dialog.setLabelText("Введите один из номеров:\n"
                            "- номер в реестре;\n"
                            "- номер эталона единиц величин;\n"
                            "- номер в перечне СИ, применяемых в качестве эталона;\n"
                            "- номер свидетельства формата 2021 года;\n"
                            "- номер записи сведений в ФИФ ОЕИ.")
        dialog.textValueChanged.connect(lambda: self._input_verify(dialog))
        result = dialog.exec()
        if result == QDialog.Accepted:
            self.number = dialog.textValue().strip()
            if self.eq_type == "" or not dialog.textValue():
                QMessageBox.warning(self, "Предупреждение", "Введите корректный номер")
                return

            self.dialog = QProgressDialog(self)
            self.dialog.setAutoClose(False)
            self.dialog.setAutoReset(False)
            self.dialog.setWindowTitle("ОЖИДАЙТЕ! Идет поиск!")
            self.dialog.setCancelButtonText("Прервать")
            self.dialog.canceled.connect(self._on_search_stopped)
            self.dialog.setRange(0, 100)
            self.dialog.setWindowModality(Qt.WindowModal)
            self.dialog.resize(350, 100)
            self.dialog.show()
            if self.eq_type == "mit":
                self._update_progressbar(0, "Поиск номера реестра")
            elif self.eq_type == "vri":
                self._update_progressbar(0, "Поиск номера свидетельства")
            elif self.eq_type == "mieta":
                self._update_progressbar(0, "Поиск номера в перечне СИ, применяемых в качестве эталонов")
            elif self.eq_type == "vri_id":
                self._update_progressbar(0, "Получение данных из свидетельства")

            self.search_thread.is_running = True

            self.ui.plainTextEdit_owner.setPlainText(ORG_NAME)

            if self.eq_type == "vri_id":
                if "-" not in self.number:
                    self.number = f"1-{self.number}"
                url = f"{URL_START}/vri/{self.number}"
                self.search_thread.url = url
                self.search_thread.start()
            else:
                url = f"{URL_START}/{self.eq_type}?rows=100&search={self.number}"
                self.search_thread.url = url
                self.search_thread.start()

    # --------------------------------ПРОВЕРКА ВВОДА НОМЕРА ДЛЯ ПОИСКА ОБОРУДОВАНИЯ------------------------------------
    def _input_verify(self, dialog):
        self.eq_type = ""
        self.get_type = ""
        if not dialog.textValue():
            dialog.setLabelText("Введите один из номеров:\n"
                                "- номер в реестре;\n"
                                "- номер эталона единиц величин;\n"
                                "- номер в перечне СИ, применяемых в качестве эталона;\n"
                                "- номер свидетельства формата 2021 года;\n"
                                "- номер записи сведений в ФИФ ОЕИ.")
            return
        rx_mit = QRegExp("^[1-9][0-9]{0,5}-[0-9]{2}$")
        rx_npe = QRegExp("^гэт[1-9][0-9]{0,2}-(([0-9]{2})|([0-9]{4}))$")
        rx_uve = QRegExp("^[1-3]\.[0-9]\.\S{3}\.\d{4}\.20[0-4]\d$")
        rx_mieta = QRegExp("^[1-9]\d{0,5}\.\d{2}\.(0Р|1Р|2Р|3Р|4Р|5Р|РЭ|ВЭ|СИ)\.\d+\s*$")
        rx_svid = QRegExp("^(С|И)\-\S{1,3}\/[0-3][0-9]\-[0-1][0-9]\-20[2-5][0-9]\/\d{8,10}$")
        rx_vri_id = QRegExp("^([1-2]\-)*\d{6,10}\s*$")
        rx_mit.setCaseSensitivity(False)
        rx_npe.setCaseSensitivity(False)
        rx_uve.setCaseSensitivity(False)
        rx_mieta.setCaseSensitivity(False)
        rx_svid.setCaseSensitivity(False)
        rx_vri_id.setCaseSensitivity(False)
        if rx_mit.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер реестра СИ")
            self.eq_type = "mit"
        elif rx_npe.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Государственный первичный эталон")
            self.eq_type = "npe"
        elif rx_uve.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер эталона единицы величины")
            self.eq_type = "uve"
        elif rx_mieta.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер в перечне СИ, применяемых в качестве эталонов")
            self.eq_type = "mieta"
        elif rx_svid.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер свидетельства о поверке")
            self.eq_type = "vri"
        elif rx_vri_id.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер записи сведений в ФИФ ОЕИ")
            self.eq_type = "vri_id"
            self.get_type = "vri_id"
        else:
            dialog.setLabelText("Введенный номер не определяется. Проверьте правильность ввода")

    # --------------------------------------ОБРАБОТКА ПОЛУЧЕННОГО ОТВЕТА ОТ СЕРВЕРА------------------------------------
    def _on_getting_resp(self, resp):
        if not resp or resp.startswith("Error") or resp.startswith("<!DOCTYPE html>"):
            QMessageBox.critical("Ошибка", f"Возникла ошибка получения сведений из ФГИС \"АРШИН\".\n{resp}")
            self.dialog.close()
            return
        elif resp == "stop":
            self.dialog.close()
            QMessageBox.information(self, "Ошибка", "Поиск прерван")
            self._clear_all()
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
                    self._get_vri_info()
                elif "mit" in self.search_thread.url:
                    self._get_mit()
                elif "vri" in self.search_thread.url:
                    self._get_vri()
                elif "mieta" in self.search_thread.url:
                    self._get_mieta()

                else:
                    self.dialog.close()

    # ---------------------------------ПОЛУЧЕНИЕ ИНФОРМАЦИИ О СИ ПО НОМЕРУ РЕЕСТРА-------------------------------------
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
                    url = f"{URL_START}/mit/{self.resp_json['result']['items'][0]['mit_id']}"
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
                        url = f"{URL_START}/mit/{self.resp_json['result']['items'][items_list.index(s)]['mit_id']}"
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
                    if 'result' in self.resp_json and 'items' in self.resp_json['result']:
                        url = f"{URL_START}/mit/{self.resp_json['result']['items'][0]['mit_id']}"
                        self.search_thread.url = url
                        self.search_thread.start()
                    else:
                        self.dialog.close()

        # получаем self.mit
        elif "mit/" in self.search_thread.url:
            self.mit = self.resp_json

            if self.eq_type == "mit":
                self._fill_mit()
                self._on_search_finished()

            elif self.eq_type == "vri" or self.eq_type == "mieta" or self.eq_type == "vri_id":
                self._fill_vri()
                self._fill_mit()
                self._get_vri_info()

    # ------------------------------------ЗАПОЛНЕНИЕ ИНФОРМАЦИИ С РЕЕСТРА----------------------------------------------
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

    # ------------------------------ПОЛУЧЕНИЕ ИНФОРМАЦИИ О СИ ПО НОМЕРУ СВИДЕТЕЛЬСТВА----------------------------------
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
                if 'result' in self.resp_json:
                    url = f"{URL_START}/vri/{self.resp_json['result']['items'][0]['vri_id']}"
                    self.search_thread.url = url
                    self.search_thread.start()
                else:
                    self.dialog.close()
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
                        url = f"{URL_START}/mit?rows=100&search={mitypeNumber}%20{mitypeTitle.replace(' ', '%20')}"
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
                                url = f"{URL_START}/mieta?rows=100&search={regNumber}"
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
                            url = f"{URL_START}/mit?rows=100&search={mitypeNumber}%20{mitypeTitle.replace(' ', '%20')}"
                            self.search_thread.url = url
                            self.search_thread.start()
                        else:
                            self._fill_vri()
                            self._get_vri_info()
                    elif 'partyMI' in self.vri['result']['miInfo']:
                        miInfo = self.vri['result']['miInfo']['partyMI']

    # -------------------------------ЗАПОЛНЕНИЕ ИНФОРМАЦИИ С НОМЕРА СВИДЕТЕЛЬСТВА--------------------------------------
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
                        self._on_search_finished()

    # ---------------------------------ПОЛУЧЕНИЕ ИНФОРМАЦИИ ОБ ЭТАЛОНЕ ИЗ АРШИНА---------------------------------------
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
                    url = f"{URL_START}/mieta/{mieta_id}"
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
            self.ui.comboBox_status.setCurrentText("СИ в качестве эталона")

            for cresult in result['cresults']:
                if 'vri_id' in cresult and 'org_title' in cresult:
                    self.vri_numbers.append([cresult['vri_id'], cresult['org_title']])

            if self.eq_type == "vri" or self.eq_type == "vri_id":
                if 'mitype_num' in result and 'mitype' in result:  # номер реестра
                    self._update_progressbar(75, "Поиск номера в реестре утвержденных типов СИ")
                    url = f"{URL_START}/mit?rows=100&search={result['mitype_num']}%20{result['mitype'].replace(' ', '%20')}"
                    self.search_thread.url = url
                    self.search_thread.start()
                else:
                    self._fill_vri()
                    self._get_vri_info()

            elif self.eq_type == "mieta":
                self._update_progressbar(50, "Поиск информации о результатах поверки СИ")
                if self.vri_numbers:
                    url = f"{URL_START}/vri/{self.vri_numbers[0][0]}"
                    self.search_thread.url = url
                    self.search_thread.start()
                else:
                    self.dialog.close()

    # ---------------------------------ПОЛУЧЕНИЕ ИНФОРМАЦИИ О ПОВЕРКАХ ИЗ АРШИНА---------------------------------------
    def _get_vri_info(self):

        self.get_type = "mieta_vri"

        if 'result' in self.vri and 'vriInfo' in self.vri['result']:
            vriInfo = self.vri['result']['vriInfo']

            row = list()
            cert_num = ""
            organization = ""
            signCipher = ""
            miOwner = ""
            vrfDate = ""
            validDate = ""
            vriType = "периодическая"
            docTitle = ""
            applicable = "1"
            stickerNum = ""
            signPass = "0"
            signMi = "0"
            structure = ""
            briefIndicator = "0"
            briefCharacteristics = ""
            ranges = ""
            values = ""
            channels = ""
            blocks = ""
            additional_info = ""
            regNumber = ""
            rankСоdе = ""
            rankTitle = ""
            schemaTitle = ""
            npenumber = ""
            schematype = ""

            # список поверок для таблицы: дата поверки, годен до или бессрочно, номер свид-ва, результат, поверитель, эталон
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
            row.append(QStandardItem(self.vri_numbers[0][1]))

            if 'organization' in vriInfo:
                if "(" in vriInfo['organization']:
                    organization = str(vriInfo['organization'])[str(vriInfo['organization']).find("(") + 1:-1]
                else:
                    organization = str(vriInfo['organization'])

            if 'signCipher' in vriInfo:
                signCipher = vriInfo['signCipher']
            if 'miOwner' in vriInfo:
                miOwner = vriInfo['miOwner']
            if 'vrfDate' in vriInfo:
                vrfDate = vriInfo['vrfDate']
            if 'validDate' in vriInfo:
                validDate = vriInfo['validDate']
            if 'vriType' in vriInfo:
                if str(vriInfo['vriType']) == "2":
                    vriType = "периодическая"
                elif str(vriInfo['vriType']) == "1":
                    vriType = "первичная"
            if 'docTitle' in vriInfo:
                docTitle = vriInfo['docTitle']
            if 'applicable' in vriInfo:
                applicable = "1"
                if 'stickerNum' in vriInfo['applicable']:
                    stickerNum = vriInfo['applicable']['stickerNum']
                if 'signPass' in vriInfo['applicable'] and vriInfo['applicable']['signPass']:
                    signPass = "1"
                if 'signMi' in vriInfo['applicable'] and vriInfo['applicable']['signMi']:
                    signMi = "1"
            if 'inapplicable' in vriInfo:
                applicable = "0"

            if 'info' in self.vri['result']:
                info = self.vri['result']['info']
                if 'structure' in info:
                    structure = info['structure']
                if 'briefIndicator' in info and info['briefIndicator']:
                    briefIndicator = "1"
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

            if self.mieta and 'result' in self.mieta:
                result = self.mieta['result']
                if 'number' in result:
                    regNumber = result['number']
                if 'rankcode' in result:
                    rankСоdе = result['rankcode']
                if 'rankclass' in result:
                    rankTitle = result['rankclass']
                if 'npenumber' in result:
                    npenumber = result['npenumber']
                if 'schematype' in result:
                    schematype = result['schematype']
                if 'schematitle' in result:
                    schemaTitle = result['schematitle']
                self.mieta.clear()
            elif 'miInfo' in self.vri['result'] and 'etaMI' in self.vri['result']['miInfo']:
                etaMI = self.vri['result']['miInfo']['etaMI']
                if 'regNumber' in etaMI:
                    regNumber = etaMI['regNumber']
                if 'rankСоdе' in etaMI:
                    rankСоdе = etaMI['rankСоdе']
                if 'rankTitle' in etaMI:
                    rankTitle = etaMI['rankTitle']
                if 'schemaTitle' in etaMI:
                    schemaTitle = etaMI['schemaTitle']

            if rankTitle and schemaTitle and regNumber:
                row.append(QStandardItem(f"{rankTitle}\n{regNumber}: {schemaTitle}"))
            else:
                row.append(QStandardItem("-"))
            self.tbl_vri_model.appendRow(row)

            if cert_num:
                self.temp_vri_dict[cert_num] = {'organization': organization,
                                                'signCipher': signCipher,
                                                'miOwner': miOwner,
                                                'vrfDate': vrfDate,
                                                'validDate': validDate,
                                                'vriType': vriType,
                                                'docTitle': docTitle,
                                                'applicable': applicable,
                                                'certNum': cert_num,
                                                'stickerNum': stickerNum,
                                                'signPass': signPass,
                                                'signMi': signMi,
                                                'inapplicable_reason': "",
                                                'structure': structure,
                                                'briefIndicator': briefIndicator,
                                                'briefCharacteristics': briefCharacteristics,
                                                'ranges': ranges,
                                                'values': values,
                                                'channels': channels,
                                                'blocks': blocks,
                                                'additional_info': additional_info,
                                                'info': "",
                                                'regNumber': regNumber,
                                                'rankСоdе': rankСоdе,
                                                'rankTitle': rankTitle,
                                                'npenumber': npenumber,
                                                'schematype': schematype,
                                                'schemaTitle': schemaTitle}
            self._on_vri_select(self.tbl_vri_model.item(0, 2).index())

            # ЕСЛИ ИЩЕМ ПО НОМЕРУ ЭТАЛОНА, ТО УДАЛЯЕМ ПЕРВУЮ ПОВЕРКУ И ИЩЕМ СЛЕДУЮЩУЮ
            if self.eq_type == "mieta":
                del self.vri_numbers[0]
                if len(self.vri_numbers) > 0:
                    self._update_progressbar(95, "Поиск информации о поверках")
                    url = f"{URL_START}/vri/{self.vri_numbers[0][0]}"
                    self.search_thread.url = url
                    self.search_thread.start()
                    return
            else:
                # ЕСЛИ ИЩЕМ ПО НОМЕРУ СВИДЕТЕЛЬСТВА И ОДНА ПОВЕРКА, ОЧИЩАЕМ СПИСОК
                if len(self.vri_numbers) == 1:
                    self.vri_numbers.clear()
                # ЕСЛИ БОЛЬШЕ ОДНОЙ ПОВЕРКИ, ТО УДАЛЯЕМ ЗАПИСАННУЮ И ИЩЕМ СЛЕДУЮЩУЮ
                for vri in self.vri_numbers:
                    if self.vri_search and self.vri_search['result']['items'][0]['vri_id'] in vri:
                        self.vri_numbers.remove(vri)
                    elif self.number in vri:
                        self.vri_numbers.remove(vri)
                if len(self.vri_numbers) > 0:
                    self._update_progressbar(95, "Поиск информации о поверках")
                    url = f"{URL_START}/vri/{self.vri_numbers[0][0]}"
                    self.search_thread.url = url
                    self.search_thread.start()
                    return
            self._on_search_finished()

    # ----------------------------------------ЗАВЕРШЕНИЕ ПОИСКА--------------------------------------------------------
    def _on_search_finished(self):
        self.eq_type = ""
        self.get_type = ""
        self.dialog.setLabelText("Поиск завершен. Данные внесены в форму.")
        self.dialog.setValue(100)
        self.dialog.setCancelButtonText("Готово")
        self._update_vri_table()

    # ---------------------------------------------ОСТАНОВКА ПОИСКА----------------------------------------------------
    def _on_search_stopped(self):
        self.search_thread.is_running = False
        self.eq_type = ""
        self.get_type = ""
        self.ui.tableView_mi_list.selectionModel().clearSelection()
        self.mit_search.clear()
        self.mit.clear()
        self.vri_search.clear()
        self.vri.clear()
        self.mieta_search.clear()
        self.mieta.clear()
        self.vri_numbers.clear()

    # ----------------------------------------ОБНОВЛЕНИЕ ПРОГРЕССА ПОИСКА----------------------------------------------
    def _update_progressbar(self, val, text):
        self.dialog.setLabelText(text)
        self.dialog.setValue(val)


class CustomSortingModel(QSortFilterProxyModel):
    def lessThan(self, left, right):
        col = left.column()

        data_left = left.data()
        data_right = right.data()

        if col == 0 or col == 1:
            data_left = QDate.fromString(data_left, "dd.MM.yyyy")
            data_right = QDate.fromString(data_right, "dd.MM.yyyy")

        return data_left < data_right


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = EquipmentWidget()

    window.showMaximized()
    sys.exit(app.exec_())
