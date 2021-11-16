from PyQt5.QtCore import Qt, QModelIndex, QAbstractTableModel, QDate, QSortFilterProxyModel
from PyQt5 import QtGui
from PyQt5.QtGui import QFont
import equipment_pkg.sql_functions as sql_func
import typing

from functions_pkg import functions as func


class MiModel(QAbstractTableModel):
    column_count = 5
    headers = ["Номер карты", "Код", "Наименование", "Тип", "Зав. номер"]

    def __init__(self):
        super(MiModel, self).__init__()
        self._mi_data = []
        self.mi_dict = dict()
        self.update_model()

    def update_model(self) -> None:
        """Обновление модели при изменении таблицы приборов (удаление, добавление, редактирование)
        :return:
        """
        self._mi_data.clear()
        self.mi_dict = func.get_mis()['mi_dict']
        for mi_id in self.mi_dict:
            row = [
                self.mi_dict[mi_id]['reg_card_number'],
                self.mi_dict[mi_id]['measure_code'],
                self.mi_dict[mi_id]['title'],
                self.mi_dict[mi_id]['modification'],
                self.mi_dict[mi_id]['number'],
                mi_id
            ]
            self._mi_data.append(row)

    def get_mi_dict(self):
        return self.mi_dict

    def delete_mi(self, mi_id) -> bool:
        if self._mi_data:
            result = sql_func.delete_equipment(mi_id)
            if result:
                self.update_model()
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
            return self._mi_data[index.row()][index.column()]

        if role == Qt.UserRole:
            return self._mi_data[index.row()][5]

        if role == Qt.BackgroundRole and index.column() == 2:
            # See below for the data structure.
            return QtGui.QColor('cyan')

        if role == Qt.TextAlignmentRole:
            if index.column() == 1:
                # Align right, vertical middle.
                return Qt.AlignCenter

        if role == Qt.ToolTipRole or role == Qt.WhatsThisRole:
            if index.column() == 2:
                return self._mi_data[index.row()][index.column()]

    def rowCount(self, parent: QModelIndex = ...) -> int:
        # The length of the outer list.
        return len(self._mi_data)

    def columnCount(self, parent: QModelIndex = ...) -> int:
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return self.column_count
