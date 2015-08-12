# -*- coding: utf-8 -*-

#------------------------------------------------------------------------------
################################# DEPENDENCIES ################################
#------------------------------------------------------------------------------

#Universal packages
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QThread, Signal, QMutex, QFileInfo
from PyQt4.QtGui import QAction, QIcon, QDialog, QDialogButtonBox, QFileDialog, QMessageBox 
from qgis.core import *
from qgis.gui import *
import os
from osgeo import gdal
from osgeo import gdalconst
import numpy as np
import csv
import operator
import traceback

#Custom script files
import NeticaWrapper as nr

#Custom dialog
from probabilistic_map_algebra_tool_dialog_base import Ui_BBNToolbox

# Initialize Qt resources from file resources.py
import resources

import os.path
import inspect

#------------------------------------------------------------------------------
############################## INITIATION CLASS ###############################
#------------------------------------------------------------------------------

class ProbabilisticMapAlgebraTool:

    def __init__(self, iface):

        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'ProbabilisticMapAlgebraTool_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = ProbabilisticMapAlgebraToolDialog(self.iface)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Probabilistic Map Algebra Tool')
        self.toolbar = self.iface.addToolBar(u'ProbabilisticMapAlgebraTool')
        self.toolbar.setObjectName(u'ProbabilisticMapAlgebraTool')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('ProbabilisticMapAlgebraTool', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        curpath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))    
        icon_path =os.path.join(curpath,'icon.png')
        self.add_action(
            icon_path,
            text=self.tr(u'Apply BBN on spatial data'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Probabilistic Map Algebra Tool'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        self.dlg.exec_()

#------------------------------------------------------------------------------
###################### GRAPHICAL USER INTERFACE CLASS #########################
#------------------------------------------------------------------------------

class ProbabilisticMapAlgebraToolDialog(QDialog, Ui_BBNToolbox):
  
  def __init__(self,iface):
    
    #initialize dialog
    QDialog.__init__( self, iface.mainWindow() )
    self.setupUi( self )
    self.iface = iface
    
    #initialize arguments 
    self.inDir = None
    self.inNet = None
    self.outputtype = []
    self.ignT = 0
    self.cpT = 0
    self.method = 'fast'
    self.canvas = False
    self.password = ""

    #connect line edits folder and file   
    self.pushButton_browsefile.clicked.connect(self.inputNet)
    self.pushButton_browsefolder.clicked.connect(self.inputDir)
    
    #connect password checkbox and line edit
    self.checkBox_allowPassword.stateChanged[int].connect(self.allowPassword)
    self.lineEdit_password.textChanged[str].connect(self.setPassword)

    #connect checkboxes and spin boxes for output map generation    
    self.checkBox_ev.stateChanged[int].connect(self.evMap)
    self.checkBox_std.stateChanged[int].connect(self.stdMap)
    self.checkBox_mp.stateChanged[int].connect(self.mpMap)
    self.checkBox_pmp.stateChanged[int].connect(self.pmpMap)
    self.checkBox_ign.stateChanged[int].connect(self.ignMap)
    self.doubleSpinBox_ign.valueChanged[float].connect(self.setIgnT)
    self.checkBox_cp.stateChanged[int].connect(self.cpMap)
    self.doubleSpinBox_cp.valueChanged[float].connect(self.setCpT)
    self.checkBox_sim.stateChanged[int].connect(self.simMap)
    
    #connect radiobuttons calculationspeed
    self.radioButton_f.toggled[bool].connect(self.setFast)
    self.radioButton_s.toggled[bool].connect(self.setSlow)
    
    #connect checkbox to plot maps
    self.checkBox_canvas.stateChanged[int].connect(self.setCanvas)
    
    #connect run,cancel buttons
    self.btnOk = self.buttonBox.button( QDialogButtonBox.Ok )
    self.btnClose = self.buttonBox.button( QDialogButtonBox.Cancel )
        
  def inputNet( self ):
    
    if self.inDir != None:
        lastDir = self.inDir
    else: lastDir = 'C:/'
    inNet = QFileDialog.getOpenFileName( self, self.tr( "Select network file" ),lastDir)        
    
    #Check file
    if inNet[-5:] != '.neta':
      QMessageBox.warning( self, self.tr( "Input error" ), self.tr( "This file is not recognized as a Bayesian belief network (.neta)" ) )
      self.lineEdit_file.setText('')
      return 

    self.inNet = str(inNet)
    self.lineEdit_file.setText(inNet)

  def inputDir( self ):
    
    if self.inDir != None:
        lastDir = self.inDir
    else: lastDir = 'C:/'   
    inDir = QFileDialog.getExistingDirectory( self, self.tr( "Select directory" ),lastDir)
    
    #Check directory
    if inDir != "":
        geotiffs = [f for f in os.listdir(inDir) if f[-4:].lower()==".tif"]
        if len(geotiffs)==0:
            QMessageBox.warning( self, self.tr( "Input Error" ), self.tr( "There are no GeoTIFF files in this directory. Please select another one." ) )
            self.lineEdit_folder.setText('')
            return        
      
    self.inDir = inDir
    self.lineEdit_folder.setText(inDir)

  def evMap (self):
      
      if self.checkBox_ev.isChecked():
          self.outputtype.append('ExpV')
      else:
          try: self.outputtype.remove('ExpV')
          except ValueError: pass

  def stdMap (self):
      
      if self.checkBox_std.isChecked():
          self.outputtype.append('StdDev')
      else:
          try: self.outputtype.remove('StdDev')
          except ValueError: pass

  def mpMap (self):
      
      if self.checkBox_mp.isChecked():
          self.outputtype.append('MostProb')
      else:
          try: self.outputtype.remove('MostProb')
          except ValueError: pass 
      
  def pmpMap (self):
      
      if self.checkBox_pmp.isChecked():
          self.outputtype.append('Prob')
      else:
          try: self.outputtype.remove('Prob')
          except ValueError: pass

  def ignMap (self):
      
      if self.checkBox_ign.isChecked():
          self.outputtype.append('Ign')
      else:
          try: self.outputtype.remove('Ign')
          except ValueError: pass
      
  def setIgnT (self,double):
      self.ignT = double

  def cpMap (self):
      
      if self.checkBox_cp.isChecked():
          self.outputtype.append('CumProb')
      else:
          try: self.outputtype.remove('CumProb')
          except ValueError: pass

  def setCpT (self,double):
      self.cpT = double

  def simMap (self):
      
      if self.checkBox_sim.isChecked():
          self.outputtype.append('Sim')
          QMessageBox.warning( self, self.tr( "Warning" ), self.tr( "For sampled maps, only the 'Slow' run mode will deliver accurate results" ) )
      else:
          try: self.outputtype.remove('Sim')
          except ValueError: pass
          
  def setFast (self):
      
      if self.radioButton_f.isChecked():
          self.method = 'fast'         
      
  def setSlow (self):
      
      if self.radioButton_s.isChecked():
          self.method = 'slow'
          
  def setCanvas (self):
      
      if self.checkBox_canvas.isChecked():
          self.canvas = True
      else:
          self.canvas = False
   
  def allowPassword (self):
      
      if self.checkBox_allowPassword.isChecked():
          self.lineEdit_password.setEnabled(True)
      else:
          self.lineEdit_password.setEnabled(False)
          self.lineEdit_password.setText("")
       
  def setPassword (self,password):
      
      self.password = password
      
  def reject( self ):
         
    QDialog.reject( self )
    
  def accept( self ):
      
    #check whether all items were filled in
    if self.inNet == None:
        QMessageBox.warning( self, self.tr( "Input error" ), self.tr( "Network file not specified" ) )
        return
    if self.inDir == None:
        QMessageBox.warning( self, self.tr( "Input error" ), self.tr( "Input map directory not specified" ) )
        return
    if len(self.outputtype) == 0:
        QMessageBox.warning( self, self.tr( "Input error" ), self.tr( "No output maps selected" ) )
        return
    
    #redefine arguments 
    self.inDir = str(self.inDir)
    self.inNet = str(self.inNet)

    #block ok button whileprocessing    
    self.btnOk.setEnabled( False )
    #self.btnClose.setText( self.tr( "Cancel" ) )
    #self.buttonBox.rejected.disconnect(self.reject)
    #self.btnClose.clicked.connect(self.stopProcessing)
    self.btnClose.setEnabled( False )
    
    #open the worker thread
    self.ABSrun = ABSrunner(self.inNet,self.inDir,self.outputtype,self.ignT,self.cpT,self.method,self.password) 
    
    # connect signals from worker thread with GUI thread
    self.ABSrun.MaprangeChanged.connect(self.NewMapRange)
    self.ABSrun.refreshMapProgress.connect(self.NewMapProgress)
    self.ABSrun.RunrangeChanged.connect(self.NewRunRange)
    self.ABSrun.refreshRunProgress.connect(self.NewRunProgress)
    self.ABSrun.PlotrangeChanged.connect(self.NewPlotRange)
    self.ABSrun.refreshPlotProgress.connect(self.NewPlotProgress)
    self.ABSrun.processingFinished.connect(self.processingFinished)
    self.ABSrun.errormessage.connect(self.handleerror)

    #start calculation thread
    self.ABSrun.start()
  
  def NewMapRange( self, maximum ):
      
    self.progressMap.setRange( 0, maximum )

  def NewMapProgress( self, progress ):
      
    self.progressMap.setValue( progress )

  def NewRunRange( self, maximum ):
      
    self.progressRun.setRange( 0, maximum )

  def NewRunProgress( self, progress ):
      
    self.progressRun.setValue( progress )
    
  def NewPlotRange( self, maximum ):
      
    self.progressPlot.setRange( 0, maximum )

  def NewPlotProgress( self, progress ):
      
    self.progressPlot.setValue( progress )  

  def processingFinished( self, outputmaps ):
      
    self.stopProcessing()
    if self.canvas: self.addRasterLayer(outputmaps)

  def stopProcessing( self ):
      
    self.restoreGui()
    if self.ABSrun != None: 
      self.ABSrun = None

  def addRasterLayer(self, maps): 
      
    for m in maps:
        fileName = m 
        fileInfo = QFileInfo(fileName) 
        baseName = fileInfo.baseName() 
        self.layer = QgsRasterLayer(fileName, baseName) 
        if not self.layer.isValid(): 
          QMessageBox.warning( self, self.tr( "Output error") , 'File '+m+' could not be added to the map canvas') 
        QgsMapLayerRegistry.instance().addMapLayer(self.layer,True)
        
  def restoreGui( self ):
      
    self.progressMap.setRange( 0, 100 )
    self.progressRun.setRange( 0, 100 )
    self.progressPlot.setRange( 0, 100 )
    self.progressMap.setValue( 0)
    self.progressRun.setValue( 0 )
    self.progressPlot.setValue( 0 )    
    
    self.buttonBox.rejected.connect(self.reject)
    self.btnClose.setText(self.tr( "Close" ))
    self.btnOk.setEnabled(True)   

  def handleerror(self,e):
    
    self.stopProcessing()
    QMessageBox.warning( self, self.tr( "Run error" ), self.tr( e ) ) 
    

#------------------------------------------------------------------------------
############################# WORKER CLASS ####################################
#------------------------------------------------------------------------------

class ABSrunner ( QThread ):
  
  #-----------------------  
  #  SIGNALS WORKER CLASS
  #----------------------- 
  
  MaprangeChanged = Signal(int)
  RunrangeChanged = Signal(int)
  PlotrangeChanged = Signal(int)
  processingFinished = Signal(list)
  refreshMapProgress = Signal(int)
  refreshRunProgress = Signal(int)
  refreshPlotProgress = Signal(int)
  errormessage = Signal(str) 
  
  #-----------------------  
  #INITIALIZE WORKER CLASS
  #-----------------------  
  
  def __init__( self,net,directory,outputtype,ignT,cpT,method,password):
    
    os.chdir(directory)
    QThread.__init__( self, QThread.currentThread() )
    
    #input 
    self.netname = net
    self.dir = directory
    self.outputtype = outputtype
    self.method = method
    self.shownet = False
    self.ignT = ignT
    self.cpT = cpT
    self.password = password
    
  #----------------
  #RUN WORKER CLASS
  #----------------
  QFileInfo
  
  def run(self):
      try: outputmaps = self.main()
      except:
          error = traceback.format_exc()
          self.errorMessage('An unknown error has occured. To detect the error, reread the user manual, check the intermediate results ('+self.dir+') or dig into the code and interprete the python error below:\n\n\n'+error)
          outputmaps = None
      self.leave(outputmaps)
      
  def main(self):  

    #test input data 
    try: 
        self.net = nr.OpenBayesNet(self.netname,self.password)
    except:
        self.errorMessage('Check whether the Netica.dll is saved correctly. This file should be saved in the "bin" folder of your QGIS installation')
        return
        
    inputvariables = self.net.Inputnodes()
    self.inputmaps = [i + '.tif' for i in inputvariables]
    self.nfiles = len(self.inputmaps)
    self.reshapedmaps = [i + '_reshaped.tif' for i in inputvariables]
    self.legends = [i + 'leg.csv' for i in inputvariables]
    self.outputvariables = self.net.Outputnodes()
    self.npixels = 100 #start value
    
    if sum(self.net.numberofnodes)==0:
        self.errorMessage('The networkfile could not be opened or does not contain a BBN model')        
        return
        
    if len(inputvariables)*len(self.outputvariables) == 0: 
        self.errorMessage('The input and output nodesets are not defined correctly')
        return
        
    if set(os.listdir(self.dir)).issuperset(set(self.inputmaps)) == False: 
        self.errorMessage("Not all necessary inputfiles are present in the directory. Inputfiles should be formatted as <inputnodename>.tif")
        return
        
    if set(os.listdir(self.dir)).issuperset(set(self.legends)) == False: 
        self.errorMessage("Not all necessary legend files are present in the directory. Legend files should be formatted as <inputnodename>leg.csv")
        return
        
    #run 
    self.prog = 0
    self.lenbar1 = (2*self.nfiles)+3
    self.MaprangeChanged.emit(self.lenbar1)   
    halt = self.reshape()
    if halt: return      
    dbf = self.combine()   
    leg = self.openLegends()
    self.lenbar2 = self.npixels
    self.RunrangeChanged.emit(self.lenbar2) 
    f = open('outputdatabase.csv', 'wb')
    outputdata = csv.writer(f,dialect = 'excel')
    if self.method == 'fast':
        dbf = self.getUniques(dbf)
        self.translate(dbf,leg)
        mes = self.runModel(outputdata)
        if mes != 'ok': 
            self.errorMessage(mes)
            return
    else: 
        self.progress1()
        blocksize = 500        
        for j in xrange(0,self.npixels,blocksize):
            try: 
                block = dbf[j:j+blocksize]
                progress = 500
            except: 
                block = dbf[j:]
                progress = len(block)
            self.translate(block,leg) 
            self.runModel(outputdata)
            if mes != 'ok': 
                self.errorMessage(mes)
                return
            self.progress2(progress)
    f.close()
    self.lenbar3 = len(self.outputvariables)*len(self.outputtype)
    self.PlotrangeChanged.emit(self.lenbar3)    
    outputmaps = self.plotMaps()
    return outputmaps
  
  def leave(self,outputmaps):      

    if outputmaps==None: 
        outputmaps = []
        self.processingFinished.emit(outputmaps)     
    else: self.processingFinished.emit(outputmaps)  
  
  #----------------  
  #HELPER FUNCTIONS
  #----------------
  
  def progress1(self):
      
    self.prog+=1
    self.refreshMapProgress.emit(self.prog)
    
  def progress2(self,p = 1):
      
    self.prog = self.prog + p
    self.refreshRunProgress.emit(self.prog - self.lenbar1)

  def progress3(self):
      
    self.prog+=1
    self.refreshPlotProgress.emit(self.prog - (self.lenbar1+self.lenbar2))      

  def errorMessage(self, text):
      
    self.errormessage.emit(text)
          
  def combine (self):
    
    dbf = np.zeros((self.npixels,len(self.reshapedmaps)),dtype = np.uint16)
    for i,rf in enumerate(self.reshapedmaps):
        data = gdal.Open(rf).ReadAsArray()
        dbf[:,i] = data.ravel()
        self.progress1()
    np.savetxt("mapdatabase.csv",dbf,fmt='%i',delimiter = ",") # SLOW
    self.progress1()
    return dbf
    
  def getUniques(self,dbf):  
    
    dbf = np.unique(dbf.view(np.dtype((np.void, dbf.dtype.itemsize*dbf.shape[1])))).view(dbf.dtype).reshape(-1, dbf.shape[1])
	#dbf = np.unique(tuple(x) for x in dbf) # SLOW
    self.progress1()
    return dbf

  def openLegends(self):
      
    legends = []    
    for i in self.inputmaps:
        leg = np.loadtxt(i[0:-4]+"leg.csv",delimiter = ',',dtype = np.str)
        legends.append(dict(leg))
    self.progress1()
    return legends
 
  def translate(self,dbf,legends):
    
    g = open('casefile.csv','wb')
    datafile = csv.writer(g,dialect = 'excel')
    datafile.writerow(['key']+['_'.join(name.split('_')[0:-1]) for name in self.reshapedmaps])    
    for row in dbf:
        linedata = [','.join([str(e) for e in row])]+['?']*self.nfiles
        for i,j in enumerate(row):
            try: linedata[i+1] = legends[i][str(j)]
            except KeyError: pass
        datafile.writerow(linedata)  
    
  def runModel (self,outputdata):  
       
    if self.method == 'slow':
        
        #run model on casefile
        data = self.net.RunCasefile('casefile.csv',output = len(self.net.Outputnodes()),ignT = self.ignT,cpT = self.cpT)
        if type(data) is str: return data         
        
        #combine model output with casefile
        g = open('casefile.csv', 'rb')
        casefiledata = csv.reader(g,dialect = 'excel')
        for i,d in enumerate(casefiledata):
            ld = d + data[i]
            outputdata.writerow(ld)
        g.close()
        
    if self.method == 'fast':    

        #run model on casefile        
        data = self.net.RunCasefile('casefile.csv',output = len(self.net.Outputnodes()),ignT = self.ignT,cpT = self.cpT)
        if type(data) is str: return data        
        r,c = np.shape(data)
        
        #combine model output with casefile in dictionary structure       
        g = open('casefile.csv', 'rb')
        casefiledata = csv.reader(g,dialect = 'excel')
        diction = dict([[d[0],d[1:] + data[i]] for i,d in enumerate(casefiledata)])
        nodatarow = [str(-9999)]*self.nfiles
        k = ','.join(nodatarow)
        diction[k] = [-9999]*(self.nfiles+c)
        g.close()
        
        #loop through mapdatabase to append output by using the dictionary
        h = open('mapdatabase.csv', 'rb')
        inputdata = csv.reader(h,dialect = 'excel')
        self.header = diction['key']       
        outputdata.writerow(self.header)        
        for row in inputdata:
            result = diction[','.join(row)]
            outputdata.writerow(result) 
            self.progress2()
        h.close()
    
    return 'ok'
   
  def plotMaps (self):

    outputmaps = []
    for n,es in enumerate(self.outputvariables):
        for l,ot in enumerate(self.outputtype):
            m = open('outputdatabase.csv','rb')
            data = csv.reader(m,dialect = 'excel')
            header = data.next()        
            index = [i for i, j in enumerate(header) if j == ot][n]    
            mapdata = [row[index] for row in data]
            filename = '_'.join([es,ot]) +'.tif'
            mapdata = np.resize(mapdata,(self.nrow,self.ncol))
            outputmaps.append(filename)
            self.plotGeotiff(filename,mapdata)
            self.progress3()
            m.close()
    return outputmaps
   
  def reshape(self):
    
    halt = False
    
    refs = [self.getReference (i,size = True) for i in self.inputmaps]    
    
    #Check resolution
    if len(set([i[1] for i in refs]))!=1: 
        self.errorMessage("Resolution of input maps differs")
        halt = True
        return halt
        
    else: resolution = refs[0][1]
    
    #Define maximum x and minimum y and deviation of other (left-upper corner of smallest grid)
    xvals = [round(j[0],1) for j in refs]
    mx = max(xvals)
    devx = [(mx-k)/resolution for k in xvals]
    
    yvals = [round(m[3],1) for m in refs]
    my = min(yvals)
    devy = [(n-my)/resolution for n in yvals]
       
    #test whether same basic raster is used (deviations must be integers)    
    if (sum([p%1 for p in devx])+sum([q%1 for q in devy])) != 0:
        self.errorMessage('Raster basis of input maps differs')
        halt = True
        return halt        
    
    #define deviation of lower-right corner   
    nrows = [refs[c][6] - devy[c] for c in range(len(self.inputmaps))]
    ncols = [refs[c][7] - devx[c] for c in range(len(self.inputmaps))]
    rowdev = [n - min(nrows) for n in nrows]    
    coldev = [m - min(ncols) for m in ncols]  

    #specify new geospatial reference    
    xul = int(mx) 
    yul = int(my)
    self.geo = [xul,resolution,0.0,yul,0.0,-resolution]
    self.nrow = int(min(nrows))
    self.ncol = int(min(ncols))
    self.npixels = self.nrow*self.ncol  
    
    #delete redundant columns
    for i,t in enumerate(self.inputmaps):
        data = gdal.Open(t, gdalconst.GA_ReadOnly).ReadAsArray()
        if coldev[i]>0: data = data[:,int(devx[i]):-int(coldev[i])]
        else: data = data[:,int(devx[i]):]       
        if rowdev[i]>0: data = data[int(devy[i]):-int(rowdev[i])]
        else: data = data[int(devy[i]):]  
        self.plotGeotiff(self.reshapedmaps[i],data)
        self.progress1() 
    
    return halt
    
  def getReference(self,bestand, size):

    data = gdal.Open(bestand, gdalconst.GA_ReadOnly)
    G = data.GetGeoTransform()
    if size:     
        data = data.ReadAsArray()
        G = list(G) + list(np.shape(data))
    return G

  def plotGeotiff(self,name,dataset):
    
    driver = gdal.GetDriverByName( "GTiff" )
    dst_ds = driver.Create(name,self.ncol,self.nrow,1, gdal.GDT_UInt16)
    dst_ds.SetGeoTransform(self.geo)
    dst_ds.GetRasterBand(1).WriteArray(dataset)
    dst_ds.FlushCache()        