from PyQt5.QtWidgets import QTabWidget, QPushButton, QWidget, QInputDialog, QLineEdit
from PyQt5.QtGui import QIcon
from typing import List, Callable

class TabWidget(QTabWidget):
    def __init__(self, parent=None):
        super(TabWidget, self).__init__(parent=parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self.removeTab)
        self.__tabHideOrShow()


    def __tabHideOrShow(self):
        if self.count() <= 1:
            self.tabBar().hide()
        else:
            self.tabBar().show()

    def replaceCurrentWidget(self, wgt, name):
        index = self.currentIndex()
        self.removeTab(index)
        self.insertTab(index, wgt, name)

    def tabInserted(self, index: int) -> None:
        self.__tabHideOrShow()
        self.setCurrentIndex(index)


    def tabRemoved(self, index):
        self.__tabHideOrShow()

    # 外部命令用
    def removeCurrentTab(self):
        self.removeTab(self.currentIndex())