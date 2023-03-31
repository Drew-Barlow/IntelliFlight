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
        self.geometry("900x600")

        self.grid_rowconfigure((0), weight=1)
        self.grid_columnconfigure((0), weight=1)

        self.tabview = customtkinter.CTkTabview(self, width=250)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.tabview.add("Train")
        self.tabview.add("Predict")
        self.tabview.tab("Train").grid_columnconfigure((0,1,2,3,4),weight=1)
        self.tabview.tab("Predict").grid_columnconfigure((0),weight=1)
        
        #TRAINING TAB
        #################################################################
        #Set text frame
        self.textFrame = customtkinter.CTkFrame(self.tabview.tab("Train"))
        self.textFrame.grid(row=0,column=0,pady=20,sticky='nsew')
        #Set training data input text
        self.inputLabel = customtkinter.CTkLabel(self.textFrame,text="Input the file path for the training data:")
        self.inputLabel.grid(row=0,column=0,pady=20,padx=20)
        #Set partition count text
        self.partitionLabel = customtkinter.CTkLabel(self.textFrame,text="Number of partitions for validation and testing:")
        self.partitionLabel.grid(row=1,column=0,pady=20,padx=20)
        #Set k value increment text
        self.kValueLabel = customtkinter.CTkLabel(self.textFrame,text="Offset between candidate values for the laplace smoothing factor k as a percentage of the dataset length:")
        self.kValueLabel.grid(row=2,column=0,pady=20,padx=20)
        #Set max k value fraction text
        self.kFractionLabel = customtkinter.CTkLabel(self.textFrame,text="The laplace smoothing factor k is at most this percentage of the dataset length:")
        self.kFractionLabel.grid(row=3,column=0,pady=20,padx=20)
        #################################################################


        #################################################################
        #Set input frame
        self.inputFrame = customtkinter.CTkFrame(self.tabview.tab("Train"))
        self.inputFrame.grid(row=0,column=2,pady=20,sticky='nsew')
        #Set training data input button
        self.button = customtkinter.CTkButton(self.inputFrame,text="Input training data" ,command=self.button_callback)
        self.button.grid(row=0,column=1,pady=20,padx=20)
        #Set partition count input slider
        self.sliderP = customtkinter.CTkSlider(self.inputFrame, from_=0, to=100, number_of_steps=10, command=self.sliderP_callback)
        self.sliderP.grid(row=1,column=1,pady=27,padx=20)
        self.sliderP.set(0)
        self.partitionOutput = customtkinter.CTkEntry(self.inputFrame,width=37,height=30)
        self.partitionOutput.grid(row=1,column=2)
        #Set k value increment slider
        self.sliderK = customtkinter.CTkSlider(self.inputFrame,from_=0, to=100, number_of_steps=10, command=self.sliderK_callback)
        self.sliderK.grid(row=2,column=1,pady=27,padx=20)
        self.sliderK.set(0)
        self.kValueOutput = customtkinter.CTkEntry(self.inputFrame,width=37,height=30)
        self.kValueOutput.grid(row=2,column=2)
        #Set max k value fraction slider
        self.SliderF = customtkinter.CTkSlider(self.inputFrame,from_=0, to=1, command=self.sliderF_callback)
        self.SliderF.grid(row=3,column=1,pady=27,padx=20)
        self.SliderF.set(0)
        self.kFractionOutput = customtkinter.CTkEntry(self.inputFrame,width=37, height=30)
        self.kFractionOutput.grid(row=3,column=2)
        #################################################################


        #################################################################
        #Set progress frame
        self.progressFrame = customtkinter.CTkFrame(self.tabview.tab("Train"))
        self.progressFrame.grid(row=0,column=4,pady=20,sticky='nsew')
        #Set training data checkbox
        self.trainingCheckbox = customtkinter.CTkCheckBox(self.progressFrame,text="")
        self.trainingCheckbox.grid(row=0,column=4,pady=27,padx=20)
        #Set partition count checkbox
        self.partitionCheckbox = customtkinter.CTkCheckBox(self.progressFrame,text="")
        self.partitionCheckbox.grid(row=1,column=4,pady=13)
        #Set k value increment checkbox
        self.kValueCheckbox = customtkinter.CTkCheckBox(self.progressFrame,text="")
        self.kValueCheckbox.grid(row=2,column=4,pady=35)
        #Set max k fraction chechbox
        self.kFractionCheckbox = customtkinter.CTkCheckBox(self.progressFrame,text="")
        self.kFractionCheckbox.grid(row=3,column=4,pady=10)
        #################################################################

        #PREDICT TAB
        #################################################################
        self.mapFrame = customtkinter.CTkFrame(self.tabview.tab("Predict"))
        self.mapFrame.grid(row=0,column=0, sticky='nsew')
        
        self.map = tkintermapview.TkinterMapView(self.mapFrame,width=500,height=500,corner_radius=0)
        self.map.grid(row=0,column=0)


    def button_callback(self):
        dialog = customtkinter.CTkInputDialog(text="Enter training data file path:", title="Training Data")
        self.trainingCheckbox.select()
        print("Test:", dialog.get_input())

    def sliderP_callback(self,value):
        value = self.sliderP.get()
        self.partitionOutput.delete(0,10)
        self.partitionOutput.insert(0,str(value))
        self.partitionCheckbox.select()
        print(value)
        
    def sliderK_callback(self, value):
        value = self.sliderK.get()
        self.kValueOutput.delete(0,10)
        self.kValueOutput.insert(0,str(value))
        self.kValueCheckbox.select()
        print(value)
    
    def sliderF_callback(self,value):
        value = self.SliderF.get()
        self.kFractionOutput.delete(0,10)
        self.kFractionOutput.insert(0,str(value))
        self.kFractionCheckbox.select()
        print(value)


if __name__ =="__main__":  
    app = App()
    app.mainloop()
