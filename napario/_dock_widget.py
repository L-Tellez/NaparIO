"""
This module save and load sets of layers
Saving saves all opened layers and create a config.yml file containing the additionals layers info
Loading reads a config.yml file and open the files specified in the config file 
"""
from napari_plugin_engine import napari_hook_implementation
from qtpy.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton,QGridLayout, QFileDialog
from qtpy.QtCore import Qt
import os 
from os import listdir
from os.path import isfile, join
import pandas as pd
import yaml

class SaveAndLoad(QWidget):
    loadPath = None
    loadInput = None

    savePath = None
    saveInput = None

    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        loadLabel = QLabel(self)
        loadLabel.setText("Loading Files from a Folder :")
        self.loadInput = QLineEdit(self)
        self.loadInput.setText(self.loadPath)
        btnBrowseload = QPushButton("Browse...")
        btnBrowseload.clicked.connect(self._on_click_browse_load)
        btnLoad = QPushButton("Load")
        btnLoad.clicked.connect(self._on_click_load)

        saveLabel = QLabel(self)
        saveLabel.setText("Save Layers to a Folder :")
        self.saveInput = QLineEdit(self)
        self.saveInput.setText(self.savePath)
        btnBrowseSave = QPushButton("Browse...")
        btnBrowseSave.clicked.connect(self._on_click_browse_save)
        btnSave = QPushButton("Save")
        btnSave.clicked.connect(self._on_click_save)

        self.setLayout(QGridLayout())

        loadLayoutX = 1
        saveLayoutX = 4
        self.layout().addWidget(loadLabel       , loadLayoutX  , 1, 1, 2,Qt.AlignHCenter)
        self.layout().addWidget(self.loadInput  , loadLayoutX+1, 1)
        self.layout().addWidget(btnBrowseload   , loadLayoutX+1, 2)
        self.layout().addWidget(btnLoad         , loadLayoutX+2, 1, 1, 2)

        self.layout().addWidget(saveLabel       , saveLayoutX  , 1, 1, 2,Qt.AlignHCenter)
        self.layout().addWidget(self.saveInput  , saveLayoutX+1, 1)
        self.layout().addWidget(btnBrowseSave   , saveLayoutX+1, 2)
        self.layout().addWidget(btnSave         , saveLayoutX+2, 1, 1, 2)

    def _on_click(self):
        print("napari has", len(self.viewer.layers), "layers")

    def _on_click_browse_load(self):
        folder = QFileDialog.getExistingDirectory() 
        if folder:
            self.loadPath = folder + os.sep
            self.loadInput.setText(self.loadPath) 
    
    def _on_click_browse_save(self):
        folder = QFileDialog.getExistingDirectory() 
        if folder:
            self.savePath = folder + os.sep
            self.saveInput.setText(self.savePath)

    def _on_click_load(self):
        self.loadFromFolders()

    def _on_click_save(self):
        self.saveLayers()

    def loadFromFolders(self):
        print("Loading Files from folder")
        self.loadAllLayers(self.loadPath)

    def saveLayers(self):
        print("Saving each layer")
        self.saveAllLayers(self.savePath)

    def loadAllLayers(self,directoryName):
        currentDirectory = str(directoryName).replace("\\", "/").replace("//", "/")

        configFile = ""

        for f in listdir(currentDirectory):
            if isfile(join(currentDirectory, f)) and f.endswith(".yml"):
                configFile = join(currentDirectory, f)

        with open(configFile, 'r') as file:
            configs = yaml.load(file, Loader=yaml.FullLoader)
            #Calibration:
            x=configs['calibration']['x']
            y=configs['calibration']['y']
            z=configs['calibration']['z']
            zFactor = z / x
            for parameter in configs['layers']:
                name = parameter['name']
                filename = parameter['filename']
                type = parameter['type']
                colormap =parameter['colormap']
                if(type == 'image'):
                    self.viewer.open(join(currentDirectory, filename),layer_type=type,name=name,colormap=colormap,scale=[zFactor, 1, 1],blending='additive')
                    continue
                if(type == 'points'):
                    pointsCsv = pd.read_csv(join(currentDirectory, filename))
                    qualities = pointsCsv['confidence'].values
                    properties = {'confidence' : qualities}
                    self.viewer.open(join(currentDirectory, filename),layer_type=type,name=name,face_colormap=colormap,scale=[zFactor, 1, 1],size=3,properties=properties,face_color='confidence',face_contrast_limits=(0.0,1.0))
                    continue
                if(type == 'shapes'):
                    self.viewer.open(join(currentDirectory, filename),layer_type=type,name=name,face_colormap=colormap,scale=[zFactor, 1, 1])
                    continue
                if(type == 'labels'):
                    self.viewer.open(join(currentDirectory, filename),layer_type=type,name=name,scale=[zFactor, 1, 1])

    def saveAllLayers(self,directoryName):
        savePath = str(directoryName).replace("\\", "/").replace("//", "/")

        layerList = self.viewer.layers

        layersArray = []
        for i in range(len(layerList)):
            currentLayer = layerList[i]
            name = currentLayer.name
            type_ = str(type(currentLayer))
            print(type_)
            if(type_.find('image')>-1):
                scale = currentLayer.scale
                type_ = 'image'
                filename = name + ".tif"
                colormap = currentLayer.colormap.name
            if(type_.find('points')>-1):
                type_ = 'points'
                filename = name + ".csv"
                colormap = currentLayer.face_colormap.name
            if(type_.find('shapes')>-1):
                type_ = 'shapes'
                filename = name + ".csv"
                colormap = currentLayer.face_colormap.name
            if(type_.find('labels')>-1):
                type_ = 'labels'
                filename = name + ".tif"
                colormap = "DummyData"

            layersArray.append({'name':name,'filename':filename,'type':type_,'colormap':colormap})
            
        layersPart = {'layers':layersArray}
        
        print(scale[1])
        print(type(scale[1]))
        zFactor = float(scale[1])

        calibrationPart = {'calibration':{'x':1,'y':1,'z':zFactor}}
        with open(join(savePath, "config.yml"), 'w+') as file:
            yaml.dump(calibrationPart, file, sort_keys=False)
            yaml.dump(layersPart, file, sort_keys=False)

        layerList.save(savePath)

@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    # you can return either a single widget, or a sequence of widgets
    return SaveAndLoad
