#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QGraphicsLineItem
import numpy as np
import copy
from typing import Union, Iterable, Optional, Tuple, List
from items import GraphicsResizableRectItem, GraphicsCrossBarItem
from pathlib import Path
import enum
import numpy as np
from pathlib import Path

from numpy.lib.npyio import load
from typing import Tuple

class BaseImageViewer(QtWidgets.QWidget):
    def __init__(self, parent):
        super(self.__class__, self).__init__(parent)
        self.graphicsview = QtWidgets.QGraphicsView(self)
        self.graphicsview.setAcceptDrops(False)
        self.graphicsview.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsview.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsview.setGeometry(0, 0, 512, 512)

        self.scene = QtWidgets.QGraphicsScene(self)
        self.graphicsview.setScene(self.scene)
        self.image_item = QtWidgets.QGraphicsPixmapItem(self.scene)
        self.overlay_item = QtWidgets.QGraphicsPixmapItem(self.scene)
        self.focus_item = GraphicsCrossBarItem(QtCore.QPointF(256, 256), 5, self.scene)

        self.rect_items = []

        self.pen = QtGui.QPen(QtCore.Qt.SolidLine)
        self.pen.setColor(QtCore.Qt.red)
        self.pen.setWidth(5)
        self.scene.addItem(self.image_item)
        self.scene.addItem(self.overlay_item)
        self.scene.addItem(self.focus_item)


    def setBoxItem(self, rect: Union[QtCore.QRect, Iterable[QtCore.QRect]], color: QtGui.QColor):
        if isinstance(rect, QtCore.QRectF):
            rect = GraphicsResizableRectItem(rect)
            self.scene.addItem(rect)
            self.rect_items.append(rect)
    
    def setImageItem(self, pixmap: QtGui.QPixmap):
        self.image_item.setPixmap(pixmap)

    def setOverlayItem(self, pixmap: QtGui.QPixmap):
        self.overlay_item.setPixmap(pixmap)
    
    def setFocusPoint(self, point: QtCore.QPointF):
        self.focus_item.setPoint(point)

    def zoom(self, ratio: float):
        trans = self.graphicsview.transform()
        zoom = QtGui.QTransform()
        zoom.scale(ratio, ratio)
        trans = trans * zoom
        self.graphicsview.setTransform(trans)
    
    def move(self, delta):
        trans = self.graphicsview.transform()


@enum.unique
class MouseState(enum.Enum):
    DEFAULT = enum.auto()   # 特に何もない状態
    MOVE = enum.auto()      # 画像全体を平行移動中
    WINDOW = enum.auto()    # 画像の輝度値の平行移動中
    SLICE = enum.auto()
    TARGET = enum.auto()    # 画像上のクロスバーを移動中

