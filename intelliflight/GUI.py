#from intelliflight.models.bayes_net import Bayes_Net
import tkinter
import tkinter.messagebox
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
        self.tabview.tab("Train").grid_columnconfigure((0,1,2,3,4,5,6,7,8,9),weight=1)
        self.tabview.tab("Predict").grid_columnconfigure((0),weight=1)

        #Training data input
        self.inputLabel = customtkinter.CTkLabel(self.tabview.tab("Train"),text="Use this button to input the file path for the training data:")
        self.inputLabel.grid(row=0,column=0)
        self.button = customtkinter.CTkButton(self.tabview.tab("Train"),text="Input training data" ,command=self.button_callback)
        self.button.grid(row=0,column=1,pady=(20))
        self.trainingCheckbox = customtkinter.CTkCheckBox(self.tabview.tab("Train"),text="")
        self.trainingCheckbox.grid(row=0,column=2)
        
        #Partition count
        self.partitionLabel = customtkinter.CTkLabel(self.tabview.tab("Train"),text="Use the slider to set the partition count:")
        self.partitionLabel.grid(row=1,column=0)
        self.sliderP = customtkinter.CTkSlider(self.tabview.tab("Train"), from_=0, to=100, number_of_steps=10, command=self.sliderP_callback)
        self.sliderP.set(0)
        self.sliderP.grid(row=1,column=1)
        self.partitionOutputLabel = customtkinter.CTkEntry(self.tabview.tab("Train"),width=37,height=30)
        self.partitionOutputLabel.grid(row=1,column=2)
        self.partitionCheckbox = customtkinter.CTkCheckBox(self.tabview.tab("Train"),text="")
        self.partitionCheckbox.grid(row=1,column=3)

        #k value increment
        self.kValueLabel = customtkinter.CTkLabel(self.tabview.tab("Train"),text="Use the slider to set the increment for each k value:")
        self.kValueLabel.grid(row=2,column=0)
        self.sliderK = customtkinter.CTkSlider(self.tabview.tab("Train"),from_=0, to=100, number_of_steps=10, command=self.sliderK_callback)
        self.sliderK.grid(row=2,column=1)
        self.sliderK.set(10)
        self.kValueOutput = customtkinter.CTkEntry(self.tabview.tab("Train"),width=37,height=30)
        self.kValueOutput.grid(row=2,column=2)
        self.kValueCheckbox = customtkinter.CTkCheckBox(self.tabview.tab("Train"),text="")
        self.kValueCheckbox.grid(row=2,column=3)

        #Max k fraction
        self.kFractionLabel = customtkinter.CTkLabel(self.tabview.tab("Train"),text="Use the slider to set the percentage of the max fraction:")
        self.kFractionLabel.grid(row=3,column=0)
        self.SliderF = customtkinter.CTkSlider(self.tabview.tab("Train"),from_=0, to=1, command=self.sliderF_callback)
        self.SliderF.grid(row=3,column=1)
        self.SliderF.set(0)
        self.kFractionOutput = customtkinter.CTkEntry(self.tabview.tab("Train"),width=40, height=30)
        self.kFractionOutput.grid(row=3,column=2)
        self.kFractionCheckbox = customtkinter.CTkCheckBox(self.tabview.tab("Train"),text="")
        self.kFractionCheckbox.grid(row=3,column=3)

    def button_callback(self):
        dialog = customtkinter.CTkInputDialog(text="Enter training data file path:", title="Training Data")
        self.trainingCheckbox.select()
        print("Test:", dialog.get_input())

    def sliderP_callback(self,value):
        value = self.sliderP.get()
        self.partitionOutputLabel.delete(0,10)
        self.partitionOutputLabel.insert(0,str(value))
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
