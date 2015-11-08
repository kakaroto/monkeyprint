# -*- coding: latin-1 -*-

#	Copyright (c) 2015 Paul Bomke
#	Distributed under the GNU GPL v2.
#
#	This file is part of monkeyprint.
#
#	monkeyprint is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	monkeyprint is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You have received a copy of the GNU General Public License
#    along with monkeyprint.  If not, see <http://www.gnu.org/licenses/>.


import pygtk
pygtk.require('2.0')
import gtk
#import gtkGLExtVTKRenderWindowInteractor
import monkeyprintModelViewer
import monkeyprintGuiHelper
import subprocess # Needed to call avrdude.
import vtk


boxSettingsWidth = 350

# Define a class for the main GUI. #############################################
class gui(gtk.Window):
	# Override init function.
	def __init__(self, modelCollection, settings, console=None, *args, **kwargs):
		# Initialise base class gtk window.
		gtk.Window.__init__(self, *args, **kwargs)
		# Set function for window close event.
		self.connect("delete-event", self.on_closing, None)
		# Set window title.
		self.set_title("Monkeyprint")
		# Set maximized.
		self.maximize()
		# Show the window.
		self.show()
		
		# Internalise model collection.
		self.modelCollection = modelCollection

		# Create print settings object.
		self.settings = settings
		
		# Internalise console text buffer to write output to.
		self.console = console
		
		# Create main box.
		self.boxMain = gtk.VBox()
		self.add(self.boxMain)
		self.boxMain.show()
		
		# Create menu bar and add at top.
		self.menuBar = menuBar(self.settings)
		self.boxMain.pack_start(self.menuBar, expand=False, fill=False)
		self.menuBar.show()
		
		# Create work area box.
		self.boxWork = gtk.HBox()
		self.boxMain.pack_start(self.boxWork)
		self.boxWork.show()
		
		# Create and pack render box.
		self.boxRender = monkeyprintModelViewer.renderView(self.settings)
		self.boxRender.show()
		self.boxWork.pack_start(self.boxRender)#, expand=True, fill= True)
		
		# Create settings box.
		self.boxSettings = boxSettings(self.settings, self.modelCollection, self.boxRender, self.console)
		self.boxSettings.show()
		self.boxWork.pack_start(self.boxSettings, expand=False, fill=False, padding = 5)

	# Override the close function.
	def on_closing(self, widget, event, data):
		# Create a dialog window with yes/no buttons.
		dialog = gtk.MessageDialog(self,
			gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
			gtk.MESSAGE_QUESTION,
			gtk.BUTTONS_YES_NO,
			"Do you really want to quit?")
          # Set the title.
		dialog.set_title("Quit Monkeyprint?")
		
		# Check the result and respond accordingly.
		response = dialog.run()
		dialog.destroy()
		if response == gtk.RESPONSE_YES:
			gtk.main_quit()
			return False # returning False makes "destroy-event" be signalled to the window.
		else:
			return True # returning True avoids it to signal "destroy-event"
	
	def main(self):
		# All PyGTK applications must have a gtk.main(). Control ends here
		# and waits for an event to occur (like a key press or mouse event).
		gtk.main()


		
		
		
		

# Define a class for the settings box. #########################################
class boxSettings(gtk.VBox):
	# Override init function.
	def __init__(self, settings, modelCollection, renderView, console=None):
		gtk.VBox.__init__(self)
		self.show()
		
		# Internalise data.
		self.settings = settings
		self.modelCollection = modelCollection
		# Import the render view so we are able to add and remove actors.
		self.renderView = renderView
		self.console = console
		
		# Create model list.
		# List will contain strings for dispayed name,
		# internal name and file name and a bool for active state.
		self.modelList = gtk.ListStore(str, str, str, bool)
		
		# Create model management frame.
		self.frameModels = gtk.Frame(label="Models")
		self.pack_start(self.frameModels, padding = 5)
		self.frameModels.show()
		# Create model list view using the model list.
		self.modelListView = modelListView(self.settings, self.modelList, self.modelCollection, self.renderView, self.updateAllEntries, self.console)
		self.frameModels.add(self.modelListView)
		self.modelListView.show()
		
		# Create notebook
#		self.notebook = gtk.Notebook()
		self.notebook = monkeyprintGuiHelper.notebook()
		self.pack_start(self.notebook)
		
		# Create model page, append to notebook and pass custom function.
		self.createModelTab()
		# Append to notebook.
		self.notebook.append_page(self.modelTab, gtk.Label('Models'))
		# Set update function for switch to model page.
		self.notebook.set_custom_function(0, self.tabSwitchModelUpdate)
		
		# Create supports page, append to notebook and pass custom function.
		self.createSupportsTab()
		self.notebook.append_page(self.supportsTab, gtk.Label('Supports'))
#		self.notebook.set_tab_sensitive(1, False)
		self.notebook.set_custom_function(1, self.tabSwitchSupportsUpdate)


		# Add slicing page, append to notebook and pass custom function.
		self.createSlicingTab()
		self.notebook.append_page(self.slicingTab, gtk.Label('Slicing'))
#		self.notebook.set_tab_sensitive(2, False)
		self.notebook.set_custom_function(2, self.tabSwitchSlicesUpdate)

		
		# Add print page.
		self.printTab = gtk.VBox()
		self.printTab.show()
		self.printTab.add(gtk.Label('print stuff'))
		self.notebook.append_page(self.printTab, gtk.Label('Print'))
#		self.notebook.set_tab_sensitive(3, False)
		
		self.notebook.show()

		# Set gui state. This controls which tabs are clickable.
		# 0: Model modifications active.
		# 1: Model modifications, supports and slicing active.
		# 2: All active.
		# Use setGuiState function to set the state. Do not set manually.
		self.setGuiState(0)

		# Create console for debug output.
		# Create frame.
		self.frameConsole = gtk.Frame(label="Output log")
		self.pack_start(self.frameConsole, padding=5)
		self.frameConsole.show()
		# Custom scrolled window.
		self.consoleView = consoleView(self.console)
		self.frameConsole.add(self.consoleView)
		
	
	def tabSwitchModelUpdate(self):
		# Set render actor visibilities.
		self.modelCollection.viewDefault()
		self.renderView.render()
		# Enable model management load and remove buttons.
		self.modelListView.setSensitive(True)

	
	def tabSwitchSupportsUpdate(self):
		# Update supports.
		self.modelCollection.updateAllSupports()
		# Set render actor visibilities.
		self.modelCollection.viewSupports()
		self.renderView.render()
		# Activate slice tab if not already activated.
		if self.getGuiState() == 1:
			self.setGuiState(2)
		# Disable model management load and remove buttons.
		self.modelListView.setSensitive(False)


	def tabSwitchSlicesUpdate(self):
		# Update slices.
		# This should run automatically.
