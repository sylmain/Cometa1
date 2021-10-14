import json
from openpyxl import load_workbook
from json.decoder import JSONDecodeError
from PyQt5.QtCore import QRegExp, QThread, pyqtSignal, Qt, QStringListModel, QEvent, QDate, QSortFilterProxyModel, \
    QItemSelectionModel, pyqtSlot, QSettings, QDateTime
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QCloseEvent
from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog, QDialog, QMessageBox, QProgressDialog, \
    QAbstractItemView, QPushButton, QMdiSubWindow
from functions_pkg.send_get_request import GetRequest
from equipment_pkg.ui_equipment import Ui_MainWindow
from functions_pkg.db_functions import MySQLConnection
import functions_pkg.functions as func
from equipment_pkg.equipment_import_file import EquipmentImportFileWidget
from equipment_pkg.equipment_functions import *

# from equipment_pkg.equipment_requests import send_request

STATUS_LIST = ["СИ", "СИ в качестве эталона", "Эталон единицы величины"]
VRI_TYPE_LIST = ["периодическая", "первичная"]
URL_START = "https://fgis.gost.ru/fundmetrology/eapi"
ORG_NAME = func.get_organization_name()
MEASURE_CODES = func.get_measure_codes()
RX_MIT = QRegExp("^[1-9][0-9]{0,5}-[0-9]{2}$")
RX_MIT.setCaseSensitivity(False)
RX_NPE = QRegExp("^гэт[1-9][0-9]{0,2}-(([0-9]{2})|([0-9]{4}))$")
RX_NPE.setCaseSensitivity(False)
RX_UVE = QRegExp("^[1-3]\.[0-9]\.\S{3}\.\d{4}\.20[0-4]\d$")
RX_UVE.setCaseSensitivity(False)
RX_MIETA = QRegExp("^[1-9]\d{0,5}\.\d{2}\.(0Р|1Р|2Р|3Р|4Р|5Р|РЭ|ВЭ|СИ)\.\d+\s*$")
RX_MIETA.setCaseSensitivity(False)
RX_CERT_NUMBER = QRegExp("^(С|И)\-\S{1,3}\/[0-3][0-9]\-[0-1][0-9]\-20[2-5][0-9]\/\d{8,10}$")
RX_CERT_NUMBER.setCaseSensitivity(False)
RX_VRI_ID = QRegExp("^([1-2]\-)*\d{1,15}\s*$")
RX_VRI_ID.setCaseSensitivity(False)


