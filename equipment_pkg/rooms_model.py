from PyQt5.QtCore import QAbstractListModel, QModelIndex, Qt, QVariant
from functions_pkg import functions as func
import typing


class RoomsModel(QAbstractListModel):

    def __init__(self):
        super(RoomsModel, self).__init__()
        self._data = list()
        self.rooms = func.get_rooms()['room_dict']
        self.dep_rooms = func.get_room_deps()['dep_rooms_dict']

    def add_dep_id(self, dep_id):
        if dep_id not in self.dep_rooms:
            return
        for room_id in self.dep_rooms[dep_id]:
            if room_id not in self._data:
                self._data.append(room_id)

    def clear_model(self) -> None:
        self._data.clear()

    def get_index(self, room_id: int) -> int:
        if room_id in self._data:
            return self._data.index(room_id)
        return -1

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            return self.rooms[self._data[index.row()]]['number']

        if role == Qt.UserRole:
            return self._data[index.row()]

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data)
