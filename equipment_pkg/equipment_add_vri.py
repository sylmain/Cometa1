from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5 import QtCore

from equipment_pkg.ui_equipment_add_vri import Ui_Form


class EquipmentAddVri(QWidget):
    start_searching_signal = QtCore.pyqtSignal(int, int, int)

    def __init__(self):
        super(EquipmentAddVri, self).__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.setWindowTitle("Поиск и добавление поверок")

        self.ui.groupBox_search_settings.setDisabled(True)

        self.ui.pushButton_start_search.clicked.connect(self._on_start_search)

        self.ui.radioButton_search.toggled.connect(
            lambda: self.ui.groupBox_search_settings.setEnabled(True) if self.ui.radioButton_search.isChecked()
            else self.ui.groupBox_search_settings.setDisabled(True))

    def set_manuf_number(self, number):
        self.ui.lineEdit_manuf_number.setText(number)
    def set_reestr(self, reestr):
        self.ui.lineEdit_reestr.setText(reestr)
    def set_title(self, title):
        self.ui.plainTextEdit_title.setPlainText(title)

    def _on_start_search(self):
        if self.ui.radioButton_search.isChecked():
            chars = int(self.ui.spinBox_min_len_value.value())
            normal = int(self.ui.spinBox_norm_search_max_count.value())
            adv = int(self.ui.spinBox_adv_search_max_count.value())
            self.start_searching_signal.emit(chars, normal, adv)
            self.close()
            return
        global MANUF_NUMBER_CHARS_MIN_FOR_SCAN
        global VRI_COUNT_MAX_FOR_NORMAL_SCAN
        global VRI_COUNT_MAX_FOR_ADV_SCAN