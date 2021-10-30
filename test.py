import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from first_try import Ui_MainWindow
from second_try import Ui_Form


class Widget(QtWidgets.QWidget, Ui_Form):
    def __init__(self, text, parent):
        super(Widget, self).__init__()
        self.setupUi(self)

        self.parent = parent
        self.label.setText(f'{self.label.text()} <b style="color: red;">{text}</b>')

        self.pushButton.setText('Назад')
        self.pushButton.setStyleSheet("background-color: rgb(0, 255, 127);")
        self.pushButton.clicked.connect(self.on_button_second)

    def on_button_second(self):
        self.parent.show()
        self.hide()


class Start_Window(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(Start_Window, self).__init__()
        self.setupUi(self)
        self.setWindowTitle('Лабораторная работа №1')

        self.lineEditGrup.setStyleSheet("font: 10pt \"HouschkaRoundedAlt 9\";")
        self.lineEditGrup.setMaxLength(9)
        self.lineEditFio.setStyleSheet("font: 10pt \"HouschkaRoundedAlt 9\";")
        self.comboBox.setStyleSheet("background-color: rgb(170, 170, 255);")
        self.pushButton.setStyleSheet("background-color: rgb(0, 255, 127);")
        self.pushButton.setToolTip('<b>Продолжить<b>')
        self.pushButton.clicked.connect(self.hide_widget)

    def hide_widget(self):
        self.widget = Widget(self.comboBox.currentText(), self)
        self.widget.show()
        self.hide()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    application = Start_Window()
    application.show()
    sys.exit(app.exec_())