#		self.modelCollection.updateAllSlices(0)
		# Set render actor visibilites.
		self.modelCollection.viewSlices()
		self.renderView.render()
		# Disable model management load and remove buttons.
		self.modelListView.setSensitive(False)
	
	def tabSwitchPrintUpdate(self):
		# Disable model management load and remove buttons.
		self.modelListView.setSensitive(False)
				


	
	
	def createModelTab(self):
		# Create tab box.
		self.modelTab = gtk.VBox()
		self.modelTab.show()
		
		# Create model management frame.
#		self.frameModels = gtk.Frame(label="Models")
#		self.modelTab.pack_start(self.frameModels, padding = 5)
#		self.frameModels.show()
		
		# Create model list view using the model list.
#		self.modelListView = modelListView(self.settings, self.modelList, self.modelCollection, self.renderView, self.updateAllEntries, self.console)
#		self.frameModels.add(self.modelListView)
#		self.modelListView.show()
		
		# Create model modification frame.
		self.frameModifications = gtk.Frame(label="Model modifications")
		self.modelTab.pack_start(self.frameModifications, expand=True, fill=True)
		self.frameModifications.show()
		self.boxModelModifications = gtk.VBox()
		self.frameModifications.add(self.boxModelModifications)
		self.boxModelModifications.show()
		self.entryScaling = entry('Scaling', modelCollection=self.modelCollection, customFunctions=[self.updateCurrentModel, self.modelCollection.updateSliceStack, self.renderView.render, self.updateAllEntries])
		self.boxModelModifications.pack_start(self.entryScaling, expand=False, fill=False)
		self.entryRotationX = entry('Rotation X', modelCollection=self.modelCollection, customFunctions=[self.updateCurrentModel, self.modelCollection.updateSliceStack, self.renderView.render, self.updateAllEntries])
		self.boxModelModifications.pack_start(self.entryRotationX, expand=False, fill=False)
		self.entryRotationY = entry('Rotation Y', modelCollection=self.modelCollection, customFunctions=[self.updateCurrentModel, self.modelCollection.updateSliceStack, self.renderView.render, self.updateAllEntries])
		self.boxModelModifications.pack_start(self.entryRotationY, expand=False, fill=False)
		self.entryRotationZ = entry('Rotation Z', modelCollection=self.modelCollection, customFunctions=[self.updateCurrentModel, self.modelCollection.updateSliceStack, self.renderView.render, self.updateAllEntries])
		self.boxModelModifications.pack_start(self.entryRotationZ, expand=False, fill=False)
		self.entryPositionX = entry('Position X', modelCollection=self.modelCollection, customFunctions=[self.updateCurrentModel, self.modelCollection.updateSliceStack, self.renderView.render, self.updateAllEntries])
		self.boxModelModifications.pack_start(self.entryPositionX, expand=False, fill=False)
		self.entryPositionY = entry('Position Y', modelCollection=self.modelCollection, customFunctions=[self.updateCurrentModel, self.modelCollection.updateSliceStack, self.renderView.render, self.updateAllEntries])
		self.boxModelModifications.pack_start(self.entryPositionY, expand=False, fill=False)
		self.entryBottomClearance = entry('Bottom clearance', modelCollection=self.modelCollection, customFunctions=[self.updateCurrentModel, self.modelCollection.updateSliceStack, self.renderView.render, self.updateAllEntries])
		self.boxModelModifications.pack_start(self.entryBottomClearance, expand=False, fill=False)

	
	def createSupportsTab(self):
		# Create tab box.
		self.supportsTab = gtk.VBox()
		self.supportsTab.show()

		# Create model management frame.
#		self.frameModels = gtk.Frame(label="Models")
#		self.supportsTab.pack_start(self.frameModels, padding = 5)
#		self.frameModels.show()
		# Create model list view using the model list.
