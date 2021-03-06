# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'rooms.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(876, 741)
        font = QtGui.QFont()
        font.setPointSize(8)
        Form.setFont(font)
        self.gridLayout_2 = QtWidgets.QGridLayout(Form)
        self.gridLayout_2.setHorizontalSpacing(15)
        self.gridLayout_2.setVerticalSpacing(3)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(10)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pushButton_delete = QtWidgets.QPushButton(Form)
        self.pushButton_delete.setEnabled(True)
        self.pushButton_delete.setMinimumSize(QtCore.QSize(180, 30))
        self.pushButton_delete.setMaximumSize(QtCore.QSize(180, 16777215))
        self.pushButton_delete.setStyleSheet("")
        self.pushButton_delete.setObjectName("pushButton_delete")
        self.horizontalLayout_2.addWidget(self.pushButton_delete)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.pushButton_add_rooms = QtWidgets.QPushButton(Form)
        self.pushButton_add_rooms.setEnabled(True)
        self.pushButton_add_rooms.setMinimumSize(QtCore.QSize(180, 30))
        self.pushButton_add_rooms.setObjectName("pushButton_add_rooms")
        self.horizontalLayout_2.addWidget(self.pushButton_add_rooms)
        self.gridLayout_2.addLayout(self.horizontalLayout_2, 2, 0, 1, 1)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout_2.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.treeView = QtWidgets.QTreeView(Form)
        self.treeView.setEnabled(True)
        self.treeView.setMinimumSize(QtCore.QSize(0, 570))
        self.treeView.setObjectName("treeView")
        self.gridLayout_2.addWidget(self.treeView, 1, 0, 1, 1)
        self.line = QtWidgets.QFrame(Form)
        self.line.setFrameShape(QtWidgets.QFrame.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridLayout_2.addWidget(self.line, 0, 2, 3, 1)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setHorizontalSpacing(8)
        self.gridLayout.setVerticalSpacing(4)
        self.gridLayout.setObjectName("gridLayout")
        self.plainTextEdit_room_info = QtWidgets.QPlainTextEdit(Form)
        self.plainTextEdit_room_info.setMaximumSize(QtCore.QSize(16777215, 40))
        self.plainTextEdit_room_info.setTabChangesFocus(True)
        self.plainTextEdit_room_info.setObjectName("plainTextEdit_room_info")
        self.gridLayout.addWidget(self.plainTextEdit_room_info, 22, 0, 1, 3)
        self.label_22 = QtWidgets.QLabel(Form)
        self.label_22.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_22.setWordWrap(True)
        self.label_22.setObjectName("label_22")
        self.gridLayout.addWidget(self.label_22, 14, 0, 1, 3)
        self.label_5 = QtWidgets.QLabel(Form)
        self.label_5.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 6, 0, 1, 3)
        self.label_9 = QtWidgets.QLabel(Form)
        self.label_9.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_9.setObjectName("label_9")
        self.gridLayout.addWidget(self.label_9, 19, 0, 1, 3)
        self.label_16 = QtWidgets.QLabel(Form)
        self.label_16.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_16.setObjectName("label_16")
        self.gridLayout.addWidget(self.label_16, 16, 0, 1, 3)
        self.plainTextEdit_room_purpose = QtWidgets.QPlainTextEdit(Form)
        self.plainTextEdit_room_purpose.setMaximumSize(QtCore.QSize(16777215, 40))
        self.plainTextEdit_room_purpose.setTabChangesFocus(True)
        self.plainTextEdit_room_purpose.setObjectName("plainTextEdit_room_purpose")
        self.gridLayout.addWidget(self.plainTextEdit_room_purpose, 10, 0, 1, 3)
        self.label_2 = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setUnderline(True)
        self.label_2.setFont(font)
        self.label_2.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.label_2.setFrameShadow(QtWidgets.QFrame.Plain)
        self.label_2.setLineWidth(0)
        self.label_2.setMidLineWidth(0)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setIndent(-1)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 5, 0, 1, 3)
        self.plainTextEdit_room_equipment = QtWidgets.QPlainTextEdit(Form)
        self.plainTextEdit_room_equipment.setMaximumSize(QtCore.QSize(16777215, 40))
        self.plainTextEdit_room_equipment.setTabChangesFocus(True)
        self.plainTextEdit_room_equipment.setObjectName("plainTextEdit_room_equipment")
        self.gridLayout.addWidget(self.plainTextEdit_room_equipment, 17, 0, 1, 3)
        self.label_6 = QtWidgets.QLabel(Form)
        self.label_6.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 8, 0, 1, 1)
        self.lineEdit_room_id = QtWidgets.QLineEdit(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_room_id.sizePolicy().hasHeightForWidth())
        self.lineEdit_room_id.setSizePolicy(sizePolicy)
        self.lineEdit_room_id.setMaximumSize(QtCore.QSize(40, 16777215))
        self.lineEdit_room_id.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit_room_id.setReadOnly(True)
        self.lineEdit_room_id.setObjectName("lineEdit_room_id")
        self.gridLayout.addWidget(self.lineEdit_room_id, 0, 2, 1, 1)
        self.comboBox_room_responsible_person = QtWidgets.QComboBox(Form)
        self.comboBox_room_responsible_person.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLength)
        self.comboBox_room_responsible_person.setFrame(True)
        self.comboBox_room_responsible_person.setObjectName("comboBox_room_responsible_person")
        self.gridLayout.addWidget(self.comboBox_room_responsible_person, 11, 1, 1, 2)
        self.label_8 = QtWidgets.QLabel(Form)
        self.label_8.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_8.setObjectName("label_8")
        self.gridLayout.addWidget(self.label_8, 11, 0, 1, 1)
        self.label_4 = QtWidgets.QLabel(Form)
        self.label_4.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 9, 0, 1, 3)
        self.plainTextEdit_room_name = QtWidgets.QPlainTextEdit(Form)
        self.plainTextEdit_room_name.setMaximumSize(QtCore.QSize(16777215, 40))
        self.plainTextEdit_room_name.setTabChangesFocus(True)
        self.plainTextEdit_room_name.setObjectName("plainTextEdit_room_name")
        self.gridLayout.addWidget(self.plainTextEdit_room_name, 7, 0, 1, 3)
        self.label_10 = QtWidgets.QLabel(Form)
        self.label_10.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_10.setObjectName("label_10")
        self.gridLayout.addWidget(self.label_10, 12, 0, 1, 3)
        self.plainTextEdit_room_conditions = QtWidgets.QPlainTextEdit(Form)
        self.plainTextEdit_room_conditions.setMaximumSize(QtCore.QSize(16777215, 40))
        self.plainTextEdit_room_conditions.setTabChangesFocus(True)
        self.plainTextEdit_room_conditions.setObjectName("plainTextEdit_room_conditions")
        self.gridLayout.addWidget(self.plainTextEdit_room_conditions, 15, 0, 1, 3)
        self.plainTextEdit_room_requirements = QtWidgets.QPlainTextEdit(Form)
        self.plainTextEdit_room_requirements.setMaximumSize(QtCore.QSize(16777215, 40))
        self.plainTextEdit_room_requirements.setTabChangesFocus(True)
        self.plainTextEdit_room_requirements.setObjectName("plainTextEdit_room_requirements")
        self.gridLayout.addWidget(self.plainTextEdit_room_requirements, 13, 0, 1, 3)
        self.label_18 = QtWidgets.QLabel(Form)
        self.label_18.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_18.setWordWrap(True)
        self.label_18.setObjectName("label_18")
        self.gridLayout.addWidget(self.label_18, 21, 0, 1, 3)
        self.plainTextEdit_room_personal = QtWidgets.QPlainTextEdit(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plainTextEdit_room_personal.sizePolicy().hasHeightForWidth())
        self.plainTextEdit_room_personal.setSizePolicy(sizePolicy)
        self.plainTextEdit_room_personal.setMinimumSize(QtCore.QSize(0, 0))
        self.plainTextEdit_room_personal.setMaximumSize(QtCore.QSize(16777215, 40))
        self.plainTextEdit_room_personal.setTabChangesFocus(True)
        self.plainTextEdit_room_personal.setObjectName("plainTextEdit_room_personal")
        self.gridLayout.addWidget(self.plainTextEdit_room_personal, 20, 0, 1, 3)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.label = QtWidgets.QLabel(Form)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 2)
        self.line_2 = QtWidgets.QFrame(Form)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.gridLayout.addWidget(self.line_2, 1, 0, 1, 3)
        self.line_3 = QtWidgets.QFrame(Form)
        self.line_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_3.setObjectName("line_3")
        self.gridLayout.addWidget(self.line_3, 4, 0, 1, 3)
        self.lineEdit_room_area = QtWidgets.QLineEdit(Form)
        self.lineEdit_room_area.setObjectName("lineEdit_room_area")
        self.gridLayout.addWidget(self.lineEdit_room_area, 8, 1, 1, 1)
        self.label_7 = QtWidgets.QLabel(Form)
        self.label_7.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_7.setObjectName("label_7")
        self.gridLayout.addWidget(self.label_7, 8, 2, 1, 1)
        self.groupBox = QtWidgets.QGroupBox(Form)
        self.groupBox.setMinimumSize(QtCore.QSize(0, 100))
        self.groupBox.setObjectName("groupBox")
        self.radioButton_own = QtWidgets.QRadioButton(self.groupBox)
        self.radioButton_own.setGeometry(QtCore.QRect(10, 20, 90, 19))
        self.radioButton_own.setObjectName("radioButton_own")
        self.radioButton_rent = QtWidgets.QRadioButton(self.groupBox)
        self.radioButton_rent.setGeometry(QtCore.QRect(10, 40, 90, 19))
        self.radioButton_rent.setObjectName("radioButton_rent")
        self.plainTextEdit_rent = QtWidgets.QPlainTextEdit(self.groupBox)
        self.plainTextEdit_rent.setGeometry(QtCore.QRect(100, 40, 301, 50))
        self.plainTextEdit_rent.setObjectName("plainTextEdit_rent")
        self.gridLayout.addWidget(self.groupBox, 18, 0, 1, 3)
        self.pushButton_save = QtWidgets.QPushButton(Form)
        self.pushButton_save.setEnabled(True)
        self.pushButton_save.setMinimumSize(QtCore.QSize(0, 30))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_save.setFont(font)
        self.pushButton_save.setStyleSheet("")
        self.pushButton_save.setObjectName("pushButton_save")
        self.gridLayout.addWidget(self.pushButton_save, 23, 0, 1, 3)
        self.lineEdit_room_number = QtWidgets.QLineEdit(Form)
        self.lineEdit_room_number.setObjectName("lineEdit_room_number")
        self.gridLayout.addWidget(self.lineEdit_room_number, 2, 1, 2, 2)
        self.label_3 = QtWidgets.QLabel(Form)
        self.label_3.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 2, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 3, 3, 1)
        self.label_8.setBuddy(self.comboBox_room_responsible_person)
        self.label_3.setBuddy(self.lineEdit_room_number)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.pushButton_delete.setText(_translate("Form", "?????????????? ??????????????????"))
        self.pushButton_add_rooms.setText(_translate("Form", "???????????????? ??????????????????"))
        self.label_22.setText(_translate("Form", "???????????????? ???????????????????????????? ????????????????????"))
        self.label_5.setText(_translate("Form", "????????????????"))
        self.label_9.setText(_translate("Form", "???????????????????? ????????????????"))
        self.label_16.setText(_translate("Form", "????????????????????????"))
        self.plainTextEdit_room_purpose.setPlaceholderText(_translate("Form", "??????????????, ???????????????????? ?????????????? ?????????????????? (?????????????????? ???????????????????????? ??????????????)"))
        self.label_2.setText(_translate("Form", "<html><head/><body><p><span style=\" font-weight:600;\">???????????????? ???????????????????? ?? ??????????????????</span></p></body></html>"))
        self.plainTextEdit_room_equipment.setPlaceholderText(_translate("Form", "????????????????????, ??????????????????????, ????????????????????, ??????????????????????"))
        self.label_6.setText(_translate("Form", "??????????????"))
        self.label_8.setText(_translate("Form", "??????????????????????????"))
        self.label_4.setText(_translate("Form", "????????????????????"))
        self.plainTextEdit_room_name.setPlaceholderText(_translate("Form", "?????????????????????? ???????????????????????? ??????????????????"))
        self.label_10.setText(_translate("Form", "????????????????????"))
        self.plainTextEdit_room_conditions.setPlaceholderText(_translate("Form", "??????????????????????, ?????????????????????????? ??????????????????, ????????????????????????, ?????????????? ????????, ?????????????????????? ????????????????"))
        self.plainTextEdit_room_requirements.setPlaceholderText(_translate("Form", "20 ?? 4 ????; 60 ?? 20 %; 100 ?? 3 ??????"))
        self.label_18.setText(_translate("Form", "???????????????????????????? ????????????????????"))
        self.plainTextEdit_room_personal.setPlaceholderText(_translate("Form", "??????????????????????????, ?????????????????????? ???????????????? (???? ????????????????????)"))
        self.label.setText(_translate("Form", "id"))
        self.lineEdit_room_area.setPlaceholderText(_translate("Form", "24,5"))
        self.label_7.setText(_translate("Form", "?? ????."))
        self.groupBox.setTitle(_translate("Form", "???????????????? ??????????????????"))
        self.radioButton_own.setText(_translate("Form", "??????????????????????"))
        self.radioButton_rent.setText(_translate("Form", "????????????????????"))
        self.plainTextEdit_rent.setPlaceholderText(_translate("Form", "??????????, ???????? ???????????????? ????????????. ????????????????"))
        self.pushButton_save.setText(_translate("Form", "??????????????????"))
        self.label_3.setText(_translate("Form", "?????????? ??????????????????"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())