class ImageViewer(BaseImageViewer):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)

        # operations = [
        #     ("ChangeAxis", "X", self.changeViewAxis),
        # ]

        # self.shortcuts = []
        # for text, shortcut_key, callback in operations:
        #     shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(shortcut_key), self)
        #     shortcut.activated.connect(callback)
        #     self.shortcuts.append(shortcut)
        self.state = MouseState.DEFAULT
        self.image_data = None
        self.overlay_data = None
        self.scale = 1.0
        self.axis = 0
        self.focus = [0, 0, 0]
        self.wlevel = 200
        self.wwidth = 600
        self.update()
    

    @QtCore.pyqtSlot
    def changeViewAxis(self):
        self.axis = (self.axis + 1) % 3
        self.update()

    def loadFile(self, filepath: Path)->bool:
        sfx = filepath.suffix
        if sfx == ".raw":
            self.image_data = Image.load(filepath)
            self.image_style = ImageStyle()
            return True
        elif sfx == ".msk":
            self.mask_data = BitMask.load(filepath)
            # self.mask_style = BitMaskStyle()
            return True
        return False

    def update(self):
        axis0, axis1 = tuple(i for i in range(3) if i != self.axis)
        spacing = self.image_data.spacing
        shape = self.image_data.data.shape
        sp_h = spacing[axis0]
        sp_w = spacing[axis1]
        img_h = shape[axis0]
        img_w = shape[axis1]
        wgt_h = self.height()
        wgt_w = self.width()
        scale_w = wgt_w / img_w
        scale_h = wgt_h / img_h
        if scale_w > scale_h:
            scale_w = scale_h * sp_w / sp_h
        else:
            scale_h = scale_w * sp_h / sp_w
        self.scale = scale_w

        self.SetImage()
        self.SetOverlay()
        self.SetBox()
        super(self.__class__, self).update()                

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        if self.image_data is None:
            return
        d = event.angleDelta().y() / 120
        if event.modifiers() & QtCore.Qt.ShiftModifier:
            ratio = 1.1**d
            inv = self.trans.inverted()[0]
            pos = inv.map(event.pos())
            self.updateTransform(pos.x(), pos.y(), ratio)
            self.scale *= ratio
        else:
            if event.buttons() & QtCore.Qt.RightButton:
                d *= 5
            axis = self.axis
            newZ = self.target[axis] + int(d)
            newZ = np.clip(newZ, 0, self.image_data.data.shape[axis] - 1)
            self.target[axis] = newZ
        
        self.update()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        btn = event.button()
        mdfr = event.modifiers()
        if QtCore.Qt.ControlModifier:
            pass


        if btn == QtCore.Qt.RightButton:
            self.state = MouseState.WINDOW
            self.start_ww = self.wwidth
            self.start_wl = self.wlevel
            self.start_pos = event.pos()
        
        elif btn == QtCore.Qt.LeftButton:
            pos = event.pos()
            if mdfr & QtCore.Qt.ShiftModifier:
                self.state = MouseState.MOVE
                self.end_pos = pos
                QtGui.QGuiApplication.setOverrideCursor(QtCore.Qt.OpenHandCursor)
            else:
                ind = np.delete(np.arange(3, dtype=np.int), self.axis)
                y, x = np.take(self.target, ind)
                x, y = self.trans.map(x + 0.5, y + 0.5)
                if -10 < pos.x() - x < 10 and -10 < pos.y() - y < 10:
                    self.state = MouseState.TARGET
                    QtGui.QGuiApplication.setOverrideCursor(QtCore.Qt.CrossCursor)
        elif btn == QtCore.Qt.MiddleButton:
            self.start_pos = event.pos()
            self.state = MouseState.SLICE
            self._start_target = self.target[self.axis]


    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self.state == MouseState.WINDOW:
            self.end_pos = event.pos()
            move = self.end_pos - self.start_pos
            self.wwidth = self.start_ww + move.x()
            self.wlevel = self.start_wl + move.y()
        
        elif self.state == MouseState.MOVE:
            inv = self.trans.inverted()[0]
            d = inv.map(event.pos()) - inv.map(self.end_pos)
            self.updateTransform(d.x(), d.y())
            self.end_pos = event.pos()
        elif self.state == MouseState.TARGET:
            inv = self.trans.inverted()[0]
            pos = inv.map(event.pos())
            yi, xi = np.arange(3)[np.arange(3) != self.axis]
            self.target[xi] = np.clip(pos.x(), 0, self.image_data.data.shape[xi] - 1)
            self.target[yi] = np.clip(pos.y(), 0, self.image_data.data.shape[yi] - 1)
        elif self.state == MouseState.SLICE:
            self.end_pos = event.pos()
            move = self.end_pos - self.start_pos
            axis = self.axis
            newZ = self.target[axis] + int(move.y() / 20)
            newZ = min(max(newZ, 0), self.image_data.data.shape[axis] - 1)
            self.target[axis] = newZ

        self.update()
    
    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        self.state = MouseState.DEFAULT
        QtGui.QGuiApplication.restoreOverrideCursor()



