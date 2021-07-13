import json
from json.decoder import JSONDecodeError

from PyQt5.QtCore import QRegExp, Qt, QThread, pyqtSignal, QDate
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox, QInputDialog

import functions_pkg.functions as func
from equipment_pkg.ui_add_eqipment_widget import Ui_Form
from functions_pkg.send_get_request import GetRequest
from departments_pkg.departments import DepartmentsWidget

url_start = "https://fgis.gost.ru/fundmetrology/eapi"


class SearchThread(QThread):
    msg_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.url = ""

    def run(self):
        self.sleep(1)
        print("thread running")
        print(self.url)
        resp = GetRequest.getRequest(self.url)
        print(resp)
        print("thread stopped")
        self.msg_signal.emit(resp)


class Ui_AddEquipment(QWidget):
    def __init__(self):
        super(Ui_AddEquipment, self).__init__()
        self.ui = Ui_Form()
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

        self.ui.label_output.setText("")
        self.dep_dict = func.get_departments()['dep_dict']
        self.ui.comboBox_measure_code.addItems(func.get_measure_codes())
        self.ui.comboBox_department.addItems(func.get_departments()['dep_name_list'])
        self.table_model = QStandardItemModel(0, 5, parent=self)
        self.ui.tableView_verification_info.setModel(self.table_model)
        self._clear_all()

    def _add_connects(self):
        self.ui.btn_check.clicked.connect(self._start_search)
        self.search_thread.msg_signal.connect(self._on_change, Qt.QueuedConnection)
        self.ui.lineEdit_input.textChanged.connect(self._verify_input)
        self.ui.lineEdit_input.returnPressed.connect(self._start_search)
        self.ui.comboBox_department.currentTextChanged.connect(self._on_dep_change)
        self.ui.tableView_verification_info.doubleClicked.connect(self._table_select)

    def _table_select(self, index):
        row = self.table_model.itemFromIndex(index).row()
        print(self.table_model.index(row, 2).data())

    def _on_dep_change(self, s):
        self.ui.comboBox_responsiblePerson.clear()
        dep_id = func.get_dep_id_from_name(s, self.dep_dict)
        self.ui.comboBox_responsiblePerson.addItems(func.get_workers_list(dep_id, func.get_workers()['worker_dict'],
                                                                          func.get_worker_deps()['dep_workers_dict'])[
                                                        'workers'])

    def _verify_input(self):
        self.eq_type = ""
        self.ui.label_output.setText("")
        rx_mit = QRegExp("^[1-9][0-9]{0,5}-[0-9]{2}$")
        rx_npe = QRegExp("^гэт[1-9][0-9]{0,2}-(([0-9]{2})|([0-9]{4}))$")
        rx_uve = QRegExp("^[1-3]\.[0-9]\.\S{3}\.\d{4}\.20[0-4]\d$")
        rx_mieta = QRegExp("^[1-9]\d{0,5}\.\d{2}\.(0Р|1Р|2Р|3Р|4Р|5Р|РЭ|ВЭ|СИ)\.\d+$")
        rx_svid = QRegExp("^(С|И)\-\S{1,3}\/[0-3][0-9]\-[0-1][0-9]\-20[2-5][0-9]\/\d{8,10}$")
        rx_mit.setCaseSensitivity(False)
        rx_npe.setCaseSensitivity(False)
        rx_uve.setCaseSensitivity(False)
        rx_mieta.setCaseSensitivity(False)
        rx_svid.setCaseSensitivity(False)
        doc_number = self.ui.lineEdit_input.text()
        if rx_mit.indexIn(self.ui.lineEdit_input.text()) == 0:
            self.eq_type = "mit"
            self.get_type = "mit"
            self.ui.label_output.setText(f"СИ с номером в реестре '{doc_number}'")
        elif rx_npe.indexIn(self.ui.lineEdit_input.text()) == 0:
            self.eq_type = "npe"
            self.get_type = "npe"
            self.ui.label_output.setText(f"Государственный первичный эталон '{doc_number}'")
        elif rx_uve.indexIn(self.ui.lineEdit_input.text()) == 0:
            self.eq_type = "uve"
            self.get_type = "uve"
            self.ui.label_output.setText(f"Эталон единицы величины '{doc_number}'")
        elif rx_mieta.indexIn(self.ui.lineEdit_input.text()) == 0:
            self.eq_type = "mieta"
            self.get_type = "mieta"
            self.ui.label_output.setText(f"СИ, применяемое в качестве эталона, с номером '{doc_number}'")
        elif rx_svid.indexIn(self.ui.lineEdit_input.text()) == 0:
            self.eq_type = "vri"
            self.get_type = "vri"
            self.ui.label_output.setText(f"СИ со свидетельством о поверке '{doc_number}'")
        else:
            self.ui.label_output.setText("Введенный номер не определяется. Проверьте правильность ввода")

    def _start_search(self):
        self._clear_all()
        if self.eq_type == "":
            QMessageBox.warning(self, "Предупреждение", "Введите корректный номер")
            return
        number = self.ui.lineEdit_input.text()

        self.ui.lineEdit_input.setDisabled(True)
        self.ui.btn_check.setDisabled(True)
        self.ui.btn_check.setText("Идет поиск...")

        self.ui.textEdit_result.setText("ОЖИДАЙТЕ!\nЗапущен поиск.\nПроцесс может длиться до 30 с.")

        url = f"{url_start}/{self.eq_type}?rows=100&search={number}"
        self.search_thread.url = url
        self.search_thread.start()

    def _on_change(self, resp):

        if not resp or resp.startswith("Error"):
            self.ui.textEdit_result.setText(f"Возникла ошибка получения сведений из ФГИС \"АРШИН\".\n{resp}")
            self._stop_search()
            return
        else:
            self.ui.textEdit_result.setText(resp)
            try:
                self.resp_json = json.loads(resp)
            except JSONDecodeError as err:
                self.ui.textEdit_result.setText(err.msg)
                self._stop_search()
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
                    self._stop_search()

    # СИ по номеру реестра
    def _get_mit(self):

        # получаем self.mit_search
        if "search" in self.search_thread.url and 'result' in self.resp_json and 'count' in self.resp_json['result']:

            # если ищем по номеру в реестре
            if self.eq_type == "mit":
                if self.resp_json['result']['count'] == 0:
                    self.ui.textEdit_result.setText(
                        f"Очевидно, вы пытались ввести номер реестра СИ, но ФГИС \"АРШИН\" не содержит такой записи.\n"
                        f"Перепроверьте правильность введенного номера: \'{self.ui.lineEdit_input.text()}\'")
                    self._stop_search()
                    return
                elif self.resp_json['result']['count'] == 1:
                    self.mit_search = self.resp_json
                    url = f"{url_start}/{self.eq_type}/{self.resp_json['result']['items'][0]['mit_id']}"
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
                        url = f"{url_start}/{self.eq_type}/{self.resp_json['result']['items'][items_list.index(s)]['mit_id']}"
                        self.search_thread.url = url
                        self.search_thread.start()
                else:
                    QMessageBox.critical(self, "Ошибка", "Слишком много результатов поиска. Уточните номер")
                    self._stop_search()
                    return

            # если ищем по номеру свидетельства

            elif self.eq_type == "vri" or self.eq_type == "mieta":
                if self.resp_json['result']['count'] == 0:
                    self.ui.textEdit_result.setText(f"Невозможно найти номер в реестре")
                else:
                    self.mit_search = self.resp_json
                    url = f"{url_start}/mit/{self.resp_json['result']['items'][0]['mit_id']}"
                    self.search_thread.url = url
                    self.search_thread.start()

        # получаем self.mit
        elif "mit/" in self.search_thread.url:
            self.mit = self.resp_json

            if self.eq_type == "mit":
                self._fill_mit()
            elif self.eq_type == "vri" or self.eq_type == "mieta":
                self._fill_vri()
                self._fill_mit()
                self._fill_vri_info()
            self._stop_search()

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
                    self.ui.textEdit_title.setText(miInfo['mitypeTitle'])
                    self.ui.textEdit_type.setPlainText(miInfo['modification'])
                    self.ui.lineEdit_modification.setText(miInfo['modification'])
                    if 'vriInfo' in self.vri['result']:
                        vriInfo = self.vri['result']['vriInfo']
                        if 'vrfDate' in vriInfo and 'validDate' in vriInfo:
                            start_date = vriInfo['vrfDate']
                            end_date = vriInfo['validDate']
                            self.ui.lineEdit_MPI.setText(str((int(end_date[-4:]) - int(start_date[-4:])) * 12))
                            self.ui.radioButton_MPI_yes.setChecked(True)
                        self._stop_search()

    # ______________________ЗАПОЛНЕНИЕ ИНФОРМАЦИИ С РЕЕСТРА__________________________
    def _fill_mit(self):
        if 'general' in self.mit:
            general = self.mit['general']
            # записываем номер реестра, наименование, тип
            if 'number' in general:
                self.ui.lineEdit_reestr.setText(general['number'])
            if 'title' in general:
                self.ui.textEdit_title.setText(general['title'])
            if 'notation' in general:
                self.ui.textEdit_type.setPlainText(" ,".join(general['notation']))
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
            self.ui.textEdit_manufacturer.setText(", ".join(manufacturer_list))
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

    # гэт
    def _get_npe(self, resp):
        try:
            resp_json = json.loads(resp)
            if resp_json['result']['count'] == 0:
                self.ui.textEdit_result.setText(
                    f"Очевидно, вы пытались ввести номер государственного первичного эталона, "
                    f"но ФГИС \"АРШИН\" не содержит такой записи.\n"
                    f"Перепроверьте правильность введенного номера: \'{self.ui.lineEdit_input.text()}\'.\n"
                    f"Актуальные эталоны можно <b>посмотреть<\\b> по ссылке "
                    f"<a href=\"https://fgis.gost.ru/fundmetrology/registry/12\">ссылка<\\a>")
            else:
                self.ui.textEdit_result.setText(resp)
        except JSONDecodeError as err:
            self.ui.textEdit_result.setText(err)

    # ZКС...
    def _get_uve(self, resp):
        try:
            resp_json = json.loads(resp)
            if resp_json['result']['count'] == 0:
                self.ui.textEdit_result.setText(
                    f"Очевидно, вы пытались ввести номер эталона единицы величины, "
                    f"но ФГИС \"АРШИН\" не содержит такой записи.\n"
                    f"Перепроверьте раскладку клавиатуры и правильность введенного номера: "
                    f"\'{self.ui.lineEdit_input.text()}\'")
            else:
                self.ui.textEdit_result.setText(resp)
        except JSONDecodeError as err:
            self.ui.textEdit_result.setText(err)

    # СИ как эталон
    def _get_mieta(self):

        # получаем self.mieta_search
        if 'result' in self.resp_json and 'count' in self.resp_json['result']:
            if self.resp_json['result']['count'] == 0:
                self.ui.textEdit_result.setText(
                    f"Очевидно, вы пытались ввести номер СИ, применяемого в качестве эталона, "
                    f"но ФГИС \"АРШИН\" не содержит такой записи.\n"
                    f"Перепроверьте раскладку клавиатуры и правильность введенного номера.")
            elif self.resp_json['result']['count'] == 1:
                self.mieta_search = self.resp_json
                if 'items' in self.resp_json['result'] and 'rmieta_id' in self.resp_json['result']['items'][0]:
                    mieta_id = self.resp_json['result']['items'][0]['rmieta_id']
                    url = f"{url_start}/mieta/{mieta_id}"
                    self.search_thread.url = url
                    self.search_thread.start()
            else:
                QMessageBox.critical(self, "Ошибка", "Слишком много результатов поиска. Уточните номер эталона")
                self._stop_search()
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
                self.ui.textEdit_mieta_schematitle.setPlainText(result['schematitle'])

            for cresult in result['cresults']:
                if 'vri_id' in cresult and 'org_title' in cresult:
                    self.vri_numbers.append([cresult['vri_id'], cresult['org_title']])

            if self.eq_type == "vri":
                if 'mitype_num' in result and 'mitype' in result:  # номер реестра
                    url = f"{url_start}/mit?rows=100&search={result['mitype_num']}%20{result['mitype'].replace(' ', '%20')}"
                    self.search_thread.url = url
                    self.search_thread.start()
                else:
                    self._fill_vri()
                    self._fill_vri_info()

            elif self.eq_type == "mieta":
                url = f"{url_start}/vri/{self.vri_numbers[0][0]}"
                self.search_thread.url = url
                self.search_thread.start()

    # номер свидетельства
    def _get_vri(self):

        global organization

        # получаем self.vri_search
        if "search" in self.search_thread.url and 'result' in self.resp_json and 'count' in self.resp_json['result']:
            if self.resp_json['result']['count'] == 0:
                self.ui.textEdit_result.setText(
                    f"Очевидно, вы пытались ввести номер свидетельства образца 2021 года, "
                    f"но ФГИС \"АРШИН\" не содержит такой записи. "
                    f"Перепроверьте раскладку клавиатуры и правильность введенного номера: "
                    f"\'{self.ui.lineEdit_input.text()}\'. "
                    f"Напоминаем, что буквы должны вводиться в русской раскладке. "
                    f"После внесения исправлений запустите поиск заново.")
                self._stop_search()
                return
            elif self.resp_json['result']['count'] == 1:
                self.vri_search = self.resp_json
                organization = self.resp_json['result']['items'][0]['org_title']

                url = f"{url_start}/vri/{self.resp_json['result']['items'][0]['vri_id']}"
                self.search_thread.url = url
                self.search_thread.start()
            else:
                QMessageBox.critical(self, "Ошибка",
                                     "Слишком много результатов поиска. Уточните номер свидетельства")
                self._stop_search()
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
                        url = f"{url_start}/mit?rows=100&search={mitypeNumber}%20{mitypeTitle.replace(' ', '%20')}"
                        self.search_thread.url = url
                        self.search_thread.start()

            else:
                if 'miInfo' in self.vri['result']:
                    if 'etaMI' in self.vri['result']['miInfo']:
                        miInfo = self.vri['result']['miInfo']['etaMI']
                        if self.eq_type == "vri":
                            if 'regNumber' in miInfo:
                                regNumber = miInfo['regNumber']
                                url = f"{url_start}/mieta?rows=100&search={regNumber}"
                                self.search_thread.url = url
                                self.search_thread.start()
                    elif 'singleMI' in self.vri['result']['miInfo'] or self.eq_type == "mieta":
                        miInfo = self.vri['result']['miInfo']['singleMI']

                        if 'mitypeNumber' in miInfo:  # номер реестра
                            mitypeNumber = miInfo['mitypeNumber']
                        if 'mitypeTitle' in miInfo:  # наименование
                            mitypeTitle = miInfo['mitypeTitle']

                        self.vri_numbers.append([self.vri_search['result']['items'][0]['vri_id'],
                                                 self.vri_search['result']['items'][0]['org_title']])

                        if mitypeNumber and mitypeTitle:
                            url = f"{url_start}/mit?rows=100&search={mitypeNumber}%20{mitypeTitle.replace(' ', '%20')}"
                            self.search_thread.url = url
                            self.search_thread.start()
                        else:
                            self._fill_vri()
                            self._fill_vri_info()
                    elif 'partyMI' in self.vri['result']['miInfo']:
                        miInfo = self.vri['result']['miInfo']['partyMI']

            # список поверок для таблицы: дата поверки, годен до или бессрочно, номер свид-ва, результат, поверитель
            # row = list()
            # row.append(QStandardItem(vriInfo['vrfDate']))
            # if 'applicable' in vriInfo and 'certNum' in vriInfo['applicable']:
            #     if 'validDate' in vriInfo:
            #         row.append(QStandardItem(vriInfo['validDate']))
            #     else:
            #         row.append(QStandardItem("Бессрочно"))
            #     row.append(QStandardItem(vriInfo['applicable']['certNum']))
            #     row.append(QStandardItem("ГОДЕН"))
            # elif 'inapplicable' in vriInfo and 'noticeNum' in vriInfo['inapplicable']:
            #     row.append(QStandardItem("-"))
            #     row.append(QStandardItem(vriInfo['inapplicable']['noticeNum']))
            #     row.append(QStandardItem("БРАК"))
            # row.append(QStandardItem(organization))
            # self.table_model.appendRow(row)
            # self.ui.tableView_verification_info.resizeRowsToContents()

    def _fill_vri_info(self):

        self.get_type = "mieta_vri"

        if 'result' in self.vri and 'vriInfo' in self.vri['result']:
            # список поверок для таблицы: дата поверки, годен до или бессрочно, номер свид-ва, результат, поверитель
            row = list()
            vriInfo = self.vri['result']['vriInfo']
            row.append(QStandardItem(vriInfo['vrfDate']))
            if 'applicable' in vriInfo and 'certNum' in vriInfo['applicable']:
                if 'validDate' in vriInfo:
                    row.append(QStandardItem(vriInfo['validDate']))
                else:
                    row.append(QStandardItem("Бессрочно"))
                row.append(QStandardItem(vriInfo['applicable']['certNum']))
                row.append(QStandardItem("ГОДЕН"))
            elif 'inapplicable' in vriInfo and 'noticeNum' in vriInfo['inapplicable']:
                row.append(QStandardItem("-"))
                row.append(QStandardItem(vriInfo['inapplicable']['noticeNum']))
                row.append(QStandardItem("БРАК"))
            if 'organization' in vriInfo:
                row.append(QStandardItem(self.vri_numbers[0][1]))
            self.table_model.appendRow(row)
            self.ui.tableView_verification_info.resizeRowsToContents()

            if self.eq_type == "mieta":
                del self.vri_numbers[0]
                if len(self.vri_numbers) > 0:
                    url = f"{url_start}/vri/{self.vri_numbers[0][0]}"
                    self.search_thread.url = url
                    self.search_thread.start()
            else:
                if len(self.vri_numbers) == 1:
                    self.vri_numbers.clear()
                for vri in self.vri_numbers:
                    if self.vri_search['result']['items'][0]['vri_id'] in vri:
                        self.vri_numbers.remove(vri)
                if len(self.vri_numbers) > 0:
                    url = f"{url_start}/vri/{self.vri_numbers[0][0]}"
                    self.search_thread.url = url
                    self.search_thread.start()

    def _clear_all(self):
        self.get_type = self.eq_type

        self.mit_search.clear()
        self.mit.clear()

        self.vri_search.clear()
        self.vri.clear()

        self.mieta_search.clear()
        self.mieta.clear()

        self.ui.textEdit_result.setText("")
        self.ui.comboBox_measure_code.setCurrentIndex(0)
        self.ui.lineEdit_reg_card_number.setText("")
        self.ui.comboBox_status.setCurrentIndex(0)
        self.ui.comboBox_department.clear()
        self.ui.comboBox_responsiblePerson.clear()
        self.ui.comboBox_room.clear()
        self.ui.lineEdit_reestr.setText("")
        self.ui.lineEdit_MPI.setText("12")
        self.ui.textEdit_title.setPlainText("")
        self.ui.textEdit_type.setPlainText("")
        self.ui.lineEdit_modification.setText("")
        self.ui.textEdit_manufacturer.setText("")
        self.ui.lineEdit_manuf_year.setText("")
        self.ui.lineEdit_expl_year.setText("")
        self.ui.lineEdit_number.setText("")
        self.ui.lineEdit_inv_number.setText("")
        self.ui.lineEdit_diapazon.setText("")
        self.ui.lineEdit_PG.setText("")
        self.ui.lineEdit_KT.setText("")
        self.ui.textEdit_other_characteristics.setPlainText("")
        self.ui.textEdit_software_inner.setPlainText("")
        self.ui.textEdit_software_outer.setPlainText("")
        self.ui.lineEdit_TO_period.setText("")
        self.ui.lineEdit_mieta_number.setText("")
        self.ui.lineEdit_mieta_rank_title.setText("")
        self.ui.lineEdit_mieta_npenumber.setText("")
        self.ui.lineEdit_mieta_schematype.setText("")
        self.ui.textEdit_mieta_schematitle.setText("")
        self.ui.comboBox_mieta_rank.setCurrentIndex(0)
        self.ui.radioButton_MPI_yes.setChecked(True)

        self.table_model.clear()

        self.table_model.setHorizontalHeaderLabels(
            ["Дата поверки", "Годен до", "Номер свидетельства", "Результат", "Организация-поверитель"])
        self.ui.tableView_verification_info.resizeRowsToContents()
        self.ui.tableView_verification_info.setColumnWidth(0, 85)
        self.ui.tableView_verification_info.setColumnWidth(1, 65)
        self.ui.tableView_verification_info.setColumnWidth(2, 170)
        self.ui.tableView_verification_info.setColumnWidth(3, 70)
        self.ui.tableView_verification_info.setColumnWidth(4, 280)

        self._stop_search()

    def _stop_search(self):
        self.ui.lineEdit_input.setDisabled(False)
        self.ui.btn_check.setText("Поиск")
        self.ui.btn_check.setDisabled(False)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    mainWindow = Ui_AddEquipment()
    mainWindow.show()
    sys.exit(app.exec_())
