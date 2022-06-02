import sys
import numpy as np
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QMessageBox,
    QMainWindow,
    QAction,
    qApp,
    QLineEdit,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QSplitter,
    QComboBox,
    QGroupBox
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from algorithms import algorithms, performAlgorithm
from constants import (
    ZOOM_MIN,
    ZOOM_MAX,
    TOOLBAR_BOTTOMS_ZOOM_COEF,
    WHEEL_SCALING_COEF,
    CURSOR_COORDS_ROUND_DIGITS,
    SCALING_ROUND_DIGITS
)


class Picture(QLabel):

    def __init__(self, *args):
        # args[0] - parent
        # args[1] - path or PIL.Image

        super().__init__(args[0])

        if isinstance(args[1], str):
            self._pixmap = QPixmap(args[1])
        else:
            self._qim = ImageQt(args[1].convert('RGB'))
            self._pixmap = QPixmap.fromImage(self._qim)
        self.setPixmap(self._pixmap)
        self.setMouseTracking(True)

    def resizeEvent(self, e):
        self.setPixmap(self._pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio))



class PicturesFrame(QFrame):

    cursorCoordsChanged = pyqtSignal(float, float)
    cursorLeavesFrame = pyqtSignal()
    wheelZoom = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.setMouseTracking(True)

        self.pics = []
        self.pics_sizes = []

        self.pos = (50, 50)
        self.prev_mouse_pos = (0, 0)

        self.scale = 1
        self.persistent_scale_array = [1]
        self.scale_index = 0

    def addPicture(self, *args):
        self.pics.append(Picture(self, *args))
        self.pics[-1].move(*self.pos)
        self.pics[-1].show()

        w, h = self.pics[-1].size().width(), self.pics[-1].size().height()
        w *= self.scale
        h *= self.scale
        self.pics[-1].resize(w, h)
        self.pics_sizes.append((w, h))

    def setScale(self, scale):
        '''
            If ZOOM_MIN <= scale <= ZOOM_MAX:
                - changes the size of all pictures according to the scale
                - set new value of self.scale
                - reset all next scale values
            Otherwise does nothing.
        '''

        if ZOOM_MIN <= scale <= ZOOM_MAX:
            self._zoomPicturesSilent(scale / self.scale)

            self.scale = scale
            self.persistent_scale_array = self.persistent_scale_array[:self.scale_index + 1]
            self.persistent_scale_array.append(self.scale)
            self.scale_index += 1

    def _zoomPicturesSilent(self, zoom):
        '''
             Always changes the size of all pictures by `zoom` times
             without any additional checks and actions
        '''

        for i in range(len(self.pics)):
            w, h = self.pics_sizes[i]
            w *= zoom
            h *= zoom
            self.pics[i].resize(w, h)
            self.pics_sizes[i] = (w, h)

    def zoomPictures(self, zoom):
        '''
            If ZOOM_MIN <= self.scale * zoom <= ZOOM_MAX:
                - changes the size of all pictures by `zoom` times
                - set new value of self.scale
                - reset all next scale values
            Otherwise does nothing.
        '''

        if ZOOM_MIN <= self.scale * zoom <= ZOOM_MAX:
            self._zoomPicturesSilent(zoom)

            self.scale *= zoom
            self.persistent_scale_array = self.persistent_scale_array[:self.scale_index + 1]
            self.persistent_scale_array.append(self.scale)
            self.scale_index += 1

    def prevScale(self):
        if self.scale_index > 0:
            prev_scale = self.scale
            self.scale_index -= 1
            self.scale = self.persistent_scale_array[self.scale_index]

            self._zoomPicturesSilent(self.scale / prev_scale)

    def nextScale(self):
        if self.scale_index + 1 < len(self.persistent_scale_array):
            prev_scale = self.scale
            self.scale_index += 1
            self.scale = self.persistent_scale_array[self.scale_index]

            self._zoomPicturesSilent(self.scale / prev_scale)

    def deletePicture(self, index):
        if 0 <= index < len(self.pics):
            self.pics[index].deleteLater()
            self.pics.pop(index)
            self.pics_sizes.pop(index)
        else:
            raise RuntimeError('PicturesFrame.deletePicture: index out of range')

    def mouseMoveEvent(self, e):
        # move pictures
        if e.buttons() == Qt.LeftButton:
            self.pos = (self.pos[0] + e.x() - self.prev_mouse_pos[0], self.pos[1] + e.y() - self.prev_mouse_pos[1])
            for pic in self.pics:
                pic.move(*self.pos)
            self.prev_mouse_pos = (e.x(), e.y())
        # emit signal cursorCoordsChanged
        x = (e.x() - self.pos[0]) / self.scale
        y = (self.pos[1] - e.y()) / self.scale
        self.cursorCoordsChanged.emit(x, y)

    def wheelEvent(self, e):
        angle = e.angleDelta().y() / 8
        # angle < 0    - на себя (zoom in)
        self.zoomPictures(WHEEL_SCALING_COEF ** (-angle))
        self.wheelZoom.emit(self.scale)

    def enterEvent(self, e):
        self.setCursor(Qt.OpenHandCursor)

    def leaveEvent(self, e):
        self.setCursor(Qt.ArrowCursor)
        self.cursorLeavesFrame.emit()

    def mousePressEvent(self, e):
        if e.buttons() == Qt.LeftButton:
            self.setCursor(Qt.ClosedHandCursor)
            self.prev_mouse_pos = (e.x(), e.y())

    def mouseReleaseEvent(self, e):
        self.setCursor(Qt.OpenHandCursor)