DefaultStyle = """\
border-style : solid; 
border-width : 1px;
border-color : rgba(255,255,255,0); 
background-color : rgba(0,192,0,128);
"""
SelectedStyle = """\
border-style : solid; 
border-width : 1px;
border-color : rgba(192,0,0,128); 
background-color : rgba(0,192,0,128);
"""


class PlaneLabel(QtWidgets.QLabel):
    def __init__(self, parent):
        super(self.__class__, self).__init__(parent)

        self.setStyleSheet(DefaultStyle)
        # wgt = RawImageWidget(self.centralWidget)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

class MyViewer(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
        self.setupUi()
        self.setAcceptDrops(True)

        operations = [
            ("Vertical Split", "V", self.addCol),
            ("Horizontal Split", "H", self.addRow),
        ]

        self.shortcuts = []
        for text, shortcut_key, callback in operations:
            shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(shortcut_key), self)
            shortcut.activated.connect(callback)
            self.shortcuts.append(shortcut)
        

    def setupUi(self):
        self.resize(512, 512)
        self.setCentralWidget(QtWidgets.QWidget(self))
        self.hboxLayout = QtWidgets.QHBoxLayout(self.centralWidget())
        self.gridLayout = QtWidgets.QGridLayout(self.centralWidget())
        self.hboxLayout.addLayout(self.gridLayout)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setHorizontalSpacing(1)
        self.gridLayout.setVerticalSpacing(1)
        
        self.viewers = [[]]
        self.addCol()
        self.update()
    
    @property
    def n_row(self):
        return len(self.viewers)

    @property
    def n_col(self):
        return len(self.viewers[0])

    @QtCore.pyqtSlot()
    def addRow(self):
        print("addCol")
        ri = self.n_row
        n_col = self.n_col

        self.viewers.append([])
        for ci in range(n_col):
            wgt = PlaneLabel(self.centralWidget())
            self.gridLayout.addWidget(wgt, ci, ri, 1, 1)
            self.viewers[ri].append(wgt)

    @QtCore.pyqtSlot()
    def addCol(self):
        print("addRow")
        ci = self.n_col
        n_row = self.n_row

        for ri in range(self.n_row):
            wgt = PlaneLabel(self.centralWidget())
            self.gridLayout.addWidget(wgt, ci, ri, 1, 1)
            self.viewers[ri].append(wgt)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
        
    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        pos = event.pos()
        tgt_ri = 0
        tgt_ci = 0
        for ri in range(self.n_row):
            for ci in range(self.n_col):
                rect = self.gridLayout.cellRect(ci, ri)
                if rect.contains(pos):
                    tgt_ri = ri
                    tgt_ci = ci
                
        url = event.mimeData().urls()
        filepath = Path(url[0].toLocalFile())
        sfx = filepath.suffix
        if sfx == ".raw":
            data = Image.load(filepath).data
            slice_img = data[data.shape[0] // 2]
            slice_img = (slice_img - 200) * (256 / 600) + 128
            slice_img = np.clip(slice_img, 0, 255)
            slice_img = slice_img.astype(np.uint8)
            img = np.zeros([slice_img.shape[0], slice_img.shape[1], 4], dtype=np.uint8)
            img[:,:,0:3] = np.dstack([slice_img] * 3)
            img[:,:,3] = 255
            qimg = QtGui.QImage(img, img.shape[1], img.shape[0], QtGui.QImage.Format_ARGB32)
            pimg = QtGui.QPixmap(qimg)

            wgt = BaseImageViewer(self.centralWidget())
            self.gridLayout.replaceWidget(
                self.viewers[tgt_ri][tgt_ci], 
                wgt
                )
            self.viewers[tgt_ri][tgt_ci] = wgt
            wgt.SetImage(pimg)

        elif sfx == ".msk":
            pass
            # overlay_data = BitMask.load(filepath)
            # self.viewer[0].SetOverlay()
        print("drop")
