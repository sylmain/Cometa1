from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QAction, QMdiSubWindow, QTextEdit
import sys
from workers_pkg.workers import WorkersWidget


class MDIWindow(QMainWindow):
    count = 0

    def __init__(self):
        super().__init__()

        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)

        bar = self.menuBar()

        file = bar.addMenu("File")
        file.addAction("New")
        file.addAction("Cascade")
        file.addAction("Tiled")

        file.triggered[QAction].connect(self.WindowTrig)

        self.setWindowTitle("MDI Application")

    def WindowTrig(self, p):
        if p.text() == "New":
            MDIWindow.count += 1
            sub = QMdiSubWindow()
            sub.setWidget(WorkersWidget())
            sub.setWindowTitle("Sub Window " + str(MDIWindow.count))
            self.mdi.addSubWindow(sub)
            sub.show()

        if p.text() == "Cascade":
            self.mdi.cascadeSubWindows()

        if p.text() == "Tiled":
            self.mdi.tileSubWindows()


app = QApplication(sys.argv)
mdiwindow = MDIWindow()
mdiwindow.show()

app.exec()
