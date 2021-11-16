from PyQt5.QtCore import pyqtSignal, pyqtSlot, QSortFilterProxyModel, Qt, QDate, QModelIndex, QRegExp
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QPushButton
from equipment_pkg.ui_equipment import Ui_MainWindow
from equipment_pkg.mimodel import MiModel
from equipment_pkg.vrimodel import VriModel
import GLOBAL_VARS
from  functions_pkg import functions as func


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

        self.mi_model = MiModel()  # модель таблицы оборудования
        self.mi_proxy_model = QSortFilterProxyModel()
        self.vri_model = VriModel()  # модель таблицы поверок
        self.vri_proxy_model = QSortFilterProxyModel()

        self._make_connects()

        self._initialize_mi_model()
        self._initialize_vri_model()

        self._add_measure_codes()
        self.ui.comboBox_status.addItems(GLOBAL_VARS.MI_STATUS_LIST)
        self.ui.comboBox_vri_vriType.addItems(GLOBAL_VARS.VRI_TYPE_LIST)

        self._initialize_start_screen()

    def _make_connects(self):
        print("_make_connects")
        # клик на прибор в таблице
        self.ui.tableView_mi_list.clicked.connect(self._on_mi_table_click)
        self.ui.tableView_mi_list.activated.connect(self._on_mi_table_click)
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

    def _initialize_mi_model(self):
        print("_initialize_mi_model")
        self.mi_proxy_model.setSourceModel(self.mi_model)
        self.ui.tableView_mi_list.setModel(self.mi_proxy_model)
        self.mi_proxy_model.sort(0, Qt.AscendingOrder)  # сортировка по первому столбцу
        self.ui.tableView_mi_list.setColumnWidth(0, 110)
        self.ui.tableView_mi_list.setColumnWidth(1, 50)
        self.ui.tableView_mi_list.setColumnWidth(2, 200)
        self.ui.tableView_mi_list.setColumnWidth(3, 100)
        self.ui.tableView_mi_list.setColumnWidth(4, 100)

        self.ui.tableView_mi_list.resizeRowsToContents()

        self.ui.tableView_mi_list.selectRow(0)
        self.ui.tableView_mi_list.clicked.emit(self.mi_proxy_model.index(0, 0))

        self.mi_model.layoutChanged.emit()

    def _initialize_vri_model(self):
        print("_initialize_vri_model")
        self.vri_proxy_model.setSourceModel(self.vri_model)
        self.ui.tableView_vri_list.setModel(self.vri_proxy_model)
        self.vri_proxy_model.sort(1, Qt.AscendingOrder)  # сортировка по второму столбцу

        self.ui.tableView_vri_list.setColumnWidth(0, 90)
        self.ui.tableView_vri_list.setColumnWidth(1, 90)
        self.ui.tableView_vri_list.setColumnWidth(2, 170)
        self.ui.tableView_vri_list.setColumnWidth(3, 85)
        self.ui.tableView_vri_list.setColumnWidth(4, 210)
        self.ui.tableView_vri_list.setColumnWidth(5, 230)

        self.ui.tableView_vri_list.resizeRowsToContents()

        self.ui.tableView_vri_list.selectRow(0)
        # self.ui.tableView_vri_list.clicked.emit(self.vri_proxy_model.index(0, 0))
        self.vri_model.layoutChanged.emit()

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
        self.ui.frame_mieta_buttons.hide()
        self.ui.frame_vri_buttons.hide()

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

    def _update_mi_tab(self, mi_id):
        mi_dict = self.mi_model.get_mi_dict()
        self.ui.lineEdit_mi_id.setText(str(mi_id))
        self.ui.lineEdit_reg_card_number.setText(mi_dict[mi_id]['reg_card_number'])

        self.ui.comboBox_measure_code.setCurrentIndex(0)
        self.ui.comboBox_measure_subcode.setCurrentIndex(0)

        measure_code_id = mi_dict[mi_id]['measure_code']
        if measure_code_id != "0":
            measure_code_name = func.get_measure_code_name_from_id(measure_code_id, self.MEASURE_CODES)
            if measure_code_name:
                if len(measure_code_id) == 2:
                    self.ui.comboBox_measure_code.setCurrentText(f"{measure_code_id} {measure_code_name}")
                elif len(measure_code_id) == 4:
                    measure_subcode_id = measure_code_id
                    measure_subcode_name = measure_code_name
                    measure_code_id = measure_code_id[:2]
                    measure_code_name = func.get_measure_code_name_from_id(measure_code_id, self.MEASURE_CODES)
                    if measure_code_name:
                        self.ui.comboBox_measure_code.setCurrentText(f"{measure_code_id} {measure_code_name}")
                    self.ui.comboBox_measure_subcode.setCurrentText(f"{measure_subcode_id} {measure_subcode_name}")

        last_scan_date = QDate(mi_dict[mi_id]['last_scan_date']).toString("dd.MM.yyyy") \
            if mi_dict[mi_id]['last_scan_date'] else ""

        self.ui.comboBox_status.setCurrentText(mi_dict[mi_id]['status'])
        self.ui.lineEdit_reestr.setText(mi_dict[mi_id]['reestr'])
        self.ui.plainTextEdit_title.setPlainText(mi_dict[mi_id]['title'])
        self.ui.plainTextEdit_type.setPlainText(mi_dict[mi_id]['type'])
        self.ui.lineEdit_modification.setText(mi_dict[mi_id]['modification'])
        self.ui.lineEdit_number.setText(mi_dict[mi_id]['number'])
        self.ui.lineEdit_inv_number.setText(mi_dict[mi_id]['inv_number'])
        self.ui.plainTextEdit_manufacturer.setPlainText(mi_dict[mi_id]['manufacturer'])
        self.ui.lineEdit_manuf_year.setText(mi_dict[mi_id]['manuf_year'])
        self.ui.lineEdit_expl_year.setText(mi_dict[mi_id]['expl_year'])
        self.ui.lineEdit_diapazon.setText(mi_dict[mi_id]['diapazon'])
        self.ui.lineEdit_PG.setText(mi_dict[mi_id]['PG'])
        self.ui.lineEdit_KT.setText(mi_dict[mi_id]['KT'])
        self.ui.plainTextEdit_other_characteristics.setPlainText(mi_dict[mi_id]['other_characteristics'])
        if mi_dict[mi_id]['MPI']:
            self.ui.radioButton_MPI_yes.setChecked(True)
            self.ui.lineEdit_MPI.setText(mi_dict[mi_id]['MPI'])
        else:
            self.ui.radioButton_MPI_no.setChecked(True)
            self.ui.lineEdit_MPI.setText("")
        self.ui.plainTextEdit_purpose.setPlainText(mi_dict[mi_id]['purpose'])
        self.ui.plainTextEdit_personal.setPlainText(mi_dict[mi_id]['personal'])
        self.ui.plainTextEdit_software_inner.setPlainText(mi_dict[mi_id]['software_inner'])
        self.ui.plainTextEdit_software_outer.setPlainText(mi_dict[mi_id]['software_outer'])
        self.ui.plainTextEdit_owner.setPlainText(mi_dict[mi_id]['owner'])
        self.ui.plainTextEdit_owner_contract.setPlainText(mi_dict[mi_id]['owner_contract'])
        self.ui.lineEdit_mi_last_scan_date.setText(last_scan_date)

        self.ui.checkBox_has_manual.setChecked(bool(mi_dict[mi_id]['RE']))
        self.ui.checkBox_has_pasport.setChecked(bool(mi_dict[mi_id]['pasport']))
        self.ui.checkBox_has_verif_method.setChecked(bool(mi_dict[mi_id]['MP']))

        self.ui.lineEdit_period_TO.setText(mi_dict[mi_id]['TO_period'])

        # self._update_owner_info(mi_id)

    def _update_vri_tab(self, vri_id):
        pass

    @pyqtSlot(QModelIndex)
    def _on_mi_table_click(self, index):
        if index.isValid():
            self.current_mi_id = index.data(Qt.UserRole)

    @pyqtSlot(QModelIndex)
    def _on_vri_table_click(self, index):
        pass

    @pyqtSlot()
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

    @pyqtSlot()
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
    def current_mi_id(self):
        return self._current_mi_id

    @current_mi_id.setter
    def current_mi_id(self, value):
        print("set mi_id")
        self._current_mi_id = value
        self._update_mi_tab(value)
        self.vri_model.layoutAboutToBeChanged.emit()
        self.vri_model.set_current_mi_id(value)
        self.vri_model.layoutChanged.emit()
        self.ui.tableView_vri_list.resizeRowsToContents()
        self.ui.tableView_vri_list.selectRow(0)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = EquipmentWidget()
    window.setWindowTitle("Средства измерений")
    window.showMaximized()
    sys.exit(app.exec())
