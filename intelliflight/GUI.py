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

        self.grid_rowconfigure((0, 1, 2), weight=1)
        self.grid_columnconfigure((0,1,2), weight=1)
        
        self.logo_label = customtkinter.CTkLabel(master=self, text="Welcome to IntelliFlight", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=1, padx =20, pady=(20,0), sticky="nsew")

        self.button = customtkinter.CTkButton(master=self, command=self.button_callback)
        self.button.grid(row=1,column=1,padx=20, pady=20, sticky="ew")


    def button_callback(self):
        print("button pressed")


if __name__ =="__main__":
    app = App()
    app.mainloop()
