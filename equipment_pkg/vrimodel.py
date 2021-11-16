from PyQt5.QtCore import Qt, QModelIndex, QAbstractTableModel, QDate, QSortFilterProxyModel
from PyQt5 import QtGui
from PyQt5.QtGui import QFont
import equipment_pkg.sql_functions as sql_func
import typing

from functions_pkg import functions as func


class VriModel(QAbstractTableModel):
    column_count = 6
    headers = ["Дата поверки", "Годен до", "Номер свидетельства", "Результат", "Организация-поверитель", "Эталон"]

    def __init__(self):
        super(VriModel, self).__init__()
        self._vri_data = []
        self.vri_dict = func.get_mis_vri_info()['mis_vri_dict']
        # self._update_model()

    def _update_model(self) -> None:
        """Обновление модели при изменении таблицы поверок (удаление, добавление, редактирование)
        :return:
        """
        self._vri_data.clear()
        for mi_id in self.vri_dict:
            for vri_id in self.vri_dict[mi_id]:
                row = [
                    self.vri_dict[mi_id][vri_id]['vri_vrfDate'],
                    self.vri_dict[mi_id][vri_id]['vri_validDate'],
                    self.vri_dict[mi_id][vri_id]['vri_certNum'],
                    self.vri_dict[mi_id][vri_id]['vri_applicable'],
                    self.vri_dict[mi_id][vri_id]['vri_organization'],
                    self.vri_dict[mi_id][vri_id]['vri_mieta_number'],
                    vri_id,
                    mi_id
                ]
                self._vri_data.append(row)

    def set_current_mi_id(self, mi_id):
        self._vri_data.clear()
        if mi_id not in self.vri_dict:
            return
        for vri_id in self.vri_dict[mi_id]:
            row = [
                QDate(self.vri_dict[mi_id][vri_id]['vri_vrfDate'])
                if self.vri_dict[mi_id][vri_id]['vri_vrfDate'] else "",
                QDate(self.vri_dict[mi_id][vri_id]['vri_validDate'])
                if self.vri_dict[mi_id][vri_id]['vri_validDate'] else "",
                self.vri_dict[mi_id][vri_id]['vri_certNum'],
                "ГОДЕН" if self.vri_dict[mi_id][vri_id]['vri_applicable'] else "БРАК",
                self.vri_dict[mi_id][vri_id]['vri_organization'],
                self.vri_dict[mi_id][vri_id]['vri_mieta_number'],
                vri_id
            ]
            self._vri_data.append(row)
        print(self._vri_data)

    def get_vri_dict(self):
        return self.vri_dict

    def delete_vri(self, vri_id) -> bool:
        if self._vri_data:
            result = sql_func.delete_verification(vri_id)
            if result:
                self._update_model()
                return True
            return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]

        if role == Qt.FontRole:
            font = QFont("Times", 8, QFont.Bold, False)
            return font

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            return self._vri_data[index.row()][index.column()]

        if role == Qt.UserRole:
            return self._vri_data[index.row()][6]

        if role == Qt.BackgroundRole and index.column() == 1:
            # See below for the data structure.
            return QtGui.QColor('cyan')

        if role == Qt.TextAlignmentRole:
            if index.column() == 1:
                # Align right, vertical middle.
                return Qt.AlignCenter

        if role == Qt.ToolTipRole or role == Qt.WhatsThisRole:
            if index.column() == 2:
                return self._vri_data[index.row()][index.column()]

    def rowCount(self, parent: QModelIndex = ...) -> int:
        # The length of the outer list.
        return len(self._vri_data)

    def columnCount(self, parent: QModelIndex = ...) -> int:
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return self.column_count
