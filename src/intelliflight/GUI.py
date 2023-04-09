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
from datetime import date, datetime, timedelta

from intelliflight.util import datautil, nws_manager

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")


root_dir = Path(__file__).parent.parent.parent


class DialogBox(customtkinter.CTkToplevel):
    def __init__(self, app, pin: tkintermapview.map_widget.CanvasPositionMarker):
        '''Dialog box to set src or dst airport when clicking a map pin.

        Positional arguments:

        - app -- the `App` instance of the main application. This object's
                 src/dst data will be modified.
        - pin -- the map pin object that was clicked, which is passed to the
                 map pin click handler (`command`).
        '''
        super().__init__()

        # Store GUI reference and airport info in member variables for access
        # by callbacks

        self.main_gui = app

        # Extract airport name data from pin object.
        # Replace '\n' with ' ' since dropdown uses spaces while pins use newlines
        self.airport_name_str = ' '.join(pin.text.split('\n'))

        self.geometry("600x200")
        self.title("Origin or Destination?")
        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grab_set()

        self.label = customtkinter.CTkLabel(
            self, text="Select if this airport is your origin or destination:")
        self.label.grid(row=0, column=0, padx=20, pady=20)

        self.dialogFrame = customtkinter.CTkFrame(self)
        self.dialogFrame.grid(row=1, column=0, padx=20)

        # The command callback functions on these buttons do not pass any arguments.
        # Use callback functions below to interact with the `App` class
        self.setOriginButton = customtkinter.CTkButton(
            self.dialogFrame, text="Origin", command=self.origin_callback)
        self.setOriginButton.grid(row=0, column=0, padx=20, pady=20)

        self.setDestButton = customtkinter.CTkButton(
            self.dialogFrame, text="Destination", command=self.destination_callback)
        self.setDestButton.grid(row=0, column=1, padx=20, pady=20)

        self.cancelButton = customtkinter.CTkButton(
            self.dialogFrame, text='Cancel', command=self.destroy)
        self.cancelButton.grid(row=0, column=2, padx=20, pady=20)

    def origin_callback(self):
        '''Set origin airport in App'''
        self.main_gui.originButton_callback(self.airport_name_str)
        self.destroy()

    def destination_callback(self):
        '''Set destination airport in App'''
        self.main_gui.destButton_callback(self.airport_name_str)
        self.destroy()


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
        self.dialogBoxWindow = None

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
        self.inputLabel.grid(row=0, column=0, pady=20, padx=20)

        # Set import button
        self.importFileButton = customtkinter.CTkButton(self.fileTab.tab(
            "Import existing model"), text="Import model file", command=self.importButton_callback)
        self.importFileButton.grid(row=0, column=1, padx=20)

        # Set import checkbox
        self.importCheckbox = customtkinter.CTkCheckBox(
            self.fileTab.tab("Import existing model"), text="")
        self.importCheckbox.grid(row=0, column=2, padx=20)
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
        self.mapLabel.grid(row=2, column=0, pady=20, padx=20)

        # Set map
        self.map = tkintermapview.TkinterMapView(
            self.mapFrame, width=500, height=500, corner_radius=0)
        self.map.grid(row=1, column=0, sticky='nsew', columnspan=3)
        self.map.set_position(42.3314, -83.0458)
        self.map.set_zoom(9)

        # Set origin airport option menu
        originOptionmenu_var = customtkinter.StringVar(
            value="Select origin airport")
        self.mapOriginOptionMenu = customtkinter.CTkOptionMenu(self.mapFrame, values=[
        ], variable=originOptionmenu_var)
        self.mapOriginOptionMenu.grid(
            row=3, column=0, padx=20, pady=20, sticky='n')

        # Set destination airport option menu
        destOptionmenu_var = customtkinter.StringVar(
            value="Select destination airport")
        self.mapDestOptionMenu = customtkinter.CTkOptionMenu(self.mapFrame, values=[
        ], variable=destOptionmenu_var)
        self.mapDestOptionMenu.grid(row=3, column=0, padx=20, pady=20)

        # Set airline option label
        self.airlineLabel = customtkinter.CTkLabel(
            self.mapFrame, text="Use these drop down menus to select the airline you are flying with and\n your departure time:")
        self.airlineLabel.grid(row=2, column=1, pady=20, padx=20)

        # Set airline option menu
        airlineOptionmenu_var = customtkinter.StringVar(
            value="Select airline name")
        self.airlineOptionMenu = customtkinter.CTkOptionMenu(self.mapFrame, values=[
        ], variable=airlineOptionmenu_var)
        self.airlineOptionMenu.grid(
            row=3, column=1, padx=20, pady=20, sticky='n')

        # Set calendar label
        self.calendarLabel = customtkinter.CTkLabel(
            self.mapFrame, text="Use the calender to set your departure date:\n")
        self.calendarLabel.grid(row=2, column=2, pady=20, padx=20)

        # Set calendar
        self.today = date.today()
        self.calendar = Calendar(
            self.mapFrame, selectmode='day', mindate=self.today, maxdate=date.today() + timedelta(days=7), borderwidth=5)
        self.calendar.grid(row=3, column=2, padx=20)

        # Set departure time option menu
        departTimeOptionmenu_var = customtkinter.StringVar(
            value="Select departure time")
        self.departTimeOptionMenu = customtkinter.CTkOptionMenu(self.mapFrame, values=[
            '00:00', '00:30',
            '01:00', '01:30',
            '02:00', '02:30',
            '03:00', '03:30',
            '04:00', '04:30',
            '05:00', '05:30',
            '06:00', '06:30',
            '07:00', '07:30',
            '08:00', '08:30',
            '09:00', '09:30',
            '10:00', '10:30',
            '11:00', '11:30',
            '12:00', '12:30',
            '13:00', '13:30',
            '14:00', '14:30',
            '15:00', '15:30',
            '16:00', '16:30',
            '17:00', '17:30',
            '18:00', '18:30',
            '19:00', '19:30',
            '20:00', '20:30',
            '21:00', '21:30',
            '22:00', '22:30',
            '23:00', '23:30',
        ], variable=departTimeOptionmenu_var)
        self.departTimeOptionMenu.grid(
            row=3, column=1, pady=20, padx=20)

        # Set divider line
        self.line = customtkinter.CTkLabel(
            self.mapFrame, text="___________________________________________________________________________________________________________________________________________________________________________________________________________________________________\n")
        self.line.grid(row=4, columnspan=3)

        # Set predict button
        self.predictButton = customtkinter.CTkButton(
            self.mapFrame, text="Run prediction", command=self.predictButton_callback)
        self.predictButton.grid(row=5, column=0, padx=20)

        # Set prediction label
        self.preditionLabel = customtkinter.CTkLabel(
            self.mapFrame, text="This is what the model has predicted:")
        self.preditionLabel.grid(row=5, column=1)

        # Set prediction key print
        self.predictionKey = customtkinter.CTkEntry(
            self.mapFrame, placeholder_text="Type of prediction", width=210)
        self.predictionKey.grid(row=6, column=1, padx=20, pady=(0, 20))

        # Set prediction label
        self.confidenceLabel = customtkinter.CTkLabel(
            self.mapFrame, text="This is the confidence of the model:")
        self.confidenceLabel.grid(row=5, column=2)

        # Set key description
        self.keyDescription = customtkinter.CTkEntry(
            self.mapFrame, placeholder_text="Prediction confidence")
        self.keyDescription.grid(row=6, column=2, padx=20, pady=(0, 20))
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
            except BufferError as e:
                self.bayes = None
                self.trainingCheckbox.deselect()
                messagebox.showerror(
                    'Error', 'Training data file is empty or malformed.')
                print(e)
            except Exception as e:
                self.bayes = None
                self.trainingCheckbox.deselect()
                messagebox.showerror(
                    'Error', message="Could not load data file")
                print(e)

    def sliderP_callback(self, value):
        value = self.sliderP.get()
        self.partitionCount = int(value)
        self.partitionOutput.delete(0, 500)
        self.partitionOutput.insert(0, str(value))

    def sliderK_callback(self, value):
        value = self.sliderK.get()
        self.kvalueCount = value
        self.kValueOutput.delete(0, 500)
        self.kValueOutput.insert(0, str(value))

    def sliderF_callback(self, value):
        value = self.SliderF.get()
        self.kFractionCount = value
        self.kFractionOutput.delete(0, 500)
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
            self.kValuePrint.delete(0, 500)
            self.kValuePrint.insert(0, str(kvalue))
            self.accuracyPrint.delete(0, 500)
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
                command=self.open_DialogBox
            ))
            # Replace '\n' with ' ' and add to menu_vals
            menu_vals.append(' '.join(name_str.split('\n')))

        # Sort alphabetically
        menu_vals.sort()

        # Set dropdown values
        self.mapOriginOptionMenu.configure(values=menu_vals)
        self.mapDestOptionMenu.configure(values=menu_vals)

        # AIRLINES
        # Get airline codes
        seen_airlines = self.bayes.key_meta.get_seen_carriers()
        # Get airline mapping data
        airline_map_path = root_dir / 'data' / 'maps' / 'L_UNIQUE_CARRIERS.csv'
        mappings = csv.DictReader(airline_map_path.open())
        # Generate 'description@code' strings for airlines in model
        airline_mappings_pruned = [
            entry
            for entry in mappings
            if entry['Code'] in seen_airlines
        ]
        airline_menu_vals = []
        for airline in airline_mappings_pruned:
            # Make string from airline properties
            name_str = f'{airline["Description"]} ({airline["Code"]})'
            airline_menu_vals.append(name_str)
        # Sort alphabetically
        airline_menu_vals.sort()
        # Set dropdown values
        self.airlineOptionMenu.configure(values=airline_menu_vals)

    """ def pin_click_handler(self, marker: tkintermapview.map_widget.CanvasPositionMarker):
        # Replace '\n' with ' ' since dropdown uses spaces while pins use newlines
        name_str = ' '.join(marker.text.split('\n'))
        # TODO: Replace this with custom dialog box
        self.open_DialogBox()

        is_src = messagebox.askyesnocancel(
            'Source or Destination?', message="Is this the source (yes) or destination (no)?")

        if is_src == True:
            self.mapOriginOptionMenu.set(name_str)

        elif is_src == False:
            self.mapDestOptionMenu.set(name_str)

        else:  # None (cancel)
            pass """

    def open_DialogBox(self, marker: tkintermapview.map_widget.CanvasPositionMarker):
        '''Create a DialogBox, passing it this App instance and the map pin'''
        if self.dialogBoxWindow is None or not self.dialogBoxWindow.winfo_exists():
            self.dialogBoxWindow = DialogBox(self, marker)
            self.dialogBoxWindow.focus()
        else:
            self.dialogBoxWindow.focus()

    # These methods are invoked by the DialogBox class and used to set
    # src/dst airport
    def originButton_callback(self, name_str: str):
        self.mapOriginOptionMenu.set(name_str)

    def destButton_callback(self, name_str: str):
        self.mapDestOptionMenu.set(name_str)

    # PREDICTION TAB FUNCTIONS
    ################################################################

    def predictButton_callback(self):
        src_airport_str = self.mapOriginOptionMenu.get()
        dst_airport_str = self.mapDestOptionMenu.get()
        airline_str = self.airlineOptionMenu.get()
        dep_time = self.departTimeOptionMenu.get()

        if any([
            src_airport_str.lower() == 'select origin airport',
            dst_airport_str.lower() == 'select destination airport',
            airline_str.lower() == 'select airline name',
            dep_time.lower() == 'select departure time'
        ]):
            messagebox.showerror(
                'Error', 'All prediction fields must have a value.')

        # [Month, Day, Year]
        date_arr: list[str] = [i for i in self.calendar.get_date().split('/')]
        date_arr[0] = date_arr[0].rjust(2, '0')
        date_arr[1] = date_arr[1].rjust(2, '0')
        date_arr[2] = f'20{date_arr[2]}'
        iso_timestamp = \
            f'{date_arr[2]}-{date_arr[0]}-{date_arr[1]}T{dep_time}:00Z'
        airline_code = airline_str.rsplit('(', maxsplit=1)[1][:-1]
        # Extract BTS from "<desc> (BTS)"
        bts_src = int(src_airport_str.rsplit('(', maxsplit=1)[1][:-1])
        bts_dst = int(dst_airport_str.rsplit('(', maxsplit=1)[1][:-1])
        if bts_src == bts_dst:
            messagebox.showerror(
                'Error', 'Origin and destination cannot be the same.')
            return
        try:
            forecast_src = nws_manager.Forecaster((root_dir / 'data' / 'maps' /
                                                   'airport_mappings.json').as_posix()).get_nws_forecast_from_bts(bts_src, iso_timestamp)
            forecast_dst = nws_manager.Forecaster((root_dir / 'data' / 'maps' /
                                                   'airport_mappings.json').as_posix()).get_nws_forecast_from_bts(bts_dst, iso_timestamp)

            data_to_discretize = [
                {
                    "CRS_DEP_TIME": ''.join(dep_time.split(':')),
                    'src_tavg': float(forecast_src['temperature']),
                    'dst_tavg': float(forecast_dst['temperature']),
                    'src_wspd': float(forecast_src['windSpeed'].split(' ')[0]),
                    'dst_wspd': float(forecast_dst['windSpeed'].split(' ')[0])
                }
            ]
            datautil.discretize(data_to_discretize)
            data_to_discretize = data_to_discretize[0]
            status_k, probability = self.bayes.make_prediction(
                bts_src,
                bts_dst,
                airline_code,
                # Strip 'Z' from timestamp
                datetime.fromisoformat(iso_timestamp[:-1]).isoweekday(),
                data_to_discretize['CRS_DEP_TIME'],
                data_to_discretize['src_tavg'],
                data_to_discretize['dst_tavg'],
                data_to_discretize['src_wspd'],
                data_to_discretize['dst_wspd']
            )

            self.predictionKey.delete(0, 500)
            prefix = 'Cancelled due to ' if status_k.find(
                'cancel:') == 0 else ''
            self.predictionKey.insert(
                0, f'{prefix}{self.bayes.key_meta.get_arrival_statuses()[status_k]}')

            self.keyDescription.delete(0, 500)
            self.keyDescription.insert(
                0, f'{round(probability * 100, 2)}% confidence')

        except ConnectionError:
            messagebox.showerror(
                'Error', 'Cannot connect to National Weather Service. Try again later.')
            return

        except ValueError as e:
            messagebox.showerror(
                'Error', 'Selected date/time is outside acceptable range. Acceptable range is within exactly 7 days from the current time.')
            raise e
            return


if __name__ == "__main__":
    app = App()
    app.mainloop()
