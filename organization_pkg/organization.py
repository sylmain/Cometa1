from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QApplication

from functions_pkg.db_functions import MySQLConnection
from organization_pkg.ui_organization import Ui_Form


class OrganizationWidget(QWidget):
    def __init__(self, parent=None):
        super(OrganizationWidget, self).__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.setWindowTitle("Информация о предприятии")
        self.setWindowIcon(QIcon("mainwindow_icon.png"))

        self.is_org_exist()
        self.ui.pushButton_save.clicked.connect(self.save_data)

    def is_org_exist(self):
        MySQLConnection.verify_connection()
        connection = MySQLConnection.get_connection()
        sql_is_exist = "SELECT COUNT(*) FROM organization_info"
        result = MySQLConnection.execute_read_query(connection, sql_is_exist)
        if result[0][0] != 0:
            self.read_data()

    def read_data(self):
        MySQLConnection.verify_connection()
        connection = MySQLConnection.get_connection()
        sql_is_exist = "SELECT * FROM organization_info WHERE org_id = 1"
        result = MySQLConnection.execute_read_query(connection, sql_is_exist)
        connection.close()
        self.ui.textEdit_full_name.setPlainText(result[0][1])
        self.ui.lineEdit_short_name.setText(result[0][2])
        self.ui.textEdit_adress.setPlainText(result[0][3])
        self.ui.lineEdit_inn.setText(result[0][4])
        self.ui.lineEdit_boss.setText(result[0][5])
        self.ui.lineEdit_boss_title.setText(result[0][6])
        self.ui.lineEdit_metrolog.setText(result[0][7])
        self.ui.lineEdit_metrolog_title.setText(result[0][8])
        self.ui.lineEdit_code_mark.setText(result[0][9])
        self.ui.lineEdit_accred_number.setText(result[0][10])
        self.ui.lineEdit_email.setText(result[0][11])
        self.ui.lineEdit_site.setText(result[0][12])

    def save_data(self):
        MySQLConnection.verify_connection()
        connection = MySQLConnection.get_connection()
        sql_replace = f"""REPLACE INTO organization_info VALUES
                        (1, 
                        '{self.ui.textEdit_full_name.toPlainText()}',
                        '{self.ui.lineEdit_short_name.text()}',
                        '{self.ui.textEdit_adress.toPlainText()}',
                        '{self.ui.lineEdit_inn.text()}',
                        '{self.ui.lineEdit_boss.text()}',
                        '{self.ui.lineEdit_boss_title.text()}',
                        '{self.ui.lineEdit_metrolog.text()}',
                        '{self.ui.lineEdit_metrolog_title.text()}',
                        '{self.ui.lineEdit_code_mark.text()}',
                        '{self.ui.lineEdit_accred_number.text()}',
                        '{self.ui.lineEdit_email.text()}',
                        '{self.ui.lineEdit_site.text()}'
                        );
                    """
        MySQLConnection.execute_query(connection, sql_replace)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = OrganizationWidget()
    window.resize(520, 700)
    window.show()
    sys.exit(app.exec())
