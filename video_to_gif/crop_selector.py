"""
可视化裁切选择器组件
"""
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QCursor


class CropSelector(QWidget):
    """可视化裁切选择器"""
    
    # 信号
    crop_changed = pyqtSignal(QRect)  # 裁切区域变化信号
    
    # 手柄大小
    HANDLE_SIZE = 8
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 裁切框（相对于视频显示区域）
        self.crop_rect = QRect()
        
        # 视频原始尺寸
        self.video_size = (0, 0)
        
        # 视频显示区域（缩放后的尺寸）
        self.display_rect = QRect()
        
        # 当前操作状态
        self.is_dragging = False
        self.is_resizing = False
        self.drag_start_pos = QPoint()
        self.crop_start_rect = QRect()
        self.active_handle = -1  # -1表示没有激活的手柄，0-7表示8个手柄
        
        # 鼠标位置
        self.mouse_pos = QPoint()
        
        # 设置鼠标追踪
        self.setMouseTracking(True)
        
        # 设置透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
    
    def set_video_size(self, width: int, height: int):
        """设置视频原始尺寸"""
        self.video_size = (width, height)
        # 默认裁切区域为整个视频
        self.crop_rect = QRect(0, 0, width, height)
        self.update()
        self.crop_changed.emit(self.crop_rect)
    
    def set_display_rect(self, rect: QRect):
        """设置视频显示区域"""
        self.display_rect = rect
        self.setGeometry(rect)
        self.update()
    
    def get_crop_rect(self) -> QRect:
        """获取当前裁切区域（视频原始坐标）"""
        return QRect(self.crop_rect)
    
    def set_crop_rect(self, rect: QRect):
        """设置裁切区域"""
        # 限制在视频范围内
        x = max(0, min(rect.x(), self.video_size[0] - 10))
        y = max(0, min(rect.y(), self.video_size[1] - 10))
        w = max(10, min(rect.width(), self.video_size[0] - x))
        h = max(10, min(rect.height(), self.video_size[1] - y))
        
        self.crop_rect = QRect(x, y, w, h)
        self.update()
        self.crop_changed.emit(self.crop_rect)
    
    def reset_crop(self):
        """重置裁切区域为整个视频"""
        if self.video_size[0] > 0 and self.video_size[1] > 0:
            self.crop_rect = QRect(0, 0, self.video_size[0], self.video_size[1])
            self.update()
            self.crop_changed.emit(self.crop_rect)
    
    def _video_to_display(self, video_x: int, video_y: int) -> QPoint:
        """将视频坐标转换为显示坐标"""
        if self.video_size[0] == 0 or self.video_size[1] == 0:
            return QPoint(0, 0)
        
        scale_x = self.display_rect.width() / self.video_size[0]
        scale_y = self.display_rect.height() / self.video_size[1]
        
        display_x = int(video_x * scale_x)
        display_y = int(video_y * scale_y)
        
        return QPoint(display_x, display_y)
    
    def _display_to_video(self, display_x: int, display_y: int) -> QPoint:
        """将显示坐标转换为视频坐标"""
        if self.display_rect.width() == 0 or self.display_rect.height() == 0:
            return QPoint(0, 0)
        
        scale_x = self.video_size[0] / self.display_rect.width()
        scale_y = self.video_size[1] / self.display_rect.height()
        
        video_x = int(display_x * scale_x)
        video_y = int(display_y * scale_y)
        
        return QPoint(video_x, video_y)
    
    def _get_handle_rects(self) -> list:
        """获取8个手柄的矩形区域（显示坐标）"""
        if self.crop_rect.isEmpty():
            return []
        
        # 将裁切框转换为显示坐标
        top_left = self._video_to_display(self.crop_rect.left(), self.crop_rect.top())
        bottom_right = self._video_to_display(self.crop_rect.right(), self.crop_rect.bottom())
        
        x1, y1 = top_left.x(), top_left.y()
        x2, y2 = bottom_right.x(), bottom_right.y()
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        
        hs = self.HANDLE_SIZE
        hs2 = hs // 2
        
        # 8个手柄：左上、上中、右上、左中、右中、左下、下中、右下
        return [
            QRect(x1 - hs2, y1 - hs2, hs, hs),  # 0: 左上
            QRect(cx - hs2, y1 - hs2, hs, hs),  # 1: 上中
            QRect(x2 - hs2, y1 - hs2, hs, hs),  # 2: 右上
            QRect(x1 - hs2, cy - hs2, hs, hs),  # 3: 左中
            QRect(x2 - hs2, cy - hs2, hs, hs),  # 4: 右中
            QRect(x1 - hs2, y2 - hs2, hs, hs),  # 5: 左下
            QRect(cx - hs2, y2 - hs2, hs, hs),  # 6: 下中
            QRect(x2 - hs2, y2 - hs2, hs, hs),  # 7: 右下
        ]
    
    def _get_handle_at_pos(self, pos: QPoint) -> int:
        """获取指定位置的手柄索引，-1表示没有"""
        handle_rects = self._get_handle_rects()
        for i, rect in enumerate(handle_rects):
            if rect.contains(pos):
                return i
        return -1
    
    def _update_cursor(self, pos: QPoint):
        """根据鼠标位置更新光标样式"""
        handle = self._get_handle_at_pos(pos)
        
        if handle in [0, 7]:  # 左上、右下
            self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
        elif handle in [2, 5]:  # 右上、左下
            self.setCursor(QCursor(Qt.CursorShape.SizeBDiagCursor))
        elif handle in [1, 6]:  # 上中、下中
            self.setCursor(QCursor(Qt.CursorShape.SizeVerCursor))
        elif handle in [3, 4]:  # 左中、右中
            self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
        elif self.crop_rect.isEmpty():
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        else:
            # 检查是否在裁切框内
            top_left = self._video_to_display(self.crop_rect.left(), self.crop_rect.top())
            bottom_right = self._video_to_display(self.crop_rect.right(), self.crop_rect.bottom())
            display_rect = QRect(top_left, bottom_right)
            
            if display_rect.contains(pos):
                self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
            else:
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            
            # 检查是否点击了手柄
            handle = self._get_handle_at_pos(pos)
            if handle >= 0:
                self.is_resizing = True
                self.active_handle = handle
                self.drag_start_pos = pos
                self.crop_start_rect = QRect(self.crop_rect)
                return
            
            # 检查是否点击了裁切框内部
            top_left = self._video_to_display(self.crop_rect.left(), self.crop_rect.top())
            bottom_right = self._video_to_display(self.crop_rect.right(), self.crop_rect.bottom())
            display_rect = QRect(top_left, bottom_right)
            
            if display_rect.contains(pos):
                self.is_dragging = True
                self.drag_start_pos = pos
                self.crop_start_rect = QRect(self.crop_rect)
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        pos = event.pos()
        self.mouse_pos = pos
        
        if self.is_resizing:
            # 调整大小
            self._do_resize(pos)
        elif self.is_dragging:
            # 拖拽移动
            self._do_drag(pos)
        else:
            # 更新光标
            self._update_cursor(pos)
        
        self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.is_resizing = False
            self.active_handle = -1
            self._update_cursor(event.pos())
    
    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件 - 重置裁切区域"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.reset_crop()
    
    def wheelEvent(self, event):
        """滚轮事件 - 缩放裁切框"""
        delta = event.angleDelta().y()
        if delta == 0:
            return
        
        # 计算缩放因子
        scale = 1.1 if delta > 0 else 0.9
        
        # 计算中心点
        center_x = self.crop_rect.center().x()
        center_y = self.crop_rect.center().y()
        
        # 计算新尺寸
        new_w = int(self.crop_rect.width() * scale)
        new_h = int(self.crop_rect.height() * scale)
        
        # 限制最小尺寸
        new_w = max(10, new_w)
        new_h = max(10, new_h)
        
        # 计算新位置（保持中心点）
        new_x = center_x - new_w // 2
        new_y = center_y - new_h // 2
        
        # 限制在视频范围内
        new_x = max(0, min(new_x, self.video_size[0] - new_w))
        new_y = max(0, min(new_y, self.video_size[1] - new_h))
        
        self.crop_rect = QRect(new_x, new_y, new_w, new_h)
        self.update()
        self.crop_changed.emit(self.crop_rect)
    
    def _do_drag(self, pos: QPoint):
        """执行拖拽移动"""
        # 计算偏移量（显示坐标）
        offset_x = pos.x() - self.drag_start_pos.x()
        offset_y = pos.y() - self.drag_start_pos.y()
        
        # 转换为视频坐标
        video_offset = self._display_to_video(abs(offset_x), abs(offset_y))
        if offset_x < 0:
            video_offset.setX(-video_offset.x())
        if offset_y < 0:
            video_offset.setY(-video_offset.y())
        
        # 计算新位置
        new_x = self.crop_start_rect.x() + video_offset.x()
        new_y = self.crop_start_rect.y() + video_offset.y()
        
        # 限制在视频范围内
        new_x = max(0, min(new_x, self.video_size[0] - self.crop_rect.width()))
        new_y = max(0, min(new_y, self.video_size[1] - self.crop_rect.height()))
        
        self.crop_rect.moveTo(new_x, new_y)
        self.crop_changed.emit(self.crop_rect)
    
    def _do_resize(self, pos: QPoint):
        """执行调整大小"""
        # 计算偏移量（显示坐标）
        offset_x = pos.x() - self.drag_start_pos.x()
        offset_y = pos.y() - self.drag_start_pos.y()
        
        # 转换为视频坐标
        video_offset = self._display_to_video(abs(offset_x), abs(offset_y))
        if offset_x < 0:
            video_offset.setX(-video_offset.x())
        if offset_y < 0:
            video_offset.setY(-video_offset.y())
        
        new_rect = QRect(self.crop_start_rect)
        
        # 根据激活的手柄调整
        if self.active_handle in [0, 3, 5]:  # 左侧
            new_x = new_rect.x() + video_offset.x()
            new_w = new_rect.width() - video_offset.x()
            if new_w >= 10:
                new_rect.setX(new_x)
                new_rect.setWidth(new_w)
        
        if self.active_handle in [2, 4, 7]:  # 右侧
            new_w = new_rect.width() + video_offset.x()
            if new_w >= 10:
                new_rect.setWidth(new_w)
        
        if self.active_handle in [0, 1, 2]:  # 上侧
            new_y = new_rect.y() + video_offset.y()
            new_h = new_rect.height() - video_offset.y()
            if new_h >= 10:
                new_rect.setY(new_y)
                new_rect.setHeight(new_h)
        
        if self.active_handle in [5, 6, 7]:  # 下侧
            new_h = new_rect.height() + video_offset.y()
            if new_h >= 10:
                new_rect.setHeight(new_h)
        
        # 限制在视频范围内
        new_rect.setX(max(0, new_rect.x()))
        new_rect.setY(max(0, new_rect.y()))
        new_rect.setWidth(min(new_rect.width(), self.video_size[0] - new_rect.x()))
        new_rect.setHeight(min(new_rect.height(), self.video_size[1] - new_rect.y()))
        
        self.crop_rect = new_rect
        self.crop_changed.emit(self.crop_rect)
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.crop_rect.isEmpty() or self.video_size[0] == 0:
            return
        
        # 将裁切框转换为显示坐标
        top_left = self._video_to_display(self.crop_rect.left(), self.crop_rect.top())
        bottom_right = self._video_to_display(self.crop_rect.right(), self.crop_rect.bottom())
        display_rect = QRect(top_left, bottom_right)
        
        # 绘制半透明遮罩（裁切框外部）
        mask_color = QColor(0, 0, 0, 128)
        
        # 上部分
        painter.fillRect(0, 0, self.width(), display_rect.top(), mask_color)
        # 下部分
        painter.fillRect(0, display_rect.bottom(), self.width(), 
                        self.height() - display_rect.bottom(), mask_color)
        # 左部分
        painter.fillRect(0, display_rect.top(), display_rect.left(), 
                        display_rect.height(), mask_color)
        # 右部分
        painter.fillRect(display_rect.right(), display_rect.top(), 
                        self.width() - display_rect.right(), 
                        display_rect.height(), mask_color)
        
        # 绘制裁切框边框
        pen = QPen(QColor(255, 255, 255), 2)
        painter.setPen(pen)
        painter.drawRect(display_rect)
        
        # 绘制辅助线（九宫格）
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setColor(QColor(255, 255, 255, 180))
        painter.setPen(pen)
        
        # 垂直辅助线
        x1 = display_rect.left() + display_rect.width() // 3
        x2 = display_rect.left() + 2 * display_rect.width() // 3
        painter.drawLine(x1, display_rect.top(), x1, display_rect.bottom())
        painter.drawLine(x2, display_rect.top(), x2, display_rect.bottom())
        
        # 水平辅助线
        y1 = display_rect.top() + display_rect.height() // 3
        y2 = display_rect.top() + 2 * display_rect.height() // 3
        painter.drawLine(display_rect.left(), y1, display_rect.right(), y1)
        painter.drawLine(display_rect.left(), y2, display_rect.right(), y2)
        
        # 绘制8个手柄
        handle_rects = self._get_handle_rects()
        for i, rect in enumerate(handle_rects):
            if i == self.active_handle:
                painter.fillRect(rect, QBrush(QColor(0, 150, 255)))
            else:
                painter.fillRect(rect, QBrush(QColor(255, 255, 255)))
            painter.drawRect(rect)
