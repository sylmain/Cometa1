from PyQt5 import QtWidgets
from PyQt5.QtCore import QUrl, QSettings, Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QWidget, QApplication, QComboBox, QLabel, QFileDialog, QInputDialog
from openpyxl import load_workbook
import functions_pkg.functions as func

from equipment_pkg.ui_equipment_add_file import Ui_Form
from functions_pkg.send_get_request import GetRequest
from GLOBAL_VARS import *

MEASURE_CODES = func.get_measure_codes()

COLUMN_NAMES = ["A(1)", "B(2)", "C(3)", "D(4)", "E(5)", "F(6)", "G(7)", "H(8)", "I(9)", "J(10)", "K(11)", "L(12)",
                "M(13)", "N(14)", "O(15)", "P(16)", "Q(17)", "R(18)", "S(19)", "T(20)", "U(21)", "V(22)", "W(23)",
                "X(24)", "Y(25)", "Z(26)", "AA(27)", "AB(28)", "AC(29)", "AD(30)", "AE(31)", "AF(32)", "AG(33)",
                "AH(34)", "AI(35)", "AJ(36)", "AK(37)", "AL(38)", "AM(39)", "AN(40)", "AO(41)", "AP(42)", "AQ(43)",
                "AR(44)", "AS(45)", "AT(46)", "AU(47)", "AV(48)", "AW(49)", "AX(50)", "AY(51)", "AZ(52)", "BA(53)",
                "BB(54)", "BC(55)", "BD(56)", "BE(57)", "BF(58)", "BG(59)", "BH(60)", "BI(61)", "BJ(62)", "BK(63)",
                "BL(64)", "BM(65)", "BN(66)", "BO(67)", "BP(68)", "BQ(69)", "BR(70)", "BS(71)", "BT(72)", "BU(73)",
                "BV(74)", "BW(75)", "BX(76)", "BY(77)", "BZ(78)", "CA(79)", "CB(80)", "CC(81)", "CD(82)", "CE(83)",
                "CF(84)", "CG(85)", "CH(86)", "CI(87)", "CJ(88)", "CK(89)", "CL(90)", "CM(91)", "CN(92)", "CO(93)",
                "CP(94)", "CQ(95)", "CR(96)", "CS(97)", "CT(98)", "CU(99)", "CV(100)", "CW(101)", "CX(102)", "CY(103)",
                "CZ(104)"]