#		self.modelListView = modelListView(self.settings, self.modelList, self.modelCollection, self.renderView, self.updateAllEntries, self.console)
#		self.frameModels.add(self.modelListView)
#		self.modelListView.show()
		
		# Create support pattern frame.
		self.frameSupportPattern = gtk.Frame(label="Support pattern")
		self.supportsTab.pack_start(self.frameSupportPattern, expand=False, fill=False)
		self.frameSupportPattern.show()
		self.boxSupportPattern = gtk.VBox()
		self.frameSupportPattern.add(self.boxSupportPattern)
		self.boxSupportPattern.show()
		self.entryOverhangAngle = entry('Overhang angle', modelCollection=self.modelCollection, customFunctions=[self.updateCurrentModel, self.modelCollection.updateSliceStack, self.renderView.render, self.updateAllEntries])
		self.boxSupportPattern.pack_start(self.entryOverhangAngle, expand=False, fill=False)
		self.entrySupportSpacingX = entry('Spacing X', modelCollection=self.modelCollection, customFunctions=[self.updateCurrentModel, self.modelCollection.updateSliceStack, self.renderView.render, self.updateAllEntries])
		self.boxSupportPattern.pack_start(self.entrySupportSpacingX, expand=False, fill=False)
		self.entrySupportSpacingY = entry('Spacing Y', modelCollection=self.modelCollection, customFunctions=[self.updateCurrentModel, self.modelCollection.updateSliceStack, self.renderView.render, self.updateAllEntries])
		self.boxSupportPattern.pack_start(self.entrySupportSpacingY, expand=False, fill=False)
		self.entrySupportMaxHeight = entry('Maximum height', modelCollection=self.modelCollection, customFunctions=[self.updateCurrentModel, self.modelCollection.updateSliceStack, self.renderView.render, self.updateAllEntries])
		self.boxSupportPattern.pack_start(self.entrySupportMaxHeight, expand=False, fill=False)
		
		# Create support geometry frame.
		self.frameSupportGeometry = gtk.Frame(label="Support geometry")
		self.supportsTab.pack_start(self.frameSupportGeometry, expand=False, fill=False)
		self.frameSupportGeometry.show()
		self.boxSupportGeometry = gtk.VBox()
		self.frameSupportGeometry.add(self.boxSupportGeometry)
		self.boxSupportGeometry.show()
		self.entrySupportBaseDiameter = entry('Base diameter', modelCollection=self.modelCollection, customFunctions=[self.updateCurrentModel, self.modelCollection.updateSliceStack, self.renderView.render, self.updateAllEntries])
		self.boxSupportGeometry.pack_start(self.entrySupportBaseDiameter, expand=False, fill=False)
		self.entrySupportTipDiameter = entry('Tip diameter', modelCollection=self.modelCollection, customFunctions=[self.updateCurrentModel, self.modelCollection.updateSliceStack, self.renderView.render, self.updateAllEntries])
		self.boxSupportGeometry.pack_start(self.entrySupportTipDiameter, expand=False, fill=False)
		self.entrySupportTipHeight = entry('Cone height', modelCollection=self.modelCollection, customFunctions=[self.updateCurrentModel, self.modelCollection.updateSliceStack, self.renderView.render, self.updateAllEntries])
		self.boxSupportGeometry.pack_start(self.entrySupportTipHeight, expand=False, fill=False)

		# Create bottom plate frame.
		self.frameBottomPlate = gtk.Frame(label="Bottom plate")
		self.supportsTab.pack_start(self.frameBottomPlate, expand=False, fill=False)
		self.frameBottomPlate.show()
		self.boxBottomPlate = gtk.VBox()
		self.frameBottomPlate.add(self.boxBottomPlate)
		self.boxBottomPlate.show()
		self.entrySupportBottomPlateThickness = entry('Bottom plate thickness', modelCollection=self.modelCollection, customFunctions=[self.updateCurrentModel, self.modelCollection.updateSliceStack, self.renderView.render, self.updateAllEntries])
		self.boxBottomPlate.pack_start(self.entrySupportBottomPlateThickness, expand=False, fill=False)
	
	def createSlicingTab(self):
		# Create tab box.
		self.slicingTab = gtk.VBox()
		self.slicingTab.show()

		# Create slicing parameters frame.
		self.frameSlicing = gtk.Frame(label="Slicing parameters")
		self.slicingTab.pack_start(self.frameSlicing, padding = 5)
		self.frameSlicing.show()
		self.boxSlicingParameters = gtk.VBox()
		self.frameSlicing.add(self.boxSlicingParameters)
		self.boxSlicingParameters.show()
		# Layer height entry.
		self.entryLayerHeight = entry('Layer height', settings=self.settings, customFunctions=[self.updateCurrentModel, self.modelCollection.updateSliceStack, self.renderView.render, self.updateAllEntries])
		self.boxSlicingParameters.pack_start(self.entryLayerHeight, expand=False, fill=False)
		
		# Create hollow and fill frame.
		self.frameFill = gtk.Frame(label="Fill parameters")
		self.slicingTab.pack_start(self.frameFill, padding = 5)
		self.frameFill.show()
		self.boxFill = gtk.VBox()
		self.frameFill.add(self.boxFill)
		self.boxFill.show()
		# Checkbox for hollow prints.
		self.checkboxHollow = gtk.CheckButton(label="Print hollow?")
		self.boxFill.pack_start(self.checkboxHollow, expand=True, fill=True)
		self.checkboxHollow.show()
		self.checkboxHollow.connect("toggled", self.callbackCheckButtonHollow)
		# Checkbox for fill structures.
		self.checkboxFill = gtk.CheckButton(label="Use fill?")
		self.boxFill.pack_start(self.checkboxFill, expand=True, fill=True)
		self.checkboxFill.show()
		self.checkboxFill.connect("toggled", self.callbackCheckButtonFill)
		# Entries.
		self.entryShellThickness = entry('Shell wall thickness', modelCollection=self.modelCollection, customFunctions=[self.updateCurrentModel, self.modelCollection.updateSliceStack, self.renderView.render, self.updateAllEntries])
		self.boxFill.pack_start(self.entryShellThickness, expand=True, fill=True)
		self.entryFillSpacing = entry('Fill spacing', modelCollection=self.modelCollection, customFunctions=[self.updateCurrentModel, self.modelCollection.updateSliceStack, self.renderView.render, self.updateAllEntries])
		self.boxFill.pack_start(self.entryFillSpacing, expand=True, fill=True)
		self.entryFillThickness = entry('Fill wall thickness', modelCollection=self.modelCollection, customFunctions=[self.updateCurrentModel, self.modelCollection.updateSliceStack, self.renderView.render, self.updateAllEntries])
		self.boxFill.pack_start(self.entryFillThickness, expand=True, fill=True)
		
		# Create preview frame.
		self.framePreview = gtk.Frame(label="Slice preview")
		self.slicingTab.pack_start(self.framePreview, padding = 5)
		self.framePreview.show()
		self.boxPreview = gtk.HBox()
		self.framePreview.add(self.boxPreview)
		self.boxPreview.show()
		self.previewSlider = monkeyprintGuiHelper.imageSlider(self.modelCollection.sliceStack, self.console, customFunctions=[self.modelCollection.updateAllSlices, self.renderView.render])
		self.boxPreview.pack_start(self.previewSlider, expand=True, fill=True, padding=5)
		self.previewSlider.show()
	
	def callbackCheckButtonHollow(self, widget, data=None):
		self.modelCollection.getCurrentModel().settings['Print hollow'].setValue(widget.get_active())
		
	def callbackCheckButtonFill(self, widget, data=None):
		self.modelCollection.getCurrentModel().settings['Fill'].setValue(widget.get_active())
		
		

# TODO should these two be placed in the notebook class?	
	def setGuiState(self, state):
		for i in range(self.notebook.get_n_pages()):
			if i<=state:
				self.notebook.set_tab_sensitive(i, True)
			else:
				self.notebook.set_tab_sensitive(i, False)
	
	def getGuiState(self):
		tab = 0
		for i in range(self.notebook.get_n_pages()):
			if self.notebook.is_tab_sensitivte(i):
				tab = i
		return tab
	
	# Function to update the current model after a change was made.
	# Updates model supports or slicing dependent on
	# the current page of the settings notebook.
	def updateCurrentModel(self):
		if self.notebook.getCurrentPage() == 0:
			self.modelCollection.getCurrentModel().updateModel()
		elif self.notebook.getCurrentPage() == 1:
			self.modelCollection.getCurrentModel().updateSupports()
		elif self.notebook.getCurrentPage() == 2:
			self.modelCollection.getCurrentModel().updateSlices()
		elif self.notebook.getCurrentPage() == 3:
			self.modelCollection.getCurrentModel().updatePrint()
			
	
	# Update all the settings if the current model has changed.
	def updateAllEntries(self, state=None):
		self.entryScaling.update()
		self.entryRotationX.update()
		self.entryRotationY.update()
		self.entryRotationZ.update()
		self.entryPositionX.update()
		self.entryPositionY.update()
		self.entryBottomClearance.update()
		self.entryOverhangAngle.update()
		self.entrySupportSpacingX.update()
		self.entrySupportSpacingY.update()
		self.entrySupportMaxHeight.update()
		self.entrySupportBaseDiameter.update()
		self.entrySupportTipDiameter.update()
		self.entrySupportTipHeight.update()
		self.entrySupportBottomPlateThickness.update()
		self.previewSlider.updateSlider()
		if state != None:
			self.setGuiState(state)
			if state == 0:
				self.notebook.setCurrentPage(0)
				

	
	
	
# A text entry including a label on the left. #################################
# Will call a function passed to it on input. Label, default value and
# callback function are taken from the settings object.

class entry(gtk.HBox):
	# Override init function.
