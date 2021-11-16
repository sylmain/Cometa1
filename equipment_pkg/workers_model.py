from PyQt5.QtCore import QAbstractListModel, QModelIndex, Qt, QVariant
from functions_pkg import functions as func
import typing


class WorkersModel(QAbstractListModel):

    def __init__(self):
        super(WorkersModel, self).__init__()
        self._data = list()
        self.workers = func.get_workers()['worker_dict']
        self.dep_workers = func.get_worker_deps()['dep_workers_dict']

    def add_dep_id(self, dep_id):
        if dep_id not in self.dep_workers:
            return
        for worker_id in self.dep_workers[dep_id]:
            if worker_id not in self._data:
                self._data.append(worker_id)

    def clear_model(self) -> None:
        self._data.clear()

    def get_index(self, worker_id: int) -> int:
        if worker_id in self._data:
            return self._data.index(worker_id)
        return -1

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            return func.get_worker_fio_from_id(self._data[index.row()], self.workers)

        if role == Qt.UserRole:
            return self._data[index.row()]

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data)
