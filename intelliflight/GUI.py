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
        self.tabview.tab("Train").grid_columnconfigure((0),weight=1)
        self.tabview.tab("Predict").grid_columnconfigure((0),weight=1)

        #Training data input
        self.button = customtkinter.CTkButton(self.tabview.tab("Train"),text="Input training data" ,command=self.button_callback)
        self.button.grid(row=0,column=0,padx=20,pady=20)

        #Partition count
        self.labalP = customtkinter.CTkLabel(self.tabview.tab("Train"),text="Use the slider to set the partition count")
        self.labalP.grid(row=1,column=0)
        self.sliderP = customtkinter.CTkSlider(self.tabview.tab("Train"), from_=0, to=100, number_of_steps=10, command=self.sliderP_callback)
        self.sliderP.grid(row=2,column=0)
        self.labelOutputP = customtkinter.CTkEntry(self.tabview.tab("Train"),width=50,height=50)
        self.labelOutputP.grid(row=3,column=0)

        #k value increment
        self.labelK = customtkinter.CTkLabel(self.tabview.tab("Train"),text="Use the slider to set the increment for each k value")
        self.labelK.grid(row=4,column=0)
        self.sliderK = customtkinter.CTkSlider(self.tabview.tab("Train"),from_=0, to=100, number_of_steps=10, command=self.sliderK_callback)
        self.sliderK.grid(row=5,column=0)
        self.labelOutputK = customtkinter.CTkEntry(self.tabview.tab("Train"),width=50,height=50)
        self.labelOutputK.grid(row=6,column=0)

        #Max k fraction
        self.labelF = customtkinter.CTkLabel(self.tabview.tab("Train"),text="Use the slider to set the percentage of the max fraction")
        self.labelF.grid(row=7,column=0)
        self.SliderF = customtkinter.CTkSlider(self.tabview.tab("Train"),from_=0, to=1, command=self.sliderF_callback)
        self.SliderF.grid(row=8,column=0)
        self.labelOutputF = customtkinter.CTkEntry(self.tabview.tab("Train"),width=50, height=50)
        self.labelOutputF.grid(row=9,column=0)

    def button_callback(self):
        dialog = customtkinter.CTkInputDialog(text="Enter training data file path:", title="Training Data")
        print("Test:", dialog.get_input())

    def sliderP_callback(self,value):
        value = self.sliderP.get()
        self.labelOutputP.insert(0,str(value))
        print(value)

    def sliderK_callback(self, value):
        value = self.sliderK.get()
        self.labelOutputK.insert(0,str(value))
        print(value)
    
    def sliderF_callback(self,value):
        value = self.SliderF.get()
        self.labelOutputF.insert(0,str(value))
        print(value)

if __name__ =="__main__":
    app = App()
    app.mainloop()
