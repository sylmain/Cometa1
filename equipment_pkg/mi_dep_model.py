from PyQt5.QtCore import QAbstractListModel, QModelIndex, Qt, QVariant
from functions_pkg import functions as func
import typing


class MiDepModel(QAbstractListModel):

    def __init__(self):
        super(MiDepModel, self).__init__()
        self._data = []
        self.mi_dep = func.get_mi_deps()['mi_deps_dict']
        self.departments = func.get_departments()['dep_dict']

    def set_current_mi_id(self, mi_id):
        self._data.clear()
        if mi_id not in self.mi_dep:
            return
        self._data = self.mi_dep[mi_id].copy()
        self._data.sort()

    def get_data(self):
        return self._data

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            return self.departments[self._data[index.row()]]['name']

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data)
