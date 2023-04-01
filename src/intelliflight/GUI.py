#from intelliflight.models.bayes_net import Bayes_Net
import tkinter
import tkintermapview
import customtkinter


customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("IntelliFlight")
        self.geometry("1920×1080")

        self.grid_rowconfigure((0), weight=1)
        self.grid_columnconfigure((0), weight=1)

        self.tabview = customtkinter.CTkTabview(self, width=250)
        self.tabview.grid(row=0, column=0,  sticky="nsew")
        self.tabview.add("Train")
        self.tabview.add("Predict")
        self.tabview.tab("Train").grid_columnconfigure((0,1),weight=1)
        self.tabview.tab("Train").grid_rowconfigure((0,1),weight=1)
        self.tabview.tab("Predict").grid_columnconfigure((0),weight=1)
        
        #TRAINING TAB
        #################################################################
        #Set text frame
        self.textFrame = customtkinter.CTkFrame(self.tabview.tab("Train"))
        self.textFrame.grid(row=0,column=0,pady=40,padx=20,sticky='nsew')
        #Set training data input text
        self.inputLabel = customtkinter.CTkLabel(self.textFrame,text="Input the file path for the training data:")
        self.inputLabel.grid(row=0,column=0,pady=20)
        #Set partition count text
        self.partitionLabel = customtkinter.CTkLabel(self.textFrame,text="Number of partitions for validation and testing:")
        self.partitionLabel.grid(row=1,column=0,pady=20)
        #Set k value increment text
        self.kValueLabel = customtkinter.CTkLabel(self.textFrame,text="Offset between candidate values for thelaplace smoothing \nfactor k as a percentage of the dataset length:")
        self.kValueLabel.grid(row=2,column=0,pady=20,padx=10)
        #Set max k value fraction text
        self.kFractionLabel = customtkinter.CTkLabel(self.textFrame,text="The laplace smoothing factor k is at most \nthis percentage of the dataset length:")
        self.kFractionLabel.grid(row=4,column=0,pady=20)
        #################################################################


        #################################################################
        #Set input frame
        self.inputFrame = customtkinter.CTkFrame(self.tabview.tab("Train"))
        self.inputFrame.grid(row=0,column=1,pady=40,padx=20,sticky='nsew')

        #Set new tab
        self.fileTab = customtkinter.CTkTabview(self.inputFrame, width=250)
        self.fileTab.grid(row=0,column=0,pady=20,padx=20,sticky='nsew')
        self.fileTab.add("Train new model")
        self.fileTab.add("Import existing model")
        self.fileTab.tab("Train new model").grid_columnconfigure((0,1),weight=1)

        #Set training data input button
        self.inputButton = customtkinter.CTkButton(self.fileTab.tab("Train new model"),text="Input training data" ,command=self.inputButton_callback)
        self.inputButton.grid(row=0,column=1,pady=20,padx=20)
        self.trainingCheckbox = customtkinter.CTkCheckBox(self.fileTab.tab("Train new model"),text="")
        self.trainingCheckbox.grid(row=0,column=2,padx=(73,0))

        self.importFileButton = customtkinter.CTkButton(self.fileTab.tab("Import existing model"),text="Import model file",command=self.importButton_callback)
        self.importFileButton.grid(row=1,column=1,pady=20,padx=20)
        self.importCheckbox = customtkinter.CTkCheckBox(self.fileTab.tab("Import existing model"),text="")
        self.importCheckbox.grid(row=1,column=2,padx=(73,0))
        #Set partition count input slider
        self.sliderP = customtkinter.CTkSlider(self.fileTab.tab("Train new model"), from_=0, to=100, number_of_steps=10, command=self.sliderP_callback)
        self.sliderP.grid(row=2,column=1,pady=30,padx=20)
        self.sliderP.set(0)
        self.partitionOutput = customtkinter.CTkEntry(self.fileTab.tab("Train new model"),width=37,height=30)
        self.partitionOutput.grid(row=2,column=2)
        #Set k value increment slider
        self.sliderK = customtkinter.CTkSlider(self.fileTab.tab("Train new model"),from_=0, to=100, number_of_steps=10, command=self.sliderK_callback)
        self.sliderK.grid(row=3,column=1,pady=27,padx=20)
        self.sliderK.set(0)
        self.kValueOutput = customtkinter.CTkEntry(self.fileTab.tab("Train new model"),width=37,height=30)
        self.kValueOutput.grid(row=3,column=2)
        #Set max k value fraction slider
        self.SliderF = customtkinter.CTkSlider(self.fileTab.tab("Train new model"),from_=0, to=1, command=self.sliderF_callback)
        self.SliderF.grid(row=4,column=1,pady=25,padx=20)
        self.SliderF.set(0)
        self.kFractionOutput = customtkinter.CTkEntry(self.fileTab.tab("Train new model"),width=37, height=30)
        self.kFractionOutput.grid(row=4,column=2)
        #################################################################

        
        #################################################################
        """ #Set bottom frame
        self.bottomFrame = customtkinter.CTkFrame(self.tabview.tab("Train"))
        self.bottomFrame.grid(row=1,column=0,sticky='n')
        #Set k value print
        self.kValuePrint = customtkinter.CTkEntry(self.bottomFrame)
        self.kValuePrint.grid(row=0,column=1)
        #Set save model button
        self.saveButton = customtkinter.CTkButton(self.bottomFrame,text="Save",command=self.saveButton_callback)
        self.saveButton.grid(row=0,column=2) """
    


        #################################################################


        #PREDICT TAB
        #################################################################
        self.mapFrame = customtkinter.CTkFrame(self.tabview.tab("Predict"))
        self.mapFrame.grid(row=0,column=0, sticky='nsew')
        
        self.map = tkintermapview.TkinterMapView(self.mapFrame,width=500,height=500,corner_radius=0)
        self.map.grid(row=0,column=0)


    def inputButton_callback(self):
        dialog = customtkinter.CTkInputDialog(text="Enter training data file path:", title="Training Data")
        self.trainingCheckbox.select()
        print("Test:", dialog.get_input())

    def sliderP_callback(self,value):
        value = self.sliderP.get()
        self.partitionOutput.delete(0,10)
        self.partitionOutput.insert(0,str(value))
        print(value)
        
    def sliderK_callback(self, value):
        value = self.sliderK.get()
        self.kValueOutput.delete(0,10)
        self.kValueOutput.insert(0,str(value))
        print(value)
    
    def sliderF_callback(self,value):
        value = self.SliderF.get()
        self.kFractionOutput.delete(0,10)
        self.kFractionOutput.insert(0,str(value))
        print(value)

    def importButton_callback(self):
        pass
    
    def saveButton_callback(self):
        pass


if __name__ =="__main__":  
    app = App()
    app.mainloop()