#	def __init__(self, string, settings, function=None):
	def __init__(self, string, settings=None, modelCollection=None, customFunctions=None):
		# Call super class init function.
		gtk.HBox.__init__(self)
		self.show()
		
		self.string = string
#		self.settings = settings
		self.modelCollection = modelCollection
		# Get settings of default model which is the only model during GUI creation.
		if self.modelCollection != None:
			self.settings = modelCollection.getCurrentModel().settings
		# If settings are provided instead of a model collection this is a
		# printer settings entry.
		elif settings != None:
			self.settings = settings
			
		self.customFunctions = customFunctions
		
		# Make label.
		self.label = gtk.Label(string+self.settings[string].unit)
		self.label.set_justify(gtk.JUSTIFY_LEFT)
		self.pack_start(self.label, expand=True, fill=True)
		self.label.show()
		
		# Make text entry.
		self.entry = gtk.Entry()
		self.pack_start(self.entry, expand=False, fill=False)
		self.entry.show()
		
		# Set entry text.
		self.entry.set_text(str(self.settings[string].value))
		
		# A bool to track if focus change was invoked by Tab key.
		self.tabKeyPressed = False
			
		# Set callback connected to Enter key and focus leave.
		#self.entry.connect("activate", self.entryCallback, entry)
		self.entry.connect("key-press-event", self.entryCallback, entry)
		self.entry.connect("focus_out_event", self.entryCallback, entry)
	
	
		
	def entryCallback(self, widget, event, entry):
		# Callback provides the following behaviour:
		# Return key sets the value and calls the function.
		# Tab key sets the value and calls the function.
		# Focus-out resets the value if the focus change was not invoked by Tab key.
		# Note: Tab will first emit a key press event, then a focus out event.
#		if event.type.value_name == "GDK_FOCUS_CHANGE" and self.entry.has_focus()==False:
#			print 'foo'
#		elif event.type.value_name == "GDK_KEY_PRESS" and event.keyval == gtk.keysyms.Return:
#			print 'bar'
		# GDK_FOCUS_CHANGE is emitted on focus in or out, so make sure the focus is gone.
		# If Tab key was pressed, set tabKeyPressed and leave.
		if event.type.value_name == "GDK_KEY_PRESS" and event.keyval == gtk.keysyms.Tab:
			self.tabKeyPressed = True
			return
		# If focus was lost and tab key was pressed or if return key was pressed, set the value.
		if (event.type.value_name == "GDK_FOCUS_CHANGE" and self.entry.has_focus()==False and self.tabKeyPressed) or (event.type.value_name == "GDK_KEY_PRESS" and event.keyval == gtk.keysyms.Return):
			# Set value.
			# In case a model collection was provided...
			if self.modelCollection != None:
				# ... set the new value in the current model's settings.
				self.modelCollection.getCurrentModel().settings[self.string].setValue(self.entry.get_text())
				# Call the models update function. This might change the settings value again.
#				self.modelCollection.getCurrentModel().update()
#				self.modelCollection.getCurrentModel().updateSupports()
				# Call the custom functions specified for the setting.
				if self.customFunctions != None:
					for function in self.customFunctions:
						function()
				# Set the entrys text field as it might have changed during the previous function call.
				self.entry.set_text(str(self.modelCollection.getCurrentModel().settings[self.string].value))
			# If this is not a model setting but a printer setting...
			elif self.settings != None:
				# ... write the value to the settings.
				self.settings[self.string].setValue(self.entry.get_text())
				# Set the entry text in case the setting was changed by settings object.
				self.entry.set_text(str(self.settings[self.string].value))
			# Reset tab pressed bool.
			self.tabKeyPressed = False
			return
		# If focus was lost without tab key press, reset the value.
		elif event.type.value_name == "GDK_FOCUS_CHANGE" and self.entry.has_focus()==False:
			#Reset value.
			if self.modelCollection != None:
				self.entry.set_text(str(self.modelCollection.getCurrentModel().settings[self.string].value))
			elif self.settings != None:
				self.entry.set_text(str(self.settings[self.string].value))
			return

		
	# Update the value in the text field if current model has changed.	
	def update(self):
		self.entry.set_text(str(self.modelCollection.getCurrentModel().settings[self.string].value))






# Main menu. ###################################################################	

class menuBar(gtk.MenuBar):
	# Override init function.
	def __init__(self, settings):
		# Call super class init function.
		gtk.MenuBar.__init__(self)
		self.show()
		
		self.settings = settings
		
		# Create file menu (does not have to be shown).
		fileMenu = gtk.Menu()
		
		# Create file menu items.
		menuItemOpen = gtk.MenuItem(label="Open project")
		menuItemSave = gtk.MenuItem(label="Save project")
		menuItemClose = gtk.MenuItem(label="Close project")
		menuItemQuit = gtk.MenuItem(label="Quit")
		
		# Add to menu.
		fileMenu.append(menuItemOpen)
		fileMenu.append(menuItemSave)
		fileMenu.append(menuItemClose)
		fileMenu.append(menuItemQuit)
		
		# Connect menu items to callback signals.
#		menuItemOpen.connect_object("activate", menuitem_response, "file.open")
#		menuItemSave.connect_object("activate", menuitem_response, "file.save")
#		menuItemClose.connect_object("activate", menuitem_response, "file.close")
#		menuItemQuit.connect_object ("activate", destroy, "file.quit")
		
		# Show the items.
		menuItemOpen.show()
		menuItemSave.show()
		menuItemClose.show()
		menuItemQuit.show()
		
		
		
		# Create file menu (does not have to be shown).
		optionsMenu = gtk.Menu()
		
		# Create file menu items.
		menuItemSettings = gtk.MenuItem(label="Settings")
		menuItemFlash = gtk.MenuItem(label="Flash firmware")
		menuItemManualControl = gtk.MenuItem(label="Manual control")
		
		# Connect callbacks.
		menuItemSettings.connect("activate", self.callbackSettings)
		menuItemFlash.connect("activate", self.callbackFlash)

		# Add to menu.
		optionsMenu.append(menuItemSettings)
		optionsMenu.append(menuItemFlash)
		optionsMenu.append(menuItemManualControl)

		
		# Connect menu items to callback signals.
#		menuItemOpen.connect_object("activate", menuitem_response, "file.open")
#		menuItemSave.connect_object("activate", menuitem_response, "file.save")
#		menuItemClose.connect_object("activate", menuitem_response, "file.close")
#		menuItemQuit.connect_object ("activate", destroy, "file.quit")
		
		# Show the items.
		menuItemSettings.show()
		menuItemFlash.show()
		menuItemManualControl.show()
		

		# Create menu bar items.
		menuItemFile = gtk.MenuItem(label="File")
		menuItemFile.set_submenu(fileMenu)
		self.append(menuItemFile)
		menuItemFile.show()
		
		menuItemOptions = gtk.MenuItem(label="Options")
		menuItemOptions.set_submenu(optionsMenu)
		self.append(menuItemOptions)
		menuItemOptions.show()
	
	def callbackSettings(self, event):
		dialogSettings(self.settings)
		
	def callbackFlash(self, event):
		firmwareDialog(self.settings)





