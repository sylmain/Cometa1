import typing

from PyQt5 import QtGui
from PyQt5.QtCore import QAbstractListModel, QModelIndex, Qt, QVariant

import GLOBAL_VARS
from functions_pkg import functions as func


class MiDepModel(QAbstractListModel):

    def __init__(self):
        super(MiDepModel, self).__init__()
        self.mi_id = 0
        self._data = []
        self.mi_dep = {}
        self.departments = {}
        self.update_model()

    def update_model(self):
        self.mi_dep = func.get_mi_deps()['mi_deps_dict']
        self.departments = func.get_departments()['dep_dict']

    def get_mi_dep_dict(self) -> dict:
        return self.mi_dep

    def set_current_mi_id(self, mi_id):
        self.mi_id = mi_id
        self._data.clear()
        if mi_id not in self.mi_dep:
            return
        self._data = self.mi_dep[mi_id].copy()
        self._data.sort()

    def get_departments(self):
        return self.departments

    def add_department(self, dep_id):
        self._data.append(dep_id)

    def remove_department(self, dep_id):
        self._data.remove(dep_id)

    def get_data(self):
        return self._data

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            return self.departments[self._data[index.row()]]['name']

        if role == Qt.UserRole:
            return self._data[index.row()]

        if role == Qt.ForegroundRole:
            if (self.mi_id in self.mi_dep and self._data[index.row()] not in self.mi_dep[self.mi_id]) \
                    or self.mi_id not in self.mi_dep:
                return QtGui.QColor(GLOBAL_VARS.COLOR_OF_CHANGED_FIELDS)

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data)
