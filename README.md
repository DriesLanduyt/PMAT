![Icon of plug-in](https://www.github.com/DriesLanduyt/PMAT/PMAT/icon.png)

#Probabilistic Map Algebra Tool (PMAT)

A Quantum GIS plug-in to apply Bayesian belief network models on raster data

© 2015, Dries Landuyt (<mailto:drieslanduyt@gmail.com>)

###Installation

**Step 1.** Save the [PMAT](www.github.com/DriesLanduyt/PMAT/PMAT) folder, present in this repository, to the following directory of Quantum GIS:

    ...\apps\qgis\python\plugins\


**Step 2.** Copy the `Netica.dll` file which can be found in your local installation of Netica or at the [Norsys website](www.norsys.com) to the following directory of your Quantum GIS installation (you will need the 32bit version for the plug-in):

    ...\bin\     

###Usage

**Step 1.** Develop a Bayesian belief network model by using the graphical user interface of Netica

Specific model requirements for the plugin include: 
* The output and input nodes of the network should be defined by assigning them respectively to the nodesets `OUT` and `IN`
* All nodes belonging to the `IN` nodeset should have statenames assigned to each of their states
* All nodes belonging to the `OUT` nodeset should have numerical statetitles assigned to each of their states 

**Step 2.** Prepare input maps

Convert the input maps to GeoTiff format and name them according to the names of the corresponding input nodes' names (`nodename.tif`). Prepare for each GeoTiff input map legend files. A legend file assigns a statename to each numerical value (not for values that represent no data) included in the GeoTiff file. The legend file should be named and structured as follows:

`nodenameleg.csv`
```
	numerical value 1		statename 1
	numerical value 2		statename 2
	numerical value 3		statename 3
	numerical value 4		statename 4
	numerical value 5		statename 5
	.				.
	.				.
	.				.
	numerical value n		statename n
```

Examples of correctly formatted GeoTiff files, legend files and network file can be found in the [Example](www.github.com/DriesLanduyt/PMAT/Example) folder

**Step 3.** Open Quantum GIS 

via the `Plugins` tab you should be able to open the plug-in. In case the plug-in does not appear in the list, search for it via `Plugins` -> `Manage and Install Plugins...` 
 
**Step 4.** Browse to the proper directory

This directory should contain the input maps (.tif), the legend files (.csv) and the network file (.neta). To test the plugin, use the [Example](www.github.com/DriesLanduyt/PMAT/Example) folder provided in this repository.

**Step 5.** Browse to the proper network file (.neta)

To test the plugin, select the `Example_Network.neta file`

**Step 6.** Select the type(s) of output map(s) you want

**Step 7.** Select a calculation method

* `Fast`: The network model will be transformed into a look-up table. This look-up table will be used to link each pixel with it's probabilistic model output. 
* `Slow`: The network model will be ran on each pixel seperately.   

**Step 8.** Specify whether you want the output being visualised on the map canvas 

Select or deselect the `Add map to canvas` checkbox

**Step 9.** Click the `OK` button, the progress bars will load successively

###Questions and bug reports

For questions or bug reports, please open an [issue](www.github.com/DriesLanduyt/PMAT/issues) in this repository

###Reference

* Landuyt, D., Van der Biest, K., Broekx, S., Staes, J., Meire, P., Goethals, P.L.M. (2015). A GIS plug-in for Bayesian belief networks: Towards a transparent software framework to assess and visualise uncertainties in ecosystem service mapping. Enviornmental Modelling and Software 71, 30-38