class PicturesList(QListWidget):

    mouseClickUnselectItems = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.mouseClickUnselectItems.connect(self.unselectPicturesListItems)

    def unselectPicturesListItems(self):
        for item in self.selectedItems():
            item.setSelected(False)

    def mouseReleaseEvent(self, e):

        super().mouseReleaseEvent(e)

        if e.button() == Qt.LeftButton and self.itemAt(e.x(), e.y()) is None:
            self.mouseClickUnselectItems.emit()


class CentralWidget(QWidget):

    def __init__(self):

        super().__init__()
        self.initUI()

    def initUI(self):

        self.pil_image_pictures = []

        self.makeAlgorithmsPanel()
        self.makePicturesListPanel()
        self.makeBottomPanel()

        self.pic_frame = PicturesFrame()
        self.pic_frame.cursorLeavesFrame.connect(lambda: self.bottom_coords_line.setText(''))
        self.pic_frame.cursorCoordsChanged.connect(
            lambda x, y: self.bottom_coords_line.setText(
                str(round(x, CURSOR_COORDS_ROUND_DIGITS)) + ',' + str(round(y, CURSOR_COORDS_ROUND_DIGITS))
            )
        )
        self.pic_frame.wheelZoom.connect(
            lambda scale: self.bottom_scale_line.setText(str(round(scale, SCALING_ROUND_DIGITS)))
        )

        splitter1 = QSplitter(Qt.Vertical)
        splitter1.setChildrenCollapsible(False)
        splitter1.addWidget(self.algorithms_panel)
        splitter1.addWidget(self.pictures_list_panel)

        grid = QGridLayout()
        grid.addWidget(self.pic_frame, 1, 0, 200, 0)
        grid.addWidget(self.bottom_panel, 201, 0)
        right = QWidget()
        right.setLayout(grid)

        splitter2 = QSplitter(Qt.Horizontal)
        splitter2.addWidget(splitter1)
        splitter2.addWidget(right)
        splitter2.setStretchFactor(0, 4)
        splitter2.setStretchFactor(1, 6)

        vbox = QVBoxLayout()
        vbox.addWidget(splitter2)
        self.setLayout(vbox)

    def makeAlgorithmsPanel(self):

        h1 = QHBoxLayout()
        l1 = QLabel()
        l1.setText("Picture 1")
        self.pictures_combobox1 = QComboBox()
        self.pictures_combobox1.setDuplicatesEnabled(True)
        h1.addWidget(l1)
        h1.addWidget(self.pictures_combobox1)

        h2 = QHBoxLayout()
        l2 = QLabel()
        l2.setText("Picture 2")
        self.pictures_combobox2 = QComboBox()
        self.pictures_combobox2.setDuplicatesEnabled(True)
        h2.addWidget(l2)
        h2.addWidget(self.pictures_combobox2)

        h3 = QHBoxLayout()
        l3 = QLabel()
        l3.setText("Algorithm")
        self.algorithms_combobox = QComboBox()
        for algorithm_name in algorithms.keys():
            self.algorithms_combobox.addItem(algorithm_name)
        h3.addWidget(l3)
        h3.addWidget(self.algorithms_combobox)

        h4 = QHBoxLayout()
        l4 = QLabel()
        l4.setText('Name of the result picture')
        self.algorithm_result_picture_name_line = QLineEdit()
        h4.addWidget(l4)
        h4.addWidget(self.algorithm_result_picture_name_line)

        self.btn_apply_algorithm = QPushButton('Apply algorithm')
        self.btn_apply_algorithm.clicked.connect(self.applyAlgorithm)

        vbox = QVBoxLayout()
        vbox.addLayout(h1)
        vbox.addLayout(h2)
        vbox.addLayout(h3)
        vbox.addLayout(h4)
        vbox.addWidget(self.btn_apply_algorithm)

        self.algorithms_panel = QGroupBox('Change detection algorithms')
        self.algorithms_panel.setLayout(vbox)

    def makePicturesListPanel(self):

        self.pictures_list = PicturesList()
        self.pictures_list.itemChanged.connect(self.picturesListItemChanged)
        self.pictures_list.itemSelectionChanged.connect(self.picturesListItemSelectionChanged)

        self.btn_load_picture = QPushButton()
        self.btn_load_picture.setText('Load picture')
        self.btn_load_picture.clicked.connect(self.showDialog)

        self.btn_delete_picture = QPushButton()
        self.btn_delete_picture.setText('Delete picture')
        self.btn_delete_picture.setVisible(False)
        self.btn_delete_picture.clicked.connect(self.deleteSelectedPicture)

        vbox = QVBoxLayout()
        vbox.addWidget(self.pictures_list)
        vbox.addWidget(self.btn_load_picture)
        vbox.addWidget(self.btn_delete_picture)

        self.pictures_list_panel = QGroupBox('Pictures')
        self.pictures_list_panel.setLayout(vbox)

    def makeBottomPanel(self):
        hbox = QHBoxLayout()
        hbox.addStretch(1)

        # self.bottom_distance_label = QLabel()
        # self.bottom_distance_label.setText('Distance:')
        # hbox.addWidget(self.bottom_distance_label)
        #
        # self.bottom_distance_line = QLineEdit()
        # self.bottom_distance_line.setReadOnly(True)
        # hbox.addWidget(self.bottom_distance_line)
        #
        # self.bottom_distance_label.setVisible(False)
        # self.bottom_distance_line.setVisible(False)

        l2 = QLabel()
        l2.setText('Coordinates:')
        hbox.addWidget(l2)

        self.bottom_coords_line = QLineEdit()
        self.bottom_coords_line.setReadOnly(True)
        hbox.addWidget(self.bottom_coords_line)

        l3 = QLabel()
        l3.setText('Scale:')
        hbox.addWidget(l3)

        self.bottom_scale_line = QLineEdit()
        self.bottom_scale_line.setText('1')
        self.bottom_scale_line.returnPressed.connect(self.scaleLineEditChangedByUser)
        hbox.addWidget(self.bottom_scale_line)

        self.bottom_panel = QWidget()
        self.bottom_panel.setLayout(hbox)

    def showDialog(self):

        path = QFileDialog.getOpenFileName(self, 'Open file')[0]

        if path:
            self.pic_frame.addPicture(path)

            self.pil_image_pictures.append(Image.open(path))

            pic_name = path.split('/')[-1]

            item = QListWidgetItem()
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            item.setText(pic_name)
            item.setCheckState(Qt.Checked)
            self.pictures_list.addItem(item)

            self.pictures_combobox1.addItem(pic_name)
            self.pictures_combobox2.addItem(pic_name)

    def showSavePictureDialog(self):
        if self.pictures_list.selectedItems():
            path = QFileDialog.getSaveFileName(self, 'Save file')[0]

            if path:
                for index in range(self.pictures_list.count()):
                    if self.pictures_list.item(index).isSelected():
                        try:
                            self.pil_image_pictures[index].convert('RGB').save(path)
                        except ValueError:
                            QMessageBox(
                                QMessageBox.Warning,
                                'Wrong format of filename!',
                                'Cannot save file because input filename is wrong.\nTry again.',
                                QMessageBox.Ok
                            ).exec_()
                        break

    def picturesListItemChanged(self):
        for index in range(self.pictures_list.count()):
            item = self.pictures_list.item(index)
            self.pic_frame.pics[index].setVisible(item.checkState() == Qt.Checked)

    def picturesListItemSelectionChanged(self):
        if self.pictures_list.selectedItems():
            self.btn_delete_picture.setVisible(True)
        else:
            self.btn_delete_picture.setVisible(False)

        for index in range(self.pictures_list.count()):
            if self.pictures_list.item(index).isSelected():
                self.pic_frame.pics[index].raise_()

    def deleteSelectedPicture(self):

        npic = self.pictures_list.count()
        for index in range(npic - 1, -1, -1):
            if self.pictures_list.item(index).isSelected():

                self.pictures_list.takeItem(index)

                self.pictures_combobox1.removeItem(index)
                self.pictures_combobox2.removeItem(index)

                self.pic_frame.deletePicture(index)

                self.pil_image_pictures.pop(index)

                self.pictures_list.unselectPicturesListItems()
                break

    def scaleLineEditChangedByUser(self):
        text = self.bottom_scale_line.text()
        text = text.replace(',', '.')   # float() can't parse symbol `,`
        try:
            scale = float(text)
            if ZOOM_MIN <= scale <= ZOOM_MAX:
                self.pic_frame.setScale(scale)
            else:
                QMessageBox(
                    QMessageBox.Warning,
                    'Scale out of range!',
                    'Input scale is out of range [0.2, 5]. Try again.',
                    QMessageBox.Ok
                ).exec_()
                self.bottom_scale_line.setText(str(round(self.pic_frame.scale, SCALING_ROUND_DIGITS)))
        except ValueError:
            QMessageBox(
                QMessageBox.Warning,
                'Wrong format of scale!',
                'Input scale must be a number from range [0.2, 5]. Try again.',
                QMessageBox.Ok
            ).exec_()
            self.bottom_scale_line.setText(str(round(self.pic_frame.scale, SCALING_ROUND_DIGITS)))

    def zoomPictures(self, zoom):
        self.pic_frame.zoomPictures(zoom)
        self.bottom_scale_line.setText(str(round(self.pic_frame.scale, SCALING_ROUND_DIGITS)))

    def prevPicturesScale(self):
        self.pic_frame.prevScale()
        self.bottom_scale_line.setText(str(round(self.pic_frame.scale, SCALING_ROUND_DIGITS)))

    def nextPicturesScale(self):
        self.pic_frame.nextScale()
        self.bottom_scale_line.setText(str(round(self.pic_frame.scale, SCALING_ROUND_DIGITS)))

    def applyAlgorithm(self):
        pic1_index = self.pictures_combobox1.currentIndex()
        pic2_index = self.pictures_combobox2.currentIndex()
        algorithm_name = self.algorithms_combobox.currentText()
        result_picture_name = self.algorithm_result_picture_name_line.text()

        if pic1_index >= 0 and pic2_index >= 0 and algorithm_name and result_picture_name:
            current_algo = algorithms[algorithm_name]
            res_im = performAlgorithm(
                current_algo,
                self.pil_image_pictures[pic1_index],
                self.pil_image_pictures[pic2_index],
            )

            # here final code is begun
            self.pil_image_pictures.append(res_im)

            self.pic_frame.addPicture(res_im)

            item = QListWidgetItem()
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            item.setText(result_picture_name)
            item.setCheckState(Qt.Checked)
            self.pictures_list.addItem(item)

            self.pictures_combobox1.addItem(result_picture_name)
            self.pictures_combobox2.addItem(result_picture_name)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        self.central_widget = CentralWidget()
        self.setCentralWidget(self.central_widget)

        self.createActions()
        self.makeMenu()
        self.makeToolbar()

        self.setWindowTitle('Change detection')
        self.setWindowIcon(QIcon('project_data/icons/icon.png'))

        self.showMaximized()

    def createActions(self):
        self.actions = {}

        exitAction = QAction(QIcon('project_data/icons/exit.png'), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.quit)
        self.actions['exit'] = exitAction

        loadPictureAction = QAction(QIcon('project_data/icons/layer-add.png'), 'Load picture', self)
        loadPictureAction.setShortcut('Ctrl+L')
        loadPictureAction.setStatusTip('Load picture')
        loadPictureAction.triggered.connect(self.central_widget.showDialog)
        self.actions['load_picture'] = loadPictureAction

        savePictureAction = QAction(QIcon('project_data/icons/save.png'), 'Save picture', self)
        savePictureAction.setShortcut('Ctrl+S')
        savePictureAction.setStatusTip('Save picture')
        savePictureAction.triggered.connect(self.central_widget.showSavePictureDialog)
        self.actions['save_picture'] = savePictureAction

        zoomInPicturesAction = QAction(QIcon('project_data/icons/zoom-in.png'), 'Zoom in', self)
        zoomInPicturesAction.setStatusTip('Zoom in pictures')
        zoomInPicturesAction.triggered.connect(lambda: self.central_widget.zoomPictures(TOOLBAR_BOTTOMS_ZOOM_COEF))
        self.actions['zoom_in'] = zoomInPicturesAction

        zoomOutPicturesAction = QAction(QIcon('project_data/icons/zoom-out.png'), 'Zoom out', self)
        zoomOutPicturesAction.setStatusTip('Zoom out pictures')
        zoomOutPicturesAction.triggered.connect(lambda: self.central_widget.zoomPictures(1 / TOOLBAR_BOTTOMS_ZOOM_COEF))
        self.actions['zoom_out'] = zoomOutPicturesAction

        prevScalePicturesAction = QAction(QIcon('project_data/icons/prev-scale.png'), 'Previous pictures scale', self)
        prevScalePicturesAction.setStatusTip('Previous pictures scale')
        prevScalePicturesAction.triggered.connect(self.central_widget.prevPicturesScale)
        self.actions['prev_scale'] = prevScalePicturesAction

        nextScalePicturesAction = QAction(QIcon('project_data/icons/next-scale.png'), 'Next pictures scale', self)
        nextScalePicturesAction.setStatusTip('Next pictures scale')
        nextScalePicturesAction.triggered.connect(self.central_widget.nextPicturesScale)
        self.actions['next_scale'] = nextScalePicturesAction

    def makeMenu(self):
        menubar = self.menuBar()

        fileMenu = menubar.addMenu('File')
        fileMenu.addAction(self.actions['load_picture'])
        fileMenu.addAction(self.actions['save_picture'])
        fileMenu.addSeparator()
        fileMenu.addAction(self.actions['exit'])

        viewMenu = menubar.addMenu('View')
        viewMenu.addSection('Zoom')
        viewMenu.addAction(self.actions['zoom_in'])
        viewMenu.addAction(self.actions['zoom_out'])
        viewMenu.addSeparator()
        viewMenu.addAction(self.actions['prev_scale'])
        viewMenu.addAction(self.actions['next_scale'])

    def makeToolbar(self):
        self.toolbar = self.addToolBar('Main toolbar')
        self.toolbar.addAction(self.actions['load_picture'])
        self.toolbar.addAction(self.actions['save_picture'])
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actions['zoom_in'])
        self.toolbar.addAction(self.actions['zoom_out'])
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actions['prev_scale'])
        self.toolbar.addAction(self.actions['next_scale'])

    def quit(self):
        reply = QMessageBox.question(self, 'Exit',
                                     "Are you sure to quit? All unsaved changes will be lost.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            qApp.quit()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Exit',
                                     "Are you sure to quit? All unsaved changes will be lost.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())
