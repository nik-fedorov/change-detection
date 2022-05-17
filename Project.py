import sys
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
    QComboBox
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from algorithms import algorithms


class Picture(QLabel):

    def __init__(self, parent, path):
        super().__init__(parent)
        self._pixmap = QPixmap(path)
        self.setPixmap(self._pixmap)

    # def rotate(self, angle):
    #     t = QTransform().rotate(angle)
    #     self._pixmap = QPixmap(self._pixmap.transformed(t))
    #     self.setPixmap(self._pixmap)
    #     self.resize(self.sizeHint())

    def resizeEvent(self, e):
        self.setPixmap(self._pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio))


class PicturesFrame(QFrame):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setStyleSheet("background-color: rgb(255, 255, 255);")

        self.pics = []
        self.pos = (50, 50)
        self.prev_mouse_pos = (0, 0)

    def addPicture(self, path):
        self.pics.append(Picture(self, path))
        self.pics[-1].move(*self.pos)
        self.pics[-1].show()

    # def rotatePictures(self, angle):
    #     for pic in self.pics:
    #         pic.rotate(angle)

    def zoomPictures(self, zoom):
        for pic in self.pics:
            w, h = pic.size().width(), pic.size().height()
            pic.resize(w * zoom, h * zoom)

    def deletePicture(self, index):
        if 0 <= index < len(self.pics):
            self.pics[index].deleteLater()
            self.pics.pop(index)
        else:
            raise RuntimeError('PicturesFrame.deletePicture: index out of range')

    def mouseMoveEvent(self, e):
        self.pos = (self.pos[0] + e.x() - self.prev_mouse_pos[0], self.pos[1] + e.y() - self.prev_mouse_pos[1])
        for pic in self.pics:
            pic.move(*self.pos)
        self.prev_mouse_pos = (e.x(), e.y())

    def wheelEvent(self, e):
        angle = e.angleDelta().y() / 8
        # angle < 0    - на себя (zoom in)
        self.zoomPictures(1.03 ** (-angle))

    def enterEvent(self, e):
        self.setCursor(Qt.OpenHandCursor)

    def leaveEvent(self, e):
        self.setCursor(Qt.ArrowCursor)

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

        self.makeAlgorithmsPanel()
        self.makePicturesListPanel()
        self.pic_frame = PicturesFrame()
        self.makeBottomPanel()

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
        self.pictures_combobox3 = QComboBox()
        for algorithm_name in algorithms.keys():
            self.pictures_combobox3.addItem(algorithm_name)
        h3.addWidget(l3)
        h3.addWidget(self.pictures_combobox3)

        self.btn_apply_algorithm = QPushButton('Apply algorithm')
        self.btn_apply_algorithm.clicked.connect(self.applyAlgorithm)

        vbox = QVBoxLayout()
        vbox.addLayout(h1)
        vbox.addLayout(h2)
        vbox.addLayout(h3)
        vbox.addWidget(self.btn_apply_algorithm)

        self.algorithms_panel = QWidget()
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

        self.pictures_list_panel = QWidget()
        self.pictures_list_panel.setLayout(vbox)

    def makeBottomPanel(self):
        hbox = QHBoxLayout()
        hbox.addStretch(1)

        self.bottom_distance_label = QLabel()
        self.bottom_distance_label.setText('Distance:')
        hbox.addWidget(self.bottom_distance_label)

        self.bottom_distance_line = QLineEdit()
        self.bottom_distance_line.setReadOnly(True)
        hbox.addWidget(self.bottom_distance_line)

        self.bottom_distance_label.setVisible(False)
        self.bottom_distance_line.setVisible(False)

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
        hbox.addWidget(self.bottom_scale_line)

        self.bottom_panel = QWidget()
        self.bottom_panel.setLayout(hbox)

    def showDialog(self):

        path = QFileDialog.getOpenFileName(self, 'Open file')[0]

        if path:
            self.pic_frame.addPicture(path)

            pic_name = path.split('/')[-1]

            item = QListWidgetItem()
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            item.setText(pic_name)
            item.setCheckState(Qt.Checked)
            self.pictures_list.addItem(item)

            self.pictures_combobox1.addItem(pic_name)
            self.pictures_combobox2.addItem(pic_name)

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

    def zoomPictures(self, zoom):
        self.pic_frame.zoomPictures(zoom)

    # def rotatePictures(self, angle):
    #     self.pic_frame.rotatePictures(angle)

    def applyAlgorithm(self):
        pic1_index = self.pictures_combobox1.currentIndex()
        pic2_index = self.pictures_combobox2.currentIndex()
        algorithm_name = self.pictures_combobox3.currentText()

        print(pic1_index, pic2_index)
        algorithms[algorithm_name]()


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
        self.setWindowIcon(QIcon('project_data/icon.png'))

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

        zoomInPicturesAction = QAction(QIcon('project_data/icons/zoom-in.png'), 'Zoom in', self)
        zoomInPicturesAction.setStatusTip('Zoom in pictures')
        zoomInPicturesAction.triggered.connect(lambda: self.central_widget.zoomPictures(1.2))
        self.actions['zoom_in'] = zoomInPicturesAction

        zoomOutPicturesAction = QAction(QIcon('project_data/icons/zoom-out.png'), 'Zoom out', self)
        zoomOutPicturesAction.setStatusTip('Zoom out pictures')
        zoomOutPicturesAction.triggered.connect(lambda: self.central_widget.zoomPictures(1 / 1.2))
        self.actions['zoom_out'] = zoomOutPicturesAction

        # rotateClockwisePicturesAction = QAction(QIcon('project_data/icons/rotate-clockwise.png'),
        #                                         'Rotate clockwise', self)
        # rotateClockwisePicturesAction.setStatusTip('Rotate pictures clockwise')
        # rotateClockwisePicturesAction.triggered.connect(lambda: self.central_widget.rotatePictures(15))
        # self.actions['rotate_clockwise'] = rotateClockwisePicturesAction
        #
        # rotateCounterClockwisePicturesAction = QAction(QIcon('project_data/icons/rotate-counterclockwise.png'),
        #                                                'Rotate counterclockwise', self)
        # rotateCounterClockwisePicturesAction.setStatusTip('Rotate pictures counterclockwise')
        # rotateCounterClockwisePicturesAction.triggered.connect(lambda: self.central_widget.rotatePictures(-15))
        # self.actions['rotate_counterclockwise'] = rotateCounterClockwisePicturesAction

    def makeMenu(self):
        menubar = self.menuBar()

        fileMenu = menubar.addMenu('File')
        fileMenu.addAction(self.actions['load_picture'])
        fileMenu.addSeparator()
        fileMenu.addAction(self.actions['exit'])

        viewMenu = menubar.addMenu('View')
        viewMenu.addSection('Zoom')
        viewMenu.addAction(self.actions['zoom_in'])
        viewMenu.addAction(self.actions['zoom_out'])
        # viewMenu.addSection('Rotate')
        # viewMenu.addAction(self.actions['rotate_clockwise'])
        # viewMenu.addAction(self.actions['rotate_counterclockwise'])

    def makeToolbar(self):
        self.toolbar = self.addToolBar('Main toolbar')
        self.toolbar.addAction(self.actions['load_picture'])
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actions['zoom_in'])
        self.toolbar.addAction(self.actions['zoom_out'])
        # self.toolbar.addSeparator()
        # self.toolbar.addAction(self.actions['rotate_clockwise'])
        # self.toolbar.addAction(self.actions['rotate_counterclockwise'])

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
