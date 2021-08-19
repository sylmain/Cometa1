import json
from openpyxl import load_workbook
from json.decoder import JSONDecodeError
from PyQt5.QtCore import QRegExp, QThread, pyqtSignal, Qt, QStringListModel, QEvent, QDate, QSortFilterProxyModel, \
    QItemSelectionModel, pyqtSlot, QSettings
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QCloseEvent
from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog, QDialog, QMessageBox, QProgressDialog, \
    QAbstractItemView, QPushButton, QMdiSubWindow
from functions_pkg.send_get_request import GetRequest
from equipment_pkg.ui_equipment import Ui_MainWindow
from functions_pkg.db_functions import MySQLConnection
import functions_pkg.functions as func
from equipment_pkg.equipment_import import EquipmentImportWidget
from equipment_pkg.equipment_functions import *

# from equipment_pkg.equipment_requests import send_request

STATUS_LIST = ["СИ", "СИ в качестве эталона", "Эталон единицы величины"]
VRI_TYPE_LIST = ["периодическая", "первичная"]
URL_START = "https://fgis.gost.ru/fundmetrology/eapi"
ORG_NAME = func.get_organization_name()
MEASURE_CODES = func.get_measure_codes()


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
            print(f" {self.url}")
            resp = GetRequest.getRequest(self.url)
            print(f"  {resp}")
            print("    thread stopped")
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
        self._appearance_init()

        self.mi_dict = dict()  # словарь оборудования из базы
        self.mi_deps = dict()  # связка прибор-много отделов
        self.mis_vri_dict = dict()  # словарь всех поверок
        self.mietas_dict = dict()  # словарь всех эталонов
        self.list_of_card_numbers = list()  # множество номеров карточек
        self.set_of_vri_id = set()  # множество id поверок (меняется при перекючении прибора)
        self.set_of_mi = set()  # множество приборов {наименование, тип, заводской номер}
        self.set_of_vri = set()  # множество поверок {дата, номер св-ва, номер эталона} (меняется)
        self.temp_vri_dict = dict()  # временный словарь поверок при поиске оборудования (или поверок)
        self.temp_set_of_vri_id = set()  # временное множество id поверок при поиске оборудования (или поверок)

        self.mit_search = dict()
        self.mit = dict()
        self.mieta_search = dict()
        self.mieta = dict()
        self.vri_search = dict()
        self.vri = dict()

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

        self._clear_all()

        self._add_measure_codes()
        self.ui.comboBox_status.addItems(STATUS_LIST)
        self.ui.comboBox_vri_vriType.addItems(VRI_TYPE_LIST)

        self.departments = func.get_departments()
        self.workers = func.get_workers()
        self.worker_deps = func.get_worker_deps()
        self.rooms = func.get_rooms()
        self.room_deps = func.get_room_deps()
        self._create_dicts()

        self._update_mi_table()
        self._update_vri_table()

        self.ui.tabWidget.setCurrentIndex(0)

    def _create_dicts(self):
        self.mi_dict = func.get_mis()['mi_dict']
        self.set_of_mi = func.get_mis()['set_of_mi']
        self.list_of_card_numbers = func.get_mis()['list_of_card_numbers']
        self.mi_deps = func.get_mi_deps()['mi_deps_dict']
        self.mis_vri_dict = func.get_mis_vri_info()['mis_vri_dict']
        self.mietas_dict = func.get_mietas()['mietas_dict']

    def _add_measure_codes(self):
        self.ui.comboBox_measure_code.addItems(["- Не определено"])
        self.ui.comboBox_measure_code.addItems(sorted(MEASURE_CODES['measure_codes_list']))

    def _add_measure_subcodes(self, new_code):
        self.ui.comboBox_measure_subcode.clear()
        self.ui.comboBox_measure_subcode.addItems(["- Не определено"])
        if "Не определено" not in new_code:
            code = new_code[:2]
            self.ui.comboBox_measure_subcode.addItems(sorted(MEASURE_CODES['measure_sub_codes_dict'][code]))

    def _add_connects(self):
        self.ui.toolButton_equip_add.clicked.connect(self._on_start_search)
        self.ui.pushButton_equip_save.clicked.connect(self._on_save_all)
        self.search_thread.msg_signal.connect(self._on_getting_resp, Qt.QueuedConnection)
        self.ui.tableView_mi_list.clicked.connect(self._on_mi_select)
        self.ui.tableView_mi_list.activated.connect(self._on_mi_select)
        self.ui.tableView_vri_list.clicked.connect(self._on_vri_select)
        self.ui.tableView_vri_list.activated.connect(self._on_vri_select)
        self.ui.pushButton_save_mi_info.clicked.connect(self._on_save_mi_info)
        self.ui.pushButton_save_vri.clicked.connect(self._on_save_vri)
        self.ui.pushButton_save_mieta.clicked.connect(self._on_save_mieta)
        self.ui.pushButton_add_vri.clicked.connect(self._on_add_vri)
        self.ui.pushButton_find_vri.clicked.connect(self._on_find_vri)
        self.ui.pushButton_clear_vri.clicked.connect(self._clear_vri_tab)
        self.ui.pushButton_clear_mieta.clicked.connect(self._clear_mieta_tab)
        self.ui.pushButton_add_dep.clicked.connect(self._on_add_dep)
        self.ui.pushButton_remove_dep.clicked.connect(self._on_remove_dep)
        self.ui.pushButton_clear.clicked.connect(self._clear_all)
        self.ui.pushButton_delete_mi.clicked.connect(self._on_delete_mi)
        self.ui.pushButton_import.clicked.connect(self._on_import)
        # self.ui.pushButton_delete_mi.clicked.connect(self._test)
        self.ui.pushButton_delete_vri.clicked.connect(self._on_delete_vri)
        self.ui.comboBox_status.currentTextChanged.connect(self._on_status_changed)
        self.ui.comboBox_measure_code.currentTextChanged.connect(self._add_measure_subcodes)
        self.ui.comboBox_measure_code.textActivated.connect(self._change_card_number)
        self.ui.comboBox_measure_subcode.textActivated.connect(self._change_card_number)
        self.ui.radioButton_applicable.toggled.connect(self._on_applicable_toggle)
        self.ui.tabWidget.currentChanged.connect(self._on_tab_changed)
        # self.ui.lineEdit_reg_card_number.textChanged.connect(self._appearance_init)

    def _change_card_number(self):
        mi_id = self.ui.lineEdit_mi_id.text()
        if mi_id:
            cur_card_number = self.mi_dict[mi_id]['reg_card_number']
        else:
            cur_card_number = ""
        # сохраняем вид измерений
        if self.ui.comboBox_measure_code.currentText().startswith("- "):
            new_meas_code = ""
        else:
            new_meas_code = self.ui.comboBox_measure_code.currentText()[:2]
        # сохраняем подвид измерений
        if self.ui.comboBox_measure_subcode.currentText().startswith("- "):
            new_sub_meas_code = ""
        else:
            new_sub_meas_code = self.ui.comboBox_measure_subcode.currentText()[2:4]
        # если нет подвида и вида, записываем сохраненный номер и выходим
        if not new_meas_code and not new_sub_meas_code:
            self.ui.lineEdit_reg_card_number.setText(cur_card_number)
            return
        # новый номер карточки и предыдущий номер карточки (на один меньше нового)
        new_number_string, prev_number_string = get_next_card_number(self.list_of_card_numbers, new_meas_code,
                                                                     new_sub_meas_code)
        # prev_number_string = get_next_card_number(self.list_of_card_numbers, new_meas_code, new_sub_meas_code)[1]

        # если выбран первоначальный (сохраненный) вид измерений, то записываем значение из словаря
        if prev_number_string == cur_card_number:
            self.ui.lineEdit_reg_card_number.setText(cur_card_number)
            return
        # если поле номера карточки пустое или сохраненный вид измерений отличается от текущего - меняем номер карточки
        if not cur_card_number or cur_card_number != prev_number_string:
            self.ui.lineEdit_reg_card_number.setText(new_number_string)

    def _on_import(self):
        self.widget = EquipmentImportWidget()
        self.widget.setWindowModality(Qt.ApplicationModal)
        self.widget.show()

    # ---------------------------------------------ВНЕШНИЙ ВИД ПРИ СТАРТЕ----------------------------------------------
    def _appearance_init(self):
        # if not self.ui.lineEdit_reg_card_number.text():
        #     self.ui.lineEdit_reg_card_number.setStyleSheet("border: 1px solid red")
        # else:
        #     self.ui.lineEdit_reg_card_number.setStyleSheet(None)
        self.ui.frame_mieta_buttons.hide()
        self.ui.frame_vri_buttons.hide()

    # -----------------------------------ВИДИМОСТЬ КНОПОК ПРИ ПЕРЕКЛЮЧЕНИИ ВКЛАДОК-------------------------------------
    def _on_tab_changed(self, tab_index):
        self.ui.frame_mi_info_buttons.hide()
        self.ui.frame_vri_buttons.hide()
        self.ui.frame_mieta_buttons.hide()
        if tab_index == 2:
            self.ui.frame_vri_buttons.show()
        elif tab_index == 1:
            self.ui.frame_mieta_buttons.show()
        elif tab_index == 0:
            self.ui.frame_mi_info_buttons.show()

    def _test(self):
        # for i in range(0, self.tbl_mi_model.rowCount()):
        #     print(self.tbl_mi_model.index(i, 2).data())
        pass

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
        cur_tab_index = self.ui.tabWidget.currentIndex()
        self.ui.tabWidget.setTabEnabled(1, False)
        self.ui.groupBox_mieta_info.hide()
        self.ui.groupBox_uve_info.hide()
        if new_status == "СИ в качестве эталона":
            self.ui.tabWidget.setTabEnabled(1, True)
            self.ui.groupBox_mieta_info.show()
        elif new_status == "Эталон единицы величины":
            self.ui.tabWidget.setTabEnabled(1, True)
            self.ui.groupBox_uve_info.show()
        self.ui.tabWidget.setCurrentIndex(cur_tab_index)

    # ----------------ОБНОВЛЕНИЕ ИНФОРМАЦИИ ПОЛЕЙ ПРИ ВЫБОРЕ ОБОРУДОВАНИЯ В ТАБЛИЦЕ ОБОРУДОВАНИЯ-----------------------
    def _on_mi_select(self, index):
        self._clear_all()
        row = index.row()
        mi_id = self.tbl_mi_model.index(row, 5).data()
        if mi_id:
            self.ui.pushButton_find_vri.show()
            if mi_id in self.mi_dict:
                self._update_mi_tab(mi_id)
                self._update_vri_table(mi_id)

        if self.tbl_vri_model.rowCount() > 0:
            self.ui.tableView_vri_list.selectionModel().select(self.tbl_vri_model.item(0, 1).index(),
                                                               QItemSelectionModel.SelectCurrent)
            self._on_vri_select(self.tbl_vri_proxy_model.index(0, 1))

    # -------------------ОБНОВЛЕНИЕ ИНФОРМАЦИИ ПОЛЕЙ ПРИ ВЫБОРЕ ПОВЕРКИ В ТАБЛИЦЕ ПОВЕРОК------------------------------
    def _on_vri_select(self, index):
        row = index.row()
        vri_id = self.tbl_vri_proxy_model.index(row, 6).data()
        # self._clear_vri_tab()

        # ЕСЛИ ПОВЕРКА ЕСТЬ В БАЗЕ
        if vri_id:
            mi_id = self.ui.lineEdit_mi_id.text()
            if mi_id:
                self.ui.lineEdit_vri_id.setText(vri_id)
                self._update_vri_tab(vri_id)
                self._update_mieta_tab(vri_id)
        else:
            if self.temp_vri_dict:
                cert_num = self.tbl_vri_proxy_model.index(row, 2).data()
                if cert_num in self.temp_vri_dict:
                    self._update_vri_tab()
                    self._update_mieta_tab()
                else:
                    self._clear_mieta_tab()

    # ------------------------------------ОБНОВЛЕНИЕ ТАБЛИЦЫ ОБОРУДОВАНИЯ----------------------------------------------
    def _update_mi_table(self):
        self.tbl_mi_model.clear()

        self.tbl_mi_model.setHorizontalHeaderLabels(
            ["Номер карточки", "Код измерений", "Наименование", "Тип", "Заводской номер", "id"])
        self.ui.tableView_mi_list.setColumnWidth(0, 110)
        self.ui.tableView_mi_list.setColumnWidth(1, 100)
        self.ui.tableView_mi_list.setColumnWidth(2, 200)
        self.ui.tableView_mi_list.setColumnWidth(3, 100)
        self.ui.tableView_mi_list.setColumnWidth(4, 110)
        self.ui.tableView_mi_list.setColumnWidth(5, 0)
        for mi_id in self.mi_dict:
            row = []
            row.append(QStandardItem(self.mi_dict[mi_id]['reg_card_number']))
            if self.mi_dict[mi_id]['measure_code'] != "0":
                row.append(QStandardItem(self.mi_dict[mi_id]['measure_code']))
            else:
                row.append(QStandardItem(""))
            row.append(QStandardItem(self.mi_dict[mi_id]['title']))
            row.append(QStandardItem(self.mi_dict[mi_id]['modification']))
            row.append(QStandardItem(self.mi_dict[mi_id]['number']))
            row.append(QStandardItem(mi_id))
            self.tbl_mi_model.appendRow(row)
        self.ui.tableView_mi_list.resizeRowsToContents()
        self.ui.tableView_mi_list.sortByColumn(0, Qt.AscendingOrder)
        self.ui.tableView_mi_list.selectionModel().clearSelection()

    # -----------------------------------------ОБНОВЛЕНИЕ ТАБЛИЦЫ ПОВЕРОК----------------------------------------------
    def _update_vri_table(self, mi_id=None):
        self.set_of_vri.clear()
        self.set_of_vri_id.clear()
        if mi_id and mi_id in self.mis_vri_dict:
            self.tbl_vri_model.clear()
            for vri_id in self.mis_vri_dict[mi_id]:
                row = list()
                regNumber = ""

                # КОЛОНКИ ТАБЛИЦЫ ПОВЕРОК
                vri_vrf_date = self.mis_vri_dict[mi_id][vri_id]['vrfDate']
                vri_valid_date = "БЕССРОЧНО"
                vri_cert_number = self.mis_vri_dict[mi_id][vri_id]['certNum']
                vri_result = "ГОДЕН"
                vri_organization = self.mis_vri_dict[mi_id][vri_id]['organization']
                vri_mieta = "нет"

                if self.mis_vri_dict[mi_id][vri_id]['applicable'] == "1":
                    if self.mis_vri_dict[mi_id][vri_id]['validDate']:
                        vri_valid_date = self.mis_vri_dict[mi_id][vri_id]['validDate']
                else:
                    vri_valid_date = "-"
                    vri_result = "БРАК"

                if vri_id in self.mietas_dict:
                    rankTitle = self.mietas_dict[vri_id]['rankclass']
                    regNumber = self.mietas_dict[vri_id]['number']
                    if rankTitle and regNumber:
                        vri_mieta = f"{regNumber}: {rankTitle.lower()}"

                row.append(QStandardItem(vri_vrf_date))
                row.append(QStandardItem(vri_valid_date))
                row.append(QStandardItem(vri_cert_number))
                row.append(QStandardItem(vri_result))
                row.append(QStandardItem(vri_organization))
                row.append(QStandardItem(vri_mieta))
                row.append(QStandardItem(vri_id))
                self.tbl_vri_model.appendRow(row)

                self.set_of_vri.add((vri_vrf_date, vri_cert_number, regNumber))
                self.set_of_vri_id.add(self.mis_vri_dict[mi_id][vri_id]['FIF_id'])

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
        self.ui.tableView_vri_list.sortByColumn(1, Qt.DescendingOrder)

    # ---------------------------------------ОБНОВЛЕНИЕ ВКЛАДКИ ОБ ОБОРУДОВАНИИ----------------------------------------
    def _update_mi_tab(self, mi_id):

        self.ui.lineEdit_mi_id.setText(mi_id)
        self.ui.lineEdit_reg_card_number.setText(self.mi_dict[mi_id]['reg_card_number'])

        self.ui.comboBox_measure_code.setCurrentIndex(0)
        self.ui.comboBox_measure_subcode.setCurrentIndex(0)
        measure_code_id = self.mi_dict[mi_id]['measure_code']
        if measure_code_id != "0":
            measure_code_name = func.get_measure_code_name_from_id(measure_code_id, MEASURE_CODES)
            if measure_code_name:
                if len(measure_code_id) == 2:
                    self.ui.comboBox_measure_code.setCurrentText(f"{measure_code_id} {measure_code_name}")
                elif len(measure_code_id) == 4:
                    measure_subcode_id = measure_code_id
                    measure_subcode_name = measure_code_name
                    measure_code_id = measure_code_id[:2]
                    measure_code_name = func.get_measure_code_name_from_id(measure_code_id, MEASURE_CODES)
                    if measure_code_name:
                        self.ui.comboBox_measure_code.setCurrentText(f"{measure_code_id} {measure_code_name}")
                    self.ui.comboBox_measure_subcode.setCurrentText(f"{measure_subcode_id} {measure_subcode_name}")

        self.ui.comboBox_status.setCurrentText(self.mi_dict[mi_id]['status'])
        self.ui.lineEdit_reestr.setText(self.mi_dict[mi_id]['reestr'])
        self.ui.plainTextEdit_title.setPlainText(self.mi_dict[mi_id]['title'])
        self.ui.plainTextEdit_type.setPlainText(self.mi_dict[mi_id]['type'])
        self.ui.lineEdit_modification.setText(self.mi_dict[mi_id]['modification'])
        self.ui.lineEdit_number.setText(self.mi_dict[mi_id]['number'])
        self.ui.lineEdit_inv_number.setText(self.mi_dict[mi_id]['inv_number'])
        self.ui.plainTextEdit_manufacturer.setPlainText(self.mi_dict[mi_id]['manufacturer'])
        self.ui.lineEdit_manuf_year.setText(self.mi_dict[mi_id]['manuf_year'])
        self.ui.lineEdit_expl_year.setText(self.mi_dict[mi_id]['expl_year'])
        self.ui.lineEdit_diapazon.setText(self.mi_dict[mi_id]['diapazon'])
        self.ui.lineEdit_PG.setText(self.mi_dict[mi_id]['PG'])
        self.ui.lineEdit_KT.setText(self.mi_dict[mi_id]['KT'])
        self.ui.plainTextEdit_other_characteristics.setPlainText(self.mi_dict[mi_id]['other_characteristics'])
        self.ui.lineEdit_MPI.setText(self.mi_dict[mi_id]['MPI'])
        self.ui.plainTextEdit_purpose.setPlainText(self.mi_dict[mi_id]['purpose'])
        self.ui.plainTextEdit_personal.setPlainText(self.mi_dict[mi_id]['personal'])
        self.ui.plainTextEdit_software_inner.setPlainText(self.mi_dict[mi_id]['software_inner'])
        self.ui.plainTextEdit_software_outer.setPlainText(self.mi_dict[mi_id]['software_outer'])
        self.ui.plainTextEdit_owner.setPlainText(self.mi_dict[mi_id]['owner'])
        self.ui.plainTextEdit_owner_contract.setPlainText(self.mi_dict[mi_id]['owner_contract'])

        if self.mi_dict[mi_id]['RE'] != "0":
            self.ui.checkBox_has_manual.setChecked(True)
        else:
            self.ui.checkBox_has_manual.setChecked(False)
        if self.mi_dict[mi_id]['pasport'] != "0":
            self.ui.checkBox_has_pasport.setChecked(True)
        else:
            self.ui.checkBox_has_pasport.setChecked(False)
        if self.mi_dict[mi_id]['MP'] != "0":
            self.ui.checkBox_has_verif_method.setChecked(True)
        else:
            self.ui.checkBox_has_verif_method.setChecked(False)
        self.ui.lineEdit_period_TO.setText(self.mi_dict[mi_id]['TO_period'])

        self._update_owner_info()

    # ---------------------------------------ОБНОВЛЕНИЕ ВКЛАДКИ О ПОВЕРКЕ----------------------------------------------
    def _update_vri_tab(self, vri_id=None):
        self._clear_vri_tab()
        # ЕСЛИ ПОВЕРКА СОХРАНЕНА
        if vri_id:
            mi_id = self.ui.lineEdit_mi_id.text()
            if mi_id and mi_id in self.mis_vri_dict and vri_id in self.mis_vri_dict[mi_id]:
                vri_dict = self.mis_vri_dict[mi_id][vri_id]
            else:
                return
        # ЕСЛИ ПОВЕРКА НЕ СОХРАНЕНА, НО ЕСТЬ ВО ВРЕМЕННОМ СЛОВАРЕ ПОВЕРОК
        else:
            row = self.ui.tableView_vri_list.currentIndex().row()
            cert_num = self.tbl_vri_proxy_model.index(row, 2).data()
            if self.temp_vri_dict and cert_num in self.temp_vri_dict:
                vri_dict = self.temp_vri_dict[cert_num]
            else:
                return
        self.ui.lineEdit_vri_id.setText(vri_id)
        self.ui.lineEdit_vri_FIF_id.setText(vri_dict['FIF_id'])
        self.ui.plainTextEdit_vri_organization.setPlainText(vri_dict['organization'])
        self.ui.lineEdit_vri_signCipher.setText(vri_dict['signCipher'])
        self.ui.plainTextEdit_vri_miOwner.setPlainText(vri_dict['miOwner'])
        self.ui.lineEdit_vrfDate.setText(vri_dict['vrfDate'])
        self.ui.lineEdit_vri_validDate.setText(vri_dict['validDate'])
        self.ui.comboBox_vri_vriType.setCurrentText(vri_dict['vriType'])
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
    def _update_mieta_tab(self, vri_id=None):
        self._clear_mieta_tab()
        if vri_id and vri_id in self.mietas_dict:
            self.ui.lineEdit_mieta_id.setText(self.mietas_dict[vri_id]['mieta_id'])
            self.ui.lineEdit_mieta_number.setText(self.mietas_dict[vri_id]['number'])
            self.ui.comboBox_mieta_rank.setCurrentText(self.mietas_dict[vri_id]['rankcode'])
            self.ui.lineEdit_mieta_rank_title.setText(self.mietas_dict[vri_id]['rankclass'])
            self.ui.lineEdit_mieta_npenumber.setText(self.mietas_dict[vri_id]['npenumber'])
            self.ui.lineEdit_mieta_schematype.setText(self.mietas_dict[vri_id]['schematype'])
            self.ui.plainTextEdit_mieta_schematitle.setPlainText(self.mietas_dict[vri_id]['schematitle'])
        elif self.temp_vri_dict:
            row = self.ui.tableView_vri_list.currentIndex().row()
            cert_num = self.tbl_vri_proxy_model.index(row, 2).data()
            # print(cert_num)
            if cert_num in self.temp_vri_dict:
                self.ui.lineEdit_mieta_number.setText(self.temp_vri_dict[cert_num]['regNumber'])
                self.ui.comboBox_mieta_rank.setCurrentText(self.temp_vri_dict[cert_num]['rankСоdе'])
                self.ui.lineEdit_mieta_rank_title.setText(self.temp_vri_dict[cert_num]['rankTitle'])
                self.ui.lineEdit_mieta_npenumber.setText(self.temp_vri_dict[cert_num]['npenumber'])
                self.ui.lineEdit_mieta_schematype.setText(self.temp_vri_dict[cert_num]['schematype'])
                self.ui.plainTextEdit_mieta_schematitle.setPlainText(self.temp_vri_dict[cert_num]['schemaTitle'])

    # --------------------------------ОБНОВЛЕНИЕ ПОЛЕЙ ОТДЕЛА, СОТРУДНИКОВ И КОМНАТ------------------------------------
    def _update_owner_info(self):
        mi_id = self.ui.lineEdit_mi_id.text()
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
                func.get_worker_fio_from_id(self.mi_dict[mi_id]['responsible_person'], self.workers['worker_dict']))

            self.ui.comboBox_room.setCurrentText(
                func.get_room_number_from_id(self.mi_dict[mi_id]['room'], self.rooms['room_dict']))

    # ------------------------------------------ОЧИСТКА ВСЕГО----------------------------------------------------------
    def _clear_all(self):
        # self.mis_vri_dict.clear()
        self.ui.pushButton_find_vri.hide()

        self.set_of_vri.clear()
        self.temp_vri_dict.clear()
        self.tbl_vri_model.clear()
        self._update_vri_table()

        self._clear_mi_tab()
        self._clear_mieta_tab()
        self._clear_vri_tab()

    # ---------------------------------ОЧИСТКА ВКЛАДКИ ОБОРУДОВАНИЯ----------------------------------------------------
    def _clear_mi_tab(self):

        # очищаем списки отделов, комнат и работников
        self.lv_dep_model.setStringList([])
        self.cb_worker_model.setStringList([])
        self.cb_room_model.setStringList([])

        self.ui.lineEdit_mi_id.setText("")
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

        # self._appearance_init()

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
        # self.temp_vri_dict.clear()
        self.ui.lineEdit_vri_id.setText("")
        self.ui.lineEdit_vri_FIF_id.setText("")
        self.ui.plainTextEdit_vri_organization.setPlainText("")
        self.ui.plainTextEdit_vri_miOwner.setPlainText("")
        self.ui.lineEdit_vrfDate.setText("")
        self.ui.lineEdit_vri_validDate.setText("")
        self.ui.comboBox_vri_vriType.setCurrentIndex(0)
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
        # todo добавить удаление ответственного и комнаты при удалении отдела

        if not self.ui.lineEdit_reg_card_number.text():
            QMessageBox.warning(self, "Ошибка сохранения", "Необходимо ввести номер регистрационной карточки")
            return

        mi_id = self.ui.lineEdit_mi_id.text()
        if not mi_id:
            mi_id = "NULL"

        reg_card_number = self.ui.lineEdit_reg_card_number.text()

        if mi_id != "NULL" and self.mi_dict[mi_id][
            'reg_card_number'] != reg_card_number and reg_card_number in self.list_of_card_numbers:
            QMessageBox.critical(self, "Ошибка", "Данный номер регистрационной карточки принадлежит другому прибору.\n"
                                                 "Сохранение невозможно")
            return

        measure_code_id = self._get_measure_code_id()
        resp_person_id = func.get_worker_id_from_fio(self.ui.comboBox_responsiblePerson.currentText(),
                                                     self.workers['worker_dict'])
        room_id = func.get_room_id_from_number(self.ui.comboBox_room.currentText(), self.rooms['room_dict'])

        sql_replace = f"REPLACE INTO mis VALUES (" \
                      f"{mi_id}, " \
                      f"'{self.ui.lineEdit_reg_card_number.text()}', " \
                      f"{measure_code_id}, " \
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
                             f"'{self.temp_vri_dict[cert_num]['info']}', " \
                             f"'{self.temp_vri_dict[cert_num]['FIF_id']}');"
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
                          f"'{self.ui.comboBox_vri_vriType.currentText()}', " \
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
                          f"'', " \
                          f"'{self.ui.lineEdit_vri_FIF_id.text()}');"
            MySQLConnection.execute_query(connection, sql_replace)

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

        self._clear_all()
        self._create_dicts()

        self._update_mi_table()
        self._update_mi_tab(mi_id)

        row = self.tbl_mi_model.indexFromItem(self.tbl_mi_model.findItems(mi_id, column=5)[0]).row()
        index = self.tbl_mi_model.index(row, 0)
        self.ui.tableView_mi_list.setCurrentIndex(index)
        self.ui.tableView_mi_list.scrollTo(index)

        QMessageBox.information(self, "Сохранено", "Информация сохранена")

    # ------------------------------------КЛИК ПО КНОПКЕ "СОХРАНИТЬ ИНФОРМАЦИЮ"----------------------------------------
    def _on_save_mi_info(self):

        reg_card_number = self.ui.lineEdit_reg_card_number.text()
        if not reg_card_number:
            QMessageBox.warning(self, "Ошибка сохранения", "Необходимо ввести номер регистрационной карточки")
            return

        mi_id = self.ui.lineEdit_mi_id.text()
        if not mi_id:
            mi_id = "NULL"

        if mi_id != "NULL" and self.mi_dict[mi_id][
            'reg_card_number'] != reg_card_number and reg_card_number in self.list_of_card_numbers:
            QMessageBox.critical(self, "Ошибка", "Данный номер регистрационной карточки принадлежит другому прибору.\n"
                                                 "Сохранение невозможно")
            return

        measure_code_id = self._get_measure_code_id()

        resp_person_id = func.get_worker_id_from_fio(self.ui.comboBox_responsiblePerson.currentText(),
                                                     self.workers['worker_dict'])
        room_id = func.get_room_id_from_number(self.ui.comboBox_room.currentText(), self.rooms['room_dict'])

        sql_replace = f"REPLACE INTO mis VALUES (" \
                      f"{mi_id}, " \
                      f"'{self.ui.lineEdit_reg_card_number.text()}', " \
                      f"{measure_code_id}, " \
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

        self.mi_dict = func.get_mis()['mi_dict']
        self.set_of_mi = func.get_mis()['set_of_mi']
        self.mi_deps = func.get_mi_deps()['mi_deps_dict']
        self.list_of_card_numbers = func.get_mis()['list_of_card_numbers']
        self._update_mi_table()
        row = self.tbl_mi_model.indexFromItem(self.tbl_mi_model.findItems(mi_id, column=5)[0]).row()
        index = self.tbl_mi_model.index(row, 0)
        self.ui.tableView_mi_list.setCurrentIndex(index)
        self.ui.tableView_mi_list.scrollTo(index)
        self._on_mi_select(index)
        QMessageBox.information(self, "Сохранено", "Информация сохранена")

    # -------------------------------------КЛИК ПО КНОПКЕ "СОХРАНИТЬ ПОВЕРКУ"------------------------------------------
    def _on_save_vri(self):

        mi_id = self.ui.lineEdit_mi_id.text()
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
            valid_date = self.ui.lineEdit_vri_validDate.text()
        else:
            applicable = 0
            cert_num = self.ui.lineEdit_vri_noticeNum.text()
            valid_date = ""

        if self.ui.checkBox_vri_briefIndicator.isChecked():
            briefIndicator = 1

        sql_replace = f"REPLACE INTO mis_vri_info VALUES (" \
                      f"{vri_id}, " \
                      f"{int(mi_id)}, " \
                      f"'{self.ui.plainTextEdit_vri_organization.toPlainText()}', " \
                      f"'{self.ui.lineEdit_vri_signCipher.text()}', " \
                      f"'{self.ui.plainTextEdit_vri_miOwner.toPlainText()}', " \
                      f"'{self.ui.lineEdit_vrfDate.text()}', " \
                      f"'{valid_date}', " \
                      f"'{self.ui.comboBox_vri_vriType.currentText()}', " \
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
                      f"'', " \
                      f"'{self.ui.lineEdit_vri_FIF_id.text()}');"
        MySQLConnection.verify_connection()
        connection = MySQLConnection.create_connection()
        result = MySQLConnection.execute_query(connection, sql_replace)
        connection.close()
        if result[0]:
            vri_id = str(result[1])
            self.mis_vri_dict = func.get_mis_vri_info()['mis_vri_dict']
            # ЕСЛИ ЭТАЛОН НЕ СОХРАНЕН, НО ЕСТЬ НОМЕР ЭТАЛОНА, СОХРАНЯЕМ ЕГО И ОБНОВЛЯЕМ ТАБЛИЦУ ПОВЕРОК
            if not self.ui.lineEdit_mieta_id.text() and self.ui.lineEdit_mieta_number.text():
                self._on_save_mieta(vri_id=vri_id)
            # ИНАЧЕ ОБНОВЛЯЕМ ТАБЛИЦУ ПОВЕРОК
            else:
                self._update_vri_table(mi_id)
            self._update_vri_tab(vri_id)
        QMessageBox.information(self, "Сохранено", "Информация о поверке сохранена")

    # ---------------------------------------КЛИК ПО КНОПКЕ "СОХРАНИТЬ ЭТАЛОН"-----------------------------------------
    def _on_save_mieta(self, mi_id="", vri_id=""):
        if not mi_id:  # если не передано mi_id, то берем с экрана
            mi_id = self.ui.lineEdit_mi_id.text()
        if not vri_id:  # если не передано vri_id, то берем с экрана
            vri_id = self.ui.lineEdit_vri_id.text()
        if not mi_id or not vri_id:  # если и на экране пусто - ошибка
            QMessageBox.critical(self, "Ошибка", "Сначала выполните сохранение оборудования и (или) поверки")
            return
        if not self.ui.lineEdit_mieta_number.text():  # если отсутствует номер эталона - ошибка
            QMessageBox.critical(self, "Ошибка", "Не указан номер в реестре эталонов")
            return

        mieta_id = self.ui.lineEdit_mieta_id.text()
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
        self._update_vri_table(mi_id)
        self._update_mieta_tab(vri_id)

        QMessageBox.information(self, "Сохранено", "Информация об эталоне сохранена")

    # -------------------------------------КЛИК ПО КНОПКЕ "УДАЛИТЬ ОБОРУДОВАНИЕ"---------------------------------------
    def _on_delete_mi(self):
        mi_id = self.ui.lineEdit_mi_id.text()
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

                self._create_dicts()

                self._update_mi_table()
                self._update_vri_table()
                self._clear_all()

    # -----------------------------------------КЛИК ПО КНОПКЕ "УДАЛИТЬ ПОВЕРКУ-"---------------------------------------
    def _on_delete_vri(self):
        vri_id = self.ui.lineEdit_vri_id.text()
        mi_id = self.ui.lineEdit_mi_id.text()
        if vri_id and mi_id:
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Подтверждение удаления")
            dialog.setText(f"Вы действительно хотите удалить поверку?\n"
                           f"Также удалится вся информация об эталоне.")
            dialog.setIcon(QMessageBox.Warning)
            btn_yes = QPushButton("&Да")
            btn_no = QPushButton("&Нет")
            dialog.addButton(btn_yes, QMessageBox.AcceptRole)
            dialog.addButton(btn_no, QMessageBox.RejectRole)
            dialog.setDefaultButton(btn_no)
            dialog.setEscapeButton(btn_no)
            result = dialog.exec()
            if result == 0:
                sql_delete_1 = f"DELETE FROM mis_vri_info WHERE vri_id = {int(vri_id)}"
                sql_delete_2 = f"DELETE FROM mietas WHERE mieta_vri_id = {int(vri_id)}"
                MySQLConnection.verify_connection()
                connection = MySQLConnection.create_connection()
                MySQLConnection.execute_transaction_query(connection, sql_delete_1, sql_delete_2)
                connection.close()

                self.mietas_dict = func.get_mietas()['mietas_dict']
                self.mis_vri_dict = func.get_mis_vri_info()['mis_vri_dict']

                self._update_vri_table(mi_id)
                if self.tbl_vri_proxy_model.rowCount() > 0:
                    vri_id = self.tbl_vri_proxy_model.index(0, 6).data()
                    if vri_id:
                        self._update_vri_tab(vri_id)
                        self._update_mieta_tab(vri_id)
                        self.ui.tableView_vri_list.selectRow(0)
                        # self.ui.tableView_vri_list.scrollTo()
                else:
                    self._clear_vri_tab()
                    self._clear_mieta_tab()

    # -------------------------------------КЛИК ПО КНОПКЕ "НАЙТИ ПОВЕРКИ"----------------------------------------------
    def _on_find_vri(self):
        mi_id = self.ui.lineEdit_mi_id.text()
        if not mi_id:
            return
        reestr_number = self.ui.lineEdit_reestr.text()
        manuf_number = self.ui.lineEdit_number.text()
        if reestr_number and manuf_number:
            self.get_type = "find_vri"
            url = f"{URL_START}/vri?year=2020&rows=100&search={reestr_number}%20{manuf_number}"
            self.search_thread.url = url
            self.search_thread.start()

    # --------------------------------ОТВЕТ НА КЛИК ПО КНОПКЕ "НАЙТИ ПОВЕРКИ"------------------------------------------
    def _on_find_vri_resp(self):
        if 'result' in self.resp_json and 'count' in self.resp_json['result']:
            if self.resp_json['result']['count'] > 0:
                for item in self.resp_json['result']['items']:
                    if str(item['vri_id']).startswith("1-"):
                        self.temp_set_of_vri_id.add(str(item['vri_id']))
        self.eq_type = "vri_id"
        self.get_type = "vri_id"
        self.number = self.temp_set_of_vri_id.pop()
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
        url = f"{URL_START}/vri/{self.number}"
        self.search_thread.url = url
        self.search_thread.start()

    # -------------------------------------КЛИК ПО КНОПКЕ "ДОБАВИТЬ ОТДЕЛ"---------------------------------------------
    def _on_add_dep(self):
        cur_dep_list = self.lv_dep_model.stringList()
        full_dep_list = self.departments['dep_name_list']
        choose_list = sorted(list(set(full_dep_list) - set(cur_dep_list)))
        mi_id = self.ui.lineEdit_mi_id.text()
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
                        func.get_worker_fio_from_id(self.mi_dict[mi_id]['responsible_person'],
                                                    self.workers['worker_dict']))
                    self.ui.comboBox_room.setCurrentText(
                        func.get_room_number_from_id(self.mi_dict[mi_id]['room'], self.rooms['room_dict']))
        else:
            QMessageBox.information(self, "Выбора нет", "Все подразделения включены в список")

    # ----------------------------------КЛИК ПО КНОПКЕ "УДАЛИТЬ ОТДЕЛ"-------------------------------------------------
    def _on_remove_dep(self):

        if not self.ui.listView_departments.selectedIndexes():
            return
        dep_name = self.ui.listView_departments.currentIndex().data()
        cur_dep_list = self.lv_dep_model.stringList()
        cur_dep_list.remove(dep_name)
        mi_id = self.ui.lineEdit_mi_id.text()

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
                func.get_worker_fio_from_id(self.mi_dict[mi_id]['responsible_person'],
                                            self.workers['worker_dict']))
            self.ui.comboBox_room.setCurrentText(
                func.get_room_number_from_id(self.mi_dict[mi_id]['room'], self.rooms['room_dict']))

    # -------------------НАЖАТИЕ КНОПКИ ДОБАВИТЬ ПОВЕРКУ ИЗ АРШИНА-----------------------------------------------------
    def _on_add_vri(self):
        dialog = QInputDialog()
        dialog.setInputMode(QInputDialog.TextInput)
        dialog.setWindowTitle("Поиск поверки в ФГИС \"Аршин\"")
        dialog.setLabelText("Введите один из номеров:\n"
                            "- номер записи сведений в ФИФ (1-32165498 или 32165498);\n"
                            "- номер свидетельства формата 2021 года (С-КС/05-05-2021/32165498);\n"
                            "- номер в перечне СИ, применяемых в качестве эталона (36438.07.РЭ.00164658).")
        dialog.textValueChanged.connect(lambda: self._input_verify_vri(dialog))
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
            if self.eq_type == "vri":
                self._update_progressbar(0, "Поиск по номеру свидетельства")
            elif self.eq_type == "mieta":
                self._update_progressbar(0, "Поиск по номеру эталона")
            elif self.eq_type == "vri_id":
                self._update_progressbar(0, "Поиск по номеру записи")

            self.search_thread.is_running = True

            if self.eq_type == "vri_id":
                if "-" not in self.number:
                    self.number = f"1-{self.number}"
                url = f"{URL_START}/vri/{self.number}"
                self.search_thread.url = url
                self.search_thread.start()
            elif self.eq_type == "vri":
                self.eq_type = "vri_id"
                self.number = self.number.rsplit("/", 1)[1]
                url = f"{URL_START}/vri/1-{self.number}"
                self.search_thread.url = url
                self.search_thread.start()
            else:
                url = f"{URL_START}/{self.eq_type}?rows=100&search={self.number}"
                self.search_thread.url = url
                self.search_thread.start()

    # -------------------НАЖАТИЕ КНОПКИ ПОИСКА ОБОРУДОВАНИЯ ИЗ АРШИНА--------------------------------------------------
    def _on_start_search(self):
        self._clear_all()
        self.ui.tableView_mi_list.selectionModel().clearSelection()
        # self.mit_search.clear()
        # self.mit.clear()
        # self.vri_search.clear()
        # self.vri.clear()
        # self.mieta_search.clear()
        # self.mieta.clear()
        # self.temp_set_of_vri_id.clear()

        dialog = QInputDialog()
        dialog.setInputMode(QInputDialog.TextInput)
        dialog.setWindowTitle("Поиск оборудования в ФГИС \"Аршин\"")
        dialog.setLabelText("Введите один из номеров:\n"
                            "- номер в реестре (19775-00);\n"
                            "- номер эталона единиц величин;\n"
                            "- номер в перечне СИ, применяемых в качестве эталона (36438.07.РЭ.00164658);\n"
                            "- номер свидетельства формата 2021 года (С-КС/05-05-2021/32165498);\n"
                            "- номер записи сведений в ФИФ (1-32165498 или 32165498).")
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
            print("connected")
            self.dialog.canceled.connect(self._on_search_stopped)
            self.dialog.setRange(0, 100)
            self.dialog.setWindowModality(Qt.WindowModal)
            self.dialog.resize(350, 100)
            self.dialog.show()
            if self.eq_type == "mit":
                print("start dialog")
                self._update_progressbar(0, "Поиск номера реестра")
            elif self.eq_type == "mieta":
                self._update_progressbar(0, "Поиск номера в перечне СИ, применяемых в качестве эталонов")
            elif self.eq_type == "vri_id":
                self._update_progressbar(0, "Получение данных из свидетельства")

            self.search_thread.is_running = True

            # ЕСЛИ ИЩЕМ ПО НОМЕРУ ПОВЕРКИ
            if self.eq_type == "vri_id":
                if "/" not in self.number:
                    if "1-" not in self.number:
                        self.number = f"1-{self.number}"
                else:
                    self.number = f"1-{self.number.rsplit('/', 1)[1]}"
                self.search_thread.url = f"{URL_START}/vri/{self.number}"

            # ЕСЛИ ИЩЕМ ПО НОМЕРУ ЭТАЛОНА
            elif self.eq_type == "mieta":
                self.number = self.number.rsplit('.', 1)[1]
                self.search_thread.url = f"{URL_START}/mieta/{self.number}"

            # ЕСЛИ ИЩЕМ ПО НОМЕРУ В РЕЕСТРЕ
            elif self.eq_type == "mit":
                self.search_thread.url = f"{URL_START}/{self.eq_type}?rows=100&search={self.number}"

            # ЗАПУСКАЕМ ПОИСК
            self.search_thread.start()

    # --------------------------------ПРОВЕРКА ВВОДА НОМЕРА ДЛЯ ПОИСКА ПОВЕРКИ-----------------------------------------
    def _input_verify_vri(self, dialog):
        self.eq_type = ""
        self.get_type = ""
        if not dialog.textValue():
            dialog.setLabelText("Введите один из номеров:\n"
                                "- номер записи сведений в ФИФ (1-32165498 или 32165498);\n"
                                "- номер свидетельства формата 2021 года (С-КС/05-05-2021/32165498);\n"
                                "- номер в перечне СИ, применяемых в качестве эталона (36438.07.РЭ.00164658).")
            return
        rx_vri_id = QRegExp("^([1-2]\-)*\d{1,15}\s*$")
        rx_svid = QRegExp("^(С|И)\-\S{1,3}\/[0-3][0-9]\-[0-1][0-9]\-20[2-5][0-9]\/\d{8,10}$")
        rx_mieta = QRegExp("^[1-9]\d{0,5}\.\d{2}\.(0Р|1Р|2Р|3Р|4Р|5Р|РЭ|ВЭ|СИ)\.\d+\s*$")
        rx_vri_id.setCaseSensitivity(False)
        rx_svid.setCaseSensitivity(False)
        rx_mieta.setCaseSensitivity(False)
        if rx_mieta.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер в перечне СИ, применяемых в качестве эталонов")
            self.eq_type = "mieta"
            self.get_type = "vri"
        elif rx_svid.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер свидетельства о поверке")
            self.eq_type = "vri"
            self.get_type = "vri"
        elif rx_vri_id.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер записи сведений в ФИФ ОЕИ")
            self.eq_type = "vri_id"
            self.get_type = "vri"
        else:
            dialog.setLabelText("Введенный номер не определяется. Проверьте правильность ввода")

    # --------------------------------ПРОВЕРКА ВВОДА НОМЕРА ДЛЯ ПОИСКА ОБОРУДОВАНИЯ------------------------------------
    def _input_verify(self, dialog):
        self.eq_type = ""
        self.get_type = ""
        if not dialog.textValue():
            dialog.setLabelText("Введите один из номеров:\n"
                                "- номер в реестре (19775-00);\n"
                                "- номер эталона единиц величин;\n"
                                "- номер в перечне СИ, применяемых в качестве эталона (36438.07.РЭ.00164658);\n"
                                "- номер свидетельства формата 2021 года (С-КС/05-05-2021/32165498);\n"
                                "- номер записи сведений в ФИФ (1-32165498 или 32165498).")
            return
        rx_mit = QRegExp("^[1-9][0-9]{0,5}-[0-9]{2}$")
        rx_npe = QRegExp("^гэт[1-9][0-9]{0,2}-(([0-9]{2})|([0-9]{4}))$")
        rx_uve = QRegExp("^[1-3]\.[0-9]\.\S{3}\.\d{4}\.20[0-4]\d$")
        rx_mieta = QRegExp("^[1-9]\d{0,5}\.\d{2}\.(0Р|1Р|2Р|3Р|4Р|5Р|РЭ|ВЭ|СИ)\.\d+\s*$")
        rx_svid = QRegExp("^(С|И)\-\S{1,3}\/[0-3][0-9]\-[0-1][0-9]\-20[2-5][0-9]\/\d{8,10}$")
        rx_vri_id = QRegExp("^([1-2]\-)*\d{1,15}\s*$")
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
            self.eq_type = "vri_id"
        elif rx_vri_id.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер записи сведений в ФИФ ОЕИ")
            self.eq_type = "vri_id"
        else:
            dialog.setLabelText("Введенный номер не определяется. Проверьте правильность ввода")

    # --------------------------------------ОБРАБОТКА ПОЛУЧЕННОГО ОТВЕТА ОТ СЕРВЕРА------------------------------------
    def _on_getting_resp(self, resp):
        if not resp or resp.startswith("Error") or resp.startswith("<!DOCTYPE html>"):
            QMessageBox.critical(self, "Ошибка", f"Возникла ошибка получения сведений из ФГИС \"АРШИН\".\n{resp}")
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
                # ЕСЛИ ИЩЕМ ПОВЕРКИ ПО НОМЕРУ В РЕЕСТРЕ И ЗАВОДСКОМУ НОМЕРУ
                if self.get_type == "find_vri":
                    self._on_find_vri_resp()
                    return
                # ЕСЛИ ДОБАВЛЯЕМ ОБОРУДОВАНИЕ
                if self.get_type != "vri":
                    if self.get_type == "find_vri_info":
                        self.vri = self.resp_json
                        self._get_vri_info()
                    elif "mit?" in self.search_thread.url:
                        self.mit_search = self.resp_json
                        self._get_mit_search()
                    elif "mit/" in self.search_thread.url:
                        self.mit = self.resp_json
                        self._get_mit()
                    elif "vri?" in self.search_thread.url:
                        self.vri_search = self.resp_json
                        self._get_vri_search()
                    elif "vri/" in self.search_thread.url:
                        self.vri = self.resp_json
                        self._get_vri()
                    elif "mieta?" in self.search_thread.url:
                        self.mieta_search = self.resp_json
                        self._get_mieta_search()
                    elif "mieta/" in self.search_thread.url:
                        self.mieta = self.resp_json
                        self._get_mieta()
                    else:
                        self.dialog.close()
                # ЕСЛИ ДОБАВЛЯЕМ РЕЗУЛЬТАТЫ ПОВЕРКИ
                else:
                    if self.eq_type == "vri_id":
                        self.vri = self.resp_json
                        self._get_vri_info()
                    elif "vri" in self.search_thread.url:
                        self._get_vri()
                    elif "mieta" in self.search_thread.url:
                        self._get_mieta()
                    else:
                        self.dialog.close()

    # ------------------------------------------ОБРАБОТКА MIT_SEARCH---------------------------------------------------
    def _get_mit_search(self):

        if 'result' in self.resp_json and 'count' in self.resp_json['result']:
            result = self.resp_json['result']

            # если ищем по номеру в реестре
            if self.eq_type == "mit":
                # если результаты не найдены
                if result['count'] == 0:
                    self._on_search_stopped()
                    QMessageBox.critical(self, "Ошибка",
                                         f"Очевидно, вы пытались ввести номер реестра СИ, но ФГИС "
                                         f"\"АРШИН\" не содержит такой записи.\n"
                                         f"Проверьте правильность введенного номера")
                    return
                # если найдена одна запись
                elif result['count'] == 1:
                    if 'items' in result and 'mit_id' in result['items'][0]:
                        mit_id = result['items'][0]['mit_id']
                        self._update_progressbar(50, "Поиск информации в реестре утвержденных типов СИ")
                        self.search_thread.url = f"{URL_START}/mit/{mit_id}"
                        self.search_thread.start()
                # если найдено от 2 до 50 записей, создаем список и даем диалог выбора подходящего реестра
                elif result['count'] < 50:
                    items_list = list()
                    if 'items' in result:
                        for item in result['items']:
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
                        self._update_progressbar(50, "Поиск информации в реестре утвержденных типов СИ")
                        url = f"{URL_START}/mit/{result['items'][items_list.index(s)]['mit_id']}"
                        self.search_thread.url = url
                        self.search_thread.start()
                    else:
                        self._on_search_stopped()
                        return
                # если результатов больше 50
                else:
                    self._on_search_stopped()
                    QMessageBox.critical(self, "Ошибка", "Слишком много результатов поиска. Уточните номер")
                    return

            # если ищем по номеру эталона или поверки
            elif self.eq_type == "mieta" or self.eq_type == "vri_id":
                # если результаты не найдены
                if result['count'] == 0:
                    self._on_search_stopped()
                    QMessageBox.critical(self, "Ошибка", f"Невозможно найти номер в реестре")
                    return
                # если результаты найдены, берем id первой записи и ищем реестр
                else:
                    self._update_progressbar(50, "Поиск информации в реестре утвержденных типов СИ")
                    if 'items' in result and 'mit_id' in result['items'][0]:
                        self.search_thread.url = f"{URL_START}/mit/{result['items'][0]['mit_id']}"
                        self.search_thread.start()
                    else:
                        self.dialog.close()
        else:
            self._on_search_stopped()
            return

    # -------------------------------------------ОБРАБОТКА MIT---------------------------------------------------------
    def _get_mit(self):

        self._fill_mi_info()

        # если ищем по номеру в реестре
        if self.eq_type == "mit":
            # КОНЕЦ ПОИСКА
            self._on_search_finished()

        # если ищем по номеру эталона или поверки
        elif self.eq_type == "mieta" or self.eq_type == "vri_id":
            self._update_progressbar(75, "Поиск информации о поверках")
            self.vri.clear()
            self._get_vri_info()

    # -------------------------------------------ОБРАБОТКА VRI_SEARCH--------------------------------------------------
    def _get_vri_search(self):

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
                    self.number = self.resp_json['result']['items'][0]['vri_id']
                    self.search_thread.url = f"{URL_START}/vri/{self.number}"
                    self.search_thread.start()
                else:
                    self.dialog.close()
            else:
                QMessageBox.critical(self, "Ошибка", "Слишком много результатов поиска. Уточните номер свидетельства")
                self.dialog.close()
                return
        else:
            self._on_search_stopped()
            return

    # -----------------------------------------------ОБРАБОТКА VRI-----------------------------------------------------
    def _get_vri(self):
        if 'result' in self.resp_json and 'miInfo' in self.resp_json['result']:
            miInfo = self.resp_json['result']['miInfo']
        else:
            self._on_search_stopped()
            return

        mitypeNumber = mitypeTitle = ""

        # ЕСЛИ ИЩЕМ ПО НОМЕРУ ЭТАЛОНА
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

        # ЕСЛИ ИЩЕМ ПО НОМЕРУ ПОВЕРКИ
        elif self.eq_type == "vri_id":

            # ЕСЛИ ЭТО ОКАЗАЛСЯ ЭТАЛОН
            if 'etaMI' in miInfo:
                miInfo = miInfo['etaMI']
                if 'regNumber' in miInfo:
                    regNumber = miInfo['regNumber'].rsplit('.', 1)[1]
                    self._update_progressbar(20, "Поиск номера эталона")
                    self.search_thread.url = f"{URL_START}/mieta/{regNumber}"
                    self.search_thread.start()

            # ЕСЛИ ЭТО ОБЫЧНОЕ СИ ИЛИ ПАРТИЯ, ЗАПУСКАЕМ ПОИСК В РЕЕСТРЕ ПО НОМЕРУ В РЕЕСТРЕ И НАИМЕНОВАНИЮ
            elif 'singleMI' in miInfo or self.eq_type == "mieta" or 'partyMI' in miInfo:

                # ДОБАВЛЯЕМ ID ПОВЕРКИ ВО ВРЕМЕННОЕ МНОЖЕСТВО
                self.temp_set_of_vri_id.add(self.number)

                # ПОЛУЧАЕМ НОМЕР В РЕЕСТРЕ И НАИМЕНОВАНИЕ
                if 'singleMI' in miInfo:
                    miInfo = miInfo['singleMI']
                elif 'partyMI' in miInfo:
                    miInfo = miInfo['partyMI']
                if 'mitypeNumber' in miInfo:  # номер реестра
                    mitypeNumber = miInfo['mitypeNumber']
                if 'mitypeTitle' in miInfo:  # наименование
                    mitypeTitle = miInfo['mitypeTitle']

                # ЕСЛИ СИ В РЕЕСТРЕ, ЗАПУСКАЕМ ПОИСК В РЕЕСТРЕ
                if mitypeNumber and mitypeTitle:
                    self._update_progressbar(25, "Поиск номера в реестре утвержденных типов СИ")
                    url = f"{URL_START}/mit?rows=100&search={mitypeNumber}%20{mitypeTitle.replace(' ', '%20')}"
                    self.search_thread.url = url
                    self.search_thread.start()
                # ЕСЛИ СИ НЕ В РЕЕСТРЕ, ПЕРЕХОДИМ К ЗАПОЛНЕНИЮ ПОВЕРОК
                else:
                    self._fill_mi_info()
                    self._update_progressbar(50, "Поиск информации о поверках")
                    self.vri.clear()
                    self._get_vri_info()

    # --------------------------------ЗАПОЛНЕНИЕ ПОЛЕЙ ВКЛАДКИ ОБЩЕЙ ИНФОРМАЦИЕЙ---------------------------------------
    def _fill_mi_info(self):
        mi_dict = get_mi_dict(mit_resp=self.mit, vri_resp=self.vri, mieta_resp=self.mieta)
        if self.mieta:
            self.ui.comboBox_status.setCurrentText("СИ в качестве эталона")
        self.ui.lineEdit_reestr.setText(mi_dict['number'])
        self.ui.plainTextEdit_title.setPlainText(mi_dict['title'])
        self.ui.plainTextEdit_type.setPlainText(mi_dict['notation'])
        self.ui.plainTextEdit_manufacturer.setPlainText(mi_dict['manufacturer'])
        self.ui.lineEdit_MPI.setText(mi_dict['MPI'])
        if mi_dict['hasMPI']:
            self.ui.radioButton_MPI_yes.setChecked(False)
        else:
            self.ui.radioButton_MPI_no.setChecked(True)
        self.ui.lineEdit_number.setText(mi_dict['manufactureNum'])
        self.ui.lineEdit_inv_number.setText(mi_dict['inventoryNum'])
        self.ui.lineEdit_manuf_year.setText(mi_dict['manufactureYear'])
        self.ui.lineEdit_modification.setText(mi_dict['modification'])
        self.ui.plainTextEdit_other_characteristics.setPlainText(mi_dict['quantity'])
        self.ui.plainTextEdit_owner.setPlainText(ORG_NAME)

    # ---------------------------------ПОЛУЧЕНИЕ ИНФОРМАЦИИ ОБ ЭТАЛОНЕ ИЗ АРШИНА---------------------------------------
    def _get_mieta_search(self):

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
                    self.search_thread.url = f"{URL_START}/mieta/{mieta_id}"
                    self.search_thread.start()
            else:
                self.dialog.close()
                QMessageBox.critical(self, "Ошибка", "Слишком много результатов поиска. Уточните номер эталона")
                return

    # -----------------------------------------------ОБРАБОТКА MIETA---------------------------------------------------
    def _get_mieta(self):

        if 'result' in self.resp_json:
            result = self.resp_json['result']

            #   ДОБАВЛЯЕМ ID ПОВЕРОК В МНОЖЕСТВО
            for cresult in result['cresults']:
                if 'vri_id' in cresult:
                    self.temp_set_of_vri_id.add(cresult['vri_id'])

            #   ЕСЛИ ИЩЕМ ПОВЕРКУ ПО НОМЕРУ ПОВЕРКИ, БЕРЕМ ID ПОВЕРКИ
            if self.get_type == "vri":
                self.eq_type = "vri_id"
                self.number = result['cresults'][0]['vri_id']
                self.search_thread.url = f"{URL_START}/vri/{self.number}"
                self.search_thread.start()
                return

            #   ЕСЛИ ИЩЕМ ОБОРУДОВАНИЕ ПО НОМЕРУ ПОВЕРКИ, БЕРЕМ НОМЕР В РЕЕСТРЕ И ПЕРЕХОДИМ К ПОИСКУ РЕЕСТРА
            if self.eq_type == "vri_id":
                if 'mitype_num' in result and 'mitype' in result:  # номер реестра и наименование СИ
                    self._update_progressbar(40, "Поиск номера в реестре утвержденных типов СИ")
                    url = f"{URL_START}/mit?rows=100&search={result['mitype_num']}%20{result['mitype'].replace(' ', '%20')}"
                    self.search_thread.url = url
                    self.search_thread.start()
                else:
                    self._fill_mi_info()
                    self._get_vri_info()

            #   ЕСЛИ ИЩЕМ ОБОРУДОВАНИЕ КАК ЭТАЛОН, ЗАПУСКАЕМ ПОИСК В РЕЕСТРЕ
            elif self.eq_type == "mieta":
                mitypeNumber = mitypeTitle = ""
                if 'mitype_num' in result:  # номер реестра
                    mitypeNumber = result['mitype_num']
                if 'mitype' in result:  # наименование
                    mitypeTitle = result['mitype']

                if mitypeNumber and mitypeTitle:
                    self._update_progressbar(25, "Поиск номера в реестре утвержденных типов СИ")
                    url = f"{URL_START}/mit?rows=100&search={mitypeNumber}%20{mitypeTitle.replace(' ', '%20')}"
                    self.search_thread.url = url
                    self.search_thread.start()
                else:
                    self._on_search_stopped()
                    return
        else:
            self._on_search_stopped()
            return

    # ---------------------------------ПОЛУЧЕНИЕ ИНФОРМАЦИИ О ПОВЕРКАХ ИЗ АРШИНА---------------------------------------
    def _get_vri_info(self):
        # self.number = ""
        self.get_type = "find_vri_info"
        if not self.vri:
            if self.temp_set_of_vri_id:
                self.number = self.temp_set_of_vri_id.pop()
                self.search_thread.url = f"{URL_START}/vri/{self.number}"
                self.search_thread.start()
                return
            else:
                # self._update_vri_table()
                # index = self.tbl_vri_proxy_model.mapFromSource(self.tbl_vri_model.index(0, 2))
                index = self.tbl_vri_proxy_model.index(0, 2)
                self.ui.tableView_vri_list.setCurrentIndex(index)
                self.ui.tableView_vri_list.scrollTo(index)
                self._on_vri_select(index)
                self._on_search_finished()
                return

        resp = get_temp_vri_dict(self.vri, self.mieta)
        result = resp[0]
        cert_number = resp[1]
        if cert_number:
            self.temp_vri_dict[cert_number] = resp[2]
            self.temp_vri_dict[cert_number]['FIF_id'] = self.number

            # формируем колонку "эталон"
            rankTitle = self.temp_vri_dict[cert_number]['rankTitle']
            regNumber = self.temp_vri_dict[cert_number]['regNumber']
            if rankTitle and regNumber:
                vri_mieta = f"{regNumber}: {rankTitle.lower()}"
            else:
                vri_mieta = "нет"
            # self.mieta.clear()

            # проверяем есть ли уже такая поверка в таблице
            # cur_vri_tuple = (self.temp_vri_dict[cert_number]['vrfDate'], cert_number, regNumber)
            # if self.number in self.set_of_vri_id:
            #     QMessageBox.information(self, "Ошибка", "Данная поверка уже добавлена")
            # else:
            row = list()
            row.append(QStandardItem(self.temp_vri_dict[cert_number]['vrfDate']))
            row.append(QStandardItem(self.temp_vri_dict[cert_number]['validDate']))
            row.append(QStandardItem(self.temp_vri_dict[cert_number]['certNum']))
            row.append(QStandardItem(result))
            row.append(QStandardItem(self.temp_vri_dict[cert_number]['organization']))
            row.append(QStandardItem(vri_mieta))
            row.append(QStandardItem(""))
            self.tbl_vri_model.appendRow(row)
        self.vri.clear()
        self._get_vri_info()

        # # ЕСЛИ ИЩЕМ ПО НОМЕРУ ЭТАЛОНА, ТО УДАЛЯЕМ ПЕРВУЮ ПОВЕРКУ И ИЩЕМ СЛЕДУЮЩУЮ
        # if self.eq_type == "mieta":
        #     if len(self.temp_set_of_vri_id) > 0:
        #         if QMessageBox.question(self, "Найдена поверка",
        #                                 f"Найдена еще одна поверка. Хотите добавить информацию о ней?") == 65536:
        #             self._on_search_finished()
        #             return
        #         self._update_progressbar(95, "Поиск информации о поверках")
        #         self.number = self.temp_set_of_vri_id.pop()
        #         url = f"{URL_START}/vri/{self.number}"
        #         self.search_thread.url = url
        #         self.search_thread.start()
        #         return
        # else:
        #     # ЕСЛИ ИЩЕМ ПО НОМЕРУ СВИДЕТЕЛЬСТВА И ОДНА ПОВЕРКА, ОЧИЩАЕМ СПИСОК
        #     if len(self.temp_set_of_vri_id) == 1:
        #         self.temp_set_of_vri_id.clear()
        #     # ЕСЛИ БОЛЬШЕ ОДНОЙ ПОВЕРКИ, ТО УДАЛЯЕМ ЗАПИСАННУЮ И ИЩЕМ СЛЕДУЮЩУЮ
        #     if self.vri_search and self.vri_search['result']['items'][0]['vri_id'] in self.temp_set_of_vri_id:
        #         self.temp_set_of_vri_id.remove(self.vri_search['result']['items'][0]['vri_id'])
        #     elif self.number in self.temp_set_of_vri_id:
        #         self.temp_set_of_vri_id.remove(self.number)
        #     if len(self.temp_set_of_vri_id) > 0:
        #         if QMessageBox.question(self, "Найдена поверка",
        #                                 "Найдена еще одна поверка. Хотите добавить информацию о ней?") == 65536:
        #             self._on_search_finished()
        #             return
        #         self._update_progressbar(95, "Поиск информации о поверках")
        #         self.number = self.temp_set_of_vri_id.pop()
        #         url = f"{URL_START}/vri/{self.number}"
        #         self.search_thread.url = url
        #         self.search_thread.start()
        #         return
        # self._on_search_finished()

    # ----------------------------------------ЗАВЕРШЕНИЕ ПОИСКА--------------------------------------------------------
    def _on_search_finished(self):
        print("finished")
        self.dialog.setLabelText("Поиск завершен. Данные внесены в форму.\n"
                                 "Вы можете внести исправления и сохранить оборудование,\n"
                                 "нажав на кнопку \"Сохранить все\"")
        self.dialog.setValue(100)
        self.dialog.setCancelButtonText("Готово")
        self.dialog.canceled.disconnect(self._on_search_stopped)
        self.dialog.canceled.connect(self._check_duplicates)
        self._clear_search_vars()
        self._update_vri_table()

    # ------------------------------------ПРОВЕРКА НАЛИЧИЯ ТАКОЙ ЖЕ ЗАПИСИ---------------------------------------------
    def _check_duplicates(self):
        self.dialog.canceled.disconnect(self._check_duplicates)
        self.dialog.close()

        mitypeTitle = self.ui.plainTextEdit_title.toPlainText()
        modification = self.ui.lineEdit_modification.text()
        manufactureNum = self.ui.lineEdit_number.text()
        if mitypeTitle and modification and manufactureNum:
            if (mitypeTitle, modification, manufactureNum) in self.set_of_mi:
                if QMessageBox.question(self, "Внимание!",
                                        f"Похожее оборудование - '{mitypeTitle} {modification} № {manufactureNum}' "
                                        f"уже записано!\n"
                                        f"Сохранение найденных результатов приведет к дублированию записи!\n"
                                        f"Хотите просмотреть информацию о сохраненном оборудовании?") != 65536:
                    mi_id = func.get_mi_id_from_set_of_mi((mitypeTitle, modification, manufactureNum), self.mi_dict)
                    row = self.tbl_mi_model.indexFromItem(self.tbl_mi_model.findItems(mi_id, column=5)[0]).row()
                    index = self.tbl_mi_model.index(row, 0)
                    self.ui.tableView_mi_list.setCurrentIndex(index)
                    self.ui.tableView_mi_list.scrollTo(index)
                    self._on_mi_select(index)
                    return

    # ---------------------------------------------ОСТАНОВКА ПОИСКА----------------------------------------------------
    def _on_search_stopped(self):
        print("stopped")
        self.search_thread.is_running = False
        self.ui.tableView_mi_list.selectionModel().clearSelection()
        self._clear_search_vars()
        self._clear_all()
        # self._clear_mi_tab()
        # self._clear_vri_tab()
        # self._clear_mieta_tab()
        # self.tbl_vri_model.clear()
        # self.temp_vri_dict.clear()
        # self._update_vri_table()
        self.dialog.canceled.disconnect(self._on_search_stopped)
        self.dialog.close()

    # -----------------------------------------ОЧИЩАЕМ ПЕРЕМЕННЫЕ ПОИСКА-----------------------------------------------
    def _clear_search_vars(self):
        self.eq_type = ""
        self.get_type = ""
        self.mit_search.clear()
        self.mit.clear()
        self.vri_search.clear()
        self.vri.clear()
        self.mieta_search.clear()
        self.mieta.clear()
        self.temp_set_of_vri_id.clear()

    # ----------------------------------------ОБНОВЛЕНИЕ ПРОГРЕССА ПОИСКА----------------------------------------------
    def _update_progressbar(self, val, text):
        self.dialog.setLabelText(text)
        self.dialog.setValue(val)

    def _get_measure_code_id(self):
        if self.ui.comboBox_measure_subcode.currentIndex() != 0:
            measure_code_id = self.ui.comboBox_measure_subcode.currentText()[:4]
        else:
            if self.ui.comboBox_measure_code.currentIndex() != 0:
                measure_code_id = self.ui.comboBox_measure_code.currentText()[:2]
            else:
                measure_code_id = "0"
        return measure_code_id

    def _get_measure_code_name(self):
        if "Не определено" not in self.ui.comboBox_measure_subcode.currentText():
            measure_code_name = self.ui.comboBox_measure_subcode.currentText()[5:]
        else:
            if "Не определено" not in self.ui.comboBox_measure_code.currentText():
                measure_code_name = self.ui.comboBox_measure_code.currentText()[3:]
            else:
                measure_code_name = ""
        return measure_code_name


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