COMBOBOX_VALUES = ["",
                   "Номер регистрационной карточки",
                   "Область измерений",
                   "Отдел",
                   "Ответственный",
                   "Помещение",
                   "Номер в реестре",
                   "Межповерочный интервал",
                   "Наименование",
                   "Тип",
                   "Модификация",
                   "Заводской номер",
                   "Инвентарный номер",
                   "Изготовитель",
                   "Год выпуска",
                   "Год введения в эксплуатацию",
                   "Диапазон измерений",
                   "Погрешность",
                   "Класс точности",
                   "Прочие характеристики",
                   "Наличие паспорта (да/нет, 1/0, истина/ложь, true/false)",
                   "Наличие РЭ (да/нет, 1/0, истина/ложь, true/false)",
                   "Наличие МП (да/нет, 1/0, истина/ложь, true/false)",
                   "Встроенное программное обеспечение",
                   "Внешнее программное обеспечение",
                   "Назначение",
                   "Допущенный персонал",
                   "Собственник",
                   "Номер и дата договора (если СИ не в собственности)",
                   "Периодичность технического обслуживания",
                   "Содержание технического обслуживания",
                   "1. Дата проведения ТО",
                   "2. Дата проведения ТО",
                   "3. Дата проведения ТО",
                   "4. Дата проведения ТО",
                   "5. Дата проведения ТО",
                   "1. Сотрудник, проводивший ТО",
                   "2. Сотрудник, проводивший ТО",
                   "3. Сотрудник, проводивший ТО",
                   "4. Сотрудник, проводивший ТО",
                   "5. Сотрудник, проводивший ТО",
                   "1. СИ как эталон - номер в перечне",
                   "2. СИ как эталон - номер в перечне",
                   "3. СИ как эталон - номер в перечне",
                   "4. СИ как эталон - номер в перечне",
                   "5. СИ как эталон - номер в перечне",
                   "6. СИ как эталон - номер в перечне",
                   "7. СИ как эталон - номер в перечне",
                   "8. СИ как эталон - номер в перечне",
                   "9. СИ как эталон - номер в перечне",
                   "10. СИ как эталон - номер в перечне",
                   "1. Дата поверки",
                   "2. Дата поверки",
                   "3. Дата поверки",
                   "4. Дата поверки",
                   "5. Дата поверки",
                   "6. Дата поверки",
                   "7. Дата поверки",
                   "8. Дата поверки",
                   "9. Дата поверки",
                   "10. Дата поверки",
                   "1. Годен до",
                   "2. Годен до",
                   "3. Годен до",
                   "4. Годен до",
                   "5. Годен до",
                   "6. Годен до",
                   "7. Годен до",
                   "8. Годен до",
                   "9. Годен до",
                   "10. Годен до",
                   "1. Номер свидетельства",
                   "2. Номер свидетельства",
                   "3. Номер свидетельства",
                   "4. Номер свидетельства",
                   "5. Номер свидетельства",
                   "6. Номер свидетельства",
                   "7. Номер свидетельства",
                   "8. Номер свидетельства",
                   "9. Номер свидетельства",
                   "10. Номер свидетельства",
                   "1. Результат",
                   "2. Результат",
                   "3. Результат",
                   "4. Результат",
                   "5. Результат",
                   "6. Результат",
                   "7. Результат",
                   "8. Результат",
                   "9. Результат",
                   "10. Результат",
                   "1. Организация-поверитель",
                   "2. Организация-поверитель",
                   "3. Организация-поверитель",
                   "4. Организация-поверитель",
                   "5. Организация-поверитель",
                   "6. Организация-поверитель",
                   "7. Организация-поверитель",
                   "8. Организация-поверитель",
                   "9. Организация-поверитель",
                   "10. Организация-поверитель"
                   ]

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

