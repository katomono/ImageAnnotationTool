import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, QPointF, pyqtSignal
from PyQt5.QtWidgets import QGraphicsLineItem, QWidget, QHBoxLayout, QGridLayout
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QWheelEvent
import numpy as np
import copy
from typing import Union, Iterable, Optional, Tuple, List
from graphicitem import GraphicsResizableRectItem, GraphicsCrossBarItem
from pathlib import Path
import enum
import numpy as np
from pathlib import Path

from numpy.lib.npyio import load
from typing import Tuple

from data import BitMask, Image
from style import BitMaskLayer, ImageLayer



class BaseImageViewer(QWidget):
    signalWheel = pyqtSignal(float)
    signalMousePress = pyqtSignal(int, QPointF)
    signalMouseRelease = pyqtSignal(int, QPointF)
    signalMouseMove = pyqtSignal(int, QPointF)
    signalDropFile = pyqtSignal(str)

    def __init__(self, parent=None):
        super(BaseImageViewer, self).__init__(parent)
        self.graphicsview = QtWidgets.QGraphicsView(self)
        self.graphicsview.setAcceptDrops(False)
        self.graphicsview.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsview.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsview.setGeometry(0, 0, 512, 512)

        self.scene = QtWidgets.QGraphicsScene(self)
        self.graphicsview.setScene(self.scene)
        self.image_item = QtWidgets.QGraphicsPixmapItem()
        self.overlay_item = QtWidgets.QGraphicsPixmapItem()
        self.focus_item = GraphicsCrossBarItem(QtCore.QPointF(256, 256), 5)

        self.rect_items = []

        self.pen = QtGui.QPen(QtCore.Qt.SolidLine)
        self.pen.setColor(QtCore.Qt.red)
        self.pen.setWidth(5)
        self.scene.addItem(self.image_item)
        self.scene.addItem(self.overlay_item)
        self.scene.addItem(self.focus_item)

        self.setAcceptDrops(True)


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
    
    def move(self, delta: QPointF):
        trans = self.graphicsview.transform()

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        mime = event.mimeData()
        if mime.hasUrls():
            event.accept()
        super(BaseImageViewer, self).dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        mime = event.mimeData()
        if mime.hasUrls():
            for url in mime.urls():
                self.signalDropFile.emit(url.toLocalFile())
        super(BaseImageViewer, self).dropEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        self.signalWheel.emit(event.angleDelta().y() / 120)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        self.signalMouseMove.emit(event.button(), event.pos())

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        self.signalMouseMove.emit(event.button(), event.pos())

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        self.signalMouseRelease.emit(event.button, event.pos())


@enum.unique
class Mode(enum.Enum):
    DEFAULT = enum.auto()   # 特に何もない状態
    MOVE = enum.auto()      # 画像全体を平行移動中
    WINDOW = enum.auto()    # 画像の輝度値の平行移動中
    FOCUS = enum.auto()
    TARGET = enum.auto()    # 画像上のクロスバーを移動中

@enum.unique
class ViewLayout(enum.Enum):
    SINGLE = enum.auto()
    MULTI = enum.auto()

class ImageViewer(QWidget):
    def __init__(self, parent):
        super(ImageViewer, self).__init__(parent)
        self.hboxLayout = QHBoxLayout()
        self.gridLayout = QGridLayout()
        self.setLayout(self.hboxLayout)
        self.hboxLayout.addLayout(self.gridLayout)

        self.viewers = [BaseImageViewer(self), BaseImageViewer(self), BaseImageViewer(self)]
        self.gridLayout.addWidget(self.viewers[0], 0, 0, 1, 1)
        self.gridLayout.addWidget(self.viewers[1], 1, 0, 1, 1)
        self.gridLayout.addWidget(self.viewers[2], 0, 1, 1, 1)
        for view in self.viewers:
            view.signalDropFile.connect(self.load)

        self.setAcceptDrops(True)

        self.mode = Mode.DEFAULT
        self.layout = ViewLayout.MULTI
        self.image_layer = None
        self.overlay_layer = None

    def changeMode(self, mode: Mode):
        self.mode = mode

    def changeLayout(self, layout: ViewLayout):
        self.layout = layout


    def changeView(self, axis0: int, axis1: int):
        if self.mode == Mode.DEFAULT:
            self.viewers[0].show()
            for view in self.viewers[1:]:
                view.hide()

            if self.image_layer is not None:
                self.image_layer.axis0 = axis0
                self.image_layer.axis1 = axis1
            if self.overlay_layer is not None:
                self.overlay_layer.axis0 = axis0
                self.overlay_layer.axis1 = axis1
        self.draw()
            
    def draw(self):
        if self.image_layer is not None:
            for view in self.viewers:
                pixmap = self.image_layer.toPixmap()
                view.setImageItem(pixmap)
        
        if self.overlay_layer is not None:
            for view in self.viewrs:
                pixmap = self.overlay_layer.toPixmap()
                view.setOverlayItem(pixmap)
        self.update()

    def load(self, filepath: str)->bool:
        filepath = Path(filepath)
        if filepath.suffix == ".raw":
            data = Image.load(filepath)
            self.image_layer = ImageLayer(data)

        if filepath.suffix == ".msk":
            data = BitMask.load(filepath)
            self.overlay_layer = BitMaskLayer(data)

        self.draw()


