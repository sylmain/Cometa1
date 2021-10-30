from PyQt5.QtWidgets import QWidget, QApplication

from equipment_pkg.ui_equipment_add_vri import Ui_Form


class EquipmentImportFileWidget(QWidget):
    def __init__(self, parent):
        super(EquipmentImportFileWidget, self).__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = EquipmentImportFileWidget("hey")

    window.show()
    sys.exit(app.exec_())
