from PyQt5.QtCore import pyqtSignal, pyqtSlot, QSortFilterProxyModel, Qt, QDate, QModelIndex, QRegExp, pyqtProperty
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QPushButton
from equipment_pkg.ui_equipment import Ui_MainWindow
from equipment_pkg.mimodel import MiModel
from equipment_pkg.vrimodel import VriModel
from equipment_pkg.mi_dep_model import MiDepModel
from equipment_pkg.workers_model import WorkersModel
from equipment_pkg.rooms_model import RoomsModel
import GLOBAL_VARS
from functions_pkg import functions as func


class EquipmentWidget(QMainWindow):
    change_mi_id_signal = pyqtSignal(int)
    change_vri_id_signal = pyqtSignal(int)

    ORG_NAME = func.get_organization_name()
    MEASURE_CODES = func.get_measure_codes()

    def __init__(self):
        super(EquipmentWidget, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._current_mi_id = 0
        self._current_vri_id = 0

        self.mi_model = MiModel()  # модель таблицы оборудования
        self.mi_proxy_model = QSortFilterProxyModel()
        self.vri_model = VriModel()  # модель таблицы поверок
        self.vri_proxy_model = QSortFilterProxyModel()
        self.mi_dep_model = MiDepModel()  # модель списка отделов
        self.ui.listView_departments.setModel(self.mi_dep_model)
        self.workers_model = WorkersModel()  # модель списка возможных ответственных
        self.ui.comboBox_responsiblePerson.setModel(self.workers_model)
        self.rooms_model = RoomsModel()  # модель списка кабинетов
        self.ui.comboBox_room.setModel(self.rooms_model)

        self._make_connects()

        self._initialize_mi_model()
        self._initialize_vri_model()

        self._initialize_start_screen()

    def _make_connects(self):
        print("_make_connects")
        # клик на прибор в таблице
        self.ui.tableView_mi_list.clicked.connect(self._on_mi_table_click)
        self.ui.tableView_mi_list.activated.connect(self._on_mi_table_click)
        # клик на поверку в таблице
        self.ui.tableView_vri_list.clicked.connect(self._on_vri_table_click)
        self.ui.tableView_vri_list.activated.connect(self._on_vri_table_click)
        # сигнал при изменении текущего mi_id
        self.change_mi_id_signal.connect(self._update_mi_tab)
        # фильтр приборов при изменении поля фильтра
        self.ui.lineEdit_equip_filter.textChanged.connect(self._filter_mi_table)
        # переключение вкладок
        self.ui.tabWidget.currentChanged.connect(self._on_tab_changed)
        # "Удалить": клик по кнопке удаления прибора
        self.ui.pushButton_delete_mi.clicked.connect(self._delete_mi)
        # смена подвидов измерений при выборе вида измерений
        self.ui.comboBox_measure_code.currentTextChanged.connect(self._add_measure_subcodes)
        # переключение флажков годен/брак
        self.ui.radioButton_applicable.clicked.connect(
            lambda: self._set_vri_applicability(True, self.ui.checkBox_unlimited.isChecked()))
        self.ui.radioButton_inapplicable.clicked.connect(
            lambda: self._set_vri_applicability(False, self.ui.checkBox_unlimited.isChecked()))
        # установка флажка бессрочной поверки
        self.ui.checkBox_unlimited.clicked.connect(
            lambda: self._set_vri_applicability(True, self.ui.checkBox_unlimited.isChecked()))

    def _initialize_mi_model(self):
        print("_initialize_mi_model")
        self.mi_proxy_model.setSourceModel(self.mi_model)
        self.ui.tableView_mi_list.setModel(self.mi_proxy_model)
        self.mi_proxy_model.sort(1, Qt.AscendingOrder)  # сортировка по первому столбцу
        self.ui.tableView_mi_list.setColumnWidth(0, 110)
        self.ui.tableView_mi_list.setColumnWidth(1, 50)
        self.ui.tableView_mi_list.setColumnWidth(2, 200)
        self.ui.tableView_mi_list.setColumnWidth(3, 100)
        self.ui.tableView_mi_list.setColumnWidth(4, 100)

        self.ui.tableView_mi_list.resizeRowsToContents()

        self.ui.tableView_mi_list.selectRow(0)
        self.ui.tableView_mi_list.clicked.emit(self.mi_proxy_model.index(0, 0))

    def _initialize_vri_model(self):
        print("_initialize_vri_model")
        self.vri_proxy_model.setSourceModel(self.vri_model)
        self.ui.tableView_vri_list.setModel(self.vri_proxy_model)
        self.vri_proxy_model.sort(1, Qt.DescendingOrder)  # сортировка по второму столбцу

        self.ui.tableView_vri_list.setColumnWidth(0, 90)
        self.ui.tableView_vri_list.setColumnWidth(1, 90)
        self.ui.tableView_vri_list.setColumnWidth(2, 170)
        self.ui.tableView_vri_list.setColumnWidth(3, 85)
        self.ui.tableView_vri_list.setColumnWidth(4, 210)
        self.ui.tableView_vri_list.setColumnWidth(5, 230)

        self.ui.tableView_vri_list.resizeRowsToContents()

        self.ui.tableView_vri_list.selectRow(0)
        self.ui.tableView_vri_list.clicked.emit(self.vri_proxy_model.index(0, 0))

    def _add_measure_codes(self):
        self.ui.comboBox_measure_code.addItems(["- Не определено"])
        self.ui.comboBox_measure_code.addItems(sorted(self.MEASURE_CODES['measure_codes_list']))

    def _add_measure_subcodes(self, meas_code_string):
        self.ui.comboBox_measure_subcode.clear()
        self.ui.comboBox_measure_subcode.addItems(["- Не определено"])
        if "Не определено" not in meas_code_string:
            meas_code = meas_code_string[:2]
            self.ui.comboBox_measure_subcode.addItems(sorted(self.MEASURE_CODES['measure_sub_codes_dict'][meas_code]))

    def _initialize_start_screen(self):
        self._add_measure_codes()
        self.ui.comboBox_status.addItems(GLOBAL_VARS.MI_STATUS_LIST)
        self.ui.comboBox_vri_vriType.addItems(GLOBAL_VARS.VRI_TYPE_LIST)

        self.ui.tabWidget.setCurrentIndex(0)
        self.ui.tabWidget.currentChanged.emit(0)

        sp = self.ui.dateEdit_vri_validDate.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.ui.dateEdit_vri_validDate.setSizePolicy(sp)
        sp = self.ui.checkBox_unlimited.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.ui.checkBox_unlimited.setSizePolicy(sp)
        sp = self.ui.label_13.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.ui.label_13.setSizePolicy(sp)

    def _on_mi_table_click(self, index):
        if index.isValid():
            self.mi_id = index.data(Qt.UserRole)

    def _on_vri_table_click(self, index):
        if index.isValid():
            self.vri_id = index.data(Qt.UserRole)

    def _on_tab_changed(self, tab_index):
        print(tab_index)
        self.ui.frame_mi_info_buttons.hide()
        self.ui.frame_vri_buttons.hide()
        self.ui.frame_mieta_buttons.hide()
        if tab_index == 2:
            self.ui.frame_vri_buttons.show()
        elif tab_index == 1:
            self.ui.frame_mieta_buttons.show()
        elif tab_index == 0:
            self.ui.frame_mi_info_buttons.show()

    def _update_mi_tab(self, mi_id):
        mi_info = self.mi_model.get_mi_info(mi_id)

        self.ui.lineEdit_mi_id.setText(f"{mi_id}")
        self.ui.lineEdit_reg_card_number.setText(mi_info['reg_card_number'])

        self.ui.comboBox_status.setCurrentText(mi_info['status'])
        self.ui.comboBox_status.update()

        self.ui.comboBox_measure_code.setCurrentText(self.mi_model.get_measure_code_text(mi_id, self.MEASURE_CODES))
        self.ui.comboBox_measure_code.update()
        self.ui.comboBox_measure_subcode.setCurrentText(self.mi_model.get_measure_subcode_text(mi_id, self.MEASURE_CODES))
        self.ui.comboBox_measure_subcode.update()
        self.ui.comboBox_responsiblePerson.setCurrentIndex(self.workers_model.get_index(mi_info['responsible_person']))
        self.ui.comboBox_responsiblePerson.update()
        self.ui.comboBox_room.setCurrentIndex(self.rooms_model.get_index(mi_info['room']))
        self.ui.comboBox_room.update()

        last_scan_date = QDate(mi_info['last_scan_date']).toString("dd.MM.yyyy") \
            if mi_info['last_scan_date'] else ""

        self.ui.lineEdit_reestr.setText(mi_info['reestr'])
        self.ui.plainTextEdit_title.setPlainText(mi_info['title'])
        self.ui.plainTextEdit_type.setPlainText(mi_info['type'])
        self.ui.lineEdit_modification.setText(mi_info['modification'])
        self.ui.lineEdit_number.setText(mi_info['number'])
        self.ui.lineEdit_inv_number.setText(mi_info['inv_number'])
        self.ui.plainTextEdit_manufacturer.setPlainText(mi_info['manufacturer'])
        self.ui.lineEdit_manuf_year.setText(mi_info['manuf_year'])
        self.ui.lineEdit_expl_year.setText(mi_info['expl_year'])
        self.ui.lineEdit_diapazon.setText(mi_info['diapazon'])
        self.ui.lineEdit_PG.setText(mi_info['PG'])
        self.ui.lineEdit_KT.setText(mi_info['KT'])
        self.ui.plainTextEdit_other_characteristics.setPlainText(mi_info['other_characteristics'])
        if mi_info['MPI']:
            self.ui.radioButton_MPI_yes.setChecked(True)
            self.ui.lineEdit_MPI.setText(mi_info['MPI'])
        else:
            self.ui.radioButton_MPI_no.setChecked(True)
            self.ui.lineEdit_MPI.setText("")
        self.ui.plainTextEdit_purpose.setPlainText(mi_info['purpose'])
        self.ui.plainTextEdit_personal.setPlainText(mi_info['personal'])
        self.ui.plainTextEdit_software_inner.setPlainText(mi_info['software_inner'])
        self.ui.plainTextEdit_software_outer.setPlainText(mi_info['software_outer'])
        self.ui.plainTextEdit_owner.setPlainText(mi_info['owner'])
        self.ui.plainTextEdit_owner_contract.setPlainText(mi_info['owner_contract'])
        self.ui.lineEdit_mi_last_scan_date.setText(last_scan_date)

        self.ui.checkBox_has_manual.setChecked(bool(mi_info['RE']))
        self.ui.checkBox_has_pasport.setChecked(bool(mi_info['pasport']))
        self.ui.checkBox_has_verif_method.setChecked(bool(mi_info['MP']))

        self.ui.lineEdit_period_TO.setText(mi_info['TO_period'])

    def _update_vri_tab(self, vri_id):

        vri_info = self.vri_model.get_vri_info(self.mi_id, vri_id)

        self.ui.lineEdit_vri_id.setText(f"{vri_id}")
        self.ui.lineEdit_vri_FIF_id.setText(vri_info['vri_FIF_id'])
        self.ui.plainTextEdit_vri_organization.setPlainText(vri_info['vri_organization'])
        self.ui.lineEdit_vri_signCipher.setText(vri_info['vri_signCipher'])
        self.ui.plainTextEdit_vri_miOwner.setPlainText(vri_info['vri_miOwner'])
        self.ui.dateEdit_vrfDate.setDate(QDate(vri_info['vri_vrfDate']))

        self.ui.comboBox_vri_vriType.setCurrentText(vri_info['vri_vriType'])
        self.ui.plainTextEdit_vri_docTitle.setPlainText(vri_info['vri_docTitle'])
        if vri_info['vri_applicable']:
            self.ui.radioButton_applicable.setChecked(True)
            self.ui.lineEdit_vri_certNum.setText(vri_info['vri_certNum'])
            self.ui.lineEdit_vri_stickerNum.setText(vri_info['vri_stickerNum'])
            self.ui.checkBox_vri_signPass.setChecked(vri_info['vri_signPass'])
            self.ui.checkBox_vri_signMi.setChecked(vri_info['vri_signMi'])
            if vri_info['vri_validDate']:
                self._set_vri_applicability(True, False)
                self.ui.dateEdit_vri_validDate.setDate(QDate(vri_info['vri_validDate']))
            else:
                self._set_vri_applicability(True, True)
        else:
            self._set_vri_applicability(False, False)
            self.ui.lineEdit_vri_noticeNum.setText(vri_info['vri_certNum'])
        self.ui.plainTextEdit_vri_structure.setPlainText(vri_info['vri_structure'])
        self.ui.checkBox_vri_briefIndicator.setChecked(vri_info['vri_briefIndicator'])
        self.ui.plainTextEdit_vri_briefCharacteristics.setPlainText(
            vri_info['vri_briefCharacteristics'])
        self.ui.plainTextEdit_vri_ranges.setPlainText(vri_info['vri_ranges'])
        self.ui.plainTextEdit_vri_values.setPlainText(vri_info['vri_values'])
        self.ui.plainTextEdit_vri_channels.setPlainText(vri_info['vri_channels'])
        self.ui.plainTextEdit_vri_blocks.setPlainText(vri_info['vri_blocks'])
        self.ui.plainTextEdit_vri_additional_info.setPlainText(vri_info['vri_additional_info'])
        self.ui.lineEdit_mieta_number.setText(vri_info['vri_mieta_number'])
        self.ui.comboBox_mieta_rank.setCurrentText(vri_info['vri_mieta_rankcode'])
        self.ui.lineEdit_mieta_rank_title.setText(vri_info['vri_mieta_rankclass'])
        self.ui.lineEdit_mieta_npenumber.setText(vri_info['vri_mieta_npenumber'])
        self.ui.lineEdit_mieta_schematype.setText(vri_info['vri_mieta_schematype'])
        self.ui.plainTextEdit_mieta_schematitle.setPlainText(vri_info['vri_mieta_schematitle'])

        last_scan_date = QDate(vri_info['vri_last_scan_date']).toString("dd.MM.yyyy") \
            if vri_info['vri_last_scan_date'] else ""

        last_save_date = QDate(vri_info['vri_last_save_date']).toString("dd.MM.yyyy") \
            if vri_info['vri_last_save_date'] else ""
        self.ui.lineEdit_vri_last_scan_date.setText(last_scan_date)
        self.ui.lineEdit_vri_last_save_date.setText(last_save_date)

    def _set_vri_applicability(self, is_applicable: bool, is_unlimited: bool) -> None:
        self.ui.radioButton_applicable.setChecked(is_applicable)  # если годен - выбираем переключатель Годен
        self.ui.radioButton_inapplicable.setChecked(not is_applicable)  # если годен - выбираем переключатель Годен

        self.ui.groupBox_inapplicable.setHidden(is_applicable)  # если годен - скрываем группу Брак
        self.ui.groupBox_applicable.setHidden(not is_applicable)  # если брак - скрываем группу Годен
        self.ui.checkBox_unlimited.setHidden(not is_applicable)  # если брак - скрываем флажок Бессрочно

        self.ui.label_13.setHidden(is_unlimited or not is_applicable)
        self.ui.dateEdit_vri_validDate.setHidden(is_unlimited or not is_applicable)

        self.ui.checkBox_unlimited.setChecked(is_unlimited)

    def _delete_mi(self) -> bool:
        """Нажатие кнопки "Удалить"
        Удаляет оборудование из всех связанных с ним таблиц
        :return:
        """
        if self._current_mi_id:
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
                self.mi_model.layoutAboutToBeChanged.emit()
                self.mi_model.delete_mi(self._current_mi_id)
                self.mi_model.layoutChanged.emit()
                QMessageBox.information(self, "Готово", "Оборудование успешно удалено")
                if self.mi_model.rowCount() == 0:
                    self.ui.pushButton_delete_mi.setDisabled(True)
                return True
            return False

    def _delete_vri(self) -> bool:
        pass

    def _filter_mi_table(self, mask):
        self.mi_proxy_model.setFilterKeyColumn(-1)  # фильтр сразу по всем столбцам
        self.mi_proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)  # не учитывать регистр
        self.mi_model.layoutAboutToBeChanged.emit()
        self.mi_proxy_model.setFilterFixedString(mask)
        self.mi_model.layoutChanged.emit()
        self.ui.tableView_mi_list.resizeRowsToContents()
        self.ui.tableView_mi_list.selectRow(0)
        self.ui.tableView_mi_list.clicked.emit(self.mi_proxy_model.index(0, 0))

    @property
    def mi_id(self):
        return self._current_mi_id

    @mi_id.setter
    def mi_id(self, value):
        self._current_mi_id = value
        # изменение модели списка отделов
        self.mi_dep_model.layoutAboutToBeChanged.emit()
        self.mi_dep_model.set_current_mi_id(value)
        self.mi_dep_model.layoutChanged.emit()

        self.workers_model.layoutAboutToBeChanged.emit()
        self.workers_model.clear_model()
        for dep_id in self.mi_dep_model.get_data():
            self.workers_model.add_dep_id(dep_id)
        self.workers_model.layoutChanged.emit()

        self.rooms_model.layoutAboutToBeChanged.emit()
        self.rooms_model.clear_model()
        for dep_id in self.mi_dep_model.get_data():
            self.rooms_model.add_dep_id(dep_id)
        self.rooms_model.layoutChanged.emit()

        # изменение модели таблицы поверок
        self.vri_model.layoutAboutToBeChanged.emit()
        self.vri_model.set_current_mi_id(value)
        self.vri_model.layoutChanged.emit()
        self.ui.tableView_vri_list.resizeRowsToContents()
        self.ui.tableView_vri_list.selectRow(0)
        self.ui.tableView_vri_list.clicked.emit(self.vri_proxy_model.index(0, 0))
        self._update_mi_tab(value)

    @property
    def vri_id(self):
        return self._current_vri_id

    @vri_id.setter
    def vri_id(self, value):
        self._current_vri_id = value
        self._update_vri_tab(value)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = EquipmentWidget()
    window.setWindowTitle("Средства измерений")
    window.showMaximized()
    sys.exit(app.exec())
