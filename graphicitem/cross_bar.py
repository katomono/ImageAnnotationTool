
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QBrush, QPainterPath, QPainter, QColor, QPen, QPixmap, QTransform, QRegion
from PyQt5.QtWidgets import QGraphicsEllipseItem, QWidget, QGraphicsRectItem, QApplication, QGraphicsView, QGraphicsScene, QGraphicsItem
from typing import Optional, Tuple, Union


class GraphicsCrossBarItem(QGraphicsEllipseItem):
    def __init__(self, center: QPointF, radius: float, parent=None):
        rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
        super(self.__class__, self).__init__(rect, parent)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.hpen = QPen(QColor(255, 255, 0), 2, Qt.SolidLine)
        self.vpen = QPen(QColor(0, 0, 255), 2, Qt.SolidLine)

    def SetHorizontalPen(self, pen: QPen) -> None:
        self.hpen = pen

    def SetVerticalPen(self, pen: QPen) -> None:
        self.vpen = pen
    
    def boundingRect(self) -> QRectF:
        rect = self.rect()
        c = rect.center()
        r = 20
        return QRectF(c.x() - r, c.y() - r, 2*r, 2*r)

    def mousePressEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        self.mousePressPos = event.pos()
        self.mousePressRect = self.rect()
        self.mousePressSelected = self.contains(self.mousePressPos)
        if not self.mousePressSelected:
            super(self.__class__, self).mouseMoveEvent(event)

    def mouseMoveEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        if self.mousePressSelected:
            x, y, w, h = self.mousePressRect.getRect()
            mouseMovePos = event.pos()
            move = mouseMovePos - self.mousePressPos
            self.setRect(x + move.x(), y + move.y(), w, h)
            self.resetTransform()
        else:
            super(self.__class__, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        self.mousePressPos = None
        self.mosuePressRect = None
        self.mousePressSelected = None

    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget]) -> None:
        rect = self.rect()
        c = rect.center()
        r = rect.width() / 2
        x = c.x()
        y = c.y()
        # painter.resetTransform()
        rect = QRectF(x - r, y - r, r * 2, r * 2)
        h = widget.height()
        w = widget.width()
        painter.setPen(self.hpen)
        s = self.mapToScene(0, 0)
        e = self.mapToScene(h, w)
        sx = s.x()
        sy = s.y()
        ex = e.x()
        ey = e.y()
        painter.drawLine(sx, y, x - r, y)
        painter.drawLine(x + r, y, ex, y)
        painter.setPen(self.vpen)
        painter.drawLine(x, sy, x, y - r)
        painter.drawLine(x, y + r, x, ey)