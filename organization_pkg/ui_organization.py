# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'organization.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(516, 703)
        self.label = QtWidgets.QLabel(Form)
        self.label.setGeometry(QtCore.QRect(30, 10, 311, 31))
        font = QtGui.QFont()
        font.setPointSize(17)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.textEdit_full_name = QtWidgets.QTextEdit(Form)
        self.textEdit_full_name.setGeometry(QtCore.QRect(30, 70, 461, 51))
        self.textEdit_full_name.setAcceptRichText(False)
        self.textEdit_full_name.setObjectName("textEdit_full_name")
        self.label_2 = QtWidgets.QLabel(Form)
        self.label_2.setGeometry(QtCore.QRect(30, 50, 120, 20))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(Form)
        self.label_3.setGeometry(QtCore.QRect(30, 120, 150, 20))
        self.label_3.setObjectName("label_3")
        self.lineEdit_short_name = QtWidgets.QLineEdit(Form)
        self.lineEdit_short_name.setGeometry(QtCore.QRect(30, 140, 461, 20))
        self.lineEdit_short_name.setObjectName("lineEdit_short_name")
        self.label_4 = QtWidgets.QLabel(Form)
        self.label_4.setGeometry(QtCore.QRect(30, 160, 150, 20))
        self.label_4.setObjectName("label_4")
        self.textEdit_adress = QtWidgets.QTextEdit(Form)
        self.textEdit_adress.setGeometry(QtCore.QRect(30, 180, 461, 51))
        self.textEdit_adress.setAcceptRichText(False)
        self.textEdit_adress.setObjectName("textEdit_adress")
        self.lineEdit_inn = QtWidgets.QLineEdit(Form)
        self.lineEdit_inn.setGeometry(QtCore.QRect(30, 250, 461, 20))
        self.lineEdit_inn.setObjectName("lineEdit_inn")
        self.label_5 = QtWidgets.QLabel(Form)
        self.label_5.setGeometry(QtCore.QRect(30, 230, 31, 20))
        self.label_5.setObjectName("label_5")
        self.lineEdit_email = QtWidgets.QLineEdit(Form)
        self.lineEdit_email.setGeometry(QtCore.QRect(30, 290, 461, 20))
        self.lineEdit_email.setObjectName("lineEdit_email")
        self.label_6 = QtWidgets.QLabel(Form)
        self.label_6.setGeometry(QtCore.QRect(30, 270, 140, 20))
        self.label_6.setObjectName("label_6")
        self.lineEdit_site = QtWidgets.QLineEdit(Form)
        self.lineEdit_site.setGeometry(QtCore.QRect(30, 330, 461, 20))
        self.lineEdit_site.setObjectName("lineEdit_site")
        self.label_7 = QtWidgets.QLabel(Form)
        self.label_7.setGeometry(QtCore.QRect(30, 310, 31, 20))
        self.label_7.setObjectName("label_7")
        self.lineEdit_boss = QtWidgets.QLineEdit(Form)
        self.lineEdit_boss.setGeometry(QtCore.QRect(30, 390, 461, 20))
        self.lineEdit_boss.setObjectName("lineEdit_boss")
        self.label_8 = QtWidgets.QLabel(Form)
        self.label_8.setGeometry(QtCore.QRect(30, 370, 111, 20))
        self.label_8.setObjectName("label_8")
        self.lineEdit_boss_title = QtWidgets.QLineEdit(Form)
        self.lineEdit_boss_title.setGeometry(QtCore.QRect(30, 430, 461, 20))
        self.lineEdit_boss_title.setObjectName("lineEdit_boss_title")
        self.label_9 = QtWidgets.QLabel(Form)
        self.label_9.setGeometry(QtCore.QRect(30, 410, 141, 20))
        self.label_9.setObjectName("label_9")
        self.lineEdit_metrolog = QtWidgets.QLineEdit(Form)
        self.lineEdit_metrolog.setGeometry(QtCore.QRect(30, 470, 461, 20))
        self.lineEdit_metrolog.setObjectName("lineEdit_metrolog")
        self.label_10 = QtWidgets.QLabel(Form)
        self.label_10.setGeometry(QtCore.QRect(30, 450, 200, 20))
        self.label_10.setObjectName("label_10")
        self.lineEdit_metrolog_title = QtWidgets.QLineEdit(Form)
        self.lineEdit_metrolog_title.setGeometry(QtCore.QRect(30, 510, 461, 20))
        self.lineEdit_metrolog_title.setObjectName("lineEdit_metrolog_title")
        self.label_11 = QtWidgets.QLabel(Form)
        self.label_11.setGeometry(QtCore.QRect(30, 490, 231, 20))
        self.label_11.setObjectName("label_11")
        self.lineEdit_code_mark = QtWidgets.QLineEdit(Form)
        self.lineEdit_code_mark.setGeometry(QtCore.QRect(30, 570, 461, 20))
        self.lineEdit_code_mark.setObjectName("lineEdit_code_mark")
        self.label_12 = QtWidgets.QLabel(Form)
        self.label_12.setGeometry(QtCore.QRect(30, 550, 231, 20))
        self.label_12.setObjectName("label_12")
        self.lineEdit_accred_number = QtWidgets.QLineEdit(Form)
        self.lineEdit_accred_number.setGeometry(QtCore.QRect(30, 610, 461, 20))
        self.lineEdit_accred_number.setObjectName("lineEdit_accred_number")
        self.label_13 = QtWidgets.QLabel(Form)
        self.label_13.setGeometry(QtCore.QRect(30, 590, 280, 20))
        self.label_13.setObjectName("label_13")
        self.pushButton_save = QtWidgets.QPushButton(Form)
        self.pushButton_save.setGeometry(QtCore.QRect(380, 650, 111, 31))
        self.pushButton_save.setObjectName("pushButton_save")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label.setText(_translate("Form", "Информация о предприятии"))
        self.label_2.setText(_translate("Form", "Полное наименование"))
        self.label_3.setText(_translate("Form", "Сокращенное наименование"))
        self.label_4.setText(_translate("Form", "Юридический адрес"))
        self.label_5.setText(_translate("Form", "ИНН"))
        self.label_6.setText(_translate("Form", "Адрес электронной почты"))
        self.label_7.setText(_translate("Form", "Сайт"))
        self.lineEdit_boss.setPlaceholderText(_translate("Form", "Иванов Петр Тимофеевич"))
        self.label_8.setText(_translate("Form", "ФИО руководителя"))
        self.label_9.setText(_translate("Form", "Должность руководителя"))
        self.lineEdit_metrolog.setPlaceholderText(_translate("Form", "Пронин Сергей Яковлевич"))
        self.label_10.setText(_translate("Form", "ФИО ответственного за метрологию"))
        self.label_11.setText(_translate("Form", "Должность ответственного за метрологию"))
        self.label_12.setText(_translate("Form", "Шифр знака поверки"))
        self.label_13.setText(_translate("Form", "Уникальный номер в реестре аккредитованных лиц"))
        self.pushButton_save.setText(_translate("Form", "Сохранить"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())
