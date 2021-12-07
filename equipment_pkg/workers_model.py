import typing

from PyQt5 import QtGui
from PyQt5.QtCore import QAbstractListModel, QModelIndex, Qt, QVariant

import GLOBAL_VARS
from functions_pkg import functions as func


class WorkersModel(QAbstractListModel):

    def __init__(self):
        super(WorkersModel, self).__init__()
        self._data = [0]
        self._current_worker_id = 0
        self.workers = {}
        self.dep_workers = {}
        self.update_model()

    def update_model(self):
        self.workers = func.get_workers()['worker_dict']
        self.dep_workers = func.get_worker_deps()['dep_workers_dict']

    def add_dep(self, dep_id, current_worker_id):
        self._current_worker_id = current_worker_id
        if dep_id not in self.dep_workers:
            return
        for worker_id in self.dep_workers[dep_id]:
            if worker_id not in self._data:
                self._data.append(worker_id)

    def remove_dep(self, dep_id):
        if dep_id not in self.dep_workers:
            return
        for worker_id in self.dep_workers[dep_id]:
            if worker_id not in self._data:
                self._data.append(worker_id)

    def clear_model(self) -> None:
        self._data.clear()
        self._data.append(0)

    def get_index(self, worker_id: int) -> int:
        if worker_id in self._data:
            return self._data.index(worker_id)
        return 0

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            if len(self._data) > index.row():
                return self.get_fio_from_worker_id(self._data[index.row()])
            return "---"

        if role == Qt.UserRole:
            return self._data[index.row()]

        if role == Qt.ForegroundRole and index.row() != self.get_index(self._current_worker_id):
            return QtGui.QColor(GLOBAL_VARS.COLOR_OF_CHANGED_FIELDS)

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data)

    def get_fio_from_worker_id(self, worker_id):
        if worker_id in self.workers:
            surname = self.workers[worker_id]['surname']
            name = self.workers[worker_id]['name']
            patronymic = self.workers[worker_id]['patronymic']
            fio = surname
            if name and patronymic:
                fio = f"{surname} {name[:1]}.{patronymic[:1]}."
            elif name:
                fio = f"{surname} {name[:1]}."
            return fio
        return "- Не назначен"
