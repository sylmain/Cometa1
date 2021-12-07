from PyQt5.QtCore import pyqtSignal, pyqtSlot, QSortFilterProxyModel, Qt, QDate, QModelIndex, QRegExp, pyqtProperty, \
    QPropertyAnimation, QPoint, QSize, QEasingCurve
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QPushButton, QInputDialog, QPlainTextEdit, \
    QTextEdit, QCheckBox
from equipment_pkg.ui_equipment import Ui_MainWindow
from equipment_pkg.mimodel import MiModel
from equipment_pkg.vrimodel import VriModel
from equipment_pkg.mi_dep_model import MiDepModel
from equipment_pkg.workers_model import WorkersModel
from equipment_pkg.rooms_model import RoomsModel
import GLOBAL_VARS
from functions_pkg import functions as func


class EquipmentWidget(QMainWindow):
    # todo добавить отключение проверки изменений (выделение цветом)

    ORG_NAME = func.get_organization_name()
    MEASURE_CODES = func.get_measure_codes()
    COLOR_OF_CHANGED_FIELDS = GLOBAL_VARS.COLOR_OF_CHANGED_FIELDS
    CSS_COLOR_STYLE = f"color: {COLOR_OF_CHANGED_FIELDS};"

    def __init__(self):
        super(EquipmentWidget, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.mi_info = dict()

        self._current_mi_id = 0
        self._current_vri_id = 0
        self._mi_title = None
        self._reg_card_number = None

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

        self.field_name_dependencies = {}
        # self.field_name_dependencies['reg_card_number'] = self.ui.lineEdit_reg_card_number
        self.field_name_dependencies['measure_code'] = self.ui.comboBox_measure_code
        self.field_name_dependencies['status'] = self.ui.comboBox_status
        self.field_name_dependencies['reestr'] = self.ui.lineEdit_reestr
        # self.field_name_dependencies['title'] = self.ui.plainTextEdit_title
        self.field_name_dependencies['type'] = self.ui.plainTextEdit_type
        self.field_name_dependencies['modification'] = self.ui.lineEdit_modification
        self.field_name_dependencies['number'] = self.ui.lineEdit_number
        self.field_name_dependencies['inv_number'] = self.ui.lineEdit_inv_number
        self.field_name_dependencies['manufacturer'] = self.ui.plainTextEdit_manufacturer
        self.field_name_dependencies['manuf_year'] = self.ui.lineEdit_manuf_year
        self.field_name_dependencies['expl_year'] = self.ui.lineEdit_expl_year
        self.field_name_dependencies['diapazon'] = self.ui.lineEdit_diapazon
        self.field_name_dependencies['PG'] = self.ui.lineEdit_PG
        self.field_name_dependencies['KT'] = self.ui.lineEdit_KT
        self.field_name_dependencies['other_characteristics'] = self.ui.plainTextEdit_other_characteristics
        self.field_name_dependencies['MPI'] = self.ui.lineEdit_MPI
        self.field_name_dependencies['purpose'] = self.ui.plainTextEdit_purpose
        self.field_name_dependencies['responsible_person'] = self.ui.comboBox_responsiblePerson
        self.field_name_dependencies['personal'] = self.ui.plainTextEdit_personal
        self.field_name_dependencies['room'] = self.ui.comboBox_room
        self.field_name_dependencies['software_inner'] = self.ui.plainTextEdit_software_inner
        self.field_name_dependencies['software_outer'] = self.ui.plainTextEdit_software_outer
        self.field_name_dependencies['RE'] = self.ui.checkBox_has_manual
        self.field_name_dependencies['pasport'] = self.ui.checkBox_has_pasport
        self.field_name_dependencies['MP'] = self.ui.checkBox_has_verif_method
        self.field_name_dependencies['TO_period'] = self.ui.lineEdit_period_TO
        self.field_name_dependencies['owner'] = self.ui.plainTextEdit_owner
        self.field_name_dependencies['owner_contract'] = self.ui.plainTextEdit_owner_contract
        self.field_name_dependencies['last_scan_date'] = self.ui.lineEdit_mi_last_scan_date

        self._make_connects()
        self._initialize_start_screen()

        self._initialize_mi_model()
        self._initialize_vri_model()

        self._make_change_connects()

    def _make_connects(self):
        print("_make_connects")
        ui = self.ui
        # клик на прибор в таблице
        ui.tableView_mi_list.clicked.connect(self._on_mi_table_click)
        ui.tableView_mi_list.activated.connect(self._on_mi_table_click)
        # клик на поверку в таблице
        ui.tableView_vri_list.clicked.connect(self._on_vri_table_click)
        ui.tableView_vri_list.activated.connect(self._on_vri_table_click)
        # фильтр приборов при изменении поля фильтра
        ui.lineEdit_equip_filter.textChanged.connect(self._filter_mi_table)
        # переключение вкладок
        ui.tabWidget.currentChanged.connect(self._on_tab_changed)
        # "Удалить": клик по кнопке удаления прибора
        ui.pushButton_delete_mi.clicked.connect(self._delete_mi)
        # смена подвидов измерений при выборе вида измерений
        ui.comboBox_measure_code.currentTextChanged.connect(self._add_measure_subcodes)
        # переключение флажков годен/брак
        ui.radioButton_applicable.clicked.connect(
            lambda: self._set_vri_applicability(True, ui.checkBox_unlimited.isChecked()))
        ui.radioButton_inapplicable.clicked.connect(
            lambda: self._set_vri_applicability(False, ui.checkBox_unlimited.isChecked()))
        # установка флажка бессрочной поверки
        ui.checkBox_unlimited.clicked.connect(
            lambda: self._set_vri_applicability(True, ui.checkBox_unlimited.isChecked()))
        # добавление отдела
        ui.pushButton_add_dep.clicked.connect(self._on_add_dep)
        # удаление отдела
        ui.pushButton_remove_dep.clicked.connect(self._on_remove_dep)
        # изменение статуса СИ (эталон или СИ)
        ui.comboBox_status.activated.connect(self._on_status_changed)
        # клик по кнопке "Обновить все"
        ui.pushButton_refresh_all.clicked.connect(self._refresh_all)
        # переключение наличия периодической поверки
        ui.radioButton_MPI_yes.toggled.connect(self._on_MPI_toggled)

    def _make_change_connects(self):
        ui = self.ui
        ui.pushButton_undo_mi_changes.clicked.connect(lambda: self._update_mi_tab(self.cur_mi_id))
        # ui.lineEdit_reg_card_number.textChanged.connect(self._change_mi_tab)
        ui.comboBox_status.activated.connect(self._change_mi_tab)
        ui.comboBox_measure_code.activated.connect(self._change_mi_tab)
        ui.comboBox_measure_subcode.activated.connect(self._change_mi_tab)
        ui.comboBox_responsiblePerson.activated.connect(self._change_mi_tab)
        ui.comboBox_room.activated.connect(self._change_mi_tab)
        ui.radioButton_MPI_yes.toggled.connect(self._change_mi_tab)
        ui.lineEdit_reestr.textChanged.connect(self._change_mi_tab)
        # ui.plainTextEdit_title.textChanged.connect(lambda: self._set_property_value(ui.plainTextEdit_title.toPlainText()))
        ui.plainTextEdit_type.textChanged.connect(self._change_mi_tab)
        ui.lineEdit_modification.textChanged.connect(self._change_mi_tab)
        ui.lineEdit_number.textChanged.connect(self._change_mi_tab)
        ui.lineEdit_inv_number.textChanged.connect(self._change_mi_tab)
        ui.plainTextEdit_manufacturer.textChanged.connect(self._change_mi_tab)
        ui.lineEdit_manuf_year.textChanged.connect(self._change_mi_tab)
        ui.lineEdit_expl_year.textChanged.connect(self._change_mi_tab)
        ui.lineEdit_diapazon.textChanged.connect(self._change_mi_tab)
        ui.lineEdit_PG.textChanged.connect(self._change_mi_tab)
        ui.lineEdit_KT.textChanged.connect(self._change_mi_tab)
        ui.plainTextEdit_other_characteristics.textChanged.connect(self._change_mi_tab)

    def _set_property_value(self, new_value):
        if self.sender().objectName() == "plainTextEdit_title":
            self.mi_title = new_value

    def _change_mi_tab(self):
        ui = self.ui
        color = f"color: {self.COLOR_OF_CHANGED_FIELDS}"
        mi_info = self.mi_model.get_mi_info(self.cur_mi_id)
        changed = False
        sender = self.sender()

        # print(sender.objectName())

        if ui.lineEdit_reg_card_number.text() != mi_info['reg_card_number']:
            ui.lineEdit_reg_card_number.setStyleSheet(self.CSS_COLOR_STYLE)
            ui.label_64.setStyleSheet(color)
            changed = self._mi_tab_state_changed()
        else:
            ui.lineEdit_reg_card_number.setStyleSheet(None)
            ui.label_64.setStyleSheet(None)

        if ui.comboBox_status.currentText() != mi_info['status']:
            ui.comboBox_status.setStyleSheet(color)
            changed = self._mi_tab_state_changed()
        else:
            ui.comboBox_status.setStyleSheet(None)

        if not mi_info['measure_code']:
            if ui.comboBox_measure_code.currentText() != "- Не определено":
                ui.comboBox_measure_code.setStyleSheet(color)
                changed = self._mi_tab_state_changed()
            else:
                ui.comboBox_measure_code.setStyleSheet(None)
            if ui.comboBox_measure_subcode.currentText() != "- Не определено":
                ui.comboBox_measure_subcode.setStyleSheet(color)
                changed = self._mi_tab_state_changed()
            else:
                ui.comboBox_measure_subcode.setStyleSheet(None)
        else:
            if not ui.comboBox_measure_code.currentText().startswith(mi_info['measure_code'][:2]):
                ui.comboBox_measure_code.setStyleSheet(color)
                changed = self._mi_tab_state_changed()
            else:
                ui.comboBox_measure_code.setStyleSheet(None)
            if len(mi_info['measure_code']) == 2 \
                    and ui.comboBox_measure_subcode.currentText() != "- Не определено":
                ui.comboBox_measure_subcode.setStyleSheet(color)
                changed = self._mi_tab_state_changed()
            elif len(mi_info['measure_code']) == 4 \
                    and not ui.comboBox_measure_subcode.currentText().startswith(mi_info['measure_code']):
                ui.comboBox_measure_subcode.setStyleSheet(color)
                changed = self._mi_tab_state_changed()
            else:
                ui.comboBox_measure_subcode.setStyleSheet(None)

        mi_dep_dict = self.mi_dep_model.get_mi_dep_dict()
        data = self.mi_dep_model.get_data()
        if (self.cur_mi_id in mi_dep_dict and set(mi_dep_dict[self.cur_mi_id]) != set(data)) \
                or (self.cur_mi_id not in mi_dep_dict and len(data) > 0):
            changed = self._mi_tab_state_changed()

        if ui.comboBox_responsiblePerson.currentIndex() != self.workers_model.get_index(mi_info['responsible_person']):
            ui.comboBox_responsiblePerson.setStyleSheet(color)
            changed = self._mi_tab_state_changed()
        else:
            ui.comboBox_responsiblePerson.setStyleSheet(None)

        if ui.comboBox_room.currentIndex() != self.rooms_model.get_index(mi_info['room']):
            ui.comboBox_room.setStyleSheet(color)
            changed = self._mi_tab_state_changed()
        else:
            ui.comboBox_room.setStyleSheet(None)

        if ui.radioButton_MPI_yes.isChecked() != bool(mi_info['MPI']):
            if ui.radioButton_MPI_yes.isChecked():
                ui.radioButton_MPI_yes.setStyleSheet(color)
                ui.label_57.setStyleSheet(color)
                ui.label_58.setStyleSheet(color)
                ui.lineEdit_MPI.setStyleSheet(color)
            else:
                ui.radioButton_MPI_no.setStyleSheet(color)
            changed = self._mi_tab_state_changed()
        else:
            ui.radioButton_MPI_no.setStyleSheet(None)
            ui.radioButton_MPI_yes.setStyleSheet(None)
            ui.label_57.setStyleSheet(None)
            ui.label_58.setStyleSheet(None)
            ui.lineEdit_MPI.setStyleSheet(None)

        if ui.lineEdit_MPI.text() != mi_info['MPI']:
            ui.lineEdit_MPI.setStyleSheet(color)
            changed = self._mi_tab_state_changed()
        else:
            ui.lineEdit_MPI.setStyleSheet(None)

        if ui.lineEdit_reestr.text() != mi_info['reestr']:
            ui.lineEdit_reestr.setStyleSheet(color)
            changed = self._mi_tab_state_changed()
        else:
            ui.lineEdit_reestr.setStyleSheet(None)

        # if ui.plainTextEdit_title.toPlainText() != mi_info['title']:
        #     self.mi_title = ui.plainTextEdit_title.toPlainText()
        #     ui.plainTextEdit_title.setStyleSheet(color)
        #     changed = self._mi_tab_state_changed()
        # else:
        #     ui.plainTextEdit_title.setStyleSheet(None)

        if ui.plainTextEdit_type.toPlainText() != mi_info['type']:
            ui.plainTextEdit_type.setStyleSheet(color)
            changed = self._mi_tab_state_changed()
        else:
            ui.plainTextEdit_type.setStyleSheet(None)

        if ui.lineEdit_modification.text() != mi_info['modification']:
            ui.lineEdit_modification.setStyleSheet(color)
            changed = self._mi_tab_state_changed()
        else:
            ui.lineEdit_modification.setStyleSheet(None)

        if ui.lineEdit_number.text() != mi_info['number']:
            ui.lineEdit_number.setStyleSheet(color)
            changed = self._mi_tab_state_changed()
        else:
            ui.lineEdit_number.setStyleSheet(None)

        if ui.lineEdit_inv_number.text() != mi_info['inv_number']:
            ui.lineEdit_inv_number.setStyleSheet(color)
            changed = self._mi_tab_state_changed()
        else:
            ui.lineEdit_inv_number.setStyleSheet(None)

        if ui.plainTextEdit_manufacturer.toPlainText() != mi_info['manufacturer']:
            ui.plainTextEdit_manufacturer.setStyleSheet(color)
            changed = self._mi_tab_state_changed()
        else:
            ui.plainTextEdit_manufacturer.setStyleSheet(None)

        if ui.lineEdit_manuf_year.text() != mi_info['manuf_year']:
            ui.lineEdit_manuf_year.setStyleSheet(color)
            changed = self._mi_tab_state_changed()
        else:
            ui.lineEdit_manuf_year.setStyleSheet(None)

        if ui.lineEdit_expl_year.text() != mi_info['expl_year']:
            ui.lineEdit_expl_year.setStyleSheet(color)
            changed = self._mi_tab_state_changed()
        else:
            ui.lineEdit_expl_year.setStyleSheet(None)

        if ui.lineEdit_diapazon.text() != mi_info['diapazon']:
            ui.lineEdit_diapazon.setStyleSheet(color)
            changed = self._mi_tab_state_changed()
        else:
            ui.lineEdit_diapazon.setStyleSheet(None)

        if ui.lineEdit_PG.text() != mi_info['PG']:
            ui.lineEdit_PG.setStyleSheet(color)
            changed = self._mi_tab_state_changed()
        else:
            ui.lineEdit_PG.setStyleSheet(None)

        if ui.lineEdit_KT.text() != mi_info['KT']:
            ui.lineEdit_KT.setStyleSheet(color)
            changed = self._mi_tab_state_changed()
        else:
            ui.lineEdit_KT.setStyleSheet(None)

        if ui.plainTextEdit_other_characteristics.toPlainText() != mi_info['other_characteristics']:
            ui.plainTextEdit_other_characteristics.setStyleSheet(color)
            changed = self._mi_tab_state_changed()
        else:
            ui.plainTextEdit_other_characteristics.setStyleSheet(None)

        self._field_was_modified(sender, mi_info)

        if not changed:
            self._return_origin_mi_tab()

    def _field_was_modified(self, sender, mi_info):
        field_name = sender.objectName().split("_", 1)[1]
        if type(sender) == QPlainTextEdit and sender.toPlainText() != mi_info[field_name]:
            sender.setStyleSheet("color: green;")
            # changed = self._mi_tab_state_changed()
        else:
            sender.setStyleSheet(None)

    def _return_origin_mi_tab(self):
        self.ui.pushButton_save_mi_info.hide()
        self.ui.pushButton_undo_mi_changes.hide()
        self._reset_mi_tab_styles()

    def _reset_mi_tab_styles(self):
        ui = self.ui
        ui.lineEdit_reg_card_number.setStyleSheet(None)
        ui.label_64.setStyleSheet(None)
        ui.comboBox_status.setStyleSheet(None)
        ui.comboBox_measure_code.setStyleSheet(None)
        ui.comboBox_measure_subcode.setStyleSheet(None)
        ui.comboBox_responsiblePerson.setStyleSheet(None)
        ui.comboBox_room.setStyleSheet(None)
        ui.radioButton_MPI_no.setStyleSheet(None)
        ui.radioButton_MPI_yes.setStyleSheet(None)
        ui.label_57.setStyleSheet(None)
        ui.label_58.setStyleSheet(None)
        ui.lineEdit_MPI.setStyleSheet(None)
        ui.lineEdit_reestr.setStyleSheet(None)
        ui.plainTextEdit_title.setStyleSheet(None)
        ui.plainTextEdit_type.setStyleSheet(None)
        ui.lineEdit_modification.setStyleSheet(None)
        ui.lineEdit_number.setStyleSheet(None)
        ui.lineEdit_inv_number.setStyleSheet(None)
        ui.plainTextEdit_manufacturer.setStyleSheet(None)
        ui.lineEdit_manuf_year.setStyleSheet(None)
        ui.lineEdit_expl_year.setStyleSheet(None)
        ui.lineEdit_diapazon.setStyleSheet(None)
        ui.lineEdit_PG.setStyleSheet(None)
        ui.lineEdit_KT.setStyleSheet(None)
        ui.plainTextEdit_other_characteristics.setStyleSheet(None)

    def _mi_tab_state_changed(self) -> bool:

        self.ui.pushButton_save_mi_info.show()
        self.ui.pushButton_undo_mi_changes.show()
        self.ui.pushButton_save_mi_info.setStyleSheet("font-weight: bold; font-size: 12px; color: #1854A8;")
        animation = QPropertyAnimation(self.ui.pushButton_save_mi_info, b'pos', self)
        animation.setKeyValueAt(0, QPoint(10, 10))
        animation.setKeyValueAt(0.25, QPoint(15, 10))
        animation.setKeyValueAt(0.5, QPoint(10, 10))
        animation.setKeyValueAt(0.75, QPoint(5, 10))
        animation.setKeyValueAt(1, QPoint(10, 10))
        animation.setDuration(200)
        animation.setLoopCount(5)
        animation.start()
        return True

    def _initialize_start_screen(self):
        self._add_measure_codes()
        self.ui.comboBox_status.addItems(GLOBAL_VARS.MI_STATUS_LIST)
        self.ui.comboBox_vri_vriType.addItems(GLOBAL_VARS.VRI_TYPE_LIST)

        self.ui.tabWidget.setCurrentIndex(0)
        self.ui.tabWidget.currentChanged.emit(0)

        self.ui.pushButton_save_mi_info.hide()
        self.ui.pushButton_undo_mi_changes.hide()

        self.ui.groupBox_uve_info.hide()

        # не сужаем поля даты поверки и годен до при бессрочной поверке или браке
        sp = self.ui.dateEdit_vri_validDate.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.ui.dateEdit_vri_validDate.setSizePolicy(sp)
        sp = self.ui.checkBox_unlimited.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.ui.checkBox_unlimited.setSizePolicy(sp)
        sp = self.ui.label_13.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.ui.label_13.setSizePolicy(sp)

    def _on_status_changed(self, index):
        self.ui.tabWidget.setTabEnabled(1, index)

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

    def _on_mi_table_click(self, index):
        if index.isValid():
            self.cur_mi_id = index.data(Qt.UserRole)

    def _on_vri_table_click(self, index):
        if index.isValid():
            self.vri_id = index.data(Qt.UserRole)

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
        mi_info = self.mi_model.get_mi_info(mi_id)

        self.ui.lineEdit_mi_id.setText(f"{mi_id}")

        for field_name in self.field_name_dependencies:
            if type(self.field_name_dependencies[field_name]) == QPlainTextEdit:
                self.field_name_dependencies[field_name].setPlainText(mi_info[field_name])
            elif type(self.field_name_dependencies[field_name]) == QTextEdit:
                self.field_name_dependencies[field_name].setText(mi_info[field_name])
            elif type(self.field_name_dependencies[field_name]) == QCheckBox:
                self.field_name_dependencies[field_name].setChecked(bool(mi_info[field_name]))

        # self.ui.lineEdit_reg_card_number.setText(mi_info['reg_card_number'])

        self.ui.comboBox_status.setCurrentText(mi_info['status'])
        self.ui.comboBox_status.update()
        self.ui.comboBox_status.activated.emit(self.ui.comboBox_status.currentIndex())

        self.ui.comboBox_measure_code.setCurrentText(self.mi_model.get_measure_code_text(mi_id, self.MEASURE_CODES))
        self.ui.comboBox_measure_code.update()
        self.ui.comboBox_measure_subcode.setCurrentText(
            self.mi_model.get_measure_subcode_text(mi_id, self.MEASURE_CODES))
        self.ui.comboBox_measure_subcode.update()

        # изменение модели списка отделов
        self.mi_dep_model.layoutAboutToBeChanged.emit()
        self.mi_dep_model.set_current_mi_id(mi_id)
        self.mi_dep_model.layoutChanged.emit()

        self._update_rooms_and_workers()

        # self.ui.lineEdit_reestr.setText(mi_info['reestr'])
        # self.ui.plainTextEdit_title.setPlainText(mi_info['title'])
        # self.ui.plainTextEdit_type.setPlainText(mi_info['type'])
        # self.ui.lineEdit_modification.setText(mi_info['modification'])
        # self.ui.lineEdit_number.setText(mi_info['number'])
        # self.ui.lineEdit_inv_number.setText(mi_info['inv_number'])
        # self.ui.plainTextEdit_manufacturer.setPlainText(mi_info['manufacturer'])
        # self.ui.lineEdit_manuf_year.setText(mi_info['manuf_year'])
        # self.ui.lineEdit_expl_year.setText(mi_info['expl_year'])
        # self.ui.lineEdit_diapazon.setText(mi_info['diapazon'])
        # self.ui.lineEdit_PG.setText(mi_info['PG'])
        # self.ui.lineEdit_KT.setText(mi_info['KT'])
        # self.ui.plainTextEdit_other_characteristics.setPlainText(mi_info['other_characteristics'])
        # self.ui.lineEdit_MPI.setText(mi_info['MPI'])

        is_unlimited = not mi_info['MPI']
        self.ui.radioButton_MPI_yes.setChecked(not is_unlimited)
        self.ui.radioButton_MPI_no.setChecked(is_unlimited)
        self.ui.radioButton_MPI_yes.toggled.emit(self.ui.radioButton_MPI_yes.isChecked())

        # self.ui.plainTextEdit_purpose.setPlainText(mi_info['purpose'])
        # self.ui.plainTextEdit_personal.setPlainText(mi_info['personal'])
        # self.ui.plainTextEdit_software_inner.setPlainText(mi_info['software_inner'])
        # self.ui.plainTextEdit_software_outer.setPlainText(mi_info['software_outer'])
        # self.ui.plainTextEdit_owner.setPlainText(mi_info['owner'])
        # self.ui.plainTextEdit_owner_contract.setPlainText(mi_info['owner_contract'])

        self.ui.lineEdit_mi_last_scan_date.setText(func.get_formatted_date(mi_info['last_scan_date']))

        # self.ui.checkBox_has_manual.setChecked(bool(mi_info['RE']))
        # self.ui.checkBox_has_pasport.setChecked(bool(mi_info['pasport']))
        # self.ui.checkBox_has_verif_method.setChecked(bool(mi_info['MP']))

        # self.ui.lineEdit_period_TO.setText(mi_info['TO_period'])

        self._return_origin_mi_tab()

    def _update_vri_tab(self, vri_id):

        vri_info = self.vri_model.get_vri_info(self.cur_mi_id, vri_id)

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

    def _on_MPI_toggled(self):
        self.ui.label_57.setVisible(self.ui.radioButton_MPI_yes.isChecked())
        self.ui.label_58.setVisible(self.ui.radioButton_MPI_yes.isChecked())
        self.ui.lineEdit_MPI.setVisible(self.ui.radioButton_MPI_yes.isChecked())

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

    # -------------------------------------КЛИК ПО КНОПКЕ "ДОБАВИТЬ ОТДЕЛ"---------------------------------------------
    def _on_add_dep(self):
        departments = self.mi_dep_model.get_departments()
        cur_dep_names = [departments[dep_id]['name'] for dep_id in self.mi_dep_model.get_data()]
        full_dep_names = [departments[dep_id]['name'] for dep_id in departments]
        choose_list = sorted(list(set(full_dep_names) - set(cur_dep_names)))
        if choose_list:
            dep_name, ok = QInputDialog.getItem(self, "Выбор отдела",
                                                "Выберите отдел, который использует данное оборудование",
                                                choose_list, current=0, editable=False)
            if ok and dep_name:
                new_dep_id = [dep_id for dep_id in departments if departments[dep_id]['name'] == dep_name][0]
                if not new_dep_id:
                    return
                self.mi_dep_model.layoutAboutToBeChanged.emit()
                self.mi_dep_model.add_department(new_dep_id)
                self.mi_dep_model.layoutChanged.emit()
                self._update_rooms_and_workers()
                self._change_mi_tab()
        else:
            QMessageBox.information(self, "Выбора нет", "Все подразделения включены в список")

    # ----------------------------------КЛИК ПО КНОПКЕ "УДАЛИТЬ ОТДЕЛ"-------------------------------------------------
    def _on_remove_dep(self):
        if not self.ui.listView_departments.selectedIndexes():
            return
        dep_id = self.ui.listView_departments.currentIndex().data(Qt.UserRole)
        self.mi_dep_model.layoutAboutToBeChanged.emit()
        self.mi_dep_model.remove_department(dep_id)
        self.mi_dep_model.layoutChanged.emit()
        self._update_rooms_and_workers()
        self._change_mi_tab()

    def _update_rooms_and_workers(self):
        mi_info = self.mi_model.get_mi_info(self.cur_mi_id)

        self.workers_model.layoutAboutToBeChanged.emit()
        self.workers_model.clear_model()
        for dep_id in self.mi_dep_model.get_data():
            self.workers_model.add_dep(dep_id, mi_info['responsible_person'])
        self.workers_model.layoutChanged.emit()
        self.ui.comboBox_responsiblePerson.setCurrentIndex(self.workers_model.get_index(mi_info['responsible_person']))
        self.ui.comboBox_responsiblePerson.update()

        self.rooms_model.layoutAboutToBeChanged.emit()
        self.rooms_model.clear_model()
        for dep_id in self.mi_dep_model.get_data():
            self.rooms_model.add_dep(dep_id, mi_info['room'])
        self.rooms_model.layoutChanged.emit()
        self.ui.comboBox_room.setCurrentIndex(self.rooms_model.get_index(mi_info['room']))
        self.ui.comboBox_room.update()

    def _refresh_all(self):
        self.mi_model.layoutAboutToBeChanged.emit()
        self.mi_model.update_model()
        self.mi_model.layoutChanged.emit()
        self.ui.tableView_mi_list.resizeRowsToContents()
        self.vri_model.update_model()
        self.workers_model.update_model()
        self.rooms_model.update_model()
        self.ui.tableView_mi_list.selectRow(0)
        self.ui.tableView_mi_list.clicked.emit(self.mi_proxy_model.index(0, 0))
        print("_refresh_all")

    def _get_measure_code(self):
        """
        :return: ВОЗВРАЩАЕМ ПОДВИД ИЗМЕРЕНИЙ, ВИД ИЗМЕРЕНИЙ ИЛИ "0" НА
        """
        if self.ui.comboBox_measure_subcode.currentIndex():
            measure_code = self.ui.comboBox_measure_subcode.currentText()[:4]
        else:
            measure_code = self.ui.comboBox_measure_code.currentText()[:2] \
                if self.ui.comboBox_measure_code.currentIndex() else ""
        return measure_code

    @property
    def cur_mi_id(self):
        return self._current_mi_id

    @cur_mi_id.setter
    def cur_mi_id(self, value):
        self._current_mi_id = value
        self.mi_info = self.mi_model.get_mi_info(value)
        self.mi_title = self.mi_info['title']
        self.vReestr = self.mi_info['reg_card_number']

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

    @property
    def mi_title(self):
        return self._mi_title

    @mi_title.setter
    def mi_title(self, value: str):
        self._mi_title = value
        self.ui.plainTextEdit_title.setPlainText(value)

    @pyqtProperty(str)
    def vReestr(self):
        return self._reg_card_number

    @vReestr.setter
    def vReestr(self, value: str):
        self._reg_card_number = value
        self.ui.lineEdit_reg_card_number.setText(value)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = EquipmentWidget()
    window.setWindowTitle("Средства измерений")
    window.showMaximized()
    sys.exit(app.exec())