class SearchThread(QThread):
    msg_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.url = ""
        self.is_running = True

    def run(self):
        if self.is_running:
            # self.msleep(500)
            print("thread running")
            print(f" {self.url}")
            resp = GetRequest.getRequest(self.url)
            print(f"  {resp}")
            print("    thread stopped")
            self.msleep(1000)
            self.msg_signal.emit(resp)
        else:
            self.msleep(1000)
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
        self.list_of_card_numbers = list()  # список номеров карточек
        self.set_of_vri_id = set()  # множество id поверок (меняется при перекючении прибора)
        self.set_of_mi = set()  # множество приборов {наименование, тип, заводской номер}
        self.temp_set_of_vri_id = set()  # временное множество id поверок при поиске оборудования (или поверок)
        self.temp_set_of_mieta_numbers = set()  # временное множество номеров эталонов при поиске оборудования (или поверок)

        self.mit_search = dict()
        self.mit = dict()
        self.mieta_search = dict()
        self.mieta = dict()
        self.vri_search = dict()
        self.vri = list()
        self.scan_info = dict()

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

        self._update_mi_dicts()
        self._update_vri_dicts()

        self._update_mi_table()
        self._update_vri_table()

        self.is_scanning_run = False

        self.ui.tabWidget.setCurrentIndex(0)

    # ДОБАВЛЕНИЕ ВИДОВ ИЗМЕРЕНИЙ В РАСКРЫВАЮЩИЙСЯ СПИСОК
    def _add_measure_codes(self):
        self.ui.comboBox_measure_code.addItems(["- Не определено"])
        self.ui.comboBox_measure_code.addItems(sorted(MEASURE_CODES['measure_codes_list']))

    # ДОБАВЛЕНИЕ ПОДВИДОВ ИЗМЕРЕНИЙ В В РАСКРЫВАЮЩИЙСЯ СПИСОК
    def _add_measure_subcodes(self, new_code):
        self.ui.comboBox_measure_subcode.clear()
        self.ui.comboBox_measure_subcode.addItems(["- Не определено"])
        if "Не определено" not in new_code:
            code = new_code[:2]
            self.ui.comboBox_measure_subcode.addItems(sorted(MEASURE_CODES['measure_sub_codes_dict'][code]))

    # ДОБАВЛЕНИЕ СОБЫТИЙ И СВЯЗЫВАНИЕ С МЕТОДАМИ
    def _add_connects(self):

        # ПРИ НАЖАТИИ "ДОБАВИТЬ ОБОРУДОВАНИЕ ИЗ ФГИС АРШИН" ЗАПУСКАЕМ ФОРМУ ВВОДА НОМЕРА
        self.ui.toolButton_equip_add.clicked.connect(self._on_start_search)

        # ПРИ НАЖАТИИ "СОХРАНИТЬ ВСЕ" СОХРАНЯЕМ ИНФОРМАЦИЮ СО ВСЕХ ВКЛАДОК В БАЗУ
        self.ui.pushButton_equip_save.clicked.connect(self._on_save_all)

        # СИГНАЛ ОТ ПОТОКА ПОИСКА ЗАПУСКАЕТ ЛОГИКУ ОТВЕТА
        self.search_thread.msg_signal.connect(self._on_getting_resp, Qt.QueuedConnection)

        # ПРИ КЛИКЕ ПО ОБОРУДОВАНИЮ ОБНОВЛЯЕМ ВСЕ ВКЛАДКИ
        self.ui.tableView_mi_list.clicked.connect(self._on_mi_click)
        self.ui.tableView_mi_list.activated.connect(self._on_mi_click)

        # ПРИ КЛИКЕ НА ПОВЕРКУ ОБНОВЛЯЕМ ВКЛАДКИ ЭТАЛОНА И ПОВЕРКИ
        self.ui.tableView_vri_list.clicked.connect(self._on_vri_select)
        self.ui.tableView_vri_list.activated.connect(self._on_vri_select)

        # ПРИ НАЖАТИИ "СОХРАНИТЬ" СОХРАНЯЕМ ИНФОРМАЦИЮ С СООТВЕТСТВУЮЩЕЙ ВКЛАДКИ В БАЗУ
        self.ui.pushButton_save_mi_info.clicked.connect(self._on_save_mi)
        self.ui.pushButton_save_vri.clicked.connect(self._on_save_vri)
        self.ui.pushButton_save_mieta.clicked.connect(self._on_save_mieta)

        self.ui.pushButton_add_vri.clicked.connect(self._on_add_vri)
        self.ui.pushButton_find_vri.clicked.connect(self._on_find_vri)

        # НАЖАТИЕ КНОПОК ОЧИСТИТЬ НА РАЗНЫХ ВКЛАДКАХ
        self.ui.pushButton_clear_mi_info.clicked.connect(self._clear_mi_tab)
        self.ui.pushButton_clear_vri.clicked.connect(self._clear_vri_and_mieta_tab)
        self.ui.pushButton_clear_mieta.clicked.connect(self._clear_mieta_tab)

        self.ui.pushButton_add_dep.clicked.connect(self._on_add_dep)
        self.ui.pushButton_remove_dep.clicked.connect(self._on_remove_dep)
        self.ui.pushButton_clear.clicked.connect(self._clear_all)
        self.ui.pushButton_refresh_all.clicked.connect(self._refresh_all)
        self.ui.pushButton_delete_all_equipment.clicked.connect(self._delete_all_from_db)
        self.ui.pushButton_full_scan.clicked.connect(self._full_scan_start)

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
        self.ui.checkBox_unlimited.toggled.connect(lambda: self.ui.dateEdit_vri_validDate.setDisabled(
            True) if self.ui.checkBox_unlimited.checkState() == 2 else self.ui.dateEdit_vri_validDate.setEnabled(True))
        # self.ui.lineEdit_reg_card_number.textChanged.connect(self._appearance_init)

    def _delete_vri_duplicates(self):
        print("Удаление дубликатов")
        for mi_id in self.mis_vri_dict:
            temp_dict = dict()
            for vri_id in self.mis_vri_dict[mi_id]:
                key = (self.mis_vri_dict[mi_id][vri_id]['vri_vrfDate'],
                       self.mis_vri_dict[mi_id][vri_id]['vri_certNum'],
                       self.mis_vri_dict[mi_id][vri_id]['vri_mieta_number'])
                if key not in temp_dict:
                    temp_dict[key] = vri_id
                # elif self.mis_vri_dict[mi_id][temp_dict[key]] == self.mis_vri_dict[mi_id][vri_id]:
                #     self._on_delete_vri(vri_id=vri_id)
                else:
                    self._on_delete_vri(vri_id=vri_id, delete_confirm=False)
                    print(f"удалена поверка № {vri_id}")
        print("Дубликаты удалены")

    def _full_scan_start(self):
        """
        Создание вспомогательных таблиц для сканирования оборудования
        Для каждого прибора проверяется условие даты последнего сканирования
        :return:
        """
        self._clear_search_vars()
        self.is_scanning_run = True
        self.scan_mi_vri_dict = dict()
        self.mi_id_list = list()

        self._delete_vri_duplicates()

        for mi_id in self.mi_dict:
            if not self.mi_dict[mi_id]['last_scan_date']:
                self.mi_id_list.append(mi_id)
                self.scan_mi_vri_dict[mi_id] = {}
                self.scan_mi_vri_dict[mi_id]['reestr'] = self.mi_dict[mi_id]['reestr']
                self.scan_mi_vri_dict[mi_id]['title'] = self.mi_dict[mi_id]['title']
                self.scan_mi_vri_dict[mi_id]['number'] = self.mi_dict[mi_id]['number']
                self.scan_mi_vri_dict[mi_id]['inv_number'] = self.mi_dict[mi_id]['inv_number']
                self.scan_mi_vri_dict[mi_id]['modification'] = self.mi_dict[mi_id]['modification']
                self.scan_mi_vri_dict[mi_id]['vris'] = []
                if mi_id in self.mis_vri_dict:
                    for vri_id in self.mis_vri_dict[mi_id]:
                        # if not self.mis_vri_dict[mi_id][vri_id]['vri_last_scan_date']:
                        if self.mis_vri_dict[mi_id][vri_id]['vri_certNum'] or \
                                self.mis_vri_dict[mi_id][vri_id]['vri_mieta_number']:
                            self.scan_mi_vri_dict[mi_id]['vris'].append((vri_id,
                                                                         self.mis_vri_dict[mi_id][vri_id][
                                                                             'vri_certNum'],
                                                                         self.mis_vri_dict[mi_id][vri_id][
                                                                             'vri_mieta_number']))
                    if not self.scan_mi_vri_dict[mi_id]:
                        self.mi_id_list.remove(mi_id)
                        self.scan_mi_vri_dict.pop(mi_id)

        # print(self.scan_mi_vri_dict)

        for mi_id in self.scan_mi_vri_dict:
            print("{" + f"'{mi_id}': {self.scan_mi_vri_dict[mi_id]}")

        count = len(self.mi_dict)
        self.progress_dialog = QProgressDialog(self)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.setWindowTitle("ОЖИДАЙТЕ! Идет поиск!")
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setRange(0, count)
        # self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.resize(350, 100)
        self.progress_dialog.show()
        self.search_thread.is_running = True

        self._scan_vri()

    def _scan_vri(self):
        """
        Запуск сканирования оборудования по приоритету имеющейся информации:
        1. Номер эталона в реестре
        2. Номер свидетельства о поверке
        3. Номер в реестре, заводской (инвентарный) номер и модификация
        4. Наименование, заводской (инвентарный) номер и модификация

        Если есть номер эталона - берем все его vri_id и записываем во временное хранилище
        Если есть номер свидетельства - ищем его в базе и записываем vri_id во временное хранилище
        Если это оказался эталон - берем все его vri_id и записываем во временное хранилище
        Если есть только номер в реестре - ищем в базе поверок по реестру, зав. номеру, модификации
        vri_id поверки записываем во временное хранилище

        :return:
        """
        self.scan_info.clear()
        self.scan_info['set_of_vri_id'] = set()
        self.scan_info['set_of_mieta_id'] = set()
        self.scan_info['list_of_scan_vri'] = list()
        self.scan_info['list_of_scan_mieta'] = list()

        if self.mi_id_list:
            self.mi_id_scan = self.mi_id_list.pop(0)
            self._on_mi_select(self.mi_id_scan)

            if self.scan_mi_vri_dict[self.mi_id_scan]['vris']:
                vri_id_scan, \
                cert_number_scan, \
                mieta_number_scan = self.scan_mi_vri_dict[self.mi_id_scan]['vris'].pop(0)

                if mieta_number_scan and RX_MIETA.indexIn(mieta_number_scan) == 0:
                    self.temp_set_of_mieta_numbers.add(mieta_number_scan)
                    url = f"https://fgis.gost.ru/fundmetrology/cm/xcdb/vri/select?" \
                          f"q=mieta.number:{mieta_number_scan}&sort=verification_date+desc"
                    self.search_thread.url = url
                    self._update_progressbar(self.progress_dialog.maximum() - len(self.mi_id_list),
                                             f"{mieta_number_scan}\nОсталось {len(self.mi_id_list) + 1} приборов")
                elif self.cert_number_scan and RX_CERT_NUMBER.indexIn(self.cert_number_scan) == 0:
                    self.number = f"1-{self.cert_number_scan.rsplit('/', 1)[1]}"
                    self.search_thread.url = f"{URL_START}/vri/{self.number}"
                    self._update_progressbar(self.progress_dialog.maximum() - len(self.mi_id_list),
                                             f"{self.cert_number_scan}\nОсталось {len(self.mi_id_list) + 1} приборов")
                elif self.cert_number_scan:
                    cur_year = QDate.currentDate().year()
                    self.cert_number_scan = str(self.cert_number_scan).replace(" ", "%20")
                    self.search_thread.url = f"{URL_START}/vri?year={cur_year}&rows=100&search={self.cert_number_scan}"
        # elif self.reestr_scan and self.number_scan:

        self.search_thread.start()

        if self.progress_dialog.isHidden():
            self.progress_dialog.show()

    def _get_next_scan_vars(self):
        # если список поверок в текущем mi_id пуст, то проверяем, есть ли еще приборы в списке приборов
        # если список приборов не пустой, переходим к следующему mi_id и берем первое vri_id в списке поверок
        # если пустой - заканчиваем сканирование
        # если список поверок у текущего оборудования не пустой, берем следующую поверку

        if self.scan_mi_vri_dict[self.mi_id_scan]['vris']:
            self.vri_id_scan, \
            self.cert_number_scan, \
            self.mieta_number_scan = self.scan_mi_vri_dict[self.mi_id_scan]['vris'].pop(0)
            return True
        else:
            self._save_scan_info(self.scan_info['scan_mit'], self.scan_info['list_of_scan_vri'],
                                 self.scan_info['list_of_scan_mieta'])
            self._update_mi_table()
            self._update_vri_table(self.mi_id_scan)
            self._scan_vri()
            return False
        self.progress_dialog.close()
        QMessageBox.information(self, "Завершение сканирования", "Оборудование просканировано. Данные сохранены.")
        return False

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

        # если выбран первоначальный (сохраненный) вид измерений, то записываем значение из словаря
        if prev_number_string == cur_card_number:
            self.ui.lineEdit_reg_card_number.setText(cur_card_number)
            return
        # если поле номера карточки пустое или сохраненный вид измерений отличается от текущего - меняем номер карточки
        if not cur_card_number or cur_card_number != prev_number_string:
            self.ui.lineEdit_reg_card_number.setText(new_number_string)

    def _on_import(self):
        self.widget = EquipmentImportFileWidget()
        self.widget.setWindowModality(Qt.ApplicationModal)
        self.widget.show()

    # ---------------------------------------------ВНЕШНИЙ ВИД ПРИ СТАРТЕ----------------------------------------------
    def _appearance_init(self):
        # self.ui.pushButton_find_vri.hide()
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
            self.ui.checkBox_unlimited.setEnabled(True)
            self.ui.dateEdit_vri_validDate.setEnabled(True)
        else:
            self.ui.groupBox_applicable.hide()
            self.ui.groupBox_inapplicable.show()
            self.ui.checkBox_unlimited.setDisabled(True)
            self.ui.dateEdit_vri_validDate.setDisabled(True)

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

    def _on_mi_click(self, index):
        row = index.row()
        mi_id = self.tbl_mi_model.index(row, 5).data()
        self._on_mi_select(mi_id)

    # ----------------ОБНОВЛЕНИЕ ИНФОРМАЦИИ ПОЛЕЙ ПРИ ВЫБОРЕ ОБОРУДОВАНИЯ В ТАБЛИЦЕ ОБОРУДОВАНИЯ-----------------------
    # преобразуем mi_id в строку, запускаем очистку всего, ищем индекс строки с mi_id,
    # делаем этот индекс текущим и видимым на экране, обновляем вкладку общей информации,
    # обновляем таблицу поверок. Если поверки существуют, выделяем первую

    def _on_mi_select(self, mi_id):
        mi_id = str(mi_id)
        self._clear_all()
        row = self.tbl_mi_model.indexFromItem(self.tbl_mi_model.findItems(mi_id, column=5)[0]).row()
        index = self.tbl_mi_model.index(row, 0)
        self.ui.tableView_mi_list.setCurrentIndex(index)
        self.ui.tableView_mi_list.scrollTo(index)
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
        if vri_id:
            self._update_vri_and_mieta_tab(vri_id)

    def _update_mi_dicts(self):
        get_mis = func.get_mis()
        self.mi_dict = get_mis['mi_dict']
        self.set_of_mi = get_mis['set_of_mi']
        self.list_of_card_numbers = get_mis['list_of_card_numbers']
        self.mi_deps = func.get_mi_deps()['mi_deps_dict']

    def _update_vri_dicts(self):
        self.mis_vri_dict = func.get_mis_vri_info()['mis_vri_dict']

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
    def _update_vri_table(self, mi_id=None, vri_id=None):
        self.set_of_vri_id.clear()
        if mi_id and mi_id in self.mis_vri_dict:
            self.tbl_vri_model.clear()
            for temp_vri_id in self.mis_vri_dict[mi_id]:
                row = list()

                # КОЛОНКИ ТАБЛИЦЫ ПОВЕРОК
                vri_vrf_date = self.mis_vri_dict[mi_id][temp_vri_id]['vri_vrfDate']
                vri_valid_date = "БЕССРОЧНО"
                vri_cert_number = self.mis_vri_dict[mi_id][temp_vri_id]['vri_certNum']
                vri_result = "ГОДЕН"
                vri_organization = self.mis_vri_dict[mi_id][temp_vri_id]['vri_organization']
                vri_mieta = "нет"

                if self.mis_vri_dict[mi_id][temp_vri_id]['vri_applicable'] != "0":
                    if self.mis_vri_dict[mi_id][temp_vri_id]['vri_validDate']:
                        vri_valid_date = self.mis_vri_dict[mi_id][temp_vri_id]['vri_validDate']
                else:
                    vri_valid_date = "-"
                    vri_result = "БРАК"

                rankTitle = self.mis_vri_dict[mi_id][temp_vri_id]['vri_mieta_rankclass']
                regNumber = self.mis_vri_dict[mi_id][temp_vri_id]['vri_mieta_number']
                if rankTitle and regNumber:
                    vri_mieta = f"{regNumber}: {rankTitle.lower()}"
                elif regNumber:
                    vri_mieta = f"{regNumber}"

                row.append(QStandardItem(vri_vrf_date))
                row.append(QStandardItem(vri_valid_date))
                row.append(QStandardItem(vri_cert_number))
                row.append(QStandardItem(vri_result))
                row.append(QStandardItem(vri_organization))
                row.append(QStandardItem(vri_mieta))
                row.append(QStandardItem(temp_vri_id))
                self.tbl_vri_model.appendRow(row)

                self.set_of_vri_id.add(self.mis_vri_dict[mi_id][temp_vri_id]['vri_FIF_id'])

        # ЕСЛИ ПЕРЕДАН АРГУМЕНТ VRI_ID, ВЫДЕЛЯЕМ СТРОКУ С ЭТОЙ ПОВЕРКОЙ
        if vri_id:
            original_index = self.tbl_vri_model.indexFromItem(self.tbl_vri_model.findItems(vri_id, column=6)[0])
            sorted_index = self.tbl_vri_proxy_model.mapFromSource(original_index)
            self.ui.tableView_vri_list.scrollTo(sorted_index)
            self.ui.tableView_vri_list.selectRow(sorted_index.row())

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

        last_scan_date = QDate(self.mi_dict[mi_id]['last_scan_date']).toString("dd.MM.yyyy") \
            if self.mi_dict[mi_id]['last_scan_date'] else ""

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
        if self.mi_dict[mi_id]['MPI']:
            self.ui.radioButton_MPI_yes.setChecked(True)
            self.ui.lineEdit_MPI.setText(self.mi_dict[mi_id]['MPI'])
        else:
            self.ui.radioButton_MPI_no.setChecked(True)
            self.ui.lineEdit_MPI.setText("")
        self.ui.plainTextEdit_purpose.setPlainText(self.mi_dict[mi_id]['purpose'])
        self.ui.plainTextEdit_personal.setPlainText(self.mi_dict[mi_id]['personal'])
        self.ui.plainTextEdit_software_inner.setPlainText(self.mi_dict[mi_id]['software_inner'])
        self.ui.plainTextEdit_software_outer.setPlainText(self.mi_dict[mi_id]['software_outer'])
        self.ui.plainTextEdit_owner.setPlainText(self.mi_dict[mi_id]['owner'])
        self.ui.plainTextEdit_owner_contract.setPlainText(self.mi_dict[mi_id]['owner_contract'])
        self.ui.lineEdit_mi_last_scan_date.setText(last_scan_date)

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
    def _update_vri_and_mieta_tab(self, vri_id):
        self._clear_vri_and_mieta_tab()
        mi_id = self.ui.lineEdit_mi_id.text()
        if mi_id and vri_id and mi_id in self.mis_vri_dict and vri_id in self.mis_vri_dict[mi_id]:
            vri_dict = self.mis_vri_dict[mi_id][vri_id]

            last_scan_date = QDate(vri_dict['vri_last_scan_date']).toString("dd.MM.yyyy") \
                if vri_dict['vri_last_scan_date'] else ""

            self.ui.lineEdit_vri_id.setText(vri_id)
            self.ui.lineEdit_vri_FIF_id.setText(vri_dict['vri_FIF_id'])
            self.ui.plainTextEdit_vri_organization.setPlainText(vri_dict['vri_organization'])
            self.ui.lineEdit_vri_signCipher.setText(vri_dict['vri_signCipher'])
            self.ui.plainTextEdit_vri_miOwner.setPlainText(vri_dict['vri_miOwner'])
            self.ui.dateEdit_vrfDate.setDate(QDate.fromString(vri_dict['vri_vrfDate'], "dd.MM.yyyy"))

            self.ui.comboBox_vri_vriType.setCurrentText(vri_dict['vri_vriType'])
            self.ui.plainTextEdit_vri_docTitle.setPlainText(vri_dict['vri_docTitle'])
            if int(vri_dict['vri_applicable']):
                self.ui.radioButton_applicable.setChecked(True)
                self.ui.lineEdit_vri_certNum.setText(vri_dict['vri_certNum'])
                self.ui.lineEdit_vri_stickerNum.setText(vri_dict['vri_stickerNum'])
                self.ui.checkBox_vri_signPass.setChecked(int(vri_dict['vri_signPass']))
                self.ui.checkBox_vri_signMi.setChecked(int(vri_dict['vri_signMi']))
                if vri_dict['vri_validDate']:
                    self.ui.checkBox_unlimited.setChecked(False)
                    self.ui.dateEdit_vri_validDate.setDate(QDate.fromString(vri_dict['vri_validDate'], "dd.MM.yyyy"))
                else:
                    self.ui.checkBox_unlimited.setChecked(True)
            else:
                self.ui.radioButton_inapplicable.setChecked(True)
                self.ui.lineEdit_vri_noticeNum.setText(vri_dict['vri_certNum'])
                self.ui.checkBox_unlimited.setChecked(False)
                self.ui.checkBox_unlimited.setDisabled(True)
                self.ui.dateEdit_vri_validDate.setDisabled(True)
            self.ui.plainTextEdit_vri_structure.setPlainText(vri_dict['vri_structure'])
            self.ui.checkBox_vri_briefIndicator.setChecked(int(vri_dict['vri_briefIndicator']))
            self.ui.plainTextEdit_vri_briefCharacteristics.setPlainText(
                vri_dict['vri_briefCharacteristics'])
            self.ui.plainTextEdit_vri_ranges.setPlainText(vri_dict['vri_ranges'])
            self.ui.plainTextEdit_vri_values.setPlainText(vri_dict['vri_values'])
            self.ui.plainTextEdit_vri_channels.setPlainText(vri_dict['vri_channels'])
            self.ui.plainTextEdit_vri_blocks.setPlainText(vri_dict['vri_blocks'])
            self.ui.plainTextEdit_vri_additional_info.setPlainText(vri_dict['vri_additional_info'])
            self.ui.lineEdit_mieta_number.setText(vri_dict['vri_mieta_number'])
            self.ui.comboBox_mieta_rank.setCurrentText(vri_dict['vri_mieta_rankcode'])
            self.ui.lineEdit_mieta_rank_title.setText(vri_dict['vri_mieta_rankclass'])
            self.ui.lineEdit_mieta_npenumber.setText(vri_dict['vri_mieta_npenumber'])
            self.ui.lineEdit_mieta_schematype.setText(vri_dict['vri_mieta_schematype'])
            self.ui.plainTextEdit_mieta_schematitle.setPlainText(vri_dict['vri_mieta_schematitle'])
            self.ui.lineEdit_vri_last_scan_date.setText(last_scan_date)

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

    # ---------------------------------------ОБНОВЛЕНИЕ ВСЕГО----------------------------------------------------------

    def _refresh_all(self):
        self._update_mi_dicts()
        self._update_vri_dicts()
        self._update_mi_table()
        self._clear_all()

    # ------------------------------------------ОЧИСТКА ВСЕГО----------------------------------------------------------
    def _clear_all(self):

        self.tbl_vri_model.clear()
        self._update_vri_table()  # для отображения заголовков таблицы поверок

        self._clear_mi_tab()
        self._clear_vri_and_mieta_tab()

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
        self.ui.lineEdit_mi_last_scan_date.setText("")

        self.ui.plainTextEdit_purpose.setPlainText("")
        self.ui.plainTextEdit_personal.setPlainText("")
        self.ui.plainTextEdit_owner.setPlainText("")
        self.ui.plainTextEdit_owner_contract.setPlainText("")
        self.ui.checkBox_has_manual.setChecked(False)
        self.ui.checkBox_has_verif_method.setChecked(False)
        self.ui.checkBox_has_pasport.setChecked(False)

    # ---------------------------------ОЧИСТКА ВКЛАДКИ ЭТАЛОНов--------------------------------------------------------
    def _clear_mieta_tab(self):
        self.ui.lineEdit_mieta_number.setText("")
        self.ui.comboBox_mieta_rank.setCurrentIndex(0)
        self.ui.lineEdit_mieta_rank_title.setText("")
        self.ui.lineEdit_mieta_npenumber.setText("")
        self.ui.lineEdit_mieta_schematype.setText("")
        self.ui.plainTextEdit_mieta_schematitle.setPlainText("")

    # --------------------------------------ОЧИСТКА ВКЛАДКИ ПОВЕРОК И ЭТАЛОНОВ___--------------------------------------
    def _clear_vri_and_mieta_tab(self):
        # self.temp_vri_dict.clear()
        self.ui.lineEdit_vri_id.setText("")
        self.ui.lineEdit_vri_FIF_id.setText("")
        self.ui.plainTextEdit_vri_organization.setPlainText("")
        self.ui.plainTextEdit_vri_miOwner.setPlainText("")
        self.ui.dateEdit_vrfDate.setDate(QDate(2021, 1, 1))
        # self.ui.dateEdit_vri_validDate.setEnabled(True)
        self.ui.checkBox_unlimited.setEnabled(True)
        self.ui.checkBox_unlimited.setChecked(False)
        self.ui.dateEdit_vri_validDate.setDate(QDate(2022, 1, 1))
        self.ui.comboBox_vri_vriType.setCurrentIndex(0)
        self.ui.plainTextEdit_vri_docTitle.setPlainText("")
        self.ui.radioButton_applicable.setChecked(True)
        self.ui.lineEdit_vri_certNum.setText("")
        self.ui.lineEdit_vri_signCipher.setText("")
        self.ui.lineEdit_vri_stickerNum.setText("")
        self.ui.checkBox_vri_signPass.setChecked(False)
        self.ui.checkBox_vri_signMi.setChecked(False)
        self.ui.lineEdit_vri_noticeNum.setText("")
        self.ui.lineEdit_vri_last_scan_date.setText("")
        self.ui.plainTextEdit_vri_structure.setPlainText("")
        self.ui.checkBox_vri_briefIndicator.setChecked(False)
        self.ui.plainTextEdit_vri_briefCharacteristics.setPlainText("")
        self.ui.plainTextEdit_vri_ranges.setPlainText("")
        self.ui.plainTextEdit_vri_values.setPlainText("")
        self.ui.plainTextEdit_vri_channels.setPlainText("")
        self.ui.plainTextEdit_vri_blocks.setPlainText("")
        self.ui.plainTextEdit_vri_additional_info.setPlainText("")
        # self.ui.lineEdit_mieta_number.setText("")
        # self.ui.comboBox_mieta_rank.setCurrentIndex(0)
        # self.ui.lineEdit_mieta_rank_title.setText("")
        # self.ui.lineEdit_mieta_npenumber.setText("")
        # self.ui.lineEdit_mieta_schematype.setText("")
        # self.ui.plainTextEdit_mieta_schematitle.setPlainText("")

    # -------------------------------------------НАЖАТИЕ КНОПКИ СОХРАНИТЬ ВСЕ------------------------------------------
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

        last_scan_date = f"'{self.mi_dict[mi_id]['last_scan_date']}'" \
            if self.mi_dict[mi_id]['last_scan_date'] else 'NULL'

        sql_replace = f"REPLACE INTO mis (" \
                      f"mi_id, " \
                      f"mis_reg_card_number, " \
                      f"mi_measure_code, " \
                      f"mi_status, " \
                      f"mi_reestr, " \
                      f"mi_title, " \
                      f"mi_type, " \
                      f"mi_modification, " \
                      f"mi_number, " \
                      f"mi_inv_number, " \
                      f"mi_manufacturer, " \
                      f"mi_manuf_year, " \
                      f"mi_expl_year, " \
                      f"mi_diapazon, " \
                      f"mi_PG, " \
                      f"mi_KT, " \
                      f"mi_other_characteristics, " \
                      f"mi_MPI, " \
                      f"mi_purpose, " \
                      f"mi_responsible_person, " \
                      f"mi_personal, " \
                      f"mi_room, " \
                      f"mi_software_inner, " \
                      f"mi_software_outer, " \
                      f"mi_RE, " \
                      f"mi_pasport, " \
                      f"mi_MP, " \
                      f"mi_TO_period, " \
                      f"mi_owner, " \
                      f"mi_owner_contract, " \
                      f"mi_last_scan_date" \
                      f") VALUES (" \
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
                      f"'{self.ui.plainTextEdit_owner_contract.toPlainText()}', " \
                      f"{last_scan_date});"

        MySQLConnection.verify_connection()
        connection = MySQLConnection.create_connection()
        result = MySQLConnection.execute_query(connection, sql_replace)

        if result[0]:
            mi_id = str(result[1])
            self._update_mi_dicts()
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
                if self.ui.checkBox_unlimited.isChecked():
                    valid_date = ""
                else:
                    valid_date = self.ui.dateEdit_vri_validDate.date().toString("dd.MM.yyyy")
            else:
                applicable = 0
                cert_num = self.ui.lineEdit_vri_noticeNum.text()
                valid_date = ""

            if self.ui.checkBox_vri_briefIndicator.isChecked():
                briefIndicator = 1
            vrf_date = self.ui.dateEdit_vrfDate.date().toString("dd.MM.yyyy")
            sql_replace = f"REPLACE INTO mis_vri_info VALUES (" \
                          f"{vri_id}, " \
                          f"{mi_id}, " \
                          f"'{self.ui.plainTextEdit_vri_organization.toPlainText()}', " \
                          f"'{self.ui.lineEdit_vri_signCipher.text()}', " \
                          f"'{self.ui.plainTextEdit_vri_miOwner.toPlainText()}', " \
                          f"'{vrf_date}', " \
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
    def _on_save_mi(self):

        mi_id = self.ui.lineEdit_mi_id.text() if self.ui.lineEdit_mi_id.text() else "NULL"

        reg_card_number = self.ui.lineEdit_reg_card_number.text()

        # ЕСЛИ ОТСУТСТВУЕТ НОМЕР КАРТОЧКИ - ОШИБКА
        if not reg_card_number:
            QMessageBox.warning(self, "Ошибка сохранения", "Необходимо ввести номер регистрационной карточки")
            return

        # ЕСЛИ НОМЕР КАРТОЧКИ УЖЕ ПРИСВОЕН ДРУГОМУ ПРИБОРУ - ОШИБКА
        if mi_id != "NULL" and self.mi_dict[mi_id]['reg_card_number'] != reg_card_number \
                and reg_card_number in self.list_of_card_numbers:
            QMessageBox.critical(self, "Ошибка", "Данный номер регистрационной карточки принадлежит другому прибору.\n"
                                                 "Сохранение невозможно")
            return

        measure_code_id = self._get_measure_code_id()

        resp_person_id = func.get_worker_id_from_fio(self.ui.comboBox_responsiblePerson.currentText(),
                                                     self.workers['worker_dict'])
        room_id = func.get_room_id_from_number(self.ui.comboBox_room.currentText(), self.rooms['room_dict'])

        last_scan_date = f"'{self.mi_dict[mi_id]['last_scan_date']}'" \
            if self.mi_dict[mi_id]['last_scan_date'] else 'NULL'

        sql_replace = f"REPLACE INTO mis (" \
                      f"mi_id, " \
                      f"mis_reg_card_number, " \
                      f"mi_measure_code, " \
                      f"mi_status, " \
                      f"mi_reestr, " \
                      f"mi_title, " \
                      f"mi_type, " \
                      f"mi_modification, " \
                      f"mi_number, " \
                      f"mi_inv_number, " \
                      f"mi_manufacturer, " \
                      f"mi_manuf_year, " \
                      f"mi_expl_year, " \
                      f"mi_diapazon, " \
                      f"mi_PG, " \
                      f"mi_KT, " \
                      f"mi_other_characteristics, " \
                      f"mi_MPI, " \
                      f"mi_purpose, " \
                      f"mi_responsible_person, " \
                      f"mi_personal, " \
                      f"mi_room, " \
                      f"mi_software_inner, " \
                      f"mi_software_outer, " \
                      f"mi_RE, " \
                      f"mi_pasport, " \
                      f"mi_MP, " \
                      f"mi_TO_period, " \
                      f"mi_owner, " \
                      f"mi_owner_contract, " \
                      f"mi_last_scan_date" \
                      f") VALUES (" \
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
                      f"'{self.ui.plainTextEdit_owner_contract.toPlainText()}', " \
                      f"{last_scan_date});"

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

        self._update_mi_dicts()
        self._update_mi_table()
        self._on_mi_select(mi_id)
        QMessageBox.information(self, "Сохранено", "Информация сохранена")

    # -------------------------------------КЛИК ПО КНОПКЕ "СОХРАНИТЬ ПОВЕРКУ"------------------------------------------
    def _on_save_vri(self):

        mi_id = self.ui.lineEdit_mi_id.text()

        # ЕСЛИ ОБОРУДОВАНИЕ НЕ СОХРАНЕНО - ОШИБКА
        if not mi_id:
            QMessageBox.critical(self, "Ошибка", "Сначала заполните и сохраните общую информацию об оборудовании, "
                                                 "затем выполните сохранение поверки")
            return

        vri_id = self.ui.lineEdit_vri_id.text() if self.ui.lineEdit_vri_id.text() else "NULL"

        applicable = 1 if self.ui.radioButton_applicable.isChecked() else 0
        cert_num = self.ui.lineEdit_vri_certNum.text() if applicable else self.ui.lineEdit_vri_noticeNum.text()
        vrf_date = self.ui.dateEdit_vrfDate.date().toString("dd.MM.yyyy")
        valid_date = self.ui.dateEdit_vri_validDate.date().toString("dd.MM.yyyy") \
            if not self.ui.checkBox_unlimited.isChecked() else ""
        signPass = 1 if (applicable and self.ui.checkBox_vri_signPass.isChecked()) else 0
        signMi = 1 if (applicable and self.ui.checkBox_vri_signMi.isChecked()) else 0
        briefIndicator = 1 if self.ui.checkBox_vri_briefIndicator.isChecked() else 0

        if self.ui.lineEdit_vri_last_scan_date.text():
            temp_last_scan_date = QDate().fromString(self.ui.lineEdit_vri_last_scan_date.text(), "dd.MM.yyyy")
            last_scan_date = temp_last_scan_date.toString("yyyy-MM-dd")
        else:
            last_scan_date = 'NULL'

        # last_scan_date = f"'{self.mis_vri_dict[mi_id][vri_id]['vri_last_scan_date']}'" \
        #     if self.mis_vri_dict[mi_id][vri_id]['vri_last_scan_date'] else 'NULL'

        sql_replace = f"REPLACE INTO mis_vri_info (" \
                      f"vri_id, " \
                      f"vri_mi_id, " \
                      f"vri_organization, " \
                      f"vri_signCipher, " \
                      f"vri_miOwner, " \
                      f"vri_vrfDate, " \
                      f"vri_validDate, " \
                      f"vri_vriType, " \
                      f"vri_docTitle, " \
                      f"vri_applicable, " \
                      f"vri_certNum, " \
                      f"vri_stickerNum, " \
                      f"vri_signPass, " \
                      f"vri_signMi, " \
                      f"vri_inapplicable_reason, " \
                      f"vri_structure, " \
                      f"vri_briefIndicator, " \
                      f"vri_briefCharacteristics, " \
                      f"vri_ranges, " \
                      f"vri_values, " \
                      f"vri_channels, " \
                      f"vri_blocks, " \
                      f"vri_additional_info, " \
                      f"vri_info, " \
                      f"vri_FIF_id, " \
                      f"vri_mieta_number, " \
                      f"vri_mieta_rankcode, " \
                      f"vri_mieta_rankclass, " \
                      f"vri_mieta_npenumber, " \
                      f"vri_mieta_schematype, " \
                      f"vri_mieta_schematitle, " \
                      f"vri_last_scan_date" \
                      f") VALUES (" \
                      f"{vri_id}, " \
                      f"{int(mi_id)}, " \
                      f"'{self.ui.plainTextEdit_vri_organization.toPlainText()}', " \
                      f"'{self.ui.lineEdit_vri_signCipher.text()}', " \
                      f"'{self.ui.plainTextEdit_vri_miOwner.toPlainText()}', " \
                      f"'{vrf_date}', " \
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
                      f"'{self.ui.lineEdit_vri_FIF_id.text()}', " \
                      f"'{self.ui.lineEdit_mieta_number.text()}', " \
                      f"'{self.ui.comboBox_mieta_rank.currentText()}', " \
                      f"'{self.ui.lineEdit_mieta_rank_title.text()}', " \
                      f"'{self.ui.lineEdit_mieta_npenumber.text()}', " \
                      f"'{self.ui.lineEdit_mieta_schematype.text()}', " \
                      f"'{self.ui.plainTextEdit_mieta_schematitle.toPlainText()}', " \
                      f"{last_scan_date});"
        print(sql_replace)
        MySQLConnection.verify_connection()
        connection = MySQLConnection.create_connection()
        result = MySQLConnection.execute_query(connection, sql_replace)
        connection.close()
        if result[0]:
            vri_id = str(result[1])
            self._update_vri_dicts()
            self._update_vri_table(mi_id, vri_id)
            self._update_vri_and_mieta_tab(vri_id)
            QMessageBox.information(self, "Сохранено", "Информация о поверке сохранена")
        else:
            QMessageBox.critical(self, "Ошибка сохранения", "Сохранение не выполнено, произошла ошибка")

    # ---------------------------------------КЛИК ПО КНОПКЕ "СОХРАНИТЬ ЭТАЛОН"-----------------------------------------
    def _on_save_mieta(self):
        mi_id = self.ui.lineEdit_mi_id.text()
        vri_id = self.ui.lineEdit_vri_id.text()
        if not vri_id:  # если и на экране пусто - ошибка
            QMessageBox.critical(self, "Ошибка", "Для оборудования отсутствуют сохраненные поверки")
            return
        if not self.ui.lineEdit_mieta_number.text():  # если отсутствует номер эталона - ошибка
            QMessageBox.critical(self, "Ошибка", "Не указан номер в реестре эталонов")
            return

        sql_replace = f"UPDATE mis_vri_info SET " \
                      f"vri_mieta_number = '{self.ui.lineEdit_mieta_number.text()}', " \
                      f"vri_mieta_rankcode = '{self.ui.comboBox_mieta_rank.currentText()}', " \
                      f"vri_mieta_npenumber = '{self.ui.lineEdit_mieta_npenumber.text()}', " \
                      f"vri_mieta_schematype = '{self.ui.lineEdit_mieta_schematype.text()}', " \
                      f"vri_mieta_schematitle = '{self.ui.plainTextEdit_mieta_schematitle.toPlainText()}', " \
                      f"vri_mieta_rankclass = '{self.ui.lineEdit_mieta_rank_title.text()}' " \
                      f"WHERE vri_id = '{int(vri_id)}';"
        MySQLConnection.verify_connection()
        connection = MySQLConnection.create_connection()
        MySQLConnection.execute_query(connection, sql_replace)
        connection.close()

        self._update_vri_dicts()
        self._update_vri_table(mi_id, vri_id)
        self._update_vri_and_mieta_tab(vri_id)

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
                MySQLConnection.verify_connection()
                connection = MySQLConnection.create_connection()
                MySQLConnection.execute_transaction_query(connection, sql_delete_1, sql_delete_2, sql_delete_3)
                connection.close()

                self._update_mi_dicts()
                self._update_vri_dicts()

                self._update_mi_table()
                self._update_vri_table()
                self._clear_all()

    # todo добавить логику по поиску прибора, который оказался эталоном
    # -----------------------------------------КЛИК ПО КНОПКЕ "УДАЛИТЬ ПОВЕРКУ-"---------------------------------------
    def _on_delete_vri(self, mi_id=None, vri_id=None, delete_confirm=True):
        if not mi_id and self.ui.lineEdit_mi_id.text():
            mi_id = self.ui.lineEdit_mi_id.text()
        if not vri_id:
            if self.ui.lineEdit_vri_id.text():
                vri_id = self.ui.lineEdit_vri_id.text()
            else:
                return

        result = 1
        if delete_confirm:
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

        if not delete_confirm or result == 0:
            sql_delete = f"DELETE FROM mis_vri_info WHERE vri_id = {int(vri_id)}"
            MySQLConnection.verify_connection()
            connection = MySQLConnection.create_connection()
            MySQLConnection.execute_transaction_query(connection, sql_delete)
            connection.close()

            self._update_vri_dicts()
            self._update_vri_table(mi_id)

            if self.tbl_vri_proxy_model.rowCount() > 0:
                vri_id = self.tbl_vri_proxy_model.index(0, 6).data()
                if vri_id:
                    self._update_vri_and_mieta_tab(vri_id)
                    self.ui.tableView_vri_list.selectRow(0)
            else:
                self._clear_vri_and_mieta_tab()
                self._clear_mieta_tab()

    # -------------------------------------КЛИК ПО КНОПКЕ "УДАЛИТЬ ВСЕ"------------------------------------------------
    def _delete_all_from_db(self):
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Подтверждение удаления")
        dialog.setText(f"Вы действительно хотите удалить всю информацию об оборудовании?\n"
                       f"Также удалится вся информация о поверках и эталонах.")
        dialog.setIcon(QMessageBox.Warning)
        btn_yes = QPushButton("&Да")
        btn_no = QPushButton("&Нет")
        dialog.addButton(btn_yes, QMessageBox.AcceptRole)
        dialog.addButton(btn_no, QMessageBox.RejectRole)
        dialog.setDefaultButton(btn_no)
        dialog.setEscapeButton(btn_no)
        result = dialog.exec()
        if result == 0:
            sql_delete_1 = f"TRUNCATE mis"
            sql_delete_2 = f"TRUNCATE mis_departments"
            sql_delete_3 = f"TRUNCATE mis_vri_info"
            MySQLConnection.verify_connection()
            connection = MySQLConnection.create_connection()
            MySQLConnection.execute_transaction_query(connection, sql_delete_1, sql_delete_2, sql_delete_3)
            connection.close()
            self._refresh_all()

    # -------------------------------------КЛИК ПО КНОПКЕ "НАЙТИ ПОВЕРКИ"----------------------------------------------
    def _on_find_vri(self):
        mi_id = self.ui.lineEdit_mi_id.text()
        if not mi_id:
            return
        reestr_number = self.ui.lineEdit_reestr.text()
        manuf_number = self.ui.lineEdit_number.text()
        self.search_thread.is_running = True
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
        self.progress_dialog = QProgressDialog(self)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.setWindowTitle("ОЖИДАЙТЕ! Идет поиск!")
        self.progress_dialog.setCancelButtonText("Прервать")
        self.progress_dialog.canceled.connect(self._on_search_stopped)
        self.progress_dialog.setRange(0, 100)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.resize(350, 100)
        self.progress_dialog.show()
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

            self.progress_dialog = QProgressDialog(self)
            self.progress_dialog.setAutoClose(False)
            self.progress_dialog.setAutoReset(False)
            self.progress_dialog.setWindowTitle("ОЖИДАЙТЕ! Идет поиск!")
            self.progress_dialog.setCancelButtonText("Прервать")
            self.progress_dialog.canceled.connect(self._on_search_stopped)
            self.progress_dialog.setRange(0, 100)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.resize(350, 100)
            self.progress_dialog.show()
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

            self.progress_dialog = QProgressDialog(self)
            self.progress_dialog.setAutoClose(False)
            self.progress_dialog.setAutoReset(False)
            self.progress_dialog.setWindowTitle("ОЖИДАЙТЕ! Идет поиск!")
            self.progress_dialog.setCancelButtonText("Прервать")
            print("connected")
            self.progress_dialog.canceled.connect(self._on_search_stopped)
            self.progress_dialog.setRange(0, 100)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.resize(350, 100)
            self.progress_dialog.show()
            if self.eq_type == "mit":
                self._update_progressbar(0, "Поиск номера в реестре утвержденных типов СИ")
            elif self.eq_type == "mieta":
                self._update_progressbar(0, "Сбор информации о СИ, применяемом в качестве эталона")
            elif self.eq_type == "vri_id":
                self._update_progressbar(0, "Сбор информации из свидетельства о поверке")

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
        if RX_MIETA.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер в перечне СИ, применяемых в качестве эталонов")
            self.eq_type = "mieta"
            self.get_type = "vri"
        elif RX_CERT_NUMBER.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер свидетельства о поверке")
            self.eq_type = "vri"
            self.get_type = "vri"
        elif RX_VRI_ID.indexIn(dialog.textValue()) == 0:
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

        if RX_MIT.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер реестра СИ")
            self.eq_type = "mit"
        elif RX_NPE.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Государственный первичный эталон")
            self.eq_type = "npe"
        elif RX_UVE.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер эталона единицы величины")
            self.eq_type = "uve"
        elif RX_MIETA.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер в перечне СИ, применяемых в качестве эталонов")
            self.eq_type = "mieta"
        elif RX_CERT_NUMBER.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер свидетельства о поверке")
            self.eq_type = "vri_id"
        elif RX_VRI_ID.indexIn(dialog.textValue()) == 0:
            dialog.setLabelText(f"Номер записи сведений в ФИФ ОЕИ")
            self.eq_type = "vri_id"
        else:
            dialog.setLabelText("Введенный номер не определяется. Проверьте правильность ввода")

    # --------------------------------------ОБРАБОТКА ПОЛУЧЕННОГО ОТВЕТА ОТ СЕРВЕРА------------------------------------
    def _on_getting_resp(self, resp):
        if not resp or resp.startswith("Error") or resp.startswith("<!DOCTYPE html>"):
            if self.is_scanning_run:
                self.progress_dialog.close()
            else:
                self._on_search_stopped()
            if "timed out" in resp:
                QMessageBox.critical(self, "Ошибка", f"ФГИС \"АРШИН\" не отвечает.\n"
                                                     f"Попробуйте запустить поиск позже.")
            else:
                QMessageBox.critical(self, "Ошибка", f"Возникла ошибка получения сведений из ФГИС \"АРШИН\".\n{resp}")
            return
        elif resp == "stop":
            QMessageBox.information(self, "Ошибка", "Поиск прерван")
            if self.is_scanning_run:
                self.progress_dialog.close()
            else:
                self._on_search_stopped()
            return
        else:
            try:
                self.resp_json = json.loads(resp)
            except JSONDecodeError as err:
                QMessageBox.critical(self, "Ошибка", f"Невозможно распознать ответ от ФГИС \"АРШИН\".\n{resp}")
                if self.is_scanning_run:
                    self.progress_dialog.close()
                else:
                    self._on_search_stopped()
                return

            if self.resp_json:

                # ЕСЛИ ИЩЕМ ПОВЕРКИ ПО НОМЕРУ В РЕЕСТРЕ И ЗАВОДСКОМУ НОМЕРУ
                if self.get_type == "find_vri":
                    self._on_find_vri_resp()
                    return

                # ЕСЛИ ЗАПУСКАЕМ СКАННЕР ОБОРУДОВАНИЯ
                elif self.is_scanning_run:

                    if 'response' not in self.resp_json and 'result' not in self.resp_json:
                        if self._get_next_scan_vars():
                            self._scan_vri()
                        else:
                            return

                    if 'xcdb/vri/select?' in self.search_thread.url:

                        if len(self.resp_json['response']['docs']) < 20:
                            for doc in self.resp_json['response']['docs']:
                                self.scan_info['set_of_vri_id'].add(doc['vri_id'])
                                if 'mieta.number' in doc:
                                    self.scan_info['set_of_mieta_id'].add(doc['mieta.number'])

                        if self.resp_json['response']['docs'] and \
                                'mi.mitnumber' in self.resp_json['response']['docs'][0] and \
                                'mi.number' in self.resp_json['response']['docs'][0]:
                            self.scan_info['reestr'] = self.resp_json['response']['docs'][0]['mi.mitnumber']
                            self.scan_info['title'] = self.resp_json['response']['docs'][0]['mi.mititle']
                            self.scan_info['manuf_number'] = self.resp_json['response']['docs'][0]['mi.number']

                            url = f"https://fgis.gost.ru/fundmetrology/cm/xcdb/vri/select?" \
                                  f"fq=mi.mitnumber:{self.scan_info['reestr']}&" \
                                  f"fq=mi.number:{self.scan_info['manuf_number']}&" \
                                  f"fl=mieta.number&fl=vri_id&q=*&rows=100&sort=verification_date+desc"
                            self.search_thread.url = url
                            self.search_thread.start()
                            return

                        if self.scan_info['set_of_mieta_id']:
                            mieta_number = self.scan_info['set_of_mieta_id'].pop()
                            url = f"https://fgis.gost.ru/fundmetrology/cm/xcdb/vri/select?" \
                                  f"q=mieta.number:{mieta_number}&fl=vri_id&sort=verification_date+desc"
                            self.search_thread.url = url
                            self.search_thread.start()
                            return

                    elif 'iaux/vri/' in self.search_thread.url:
                        self.scan_info['list_of_scan_vri'].append(self.resp_json)
                        self.scan_info['list_of_scan_vri'][len(self.scan_info['list_of_scan_vri']) - 1]['vri_FIF_id'] = \
                            self.search_thread.url.rsplit('/', 1)[1]

                        if 'etaMI' in self.resp_json['result']['miInfo']:
                            mieta_number = self.resp_json['result']['miInfo']['etaMI']['regNumber']
                            url = f"https://fgis.gost.ru/fundmetrology/cm/icdb/mieta/select?" \
                                  f"q=number:{mieta_number}"
                            self.search_thread.url = url
                            self.search_thread.start()
                            return
                        else:
                            self.scan_info['list_of_scan_mieta'].append("")

                    elif 'icdb/mieta/select?' in self.search_thread.url:
                        if len(self.resp_json['response']['docs']) == 1:
                            self.scan_info['list_of_scan_mieta'].append(self.resp_json['response']['docs'][0])
                            self.scan_info['list_of_scan_mieta'][len(self.scan_info['list_of_scan_mieta']) - 1][
                                'vri_FIF_id'] = \
                            self.scan_info['list_of_scan_vri'][len(self.scan_info['list_of_scan_vri']) - 1][
                                'vri_FIF_id']
                        else:
                            self.scan_info['list_of_scan_mieta'].append("")

                    elif 'api/registry/4/data?' in self.search_thread.url:
                        if self.resp_json['result']['items']:
                            self.scan_info['scan_mit'] = self.resp_json['result']['items'][0]
                        print(self.scan_info['scan_mit'])
                        print(self.scan_info['list_of_scan_vri'])
                        print(self.scan_info['list_of_scan_mieta'])

                        if self._get_next_scan_vars():
                            self._scan_vri()
                        else:
                            return

                    if self.scan_info['set_of_vri_id']:
                        vri_id = self.scan_info['set_of_vri_id'].pop()
                        url = f"https://fgis.gost.ru/fundmetrology/cm/iaux/vri/{vri_id}"
                        self.search_thread.url = url
                        self.search_thread.start()
                        return

                    url = f"https://fgis.gost.ru/fundmetrology/api/registry/4/data?" \
                          f"pageNumber=1&pageSize=20&orgID=CURRENT_ORG&" \
                          f"filterBy=foei:NumberSI&filterValues={self.scan_info['reestr']}&" \
                          f"filterBy=foei:NameSI&filterValues={self.scan_info['title']}"
                    self.search_thread.url = url
                    self.search_thread.start()
                    return

                # ЕСЛИ ДОБАВЛЯЕМ ОБОРУДОВАНИЕ
                elif self.get_type != "vri":
                    if self.get_type == "find_vri_info":
                        self.vri.append(self.resp_json)
                        # self._get_vri_info()
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
                        self.vri.append(self.resp_json)
                        self.vri[len(self.vri) - 1]['vri_id'] = self.search_thread.url.rsplit('/', 1)[1]
                        self._get_vri()
                    elif "mieta?" in self.search_thread.url:
                        self.mieta_search = self.resp_json
                        self._get_mieta_search()
                    elif "mieta/" in self.search_thread.url:
                        self.mieta = self.resp_json
                        self._get_mieta()
                    else:
                        self._on_search_stopped()
                # ЕСЛИ ДОБАВЛЯЕМ РЕЗУЛЬТАТЫ ПОВЕРКИ
                else:
                    if self.eq_type == "vri_id":
                        self.vri.append(self.resp_json)
                        # self._get_vri_info()
                    elif "vri" in self.search_thread.url:
                        self._get_vri()
                    elif "mieta" in self.search_thread.url:
                        self._get_mieta()
                    else:
                        self._on_search_stopped()
            else:
                QMessageBox.critical(self, "Ошибка", f"Возникла ошибка получения сведений из ФГИС \"АРШИН\".\n{resp}")
                self._on_search_stopped()
                return

    # СОХРАНЕНИЕ ИНФОРМАЦИИ ПО РЕЗУЛЬТАТАМ ДОБАВЛЕНИЯ ОБОРУДОВАНИЯ ИЗ АРШИНА ПО НОМЕРУ
    def _save_from_arshin(self):
        save_dict = get_resp_dict(self.mit, self.vri, self.mieta)

        reg_card_number = f"{QDateTime().currentDateTime().toString('dd_MM_yy HH:mm:ss:zzz')}"
        quantity = f"Количество: {save_dict['quantity']}" if save_dict['quantity'] else ""
        status = "СИ в качестве эталона" if save_dict['mieta_number'] else "СИ"

        sql_insert = f"INSERT INTO mis (" \
                     f"mis_reg_card_number, " \
                     f"mi_status, " \
                     f"mi_reestr, " \
                     f"mi_title, " \
                     f"mi_type, " \
                     f"mi_modification, " \
                     f"mi_number, " \
                     f"mi_inv_number, " \
                     f"mi_manufacturer, " \
                     f"mi_manuf_year, " \
                     f"mi_MPI, " \
                     f"mi_other_characteristics" \
                     f") VALUES (" \
                     f"'{reg_card_number}', " \
                     f"'{status}', " \
                     f"'{save_dict['mi_reestr']}', " \
                     f"'{save_dict['mi_title']}', " \
                     f"'{save_dict['mi_type']}', " \
                     f"'{save_dict['mi_modification']}', " \
                     f"'{save_dict['mi_number']}', " \
                     f"'{save_dict['mi_inv_number']}', " \
                     f"'{save_dict['mi_manufacturer']}', " \
                     f"'{save_dict['mi_manuf_year']}', " \
                     f"'{save_dict['mi_MPI']}', " \
                     f"'{quantity}'" \
                     f")"
        print(sql_insert)
        MySQLConnection.verify_connection()
        connection = MySQLConnection.create_connection()
        result = MySQLConnection.execute_query(connection, sql_insert)
        if result[0]:
            mi_id = result[1]
            if self.eq_type == "vri_id" or self.eq_type == "mieta":
                if save_dict['vris']:
                    for vri_dict in save_dict['vris']:
                        sql_insert = f"INSERT INTO mis_vri_info (" \
                                     f"vri_id, " \
                                     f"vri_mi_id, " \
                                     f"vri_organization, " \
                                     f"vri_signCipher, " \
                                     f"vri_miOwner, " \
                                     f"vri_vrfDate, " \
                                     f"vri_validDate, " \
                                     f"vri_vriType, " \
                                     f"vri_docTitle, " \
                                     f"vri_applicable, " \
                                     f"vri_certNum, " \
                                     f"vri_stickerNum, " \
                                     f"vri_signPass, " \
                                     f"vri_signMi, " \
                                     f"vri_inapplicable_reason, " \
                                     f"vri_structure, " \
                                     f"vri_briefIndicator, " \
                                     f"vri_briefCharacteristics, " \
                                     f"vri_ranges, " \
                                     f"vri_values, " \
                                     f"vri_channels, " \
                                     f"vri_blocks, " \
                                     f"vri_additional_info, " \
                                     f"vri_info, " \
                                     f"vri_FIF_id, " \
                                     f"vri_mieta_number, " \
                                     f"vri_mieta_rankcode, " \
                                     f"vri_mieta_rankclass, " \
                                     f"vri_mieta_npenumber, " \
                                     f"vri_mieta_schematype, " \
                                     f"vri_mieta_schematitle" \
                                     f") VALUES (" \
                                     f"NULL, " \
                                     f"{mi_id}, " \
                                     f"'{vri_dict['vri_organization']}', " \
                                     f"'{vri_dict['vri_signCipher']}', " \
                                     f"'{vri_dict['vri_miOwner']}', " \
                                     f"'{vri_dict['vri_vrfDate']}', " \
                                     f"'{vri_dict['vri_validDate']}', " \
                                     f"'{vri_dict['vri_vriType']}', " \
                                     f"'{vri_dict['vri_docTitle']}', " \
                                     f"{int(vri_dict['vri_applicable'])}, " \
                                     f"'{vri_dict['vri_certNum']}', " \
                                     f"'{vri_dict['vri_stickerNum']}', " \
                                     f"{int(vri_dict['vri_signPass'])}, " \
                                     f"{int(vri_dict['vri_signMi'])}, " \
                                     f"'', " \
                                     f"'{vri_dict['vri_structure']}', " \
                                     f"{int(vri_dict['vri_briefIndicator'])}, " \
                                     f"'{vri_dict['vri_briefCharacteristics']}', " \
                                     f"'{vri_dict['vri_ranges']}', " \
                                     f"'{vri_dict['vri_values']}', " \
                                     f"'{vri_dict['vri_channels']}', " \
                                     f"'{vri_dict['vri_blocks']}', " \
                                     f"'{vri_dict['vri_additional_info']}', " \
                                     f"'', " \
                                     f"'{vri_dict['vri_FIF_id']}', " \
                                     f"'{save_dict['mieta_number']}', " \
                                     f"'{save_dict['mieta_rankcode']}', " \
                                     f"'{save_dict['mieta_rankclass']}', " \
                                     f"'{save_dict['mieta_npenumber']}', " \
                                     f"'{save_dict['mieta_schematype']}', " \
                                     f"'{save_dict['mieta_schematitle']}')"
                        print(sql_insert)
                        MySQLConnection.execute_query(connection, sql_insert)
                connection.close()
                self._update_vri_dicts()
            self._update_mi_dicts()
            self._update_mi_table()
            self._on_mi_select(mi_id)

        connection.close()

    # СОХРАНЕНИЕ ИНФОРМАЦИИ ПО РЕЗУЛЬТАТАМ ПОЛНОЙ ПРОВЕРКИ (СКАНИРОВАНИЯ) ОБОРУДОВАНИЯ
    def _save_scan_info(self, mit_scan=None, vri_scan=None, mieta_scan=None):
        scan_dict = get_resp_dict_new(mit_scan, vri_scan, mieta_scan)
        MySQLConnection.verify_connection()
        connection = MySQLConnection.create_connection()

        # Если никакие результаты для прибора не найдены, записываем дату сканирования в поверки, обновляем
        # словарь поверок и выходим
        if not scan_dict:
            # for vri_id in self.mis_vri_dict[self.mi_id_scan]:
            sql_update = f"UPDATE mis_vri_info SET " \
                         f"vri_last_scan_date='{QDate.currentDate().toString('yyyy-MM-dd')}' " \
                         f"WHERE vri_mi_id={int(self.mi_id_scan)};"
            MySQLConnection.execute_query(connection, sql_update)
            connection.close()
            self._update_vri_dicts()
            return

        mi_status = "СИ в качестве эталона" if scan_dict['mietas'] else "СИ"
        sql_update = f"UPDATE mis SET " \
                     f"mi_status='{mi_status}', " \
                     f"mi_reestr='{scan_dict['mi_reestr']}', " \
                     f"mi_title='{scan_dict['mi_title']}', " \
                     f"mi_type='{scan_dict['mi_type']}', " \
                     f"mi_modification='{scan_dict['mi_modification']}', " \
                     f"mi_number='{scan_dict['mi_number']}', " \
                     f"mi_inv_number='{scan_dict['mi_inv_number']}', " \
                     f"mi_manufacturer='{scan_dict['mi_manufacturer']}', " \
                     f"mi_manuf_year='{scan_dict['mi_manuf_year']}', " \
                     f"mi_MPI='{scan_dict['mi_MPI']}', " \
                     f"mi_last_scan_date='{QDate.currentDate().toString('yyyy-MM-dd')}' " \
                     f"WHERE mi_id={int(self.mi_id_scan)};"

        MySQLConnection.execute_query(connection, sql_update)
        self._update_mi_dicts()
        self._update_mi_table()

        for vri_info in scan_dict['vris']:
            # vri_info = scan_dict['vris'][0]
            sql_insert = f"INSERT INTO mis_vri_info (" \
                         f"vri_id, " \
                         f"vri_mi_id, " \
                         f"vri_organization, " \
                         f"vri_signCipher, " \
                         f"vri_miOwner, " \
                         f"vri_vrfDate, " \
                         f"vri_validDate, " \
                         f"vri_vriType, " \
                         f"vri_docTitle, " \
                         f"vri_applicable, " \
                         f"vri_certNum, " \
                         f"vri_stickerNum, " \
                         f"vri_signPass, " \
                         f"vri_signMi, " \
                         f"vri_inapplicable_reason, " \
                         f"vri_structure, " \
                         f"vri_briefIndicator, " \
                         f"vri_briefCharacteristics, " \
                         f"vri_ranges, " \
                         f"vri_values, " \
                         f"vri_channels, " \
                         f"vri_blocks, " \
                         f"vri_additional_info, " \
                         f"vri_info, " \
                         f"vri_FIF_id, " \
                         f"vri_mieta_number, " \
                         f"vri_mieta_rankcode, " \
                         f"vri_mieta_rankclass, " \
                         f"vri_mieta_npenumber, " \
                         f"vri_mieta_schematype, " \
                         f"vri_mieta_schematitle" \
                         f") VALUES (" \
                         f"NULL, " \
                         f"{int(self.mi_id_scan)}, " \
                         f"'{vri_info['vri_organization']}', " \
                         f"'{vri_info['vri_signCipher']}', " \
                         f"'{vri_info['vri_miOwner']}', " \
                         f"'{vri_info['vri_vrfDate']}', " \
                         f"'{vri_info['vri_validDate']}', " \
                         f"'{vri_info['vri_vriType']}', " \
                         f"'{vri_info['vri_docTitle']}', " \
                         f"{int(vri_info['vri_applicable'])}, " \
                         f"'{vri_info['vri_certNum']}', " \
                         f"'{vri_info['vri_stickerNum']}', " \
                         f"{int(vri_info['vri_signPass'])}, " \
                         f"{int(vri_info['vri_signMi'])}, " \
                         f"'', " \
                         f"'{vri_info['vri_structure']}', " \
                         f"{int(vri_info['vri_briefIndicator'])}, " \
                         f"'{vri_info['vri_briefCharacteristics']}', " \
                         f"'{vri_info['vri_ranges']}', " \
                         f"'{vri_info['vri_values']}', " \
                         f"'{vri_info['vri_channels']}', " \
                         f"'{vri_info['vri_blocks']}', " \
                         f"'', " \
                         f"'', " \
                         f"'{vri_info['vri_FIF_id']}', " \
                         f"'', " \
                         f"'', " \
                         f"'', " \
                         f"'', " \
                         f"'', " \
                         f"'')"
            print(sql_insert)
            MySQLConnection.execute_query(connection, sql_insert)

        for mieta_info in scan_dict['mietas']:
            sql_update = f"UPDATE mis_vri_info SET " \
                         f"vri_mieta_number='{mieta_info['mieta_number']}', " \
                         f"vri_mieta_rankcode='{mieta_info['mieta_rankcode']}', " \
                         f"vri_mieta_rankclass='{mieta_info['mieta_rankclass']}', " \
                         f"vri_mieta_npenumber='{mieta_info['mieta_npenumber']}', " \
                         f"vri_mieta_schematype='{mieta_info['mieta_schematype']}', " \
                         f"vri_mieta_schematitle='{mieta_info['mieta_schematitle']}' " \
                         f"WHERE vri_FIF_id='{mieta_info['vri_FIF_id']}';"
            print(sql_update)
            MySQLConnection.execute_query(connection, sql_update)

        # for vri_id in self.mis_vri_dict[self.mi_id_scan]:
        #     sql_update = f"UPDATE mis_vri_info SET " \
        #                  f"vri_last_scan_date='{QDate.currentDate().toString('yyyy-MM-dd')}' " \
        #                  f"WHERE vri_id={int(vri_id)};"
        # MySQLConnection.execute_query(connection, sql_update)

        self._update_vri_dicts()
        connection.close()

    # ------------------------------------------ОБРАБОТКА MIT_SEARCH---------------------------------------------------
    def _get_mit_search(self):
        if 'result' in self.resp_json and 'count' in self.resp_json['result']:
            result = self.resp_json['result']
            count = result.get('count', "")

            # если ищем по номеру в реестре
            if self.eq_type == "mit":
                # если результаты не найдены, останавливаем поиск и выдаем сообщение
                if count == 0:
                    self._on_search_stopped()
                    QMessageBox.critical(self, "Ошибка",
                                         f"Очевидно, вы пытались ввести номер из реестра утвержденных типв СИ, но ФГИС "
                                         f"\"АРШИН\" не содержит такой записи.\n"
                                         f"Проверьте правильность введенного номера")
                    return
                # если найдена одна запись, устанавливаем прогресс в 50 и ищем полную информацию о реестре по mit_id
                elif count == 1:
                    if 'items' in result and 'mit_id' in result['items'][0]:
                        mit_id = result['items'][0]['mit_id']
                        self._update_progressbar(50, "Поиск информации в реестре утвержденных типов СИ")
                        self.search_thread.url = f"{URL_START}/mit/{mit_id}"
                        self.search_thread.start()
                # если найдено от 2 до 50 записей, создаем список и даем диалог выбора подходящего реестра
                elif count < 50:
                    items_list = list()
                    if 'items' in result:
                        for item in result['items']:
                            item_name_list = list()
                            item_name_list.append(item.get('number', ""))
                            item_name_list.append(item.get('title', ""))
                            item_name_list.append(item.get('notation', ""))
                            item_name_list.append(item.get('manufactorer', ""))
                            item_name = " ".join(item_name_list)
                            if len(item_name) > 150:
                                items_list.append(f"{item_name[:150]}...")
                            else:
                                items_list.append(item_name)

                    s, ok = QInputDialog.getItem(self, "Выбор типа СИ", "Выберите необходимый тип СИ", items_list,
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
                    self._save_from_arshin()
                    self._on_search_finished()
                    return
                # если результаты найдены, берем id первой записи и ищем реестр
                else:
                    self._update_progressbar(80, "Сбор информации о типе СИ")
                    if 'items' in result and 'mit_id' in result['items'][0]:
                        self.search_thread.url = f"{URL_START}/mit/{result['items'][0]['mit_id']}"
                        self.search_thread.start()
                    else:
                        self.progress_dialog.close()
        else:
            self._on_search_stopped()
            return

    # -------------------------------------------ОБРАБОТКА MIT---------------------------------------------------------
    def _get_mit(self):
        # СОХРАНЯЕМ РЕЗУЛЬТАТЫ ПОИСКА
        self._save_from_arshin()
        self._on_search_finished()

    # -------------------------------------------ОБРАБОТКА VRI_SEARCH--------------------------------------------------
    def _get_vri_search(self):
        # получаем self.vri_search
        if "search" in self.search_thread.url and 'result' in self.resp_json and 'count' in self.resp_json[
            'result']:
            if self.resp_json['result']['count'] == 0:
                self.progress_dialog.close()
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
                    self.progress_dialog.close()
            else:
                QMessageBox.critical(self, "Ошибка", "Слишком много результатов поиска. Уточните номер свидетельства")
                self.progress_dialog.close()
                return
        else:
            self._on_search_stopped()
            return

    # -----------------------------------------------ОБРАБОТКА VRI-----------------------------------------------------
    def _get_vri(self):

        # ЕСЛИ ИЩЕМ ПО НОМЕРУ ЭТАЛОНА
        if self.eq_type == "mieta":
            # ЕСЛИ В СПИСКЕ ID ПОВЕРОК БОЛЕЕ ОДНОЙ ЗАПИСИ, ПЕРЕХОДИМ К ПОИСКУ ВТОРОЙ И Т.Д.,
            # ИНАЧЕ ПЕРЕХОДИМ К ПОИСКУ РЕЕСТРА
            if self.temp_set_of_vri_id:
                self.search_thread.url = f"{URL_START}/vri/{self.temp_set_of_vri_id.pop()}"
                self.search_thread.start()
                return

            elif 'result' in self.mieta:
                result = self.mieta['result']

                reestr = result.get('mitype_num', "")
                title = result.get('mitype', "")
                if reestr and title:
                    self._update_progressbar(60, "Поиск номера в реестре утвержденных типов СИ")
                    self.search_thread.url = f"{URL_START}/mit?rows=100&search={reestr}%20{title.replace(' ', '%20')}"
                    self.search_thread.start()
                    return

        current_vri = self.vri[len(self.vri) - 1]
        if 'result' not in current_vri or 'miInfo' not in current_vri['result']:
            self._on_search_stopped()
            QMessageBox.critical(self, "Ошибка",
                                 f"Произошла ошибка получения данных из ФГИС \"АРШИН\".\n"
                                 f"Попробуйте запустить поиск заново.")
            return

        miInfo = current_vri['result']['miInfo']

        # ЕСЛИ ИЩЕМ ПО НОМЕРУ ПОВЕРКИ
        if self.eq_type == "vri_id":

            # ЕСЛИ ЭТО ОКАЗАЛСЯ ЭТАЛОН, ПЕРЕХОДИМ К ПОИСКУ ЭТАЛОНА
            if 'etaMI' in miInfo:
                miInfo = miInfo['etaMI']
                if 'regNumber' in miInfo:
                    regNumber = miInfo['regNumber'].rsplit('.', 1)[1]
                    self.vri.clear()
                    self.eq_type = "mieta"
                    self._update_progressbar(20, "Получение информации об эталоне")
                    self.search_thread.url = f"{URL_START}/mieta/{regNumber}"
                    self.search_thread.start()
                    return

            # ЕСЛИ ЭТО ОБЫЧНОЕ СИ ИЛИ ПАРТИЯ, ЗАПУСКАЕМ ПОИСК В РЕЕСТРЕ ПО НОМЕРУ В РЕЕСТРЕ И НАИМЕНОВАНИЮ
            elif 'singleMI' in miInfo or 'partyMI' in miInfo:

                # ДОБАВЛЯЕМ ID ПОВЕРКИ ВО ВРЕМЕННОЕ МНОЖЕСТВО
                # self.temp_list_of_vri_id.append(self.number)

                # ПОЛУЧАЕМ НОМЕР В РЕЕСТРЕ И НАИМЕНОВАНИЕ
                if 'singleMI' in miInfo:
                    miInfo = miInfo['singleMI']
                elif 'partyMI' in miInfo:
                    miInfo = miInfo['partyMI']
                reestr = miInfo.get('mitypeNumber', "")
                title = miInfo.get('mitypeTitle', "")

                # ЕСЛИ СИ В РЕЕСТРЕ, ЗАПУСКАЕМ ПОИСК В РЕЕСТРЕ
                if reestr and title:
                    self._update_progressbar(50, "Поиск номера в реестре утвержденных типов СИ")
                    self.search_thread.url = f"{URL_START}/mit?rows=100&search={reestr}%20{title.replace(' ', '%20')}"
                    self.search_thread.start()
                    return
                # ЕСЛИ СИ НЕ В РЕЕСТРЕ, ПЕРЕХОДИМ К СОХРАНЕНИЮ РЕЗУЛЬТАТОВ ПОИСКА
                else:
                    self._save_from_arshin()
                    self._on_search_finished()
                    return

    # ---------------------------------ПОЛУЧЕНИЕ ИНФОРМАЦИИ ОБ ЭТАЛОНЕ ИЗ АРШИНА---------------------------------------
    def _get_mieta_search(self):
        # получаем self.mieta_search
        if 'result' in self.resp_json and 'count' in self.resp_json['result']:
            if self.resp_json['result']['count'] == 0:
                self.progress_dialog.close()
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
                self.progress_dialog.close()
                QMessageBox.critical(self, "Ошибка", "Слишком много результатов поиска. Уточните номер эталона")
                return

    # -----------------------------------------------ОБРАБОТКА MIETA---------------------------------------------------
    def _get_mieta(self):
        if 'result' in self.mieta:
            result = self.mieta['result']

            #   ЕСЛИ ИЩЕМ ПОВЕРКУ ПО НОМЕРУ ПОВЕРКИ, БЕРЕМ ID ПОВЕРКИ
            if self.get_type == "vri":
                self.eq_type = "vri_id"
                self.number = result['cresults'][0]['vri_id']
                self.search_thread.url = f"{URL_START}/vri/{self.number}"
                self.search_thread.start()
                return

            #   ЕСЛИ ДОБАВЛЯЕМ ОБОРУДОВАНИЕ ПО НОМЕРУ ПОВЕРКИ,
            #   БЕРЕМ НОМЕР В РЕЕСТРЕ, НАИМЕНОВАНИЕ И ПЕРЕХОДИМ К ПОИСКУ РЕЕСТРА
            if self.eq_type == "vri_id":
                reestr = result.get('mitype_num', "")
                title = result.get('mitype', "")
                if reestr and title:
                    self._update_progressbar(40, "Поиск номера в реестре утвержденных типов СИ")
                    self.search_thread.url = f"{URL_START}/mit?rows=100&search={reestr}%20{title.replace(' ', '%20')}"
                    self.search_thread.start()
                    return
                else:  # НЕВОЗМОЖНО, Т.К. ЭТАЛОН НЕ МОЖЕТ БЫТЬ НЕ В РЕЕСТРЕ
                    self._save_from_arshin()
                    return

            #   ЕСЛИ ДОБАВЛЯЕМ ОБОРУДОВАНИЕ ПО НОМЕРУ ЭТАЛОНА, СОХРАНЯЕМ ID ПОВЕРОК ВО ВРЕМЕННЫЙ СПИСОК,
            #   БЕРЕМ ПЕРВЫЙ ID НОМЕР В СПИСКЕ(САМЫЙ СВЕЖИЙ ПО ДАТЕ) И ПЕРЕХОДИМ К ПОИСКУ ИНФОРМАЦИИ О ПОВЕРКЕ
            if self.eq_type == "mieta":
                if 'cresults' in result:
                    for cresult in result['cresults']:
                        if 'vri_id' in cresult:
                            self.temp_set_of_vri_id.add(cresult['vri_id'])
                    self._update_progressbar(40, "Поиск информации о поверках")
                    self.search_thread.url = f"{URL_START}/vri/{self.temp_set_of_vri_id.pop()}"
                    self.search_thread.start()
                    return
        else:
            self._on_search_stopped()
            return

    # ----------------------------------------ЗАВЕРШЕНИЕ ПОИСКА--------------------------------------------------------
    def _on_search_finished(self):
        print("finished")
        if self.progress_dialog:
            self.progress_dialog.setLabelText("Поиск завершен")
            self.progress_dialog.setValue(100)
            self.progress_dialog.setCancelButtonText("Готово")
            self.progress_dialog.canceled.disconnect(self._on_search_stopped)
            self.progress_dialog.canceled.connect(self._check_duplicates)
        self._clear_search_vars()
        self._update_vri_table()

    # ------------------------------------ПРОВЕРКА НАЛИЧИЯ ТАКОЙ ЖЕ ЗАПИСИ---------------------------------------------
    def _check_duplicates(self):
        self.progress_dialog.canceled.disconnect(self._check_duplicates)
        self.progress_dialog.close()

        title = self.ui.plainTextEdit_title.toPlainText()
        modification = self.ui.lineEdit_modification.text()
        number = self.ui.lineEdit_number.text()
        if title and modification and number:
            if (title, modification, number) in self.set_of_mi:
                if QMessageBox.question(self, "Внимание!",
                                        f"Похожее оборудование - '{title} {modification} № {number}' "
                                        f"уже записано!\n"
                                        f"Сохранение найденных результатов приведет к дублированию записи!\n"
                                        f"Хотите просмотреть информацию о сохраненном оборудовании?") != 65536:
                    mi_id = func.get_mi_id_from_set_of_mi((title, modification, number), self.mi_dict)
                    self._on_mi_select(mi_id)
                    return

    # ---------------------------------------------ОСТАНОВКА ПОИСКА----------------------------------------------------
    def _on_search_stopped(self):
        print("stopped")
        self.search_thread.is_running = False
        self.ui.tableView_mi_list.selectionModel().clearSelection()
        self._clear_search_vars()
        self._clear_all()
        if self.get_type == "scan_cert_number":
            self.progress_dialog.close()
        elif self.progress_dialog:
            self.progress_dialog.canceled.disconnect(self._on_search_stopped)
            self.progress_dialog.close()

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
        self.temp_set_of_mieta_numbers.clear()
        self.mi_id_scan = ""
        self.vri_id_scan = ""
        self.cert_number_scan = ""
        self.mieta_number_scan = ""
        self.mit_scan = ""
        self.mieta_scan = []
        self.vri_scan = []

    # ----------------------------------------ОБНОВЛЕНИЕ ПРОГРЕССА ПОИСКА----------------------------------------------
    def _update_progressbar(self, val, text):
        self.progress_dialog.setLabelText(text)
        self.progress_dialog.setValue(val)

    def _get_measure_code_id(self):
        """
        :return: ВОЗВРАЩАЕМ ПОДВИД ИЗМЕРЕНИЙ, ВИД ИЗМЕРЕНИЙ ИЛИ "0" НА
        """
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