class EquipmentImportFileWidget(QWidget):
    def __init__(self):
        super(EquipmentImportFileWidget, self).__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.search_thread = SearchThread()

        self.column_count = 0
        self.combobox_remain_items = COMBOBOX_VALUES.copy()

        self.combobox_list = list()
        self.combobox_items_dict = dict()
        self.final_dict = dict()

        self.mit = dict()
        self.vri = dict()
        self.mieta = dict()

        for column_name in COLUMN_NAMES:
            self.combobox_items_dict[column_name] = ""

        self.ui.pushButton_add_column.clicked.connect(lambda: self._add_column())
        self.ui.pushButton_add_columns.clicked.connect(lambda: self._add_columns(self.ui.spinBox_add_columns.value()))
        self.ui.pushButton_file_select.clicked.connect(self._file_select)
        self.ui.pushButton_import_start.clicked.connect(self._import_start)

        self._add_column()

    def _add_columns(self, col_number=1):
        for i in range(col_number):
            self._add_column()

    def _add_column(self):
        if self.column_count < len(COLUMN_NAMES):
            cur_label_name = COLUMN_NAMES[self.column_count]

            label = QLabel(self.ui.scrollAreaWidgetContents)
            label.setText(f"Колонка {cur_label_name}")

            comboBox = QComboBox(self.ui.scrollAreaWidgetContents)
            comboBox.setObjectName(cur_label_name)

            self.ui.formLayout.setWidget(0 + self.column_count, QtWidgets.QFormLayout.LabelRole, label)
            self.ui.formLayout.setWidget(0 + self.column_count, QtWidgets.QFormLayout.FieldRole, comboBox)
            print(comboBox.objectName())
            comboBox.textActivated.connect(lambda: self._add_combobox_items(comboBox))

            self.column_count = self.column_count + 1
            self.combobox_list.append(comboBox)
            self._add_combobox_items(comboBox)

    def _add_combobox_items(self, cur_combobox):
        self.combobox_items_dict[cur_combobox.objectName()] = cur_combobox.currentText()

        for combobox in self.combobox_list:
            combobox.clear()
            free_items_list = COMBOBOX_VALUES.copy()
            for column_name in self.combobox_items_dict:
                if self.combobox_items_dict[column_name] != "" and column_name != combobox.objectName():
                    free_items_list.remove(self.combobox_items_dict[column_name])
            combobox.addItems(free_items_list)
            combobox.setCurrentText(self.combobox_items_dict[combobox.objectName()])
        print(self.combobox_items_dict)

    def _file_select(self):
        dir_name = str(SETTINGS.value("paths/cometa_path"))
        file_path = QFileDialog.getOpenFileName(caption="Выберите файл для импорта", directory=dir_name,
                                                filter="Excel (*.xlsx)")
        self.ui.lineEdit_file_path.setText(file_path[0])

    def _import_start(self):
        wb = load_workbook(filename=self.ui.lineEdit_file_path.text())
        sheet = wb.active
        start_row = self.ui.spinBox_start_row.value()
        count = sheet.max_row
        print(start_row, count)
        for i in range(start_row, count + 1):
            self.final_dict[i] = dict()

            reg_card_number = measure_code = department = responsiblePerson = room = reestr = MPI \
                = title = type = modification = number = inv_number = manufacturer = manuf_year \
                = expl_year = diapazon = PG = KT = other_characteristics = has_pasport = has_manual \
                = has_verif_method = software_inner = software_outer = purpose = personal = owner \
                = owner_contract = period_TO = content_TO = TO_date_1 = TO_date_2 = TO_date_3 = TO_date_4 \
                = TO_date_5 = TO_worker_1 = TO_worker_2 = TO_worker_3 = TO_worker_4 = TO_worker_5 \
                = mieta_number_1 = mieta_number_2 = mieta_number_3 = mieta_number_4 = mieta_number_5 \
                = mieta_number_6 = mieta_number_7 = mieta_number_8 = mieta_number_9 = mieta_number_10 \
                = vrfDate_1 = vrfDate_2 = vrfDate_3 = vrfDate_4 = vrfDate_5 = vrfDate_6 = vrfDate_7 \
                = vrfDate_8 = vrfDate_9 = vrfDate_10 = validDate_1 = validDate_2 = validDate_3 = validDate_4 \
                = validDate_5 = validDate_6 = validDate_7 = validDate_8 = validDate_9 = validDate_10 \
                = certNum_1 = certNum_2 = certNum_3 = certNum_4 = certNum_5 = certNum_6 = certNum_7 = certNum_8 \
                = certNum_9 = certNum_10 = vrf_result_1 = vrf_result_2 = vrf_result_3 = vrf_result_4 = vrf_result_5 \
                = vrf_result_6 = vrf_result_7 = vrf_result_8 = vrf_result_9 = vrf_result_10 = vrf_organization_1 \
                = vrf_organization_2 = vrf_organization_3 = vrf_organization_4 = vrf_organization_5 \
                = vrf_organization_6 = vrf_organization_7 = vrf_organization_8 = vrf_organization_9 \
                = vrf_organization_10 = ""

            for column_name in self.combobox_items_dict:
                column_letter = column_name.split("(")[0]
                if self.combobox_items_dict[column_name] == "Номер регистрационной карточки":
                    reg_card_number = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Область измерений":
                    measure_code = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Отдел":
                    department = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Ответственный":
                    responsiblePerson = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Помещение":
                    room = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Номер в реестре":
                    reestr = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Межповерочный интервал":
                    MPI = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Наименование":
                    title = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Тип":
                    type = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Модификация":
                    modification = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Заводской номер":
                    number = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Инвентарный номер":
                    inv_number = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Изготовитель":
                    manufacturer = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Год выпуска":
                    manuf_year = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Год введения в эксплуатацию":
                    expl_year = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Диапазон измерений":
                    diapazon = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Погрешность":
                    PG = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Класс точности":
                    KT = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Прочие характеристики":
                    other_characteristics = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Наличие паспорта (да/нет, 1/0, истина/ложь, true/false)":
                    has_pasport = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Наличие РЭ (да/нет, 1/0, истина/ложь, true/false)":
                    has_manual = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Наличие МП (да/нет, 1/0, истина/ложь, true/false)":
                    has_verif_method = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Встроенное программное обеспечение":
                    software_inner = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Внешнее программное обеспечение":
                    software_outer = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Назначение":
                    purpose = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Допущенный персонал":
                    personal = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Собственник":
                    owner = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Номер и дата договора (если СИ не в собственности)":
                    owner_contract = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Периодичность технического обслуживания":
                    period_TO = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "Содержание технического обслуживания":
                    content_TO = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "1. Дата проведения ТО":
                    TO_date_1 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "2. Дата проведения ТО":
                    TO_date_2 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "3. Дата проведения ТО":
                    TO_date_3 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "4. Дата проведения ТО":
                    TO_date_4 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "5. Дата проведения ТО":
                    TO_date_5 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "1. Сотрудник, проводивший ТО":
                    TO_worker_1 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "2. Сотрудник, проводивший ТО":
                    TO_worker_2 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "3. Сотрудник, проводивший ТО":
                    TO_worker_3 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "4. Сотрудник, проводивший ТО":
                    TO_worker_4 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "5. Сотрудник, проводивший ТО":
                    TO_worker_5 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "1. СИ как эталон - номер в перечне":
                    mieta_number_1 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "2. СИ как эталон - номер в перечне":
                    mieta_number_2 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "3. СИ как эталон - номер в перечне":
                    mieta_number_3 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "4. СИ как эталон - номер в перечне":
                    mieta_number_4 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "5. СИ как эталон - номер в перечне":
                    mieta_number_5 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "6. СИ как эталон - номер в перечне":
                    mieta_number_6 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "7. СИ как эталон - номер в перечне":
                    mieta_number_7 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "8. СИ как эталон - номер в перечне":
                    mieta_number_8 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "9. СИ как эталон - номер в перечне":
                    mieta_number_9 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "10. СИ как эталон - номер в перечне":
                    mieta_number_10 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "1. Дата поверки":
                    vrfDate_1 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "2. Дата поверки":
                    vrfDate_2 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "3. Дата поверки":
                    vrfDate_3 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "4. Дата поверки":
                    vrfDate_4 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "5. Дата поверки":
                    vrfDate_5 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "6. Дата поверки":
                    vrfDate_6 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "7. Дата поверки":
                    vrfDate_7 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "8. Дата поверки":
                    vrfDate_8 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "9. Дата поверки":
                    vrfDate_9 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "10. Дата поверки":
                    vrfDate_10 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "1. Годен до":
                    validDate_1 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "2. Годен до":
                    validDate_2 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "3. Годен до":
                    validDate_3 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "4. Годен до":
                    validDate_4 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "5. Годен до":
                    validDate_5 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "6. Годен до":
                    validDate_6 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "7. Годен до":
                    validDate_7 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "8. Годен до":
                    validDate_8 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "9. Годен до":
                    validDate_9 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "10. Годен до":
                    validDate_10 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "1. Номер свидетельства":
                    certNum_1 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "2. Номер свидетельства":
                    certNum_2 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "3. Номер свидетельства":
                    certNum_3 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "4. Номер свидетельства":
                    certNum_4 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "5. Номер свидетельства":
                    certNum_5 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "6. Номер свидетельства":
                    certNum_6 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "7. Номер свидетельства":
                    certNum_7 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "8. Номер свидетельства":
                    certNum_8 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "9. Номер свидетельства":
                    certNum_9 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "10. Номер свидетельства":
                    certNum_10 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "1. Результат":
                    vrf_result_1 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "2. Результат":
                    vrf_result_2 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "3. Результат":
                    vrf_result_3 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "4. Результат":
                    vrf_result_4 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "5. Результат":
                    vrf_result_5 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "6. Результат":
                    vrf_result_6 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "7. Результат":
                    vrf_result_7 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "8. Результат":
                    vrf_result_8 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "9. Результат":
                    vrf_result_9 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "10. Результат":
                    vrf_result_10 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "1. Организация-поверитель":
                    vrf_organization_1 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "2. Организация-поверитель":
                    vrf_organization_2 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "3. Организация-поверитель":
                    vrf_organization_3 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "4. Организация-поверитель":
                    vrf_organization_4 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "5. Организация-поверитель":
                    vrf_organization_5 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "6. Организация-поверитель":
                    vrf_organization_6 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "7. Организация-поверитель":
                    vrf_organization_7 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "8. Организация-поверитель":
                    vrf_organization_8 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "9. Организация-поверитель":
                    vrf_organization_9 = str(sheet[f"{column_letter}{i}"].value)
                elif self.combobox_items_dict[column_name] == "10. Организация-поверитель":
                    vrf_organization_10 = str(sheet[f"{column_letter}{i}"].value)
            self.final_dict[i] = dict()
            self.final_dict[i]['reg_card_number'] = reg_card_number
            self.final_dict[i]['measure_code'] = measure_code
            self.final_dict[i]['department'] = department
            self.final_dict[i]['responsiblePerson'] = responsiblePerson
            self.final_dict[i]['room'] = room
            self.final_dict[i]['reestr'] = reestr
            self.final_dict[i]['MPI'] = MPI
            self.final_dict[i]['title'] = title
            self.final_dict[i]['type'] = type
            self.final_dict[i]['modification'] = modification
            self.final_dict[i]['number'] = number
            self.final_dict[i]['inv_number'] = inv_number
            self.final_dict[i]['manufacturer'] = manufacturer
            self.final_dict[i]['manuf_year'] = manuf_year
            self.final_dict[i]['expl_year'] = expl_year
            self.final_dict[i]['diapazon'] = diapazon
            self.final_dict[i]['PG'] = PG
            self.final_dict[i]['KT'] = KT
            self.final_dict[i]['other_characteristics'] = other_characteristics
            self.final_dict[i]['has_pasport'] = has_pasport
            self.final_dict[i]['has_manual'] = has_manual
            self.final_dict[i]['has_verif_method'] = has_verif_method
            self.final_dict[i]['software_inner'] = software_inner
            self.final_dict[i]['software_outer'] = software_outer
            self.final_dict[i]['purpose'] = purpose
            self.final_dict[i]['personal'] = personal
            self.final_dict[i]['owner'] = owner
            self.final_dict[i]['owner_contract'] = owner_contract
            self.final_dict[i]['period_TO'] = period_TO
            self.final_dict[i]['content_TO'] = content_TO
            self.final_dict[i]['TO_date_1'] = TO_date_1
            self.final_dict[i]['TO_date_2'] = TO_date_2
            self.final_dict[i]['TO_date_3'] = TO_date_3
            self.final_dict[i]['TO_date_4'] = TO_date_4
            self.final_dict[i]['TO_date_5'] = TO_date_5
            self.final_dict[i]['TO_worker_1'] = TO_worker_1
            self.final_dict[i]['TO_worker_2'] = TO_worker_2
            self.final_dict[i]['TO_worker_3'] = TO_worker_3
            self.final_dict[i]['TO_worker_4'] = TO_worker_4
            self.final_dict[i]['TO_worker_5'] = TO_worker_5
            self.final_dict[i]['mieta_number_1'] = mieta_number_1
            self.final_dict[i]['mieta_number_2'] = mieta_number_2
            self.final_dict[i]['mieta_number_3'] = mieta_number_3
            self.final_dict[i]['mieta_number_4'] = mieta_number_4
            self.final_dict[i]['mieta_number_5'] = mieta_number_5
            self.final_dict[i]['mieta_number_6'] = mieta_number_6
            self.final_dict[i]['mieta_number_7'] = mieta_number_7
            self.final_dict[i]['mieta_number_8'] = mieta_number_8
            self.final_dict[i]['mieta_number_9'] = mieta_number_9
            self.final_dict[i]['mieta_number_10'] = mieta_number_10
            self.final_dict[i]['vrfDate_1'] = vrfDate_1
            self.final_dict[i]['vrfDate_2'] = vrfDate_2
            self.final_dict[i]['vrfDate_3'] = vrfDate_3
            self.final_dict[i]['vrfDate_4'] = vrfDate_4
            self.final_dict[i]['vrfDate_5'] = vrfDate_5
            self.final_dict[i]['vrfDate_6'] = vrfDate_6
            self.final_dict[i]['vrfDate_7'] = vrfDate_7
            self.final_dict[i]['vrfDate_8'] = vrfDate_8
            self.final_dict[i]['vrfDate_9'] = vrfDate_9
            self.final_dict[i]['vrfDate_10'] = vrfDate_10
            self.final_dict[i]['validDate_1'] = validDate_1
            self.final_dict[i]['validDate_2'] = validDate_2
            self.final_dict[i]['validDate_3'] = validDate_3
            self.final_dict[i]['validDate_4'] = validDate_4
            self.final_dict[i]['validDate_5'] = validDate_5
            self.final_dict[i]['validDate_6'] = validDate_6
            self.final_dict[i]['validDate_7'] = validDate_7
            self.final_dict[i]['validDate_8'] = validDate_8
            self.final_dict[i]['validDate_9'] = validDate_9
            self.final_dict[i]['validDate_10'] = validDate_10
            self.final_dict[i]['certNum_1'] = certNum_1
            self.final_dict[i]['certNum_2'] = certNum_2
            self.final_dict[i]['certNum_3'] = certNum_3
            self.final_dict[i]['certNum_4'] = certNum_4
            self.final_dict[i]['certNum_5'] = certNum_5
            self.final_dict[i]['certNum_6'] = certNum_6
            self.final_dict[i]['certNum_7'] = certNum_7
            self.final_dict[i]['certNum_8'] = certNum_8
            self.final_dict[i]['certNum_9'] = certNum_9
            self.final_dict[i]['certNum_10'] = certNum_10
            self.final_dict[i]['vrf_result_1'] = vrf_result_1
            self.final_dict[i]['vrf_result_2'] = vrf_result_2
            self.final_dict[i]['vrf_result_3'] = vrf_result_3
            self.final_dict[i]['vrf_result_4'] = vrf_result_4
            self.final_dict[i]['vrf_result_5'] = vrf_result_5
            self.final_dict[i]['vrf_result_6'] = vrf_result_6
            self.final_dict[i]['vrf_result_7'] = vrf_result_7
            self.final_dict[i]['vrf_result_8'] = vrf_result_8
            self.final_dict[i]['vrf_result_9'] = vrf_result_9
            self.final_dict[i]['vrf_result_10'] = vrf_result_10
            self.final_dict[i]['vrf_organization_1'] = vrf_organization_1
            self.final_dict[i]['vrf_organization_2'] = vrf_organization_2
            self.final_dict[i]['vrf_organization_3'] = vrf_organization_3
            self.final_dict[i]['vrf_organization_4'] = vrf_organization_4
            self.final_dict[i]['vrf_organization_5'] = vrf_organization_5
            self.final_dict[i]['vrf_organization_6'] = vrf_organization_6
            self.final_dict[i]['vrf_organization_7'] = vrf_organization_7
            self.final_dict[i]['vrf_organization_8'] = vrf_organization_8
            self.final_dict[i]['vrf_organization_9'] = vrf_organization_9
            self.final_dict[i]['vrf_organization_10'] = vrf_organization_10
            self._verification_start(i)

        for item in self.final_dict:
            print(self.final_dict[item])

    def _get_mit(self, reestr):
        self.search_thread.url = f"{URL_START}/mit?search={reestr}"
        self.search_thread.run()

    def _verification_start(self, i):
        reestr = self.final_dict[i]['reestr']
        if reestr and not self.mit:
            self._get_mit(reestr)

        measure_code = self.final_dict[i]['measure_code']
        if measure_code == "" or measure_code not in MEASURE_CODES['measure_codes_dict']:
            s, ok = QInputDialog.getItem(self, "Выбор области измерений", f"Выберите область измерений для позиции № "
                                                                          f"{i} {self.final_dict[i]['title']}",
                                         MEASURE_CODES['measure_codes_list'], current=0, editable=False)
            if ok and s:
                self.final_dict[i]['measure_code'] = s
            else:
                return


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = EquipmentImportFileWidget()

    window.show()
    sys.exit(app.exec_())
