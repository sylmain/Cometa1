import typing

from PyQt5 import QtGui
from PyQt5.QtCore import QAbstractListModel, QModelIndex, Qt, QVariant

import GLOBAL_VARS
from functions_pkg import functions as func


class RoomsModel(QAbstractListModel):

    def __init__(self):
        super(RoomsModel, self).__init__()
        self._data = [0]
        self._current_room_id = 0
        self.rooms = {}
        self.dep_rooms = {}
        self.update_model()

    def update_model(self):
        self.rooms = func.get_rooms()['room_dict']
        self.dep_rooms = func.get_room_deps()['dep_rooms_dict']

    def add_dep(self, dep_id, current_room_id):
        self._current_room_id = current_room_id
        if dep_id not in self.dep_rooms:
            return
        for room_id in self.dep_rooms[dep_id]:
            if room_id not in self._data:
                self._data.append(room_id)

    def clear_model(self) -> None:
        self._data.clear()
        self._data.append(0)

    def get_index(self, room_id: int) -> int:
        if room_id in self._data:
            return self._data.index(room_id)
        return 0

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            if len(self._data) > index.row():
                room_number = self.rooms[self._data[index.row()]]['number'] \
                    if self._data[index.row()] in self.rooms else "- Не определено"
                return room_number
            return "---"

        if role == Qt.UserRole:
            return self._data[index.row()]

        if role == Qt.ForegroundRole and index.row() != self.get_index(self._current_room_id):
            return QtGui.QColor(GLOBAL_VARS.COLOR_OF_CHANGED_FIELDS)

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data)
