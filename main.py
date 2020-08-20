import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QWidget, QAction, QTabWidget,QVBoxLayout, QShortcut
from PyQt5.QtGui import QIcon, QKeySequence, QDropEvent, QDragEnterEvent
from PyQt5.QtCore import pyqtSlot

from widget import TabWidget, ImageViewer

class MultiTool(QMainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.initUI()
        self.show()
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(self.tab_wgt.removeCurrentTab)
        QShortcut(QKeySequence("Alt+F4"), self).activated.connect(self.close)
        QShortcut(QKeySequence("F1"), self).activated.connect(self.addImageViewer)

    def addImageViewer(self):
        wgt = ImageViewer(self)
        if isinstance(wgt, ImageViewer):
            self.tab_wgt.addTab(wgt, wgt.__class__.__name__)
            QShortcut(QKeySequence("A"), wgt).activated.connect(lambda: wgt.changeView(1, 2))
            QShortcut(QKeySequence("S"), wgt).activated.connect(lambda: wgt.changeView(0, 2))
            QShortcut(QKeySequence("C"), wgt).activated.connect(lambda: wgt.changeView(0, 1))

    def initUI(self):
        self.title = "PyQt5 tabs - pythonspot.com"
        self.setWindowTitle(self.title)
        self.resize(500, 500)
        self.tab_wgt = TabWidget(self.centralWidget())
        self.setCentralWidget(self.tab_wgt)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MultiTool()
    sys.exit(app.exec_())