# Model list. ##################################################################
class modelListView(gtk.VBox):
	def __init__(self, settings, modelList, modelCollection, renderView, guiUpdateFunction, console=None):
		gtk.VBox.__init__(self)
		self.show()

		# Internalise settings.
		self.settings = settings
		# Internalise model collection and optional console.
		self.modelList = modelList
		self.modelCollection = modelCollection
		# Import the render view so we are able to add and remove actors.
		self.renderView = renderView
		self.guiUpdateFunction = guiUpdateFunction
		self.console = console
		
		self.modelRemovedFlag = False
		
		# Create the scrolled window.
		self.scrolledWindow = gtk.ScrolledWindow()
		self.scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		self.pack_start(self.scrolledWindow, expand=True, fill=True, padding = 5)
		self.scrolledWindow.show()
		# Create view for model list.
		self.viewModels = gtk.TreeView()
		self.viewModels.set_model(self.modelList)
		self.viewModels.show()
#		self.viewModels.set_headers_visible(False)	# Make column invisible.
		self.viewModels.set_headers_clickable(True)
		self.viewModels.set_reorderable(True)
		self.scrolledWindow.add(self.viewModels)
		# Add model name column and respective text cell renderer.
		self.columnModel = gtk.TreeViewColumn('Model name')
		self.viewModels.append_column(self.columnModel)
		self.cellModel = gtk.CellRendererText()
		self.cellModel.set_property('editable', True)
		self.cellModel.connect('edited', self.callbackEdited, self.modelList)
		self.columnModel.pack_start(self.cellModel, True)
		self.columnModel.add_attribute(self.cellModel, 'text', 0)
		self.columnModel.set_sort_column_id(0)
		# Add active? column and respective toggle cell renderer.
		self.columnActive = gtk.TreeViewColumn('Active?')
		self.viewModels.append_column(self.columnActive)
		self.cellActive = gtk.CellRendererToggle()
		self.cellActive.set_property('activatable', True)
		self.cellActive.connect("toggled", self.callbackToggleChanged, self.modelList)
		self.columnActive.pack_start(self.cellActive, False)
		self.columnActive.add_attribute(self.cellActive, 'active', 3)
		self.columnActive.set_sort_column_id(3)

		# Create item selection.
		self.modelSelection = self.viewModels.get_selection()
		# Avoid multiple selection.
		self.modelSelection.set_mode(gtk.SELECTION_SINGLE)
		# Connect to selection change event function.
		self.modelSelection.connect('changed', self.onSelectionChanged)
		
		# Create button box.
		self.boxButtons = gtk.HBox()
		self.boxButtons.show()
		self.pack_start(self.boxButtons, expand=False)
		# Create model load and remove button.
		self.buttonLoad = gtk.Button("Load")
		self.buttonLoad.show()
		self.buttonLoad.connect("clicked", self.callbackLoad)
		self.boxButtons.pack_start(self.buttonLoad)
		self.buttonRemove = gtk.Button("Remove")
		self.buttonRemove.set_sensitive(False)
		self.buttonRemove.show()
		self.buttonRemove.connect("clicked", self.callbackRemove)
		self.boxButtons.pack_start(self.buttonRemove)
	
	# Add an item and set it selected.
	def add(self, displayName, internalName, filename):
		# Append list item and get its iter.
		newIter = self.modelList.append([displayName, internalName, filename, True])
		# Set the iter selected.
		self.modelSelection.select_iter(newIter)
		# Make supports and slice tab available if this is the first model.
		if len(self.modelList)< 2:
			self.guiUpdateFunction(state=1)
	
	# Remove an item and set the selection to the next.
	def remove(self, currentIter):
		# Get the path of the current iter.
		currentPath = self.modelList.get_path(currentIter)[0]
		deletePath = currentPath
		# Check what to select next.
		# If current selection at end of list but not the last element...
		if currentPath == len(self.modelList) - 1 and len(self.modelList) > 1:
			# ... select the previous item.
			currentPath -= 1
			self.modelSelection.select_path(currentPath)		
		# If current selection is somewhere in the middle...
		elif currentPath < len(self.modelList) - 1 and len(self.modelList) > 1:
			# ... selected the next item.
			currentPath += 1
			self.modelSelection.select_path(currentPath)
		# If current selection is the last element remaining...
		elif len(self.modelList)	== 1:
			# ... set the default model as current model.
			self.modelCollection.setCurrentModelId("default")
			# Deactivate the remove button.
			self.buttonRemove.set_sensitive(False)
			# Update the gui.
			self.guiUpdateFunction(state=0)
			# TODO: Disable all the input entries and the supports/slicing/print tabs.
		
		# Now that we have the new selection, we can delete the previously selected model.
		self.renderView.removeActors(self.modelCollection.getModel(self.modelList[(deletePath,0,0)][1]).getActor())
		self.renderView.removeActors(self.modelCollection.getModel(self.modelList[(deletePath,0,0)][1]).getBoxActor())
		# Some debug output...
		if self.console:
			self.console.addLine("Removed model " + self.modelList.get_value(currentIter,0) + ".")
		# Remove the model from the model collection object.
		self.modelCollection.remove(self.modelList[currentIter][1])
		# Remove the item and check if there's a next item.
		iterValid = self.modelList.remove(currentIter)
		# Update the slice stack.
		self.modelCollection.updateSliceStack()
		# Update the slider.
		self.guiUpdateFunction()
		# Refresh view.
		self.renderView.render()
		
	
	# Load a new item into the model list and set it selected.
	def callbackLoad(self, widget, data=None):
		filepath = ""

		# File open dialog to retrive file name and file path.
		dialog = gtk.FileChooserDialog("Load model", None, gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
		dialog.set_current_folder(self.settings['currentFolder'].value)
		# File filter for the dialog.
		fileFilter = gtk.FileFilter()
	#	fileFilter.add_mime_type("image/gif")	TODO
		fileFilter.set_name("Stl files")
		fileFilter.add_pattern("*.stl")
		dialog.add_filter(fileFilter)
		# Run the dialog and return the file path.
		response = dialog.run()
		# Check the response.
		if response == gtk.RESPONSE_OK:
			filepath = dialog.get_filename()
		elif response == gtk.RESPONSE_CANCEL:
			pass
		# Close the dialog.
		dialog.destroy()
		# Check if file is an stl. If yes, load.
		if filepath.lower()[-3:] != "stl":
			if self.console:
				self.console.addLine("File \"" + filepath + "\" is not an stl file.")
		else:
			# Get filename without path.
			filenameStlParts = filepath.split('/')
			filename = filenameStlParts[-1]
			if self.console:
				self.console.addLine("Loading file \"" + filename + "\".")
			# Save path for next use.
			self.settings['currentFolder'].value = filepath[:-len(filenameStlParts[-1])]
			# Check if there is a file with the same name loaded already.
			# Use the permanent file id in second row for this.
			copyNumber = 0
			for row in self.modelList:
				# Check if filename already loaded.
				if filename == row[1][:len(filename)]:
					# If so, set the copy number to 1.
					copyNumber = 1
					# Check if this is a copy already.
					if len(row[1]) > len(filename):
						if int(row[1][len(filename)+2:len(row[1])-1]) >= copyNumber:
							copyNumber = int(row[1][len(filename)+2:len(row[1])-1]) + 1
			if copyNumber > 0:
				filename = filename + " (" + str(copyNumber) + ")"
		# Hide the previous models bounding box.
		self.modelCollection.getCurrentModel().hideBox()
		# Load the model into the model collection.
		self.modelCollection.add(filename, filepath)
		# Add the filename to the list and set selected.
		self.add(filename, filename, filepath)	
		# Activate the remove button which was deactivated when there was no model.
		self.buttonRemove.set_sensitive(True)
		# Add actor to render view.
#		self.renderView.addActor(self.modelCollection.getCurrentModel().getActor())
		self.renderView.addActors(self.modelCollection.getCurrentModel().getAllActors())

		
		self.renderView.render()

	# Delete button callback.
	def callbackRemove(self, widget, data=None):
		model, treeiter = self.modelSelection.get_selected()
		self.remove(treeiter)

	# Name edited callback.
	def callbackEdited(self, cell, path, new_text, model):
		model[path][0] = new_text
		
	# Active state toggled callback.
	def callbackToggleChanged(self, cell, path, model):
		# Toggle active flag in model list.
		model[path][3] = not model[path][3]
		# Toggle active flag in model collection.
		self.modelCollection.getCurrentModel().setActive(model[path][3])
		# Console output.
		if self.console:
			if model[path][3] == True:
				self.console.addLine("Model " + model[path][0] + " activated.")
			else:
				self.console.addLine("Model " + model[path][0] + " deactivated.")

	# Selection changed callback.
	def onSelectionChanged(self, selection):
		# Hide the previous models bounding box actor.
		self.modelCollection.getCurrentModel().hideBox()
		model, treeiter = selection.get_selected()
		if treeiter != None:	# Make sure someting is selected.
			if self.console:
				self.console.addLine("Model " + model[treeiter][0] + " selected.")
			# Set current model in model collection.
			self.modelCollection.setCurrentModelId(model[treeiter][1])
			# Show bounding box.
			self.modelCollection.getCurrentModel().showBox()
			self.renderView.render()
			# Update the gui.
			self.guiUpdateFunction()
	
	# Disable buttons so models can only be loaded in first tab.
	def setSensitive(self, sensitive):
		self.buttonLoad.set_sensitive(sensitive)
		self.buttonRemove.set_sensitive(sensitive)



# Window for firmware upload. ##################################################
class firmwareDialog(gtk.Window):
	# Override init function.
	def __init__(self, settings):
		# Call super class init function.
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
		self.show()
		
		# Internalise settings.
		self.settings = settings
		
		# Main container.
		box = gtk.VBox()
		self.add(box)
		box.show()
#TODO: Rebuild with entry objects.		
		# Description.
		label = gtk.Label("Push the reset button on your controller board and press \"Flash firmware\"!")
		box.pack_start(label, expand=False, fill=False)
		label.show()
		
		# Table for the entries.
		table = gtk.Table()
		box.pack_start(table)
		table.show()
		# Avrdude options.
		# MCU.
		labelMCU = gtk.Label('MCU')
		table.attach(labelMCU, 0,1,0,1)
		labelMCU.show()
		self.entryMCU = gtk.Entry()
		self.entryMCU.set_text(self.settings['avrdudeMCU'].value)
		table.attach(self.entryMCU, 1,2,0,1)
		self.entryMCU.show()
		# Programmer.
		labelProgrammer = gtk.Label('Programmer')
		table.attach(labelProgrammer, 0,1,1,2)
		labelProgrammer.show()
		self.entryProgrammer = gtk.Entry()
		self.entryProgrammer.set_text(self.settings['avrdudeProgrammer'].value)
		table.attach(self.entryProgrammer, 1,2,1,2)
		self.entryProgrammer.show()
		# Port.
		labelPort = gtk.Label('Port')
		table.attach(labelPort, 0,1,2,3)
		labelPort.show()
		self.entryPort = gtk.Entry()
		self.entryPort.set_text(self.settings['avrdudePort'].value)
		table.attach(self.entryPort, 1,2,2,3)
		self.entryPort.show()
		# Baud.
		labelBaud = gtk.Label('Baud')
		table.attach(labelBaud, 0,1,3,4)
		labelBaud.show()
		self.entryBaud = gtk.Entry()
		self.entryBaud.set_text(self.settings['avrdudeBaud'].value)
		table.attach(self.entryBaud, 1,2,3,4)
		self.entryBaud.show()
		# Options.
		labelOptions = gtk.Label('Options, space separated')
		table.attach(labelOptions, 0,1,4,5)
		labelOptions.show()
		self.entryOptions = gtk.Entry()
		self.entryOptions.set_text(self.settings['avrdudeOptions'].value)
		table.attach(self.entryOptions, 1,2,4,5)
		self.entryOptions.show()
		# File path.
		labelPath = gtk.Label('File path')
		table.attach(labelPath, 0,1,5,6)
		labelPath.show()
		self.entryPath = gtk.Entry()
		self.entryPath.set_text(self.settings['avrdudePath'].value)
		table.attach(self.entryPath, 1,2,5,6)
		self.entryPath.show()
		

		# Set callback connected to Enter key and focus leave.
		#self.entry.connect("activate", self.entryCallback, entry)
		self.entryMCU.connect("key-press-event", self.entryCallback, entry)
		self.entryProgrammer.connect("key-press-event", self.entryCallback, entry)
		self.entryPort.connect("key-press-event", self.entryCallback, entry)
		self.entryBaud.connect("key-press-event", self.entryCallback, entry)
		self.entryOptions.connect("key-press-event", self.entryCallback, entry)
		self.entryPath.connect("key-press-event", self.entryCallback, entry)
		
		# Buttons.
		boxButtons = gtk.HBox()
		box.pack_start(boxButtons, expand=False, fill=False)
		boxButtons.show()
		# Flash button.
		buttonFlash = gtk.Button("Flash firmware")
		boxButtons.pack_start(buttonFlash, expand=False, fill=False)
		buttonFlash.connect("clicked", self.callbackFlash)
		buttonFlash.show()
		# Back to defaults button.
		buttonDefaults = gtk.Button("Restore defaults")
		boxButtons.pack_start(buttonDefaults, expand=False, fill=False)
		buttonDefaults.connect("clicked", self.callbackDefaults)
		buttonDefaults.show()
		# Close button.
		buttonClose = gtk.Button("Close")
		boxButtons.pack_start(buttonClose, expand=False, fill=False)
		buttonClose.connect("clicked", self.callbackClose)
		buttonClose.show()

	def entryCallback(self, widget, event, entry):
		# Only fire on Return or Tab event.
		if event.keyval == gtk.keysyms.Tab or event.keyval == gtk.keysyms.Return:
			# Process options.
			# Extract additional options into list and eliminate '-' from options.
			optionList = self.entryOptions.get_text().replace('-','')
			# Split into option list.
			optionList = optionList.split(' ')
			# Add '-' to options. This way users can input options with and without '-'.
			optionList = ['-' + option for option in optionList]
			# Concatenate into string for display.
			optionString = ''
			for option in optionList:
				optionString = optionString + option + ' '
			# Remove trailing space.
			optionString = optionString[:-1]
			self.entryOptions.set_text(optionString)
		
			# Take the entry texts and put them into settings.
			self.settings['avrdudeSettings'].value = [self.entryMCU.get_text(), self.entryProgrammer.get_text(), self.entryPort.get_text(), self.entryBaud.get_text(), optionString, self.entryPath.get_text()]

	def callbackFlash(self, widget, data=None):
		# Create avrdude commandline string.
		avrdudeString = 'avrdude -p ' + self.entryMCU.get_text() + ' -P ' + self.entryPort.get_text() + ' -c ' + self.entryProgrammer.get_text() + ' ' + self.entryOptions.get_text() + ' -b ' + self.entryBaud.get_text() + ' -U flash:w:' + self.entryPath.get_text()
		print avrdudeString
		# Extract additional options into list and eliminate '-' from options.
		optionList = self.entryOptions.get_text().replace('-','')
		# Split into option list.
		optionList = optionList.split(' ')
		# Add '-' to options. This way users can input options with and without '-'.
		optionList = ['-' + option for option in optionList]
		# Call avrdude and get it's output.
		try:
			# Call avrdude. No spaces in options!
			avrdudeOutput = subprocess.check_output(['avrdude', '-p' + self.entryMCU.get_text(), '-P' + self.entryPort.get_text(), '-c' + self.entryProgrammer.get_text(), '-b' + self.entryBaud.get_text(), '-U flash:w:' + self.entryPath.get_text()] + optionList)
		except:
			print 'foo'

	def callbackDefaults(self, widget, data=None):
		# Get default settings.
		self.settings['avrdudeSettings'].value = self.settings['avrdudeSettingsDefault'].value
		# Set text entries.
		self.entryMCU.set_text(self.settings['avrdudeSettings'].value[0])
		self.entryProgrammer.set_text(self.settings['avrdudeSettings'].value[1])
		self.entryPort.set_text(self.settings['avrdudeSettings'].value[2])
		self.entryBaud.set_text(self.settings['avrdudeSettings'].value[3])
		self.entryOptions.set_text(self.settings['avrdudeSettings'].value[4])
		self.entryPath.set_text(self.settings['avrdudeSettings'].value[5])

	def callbackClose(self, widget, data=None):
		self.destroy()



# Settings window. #############################################################
# Define a window for all the settings that are related to the printer.

class dialogSettings(gtk.Window):
	# Override init function.
	def __init__(self, settings):
		# Call super class init function.
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
		self.show()
		
		# Internalise settings.
		self.settings = settings
		
		# Save settings in case of cancelling.
		self.settingsBackup = settings
		
		# Vertical box for settings and bottom buttons.
		self.boxMain = gtk.VBox()
		self.add(self.boxMain)
		self.boxMain.show()
		
		# Horizontal box for columns.
		self.boxSettings = gtk.HBox()
		self.boxMain.pack_start(self.boxSettings)
		self.boxSettings.show()

		# Vertical box for column 1.
		self.boxCol1 = gtk.VBox()
		self.boxSettings.pack_start(self.boxCol1)
		self.boxCol1.show()
		
		# Frame for serial settings.
		self.frameSerial = gtk.Frame('Serial communication')
		self.boxCol1.pack_start(self.frameSerial)
		self.frameSerial.show()
		self.boxSerial = gtk.VBox()
		self.frameSerial.add(self.boxSerial)
		self.boxSerial.show()
		# Add entries.
		# Port.
		self.entryPort = entry('Port', self.settings)
		self.boxSerial.pack_start(self.entryPort)
		self.entryPort.show()
		# Baud rate.
		self.entryBaud = entry('Baud rate', self.settings)
		self.boxSerial.pack_start(self.entryBaud)
		self.entryBaud.show()
		# Test button and output for serial communication.
		# Box for button and text output.
		self.boxSerialTest = gtk.HBox()
		self.boxSerial.pack_start(self.boxSerialTest)
		self.boxSerialTest.show()
		# Button.
		self.buttonSerialTest = gtk.Button("Test connection")
		self.boxSerialTest.pack_start(self.buttonSerialTest, expand=False, fill=False)
		self.buttonSerialTest.connect("clicked", self.callbackSerialTest)
		self.buttonSerialTest.show()
		# Text entry to show connection test result.
		self.textOutputSerialTest = gtk.Entry()
		self.boxSerialTest.pack_start(self.textOutputSerialTest, expand=False, fill=False)
		self.textOutputSerialTest.show()
		
		
		# Frame for build volume settings.
		self.frameBuildVolume = gtk.Frame('Build volume')
		self.boxCol1.pack_start(self.frameBuildVolume)
		self.frameBuildVolume.show()
		self.boxBuildVolume = gtk.VBox()
		self.frameBuildVolume.add(self.boxBuildVolume)
		self.boxBuildVolume.show()
		# Add entries.
		self.entryBuildSizeX= entry('Build size X', self.settings)
		self.boxBuildVolume.pack_start(self.entryBuildSizeX)
		self.entryBuildSizeX.show()
		self.entryBuildSizeY= entry('Build size Y', self.settings)
		self.boxBuildVolume.pack_start(self.entryBuildSizeY)
		self.entryBuildSizeY.show()
		self.entryBuildSizeZ= entry('Build size Z', self.settings)
		self.boxBuildVolume.pack_start(self.entryBuildSizeZ)
		self.entryBuildSizeZ.show()
		
		# Frame for projector settings.
		self.frameProjector = gtk.Frame('Projector')
		self.boxCol1.pack_start(self.frameProjector, expand=False, fill=False)
		self.frameProjector.show()
		self.boxProjector = gtk.VBox()
		self.frameProjector.add(self.boxProjector)
		self.boxProjector.show()
		self.entryProjectorSizeX= entry('Projector size X', self.settings)
		self.boxProjector.pack_start(self.entryProjectorSizeX, expand=False, fill=False)
		self.entryProjectorSizeX.show()
		self.entryProjectorSizeY= entry('Projector size Y', self.settings)
		self.boxProjector.pack_start(self.entryProjectorSizeY, expand=False, fill=False)
		self.entryProjectorSizeY.show()
		self.entryProjectorPositionX= entry('Projector position X', self.settings)
		self.boxProjector.pack_start(self.entryProjectorPositionX, expand=False, fill=False)
		self.entryProjectorPositionX.show()
		self.entryProjectorPositionY= entry('Projector position Y', self.settings)
		self.boxProjector.pack_start(self.entryProjectorPositionY, expand=False, fill=False)
		self.entryProjectorPositionY.show()
		
		# Vertical box for column 2.
		self.boxCol2 = gtk.VBox()
		self.boxSettings.pack_start(self.boxCol2)
		self.boxCol2.show()
		
		# Frame for Tilt stepper.
		self.frameTiltStepper = gtk.Frame('Tilt stepper')
		self.boxCol2.pack_start(self.frameTiltStepper, expand=False, fill=False)
		self.frameTiltStepper.show()
		self.boxTilt = gtk.VBox()
		self.frameTiltStepper.add(self.boxTilt)
		self.boxTilt.show()
		# Entries.
		# Resolution.
		self.entryTiltStepsPerDeg = entry('Tilt steps / °', self.settings)
		self.boxTilt.pack_start(self.entryTiltStepsPerDeg, expand=False, fill=False)
		self.entryTiltStepsPerDeg.show()
		# Tilt angle.
		self.entryTiltAngle = entry('Tilt angle', self.settings)
		self.boxTilt.pack_start(self.entryTiltAngle, expand=False, fill=False)
		self.entryTiltAngle.show()
		# Tilt speed.
		self.entryTiltSpeed = entry('Tilt speed', self.settings)
		self.boxTilt.pack_start(self.entryTiltSpeed, expand=False, fill=False)
		self.entryTiltSpeed.show()
		
		# Frame for Tilt stepper.
		self.frameBuildStepper = gtk.Frame('Build platform stepper')
		self.boxCol2.pack_start(self.frameBuildStepper, expand=False, fill=False)
		self.frameBuildStepper.show()
		self.boxBuildStepper = gtk.VBox()
		self.frameBuildStepper.add(self.boxBuildStepper)
		self.boxBuildStepper.show()
		# Entries.
		# Resolution.
		self.entryBuildStepsPerMm = entry('Build steps / mm', self.settings)
		self.boxBuildStepper.pack_start(self.entryBuildStepsPerMm, expand=False, fill=False)
		self.entryBuildStepsPerMm.show()
		# Ramp slope.
		self.entryBuildRampSlope = entry('Ramp slope', self.settings)
		self.boxBuildStepper.pack_start(self.entryBuildRampSlope, expand=False, fill=False)
		self.entryBuildRampSlope.show()
		# Tilt speed.
		self.entryBuildSpeed = entry('Build platform speed', self.settings)
		self.boxBuildStepper.pack_start(self.entryBuildSpeed, expand=False, fill=False)
		self.entryBuildSpeed.show()
		
		# Horizontal box for buttons.
		self.boxButtons = gtk.HBox()
		self.boxMain.pack_start(self.boxButtons, expand=False, fill=False)
		self.boxButtons.show()
		
		# Close button.
		self.buttonClose = gtk.Button("Close")
		self.boxButtons.pack_end(self.buttonClose, expand=False, fill=False)
		self.buttonClose.connect("clicked", self.callbackClose)
		self.buttonClose.show()
		
		# Cancel button.
		self.buttonCancel = gtk.Button("Cancel")
		self.boxButtons.pack_end(self.buttonCancel, expand=False, fill=False)
		self.buttonCancel.connect("clicked", self.callbackCancel)
		self.buttonCancel.show()
		
		# Restore defaults button.
		self.buttonDefaults = gtk.Button("Load defaults")
		self.boxButtons.pack_end(self.buttonDefaults, expand=False, fill=False)
		self.buttonDefaults.connect("clicked", self.callbackDefaults)
		self.buttonDefaults.show()

	
	# Serial test function.
	def callbackSerialTest(self, widget, data=None):
		# TODO
		pass
	
	# Defaults function.
	def callbackDefaults(self, widget, data=None):
		# Load default settings.
		self.settings.loadDefaults()
		
	# Cancel function.
	def callbackCancel(self, widget, data=None):
		# Restore values.
		self.settings = self.settingsBackup
		# Close without saving.
		self.destroy()

	# Destroy function.
	def callbackClose(self, widget, data=None):
		# Close and reopen serial if it is open.
		# TODO
		# Close.
		self.destroy()


# Output console. ##############################################################
# We define the console view and its text buffer 
# separately. This way we can have multiple views that share
# the same text buffer on different tabs...

class consoleText(gtk.TextBuffer):
	# Override init function.
	def __init__(self):
		gtk.TextBuffer.__init__(self)
	# Add text method.
	def addLine(self, string):
		self.insert(self.get_end_iter(),"\n"+string)	


# Creates a text viewer window that automatically scrolls down on new entries.
class consoleView(gtk.Frame):#ScrolledWindow):
	# Override init function.
	def __init__(self, textBuffer):
		gtk.Frame.__init__(self)
		self.show()
		# Create box for content.
		self.box = gtk.VBox()
		self.add(self.box)
		self.box.show()
		
		# Create the scrolled window.
		self.scrolledWindow = gtk.ScrolledWindow()
		self.scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		self.box.pack_start(self.scrolledWindow, expand=True, fill=True, padding=5)
		self.scrolledWindow.show()
		# Text view.
		self.textViewConsole = gtk.TextView(buffer=textBuffer)
		self.textViewConsole.set_editable(False)
		self.textViewConsole.set_wrap_mode(gtk.WRAP_WORD)
		self.scrolledWindow.add(self.textViewConsole)
		self.textViewConsole.show()
		# Get text buffer to write to.
#		self.textBuffer = self.textViewConsole.get_buffer()	
		# Insert start up message.
#		self.textBuffer.insert(self.textBuffer.get_end_iter(),"Monkeyprint " + "VERSION")
		# Get adjustment object to rescroll to bottom.
		self.vAdjustment = self.textViewConsole.get_vadjustment()
		# Connect changed signal to rescroll function.
		self.vAdjustment.connect('changed', lambda a, s=self.scrolledWindow: self.rescroll(a,s))

	# Rescroll to bottom if text added.
	def rescroll(self, adj, scroll):
		adj.set_value(adj.upper-adj.page_size)
		scroll.set_vadjustment(adj)

