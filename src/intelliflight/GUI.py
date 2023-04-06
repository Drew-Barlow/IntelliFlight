import csv
import json
from intelliflight.models.bayes_net import Bayes_Net
import tkinter
import tkintermapview
import customtkinter
from tkcalendar import Calendar
from tkinter.filedialog import askopenfilename
from tkinter import messagebox
from pathlib import Path

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")


root_dir = Path(__file__).parent.parent.parent


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.bayes = Bayes_Net()
        self.title("IntelliFlight")
        self.geometry("1920×1080")

        self.partitionCount = None
        self.kvalueCount = None
        self.kFractionCount = None
        self.originMarkerList = []
        self.destMarkerList = []

        self.grid_rowconfigure((0), weight=1)
        self.grid_columnconfigure((0), weight=1)

        self.tabview = customtkinter.CTkTabview(self, width=250)
        self.tabview.grid(row=0, column=0, sticky="nsew")
        self.tabview.add("Train")
        self.tabview.add("Predict")
        self.tabview.tab("Train").grid_columnconfigure((0, 1), weight=1)
        self.tabview.tab("Train").grid_rowconfigure((0, 1), weight=1)
        self.tabview.tab("Predict").grid_columnconfigure((0), weight=1)
        self.tabview.tab("Predict").grid_rowconfigure((0, 1), weight=1)

        # TRAINING TAB
        #################################################################

        # Welcome
        self.trainingWelcomeMsg = customtkinter.CTkLabel(self.tabview.tab(
            "Train"), text="Welcome to the IntelliFlight model training tab. \nYou have the option of training the model with new data or import an existing model.", font=("Ariel", 18))
        self.trainingWelcomeMsg.grid(row=0, column=0)

        # Set input frame
        self.inputFrame = customtkinter.CTkFrame(self.tabview.tab("Train"))
        self.inputFrame.grid(row=1, column=0, pady=20, padx=20, sticky='nsew')

        # Set new input tab
        self.fileTab = customtkinter.CTkTabview(self.inputFrame, width=250)
        self.fileTab.grid(row=0, column=0, pady=20, padx=20, sticky='nsew')
        self.fileTab.add("Train new model")
        self.fileTab.add("Import existing model")
        self.fileTab.tab("Train new model").grid_columnconfigure(
            (0, 1), weight=1)

        # NEW MODEL TAB
        # Set training data input text
        self.inputLabel = customtkinter.CTkLabel(self.fileTab.tab(
            "Train new model"), text="Input the file path for the training data:")
        self.inputLabel.grid(row=0, column=0, pady=20)

        # Set training data input button
        self.inputButton = customtkinter.CTkButton(self.fileTab.tab(
            "Train new model"), text="Input training data", command=self.inputButton_callback)
        self.inputButton.grid(row=0, column=1, pady=20, padx=20)
        self.trainingCheckbox = customtkinter.CTkCheckBox(
            self.fileTab.tab("Train new model"), text="")
        self.trainingCheckbox.grid(row=0, column=2, padx=(73, 0))

        # Set partition count text
        self.partitionLabel = customtkinter.CTkLabel(self.fileTab.tab(
            "Train new model"), text="Number of partitions for validation and testing:")
        self.partitionLabel.grid(row=1, column=0, pady=20)

        # Set partition count input slider
        self.sliderP = customtkinter.CTkSlider(self.fileTab.tab(
            "Train new model"), from_=3, to=10, number_of_steps=7, command=self.sliderP_callback)
        self.sliderP.grid(row=1, column=1, pady=30, padx=20)
        self.sliderP.set(3)
        self.partitionOutput = customtkinter.CTkEntry(
            self.fileTab.tab("Train new model"), width=37, height=30)
        self.partitionOutput.grid(row=1, column=2)

        # Set k value increment text
        self.kValueLabel = customtkinter.CTkLabel(self.fileTab.tab(
            "Train new model"), text="Offset between candidate values for thelaplace smoothing \nfactor k as a percentage of the dataset length:")
        self.kValueLabel.grid(row=2, column=0, pady=20, padx=10)

        # Set k value increment slider
        self.sliderK = customtkinter.CTkSlider(self.fileTab.tab(
            "Train new model"), from_=0.05, to=1, number_of_steps=19, command=self.sliderK_callback)
        self.sliderK.grid(row=2, column=1, pady=27, padx=20)
        self.sliderK.set(0.05)
        self.kValueOutput = customtkinter.CTkEntry(
            self.fileTab.tab("Train new model"), width=37, height=30)
        self.kValueOutput.grid(row=2, column=2)

        # Set max k value fraction text
        self.kFractionLabel = customtkinter.CTkLabel(self.fileTab.tab(
            "Train new model"), text="The laplace smoothing factor k is at most \nthis percentage of the dataset length:")
        self.kFractionLabel.grid(row=3, column=0, pady=20)

        # Set max k value fraction slider
        self.SliderF = customtkinter.CTkSlider(self.fileTab.tab(
            "Train new model"), from_=0, to=1, command=self.sliderF_callback)
        self.SliderF.grid(row=3, column=1, pady=25, padx=20)
        self.SliderF.set(0)
        self.kFractionOutput = customtkinter.CTkEntry(
            self.fileTab.tab("Train new model"), width=37, height=30)
        self.kFractionOutput.grid(row=3, column=2)

        # Set divider line
        self.line = customtkinter.CTkLabel(self.fileTab.tab(
            "Train new model"), text="________________________________________________________________________________________________________________________________________\n")
        self.line.grid(row=4, columnspan=3)

        # Set Run button
        self.runButton = customtkinter.CTkButton(self.fileTab.tab(
            "Train new model"), text='Run Model', command=self.runButton_callback)
        self.runButton.grid(row=5, column=0, sticky='w', padx=(20, 0))

        # Set k value print
        self.kValuePrint = customtkinter.CTkEntry(self.fileTab.tab(
            "Train new model"), placeholder_text="Model's k value")
        self.kValuePrint.grid(row=5, column=0, sticky='e')

        # Set accuracy print
        self.accuracyPrint = customtkinter.CTkEntry(self.fileTab.tab(
            "Train new model"), placeholder_text="Accuracy of model")
        self.accuracyPrint.grid(row=5, column=1, padx=(20, 0))

        # Set save model button
        self.saveButton = customtkinter.CTkButton(self.fileTab.tab(
            "Train new model"), text="Save", command=self.saveButton_callback)
        self.saveButton.grid(row=5, column=2, sticky='e', padx=(0, 20))
        #################################################################

        # IMPORT MODEL TAB
        #################################################################
        # Set existing model input text
        self.inputLabel = customtkinter.CTkLabel(self.fileTab.tab(
            "Import existing model"), text="Input the file path for the existing model:")
        self.inputLabel.grid(row=0, column=0, pady=20)

        # Set import button
        self.importFileButton = customtkinter.CTkButton(self.fileTab.tab(
            "Import existing model"), text="Import model file", command=self.importButton_callback)
        self.importFileButton.grid(row=0, column=1)

        # Set import checkbox
        self.importCheckbox = customtkinter.CTkCheckBox(
            self.fileTab.tab("Import existing model"), text="")
        self.importCheckbox.grid(row=0, column=2)

        """  # Set divider line
        self.line = customtkinter.CTkLabel(self.fileTab.tab(
            "Import existing model"), text="___________________________________________________________________________________________________________\n")
        self.line.grid(row=1, columnspan=3)

        # Set Run button
        self.runButton = customtkinter.CTkButton(self.fileTab.tab(
            "Import existing model"), text='Run Model', command=self.runButton_callback)
        self.runButton.grid(row=2, column=0)

        # Set k value print
        self.kValuePrint = customtkinter.CTkEntry(self.fileTab.tab(
            "Import existing model"), placeholder_text="Model's k value")
        self.kValuePrint.grid(row=2, column=1)

        # Set accuracy print
        self.accuracyPrint = customtkinter.CTkEntry(self.fileTab.tab(
            "Import existing model"), placeholder_text="Accuracy of model")
        self.accuracyPrint.grid(row=2, column=2) """
        ################################################################

        # PREDICT TAB
        #################################################################
        # welcome
        self.predictWelcomeMsg = customtkinter.CTkLabel(self.tabview.tab(
            "Predict"), text="Welcome to the IntelliFlight prediction tab. \nHere you can use the model to predict whether or not your flight will be delayed.", font=("Ariel", 18))
        self.predictWelcomeMsg.grid(row=0, column=0, columnspan=2)

        # Set map frame
        self.mapFrame = customtkinter.CTkFrame(self.tabview.tab("Predict"))
        self.mapFrame.grid(row=1, column=0, pady=20, padx=20, sticky='nsew')

        # Set map label
        self.mapLabel = customtkinter.CTkLabel(
            self.mapFrame, text="Use the map or drop down menus to choose your origin and\n destination airports:")
        self.mapLabel.grid(row=0, column=0, pady=20, padx=20)

        # Set map
        self.map = tkintermapview.TkinterMapView(
            self.mapFrame, width=300, height=300, corner_radius=0)
        self.map.grid(row=1, column=0)
        self.map.fit_bounding_box(
            (49.002494, -124.409591), (24.523096, -66.949895))

        # # Set map position with mouse click
        # self.map.add_right_click_menu_command(
        #     label="Select origin", command=self.addMapMarkerOrigin, pass_coords=True)
        # self.map.add_right_click_menu_command(
        #     label="Select destination", command=self.addMapMarkerDest, pass_coords=True)

        # Set origin airport option menu
        originOptionmenu_var = customtkinter.StringVar(
            value="Select origin airport")
        self.mapOriginOptionMenu = customtkinter.CTkOptionMenu(self.mapFrame, values=[
                                                               "test", "tests"], variable=originOptionmenu_var, command=self.originOptionMenu_callback)
        self.mapOriginOptionMenu.grid(
            row=2, column=0, padx=(20, 0), sticky='w')

        # Set destination airport option menu
        destOptionmenu_var = customtkinter.StringVar(
            value="Select destination airport")
        self.mapDestOptionMenu = customtkinter.CTkOptionMenu(self.mapFrame, values=[
                                                             "testing", "test"], variable=destOptionmenu_var, command=self.destOptionMenu_callback)
        self.mapDestOptionMenu.grid(row=2, column=0, padx=(0, 13), sticky='e')

        # Set airline option menu
        airlineOptionmenu_var = customtkinter.StringVar(
            value="Select airline name")
        self.airlineOptionMenu = customtkinter.CTkOptionMenu(self.mapFrame, values=[
                                                             "airline"], variable=airlineOptionmenu_var, command=self.airlineOptionMenu_callback)
        self.airlineOptionMenu.grid(row=2, column=1, padx=(0, 190), sticky='w')

        # Set calendar label
        self.calendarLabel = customtkinter.CTkLabel(
            self.mapFrame, text="Use the calender to set your departure date:")
        self.calendarLabel.grid(row=0, column=1, pady=20, padx=20)

        # Set calendar
        self.calendar = Calendar(
            self.mapFrame, selectmode='day', year=2023, month=4, day=1, borderwidth=5)
        self.calendar.grid(row=1, column=1, pady=20, padx=20, sticky='n')

        # Set departure date button
        self.setDepartDateButton = customtkinter.CTkButton(
            self.mapFrame, text="Set departure date", command=self.setDepartDateButton_callback)
        self.setDepartDateButton.grid(
            row=1, column=1, pady=20, padx=20, sticky='s')

        # Set departure time option menu
        departTimeOptionmenu_var = customtkinter.StringVar(
            value="Select departure time")
        self.departTimeOptionMenu = customtkinter.CTkOptionMenu(self.mapFrame, values=[
                                                                "time"], variable=departTimeOptionmenu_var, command=self.departTimeOptionMenu_callback)
        self.departTimeOptionMenu.grid(
            row=2, column=1, pady=20, padx=20, sticky='e')

        # Set divider line
        self.line = customtkinter.CTkLabel(
            self.mapFrame, text="______________________________________________________________________________________________________________________\n")
        self.line.grid(row=3, columnspan=3)

        # Set predict button
        self.predictButton = customtkinter.CTkButton(
            self.mapFrame, text="Run prediction", command=self.predictButton_callback)
        self.predictButton.grid(row=4, column=0, padx=20, pady=20, sticky='w')

        # Set prediction key print
        self.predictionKey = customtkinter.CTkEntry(
            self.mapFrame, placeholder_text="Type of prediction")
        self.predictionKey.grid(row=4, column=1, sticky='w')

        # Set key description
        self.keyDescription = customtkinter.CTkEntry(
            self.mapFrame, placeholder_text="Prediction description")
        self.keyDescription.grid(row=4, column=1, pady=20, padx=20, sticky='e')
        ################################################################

        # TRAINING TAB FUNCTIONS
        ################################################################
    def inputButton_callback(self):
        data_path = askopenfilename()
        if len(data_path) > 0:  # Didn't cancel
            print("Data file:", data_path)
            try:
                self.bayes = Bayes_Net()
                self.bayes.load_data(data_path)
                self.trainingCheckbox.select()
            except Exception as e:
                self.bayes = None
                self.trainingCheckbox.deselect()
                messagebox.showerror(
                    'Error', message="Could not load data file")
                print(e)

    def sliderP_callback(self, value):
        value = self.sliderP.get()
        self.partitionCount = int(value)
        self.partitionOutput.delete(0, 10)
        self.partitionOutput.insert(0, str(value))

    def sliderK_callback(self, value):
        value = self.sliderK.get()
        self.kvalueCount = value
        self.kValueOutput.delete(0, 10)
        self.kValueOutput.insert(0, str(value))

    def sliderF_callback(self, value):
        value = self.SliderF.get()
        self.kFractionCount = value
        self.kFractionOutput.delete(0, 10)
        self.kFractionOutput.insert(0, str(value))

    def importButton_callback(self):
        data_path = askopenfilename()
        if len(data_path) > 0:  # Didn't cancel
            print("Data file:", data_path)
            try:
                self.bayes = Bayes_Net(data_path)
                self.importCheckbox.select()
                self.populate_prediction_screen()
            except Exception as e:
                self.bayes = None
                self.importCheckbox.deselect()
                messagebox.showerror(
                    'Error', message="Could not load data file")
                print(e)
                raise e

    def saveButton_callback(self):
        if self.bayes.p_tables.is_fit():
            if messagebox.askyesno('Save model', message="Would you like to save this model?") is True:
                self.bayes.export_parameters()
        else:
            messagebox.showerror(
                'Error', message="You must train the model first")

    def runButton_callback(self):
        if not self.bayes.dataset.data_loaded():
            messagebox.showerror('Error', message="You most input a dataset")
        elif self.partitionCount is not None and self.kvalueCount is not None and self.kFractionCount is not None:
            kvalue, accuracy = self.bayes.train_model(
                self.partitionCount, self.kvalueCount, self.kFractionCount)
            self.kValuePrint.delete(0, 10)
            self.kValuePrint.insert(0, str(kvalue))
            self.accuracyPrint.delete(0, 10)
            self.accuracyPrint.insert(0, str(accuracy))
            self.populate_prediction_screen()
        else:
            messagebox.showerror('Error', message="Slider not set")

    def populate_prediction_screen(self):
        # Clear map
        self.map.delete_all_marker()
        self.airport_markers = []
        # Get airport codes
        seen_airports = self.bayes.key_meta.get_seen_airports()
        # Get airport mapping data
        airport_map_path = root_dir / 'data' / 'maps' / 'airport_mappings.json'
        mappings = json.load(airport_map_path.open())

        # Filter for airports in training data
        mappings_pruned = [
            entry
            for entry in mappings
            if entry['bts_id'] in seen_airports
        ]
        # Store airports in variable
        self.airports: list[tkintermapview.map_widget.CanvasPositionMarker] = mappings_pruned
        menu_vals = []  # Strings for dropdown menus
        for airport in self.airports:
            # Make string from airport properties
            desc_split = airport["desc"].split(": ", maxsplit=1)
            name_str = f'{desc_split[0]}:\n{desc_split[1]}\n({airport["bts_id"]})'
            # Add marker to list and map
            self.airport_markers.append(self.map.set_marker(
                float(airport['location']['lat']),
                float(airport['location']['lon']),
                name_str,
                command=self.pin_click_handler
            ))
            # Replace '\n' with ' ' and add to menu_vals
            menu_vals.append(' '.join(name_str.split('\n')))

        # Sort alphabetically
        menu_vals.sort()

        # Set dropdown values
        self.mapOriginOptionMenu.configure(values=menu_vals)
        self.mapDestOptionMenu.configure(values=menu_vals)

    def pin_click_handler(self, marker: tkintermapview.map_widget.CanvasPositionMarker):
        # Replace '\n' with ' ' since dropdown uses spaces while pins use newlines
        name_str = ' '.join(marker.text.split('\n'))
        # TODO: Replace this with custom dialog box
        is_src = messagebox.askyesnocancel(
            'Source or Destination?', message="Is this the source (yes) or destination (no)?")

        if is_src == True:
            self.mapOriginOptionMenu.set(name_str)

        elif is_src == False:
            self.mapDestOptionMenu.set(name_str)

        else:  # None (cancel)
            pass

    # PREDICTION TAB FUNCTIONS
    ################################################################

    def originOptionMenu_callback(self, test):
        print(test)
        pass

    def destOptionMenu_callback(self):
        pass

    def setDepartDateButton_callback(self):
        print(self.calendar.get_date())

    def airlineOptionMenu_callback(self):
        pass

    def departTimeOptionMenu_callback(self):
        pass

    def predictButton_callback(self):
        pass

    def addMapMarkerOrigin(self, coords):
        print("Add origin:", coords)
        for marker in self.originMarkerList:
            marker.delete()
        originMarker = self.map.set_marker(coords[0], coords[1], text="Origin")
        self.originMarkerList.append(originMarker)

    def addMapMarkerDest(self, coords):
        print("Add destination", coords)
        for marker in self.destMarkerList:
            marker.delete()
        destMarker = self.map.set_marker(coords[0], coords[1], text="Dest")
        self.destMarkerList.append(destMarker)


if __name__ == "__main__":
    app = App()
    app.mainloop()
