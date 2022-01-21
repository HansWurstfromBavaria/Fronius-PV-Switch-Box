#PV-Switch v1.0 --- by Hans Wurst 6.1.2022
#Tested on Raspberry Pi Zero W v1.1 with 3,5" Display.
#Readout of Values tested with Fronius Symo 10.0-3-M Inverter.

import tkinter as tk
import requests
from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import RPi.GPIO as GPIO #To run this software on PC, #-comment every line containing GPIO-Stuff

hostname = "http://192.168.2.151" #IP-Address of Fronius Inverter
PV_Max_Leistung = 9750 #Max Power of PV-System in W
Switch_GPIO_Port = 5 #GPIO-Port of Relais (with Control Circuit)
Abschaltschwelle_Netzbezug = 200 #Fixed value. Drawing that much Power from the Grid, the Relais gets switched off
GUI_Updaterate = 15000 #Update rate of GUI in ms

class PVSchalter:
    def __init__(self, master=None):

        GPIO.setmode(GPIO.BCM) #Might need to change this for different Raspberry Pi
        GPIO.setwarnings(False) #Suppress Errors
        GPIO.setup(Switch_GPIO_Port, GPIO.OUT)

        self.TopLevel = tk.Tk() #Tkinter Object
        self.TopLevel.title("PV-Schalter")
        self.TopLevel.attributes('-fullscreen', True)

        self.fig = Figure(figsize=(2.8, 2.8), dpi=100) #Create Matplotlib Pie-Chart Figure
        self.ax = self.fig.add_subplot(111)

        self.Schaltschwelle = 3100 #Initial value of Switch Threshold

        #Create GUI. Left Frame (Pie Chart) und Right Frame (Labels und Bottons) with Content.
        #GUI created with PyGubu.
        self.RechterFrame = tk.Frame(self.TopLevel)
        self.label1 = tk.Label(self.RechterFrame)
        self.label1.configure(background='#ffff00', font='{Arial} 10 {}', text='PV-Leistung:')
        self.label1.grid(column='0', row='1', sticky='e')
        self.RechterFrame.rowconfigure('1', weight='1')
        self.RechterFrame.columnconfigure('0', minsize='10', pad='0', weight='1')
        self.label2 = tk.Label(self.RechterFrame)
        self.label2.configure(background='#ffff00', font='{Arial} 10 {}', text='Eigenverbrauch:')
        self.label2.grid(column='0', row='2', sticky='e')
        self.RechterFrame.rowconfigure('2', weight='1')
        self.label3 = tk.Label(self.RechterFrame)
        self.label3.configure(background='#ffff00', font='{Arial} 10 {}', text='Übrige Leistung:')
        self.label3.grid(column='0', row='3', sticky='e')
        self.RechterFrame.rowconfigure('3', weight='1')
        self.label4 = tk.Label(self.RechterFrame)
        self.label4.configure(background='#ffff00', font='{Arial} 10 {}', text='Schaltschwelle:')
        self.label4.grid(column='0', row='4', sticky='e')
        self.RechterFrame.rowconfigure('4', minsize='0', weight='1')
        self.Button_Reset = tk.Button(self.RechterFrame)
        self.Button_Reset.configure(activebackground='#a80dce' ,background='#a80dce', height='3', text='Reset', width='20')
        self.Button_Reset.grid(column='0', columnspan='2', row='6', rowspan='1')
        self.Button_Reset.grid_propagate(0)
        self.RechterFrame.rowconfigure('6', pad='10', weight='1')
        self.Button_Reset.configure(command=self.Fkt_Reset)
        self.Button_Ab = tk.Button(self.RechterFrame)
        self.Button_Ab.configure(activebackground='#80ffff', background='#80ffff', borderwidth='1', height='3', text='Schwelle\nAb', width='8', highlightthickness=0)
        self.Button_Ab.grid(column='0', row='5')
        self.Button_Ab.grid_propagate(0)
        self.RechterFrame.rowconfigure('5', minsize='0', pad='0', weight='1')
        self.Button_Ab.configure(command=self.Fkt_SchwelleAb)
        self.Anzeige_PV_Leistung = tk.Label(self.RechterFrame)
        self.Anzeige_PV_Leistung.configure(background='#ffff00', font='{Arial} 12 {}', text='') #Text will be replaced after first call of Fkt_UpdateGUI.
        self.Anzeige_PV_Leistung.grid(column='1', row='1')
        self.RechterFrame.columnconfigure('1', minsize='0', pad='0')
        self.Anzeige_Eigenverbrauch = tk.Label(self.RechterFrame)
        self.Anzeige_Eigenverbrauch.configure(background='#ffff00', font='{Arial} 12 {}', text='') 
        self.Anzeige_Eigenverbrauch.grid(column='1', row='2')
        self.Anzeige_LeistungUebrig = tk.Label(self.RechterFrame)
        self.Anzeige_LeistungUebrig.configure(background='#ffff00', font='{Arial} 12 {}', text='')
        self.Anzeige_LeistungUebrig.grid(column='1', row='3')
        self.Anzeige_Schaltschwelle = tk.Label(self.RechterFrame)
        self.Anzeige_Schaltschwelle.configure(background='#ffff00', font='{Arial} 12 {}', text=str(self.Schaltschwelle)+'W')
        self.Anzeige_Schaltschwelle.grid(column='1', row='4')
        self.Button_Auf = tk.Button(self.RechterFrame)
        self.Button_Auf.configure(activebackground='#80ffff', background='#80ffff', borderwidth='1', default='normal', height='3', text='Schwelle\nAuf', highlightthickness=0)
        self.Button_Auf.configure(width='8')
        self.Button_Auf.grid(column='1', row='5')
        self.Button_Auf.grid_propagate(0)
        self.Button_Auf.configure(command=self.Fkt_SchwelleAuf)
        self.Anzeige_ONOFF = tk.Label(self.RechterFrame)
        self.Anzeige_ONOFF.configure(background='#ff0000', font='{Arial} 12 {bold}', text='AUS')
        self.Anzeige_ONOFF.grid(column='0', columnspan='2', row='7')
        self.RechterFrame.rowconfigure('7', pad='10')
        self.RechterFrame.configure(background='#ffff00', height='320', width='200', highlightthickness=0)
        self.RechterFrame.grid(column='1', row='0')
        self.RechterFrame.grid_propagate(0)
        self.TopLevel.rowconfigure('0', weight='1')
        self.TopLevel.columnconfigure('1', pad='0', weight='1')
        self.LinkerFrame = tk.Frame(self.TopLevel)
        self.LinkerFrame.configure(background='#ffffff', height='320', width='280')
        self.LinkerFrame.grid(column='0', row='0')
        self.TopLevel.configure(height='0', width='0')
        self.TopLevel.geometry('480x320')
        self.TopLevel.configure(background='#FFFFFF')

        self.MatPlotLibCanvas = FigureCanvasTkAgg(self.fig, master = self.LinkerFrame) #Create Canvas for MatPlotLib Pie Chart. Will be filled at Fkt_UpdateGUI
        self.MatPlotLibCanvas.get_tk_widget().grid(column='0', row='0')

        self.Fkt_UpdateGUI() #First call here, afterwards automatically every xx Seconds

        self.mainwindow = self.TopLevel #Main widget
    
    def Fkt_HoleWerte(self):
        # Method to capture and analyze Values of Fronius Symo Inverter (via CGI Script as JSON)
        #Return Values:
        #Netzbezug => Current drawn from Grid. Positive value if Current drawn from grid, negative if current is supplied to grid
        #PV_Leistung => Current PV-Power in W
        #PV_Eigenverbrauch => How much Power in W is currently used by my own
        #PV_Potential => Currently missing PV-Power due to less sunshine
        #PV_EigenverbrauchsPotential => Current potential of PV-Power for self usage due to less consumption.
        
        try:
            url = hostname + "/solar_api/v1/GetMeterRealtimeData.cgi?Scope=System"
            r = requests.get(url, timeout=60)
            Daten = r.json()
            Netzbezug = Daten['Body']['Data']['0']['PowerReal_P_Sum']

            url = hostname + "/solar_api/v1/GetInverterRealtimeData.cgi?Scope=System"
            r = requests.get(url, timeout=60)
            Daten = r.json()
            PV_Leistung = Daten['Body']['Data']['PAC']['Values']['1']
        except:
            Netzbezug = 0 
            PV_Leistung = 0
            self.Anzeige_ONOFF.config(text = 'Auslesefehler!', background='#FFFF00') #Error reporting in GUI
        
        if (PV_Leistung > PV_Max_Leistung) or PV_Leistung<0: #Deal with wrong values
            PV_Leistung = 0 

        GesamtHausverbrauch = Netzbezug + PV_Leistung #Always correct, because "Netzbezug" can get negative 

        if Netzbezug<0: #Excess Power is supplied to grid
            PV_Eigenverbrauch = GesamtHausverbrauch
        elif Netzbezug>=0: #Power is drawn from grid
            PV_Eigenverbrauch = PV_Leistung #100% of our PV Power is used by myself

        PV_Potential = PV_Max_Leistung-PV_Leistung 

        if PV_Potential<0: #Deal with wrong values
            PV_Potential=0

        PV_EigenverbrauchsPotential = PV_Leistung-PV_Eigenverbrauch 

        return Netzbezug, PV_Leistung, PV_Eigenverbrauch, PV_Potential, PV_EigenverbrauchsPotential

    def Fkt_UpdateGUI(self):
        #Method to update GUI content 

        print("Aktualisieren...")
        Netzbezug, PV_Leistung, PV_Eigenverbrauch, PV_Potential, PV_EigenverbrauchsPotential = self.Fkt_HoleWerte()

        if PV_Leistung>0: #Change W to kW if values >0
            PV_Leistung_kW = PV_Leistung/1000
        else:
            PV_Leistung_kW=0
        if PV_Eigenverbrauch>0:
            PV_Eigenverbrauch_kW = PV_Eigenverbrauch/1000
        else:
            PV_Eigenverbrauch_kW=0
        if PV_Eigenverbrauch>0:
            PV_EigenverbrauchsPotential_kW = PV_EigenverbrauchsPotential/1000
        else:
            PV_EigenverbrauchsPotential_kW=0

        self.Anzeige_PV_Leistung.config(text = str(round(PV_Leistung_kW,2))+'kW') #Change labels in the GUI (Right Side)
        self.Anzeige_Eigenverbrauch.config(text = str(round(PV_Eigenverbrauch_kW,2))+'kW')
        self.Anzeige_LeistungUebrig.config(text = str(round(PV_EigenverbrauchsPotential_kW,2))+'kW')

        #Switch GPIO/Relais
        if PV_EigenverbrauchsPotential>self.Schaltschwelle:
            GPIO.output(Switch_GPIO_Port, GPIO.HIGH)
            self.Anzeige_ONOFF.config(text = 'AN', background='#00FF00') #ON and green Background
        elif Netzbezug>Abschaltschwelle_Netzbezug:
            GPIO.output(Switch_GPIO_Port, GPIO.LOW)
            self.Anzeige_ONOFF.config(text = 'AUS', background='#ff0000') #OFF and red Background

        self.ax.clear() #Delete and Redraw Pie Chart
        self.Ftk_ZeichneKuchenDiagramm(PV_Leistung, PV_Eigenverbrauch, PV_Potential, PV_EigenverbrauchsPotential)
        self.MatPlotLibCanvas.draw_idle()

        self.TopLevel.after(GUI_Updaterate, self.Fkt_UpdateGUI) #Automatical recall every GUI_Updaterate [ms]

    def Fkt_Reset(self): 
        #Method for Reset Button
        
        GPIO.output(Switch_GPIO_Port, GPIO.LOW) #Switch GPIO/Relais off
        self.Anzeige_ONOFF.config(text = 'AUS', background='#ff0000') #OFF and red Background

    def Fkt_SchwelleAb(self): 
        #Method for Threshold down Button
        
        if self.Schaltschwelle>100: #Minimum Value is 100W
            self.Schaltschwelle = self.Schaltschwelle - 100
            self.Anzeige_Schaltschwelle.config(text = str(self.Schaltschwelle)+'W')
            self.Fkt_Reset() #Neubewertung der Situation

    def Fkt_SchwelleAuf(self): 
        #Method for Threshold up Button
        
        if self.Schaltschwelle<5000: #More than 5000W (3500W+Buffer) is not considered sensefull for this application
            self.Schaltschwelle = self.Schaltschwelle + 100
            self.Anzeige_Schaltschwelle.config(text = str(self.Schaltschwelle)+'W')
            self.Fkt_Reset() #Reset

    def Ftk_ZeichneKuchenDiagramm(self, PV_Leistung, PV_Eigenverbrauch, PV_Potential, PV_EigenverbrauchsPotential):
        #Method to create Pie Chart on left side of GUI

        if PV_Leistung>0: #Draw Pie Chart if PV-Power >0

            KuchenWerteAußen = [PV_Potential, PV_Leistung]
            self.wedges1 = self.ax.pie( KuchenWerteAußen, #Pie Chart, showing current PV Power and remaining Power of installed system
                    radius=1.5,
                    autopct=None,
                    labels = None, 
                    colors=("cornflowerblue", "blue"),
                    startangle = 90,
                    wedgeprops=dict(width=1, edgecolor='w'),
                    textprops = dict(color ="blue"))

            KuchenWerteInnen = [PV_EigenverbrauchsPotential, PV_Eigenverbrauch]
            self.wedges2 = self.ax.pie( KuchenWerteInnen, #Pie Chart, showing self used Power of PV System and remaining Power that could be used by myself
                    radius=0.8,
                    autopct=None,
                    labels = None,
                    labeldistance=1.2, 
                    colors=("lime", "darkgreen"),
                    startangle = 90,
                    wedgeprops=dict(width=0.8, edgecolor='w'),
                    textprops = dict(color ="darkgreen"))

        else: #For PV Power <=0, draw a grey, empty and symbolic Pie Chart
            self.wedges1 = self.ax.pie( [100,0], 
                radius=1,
                autopct=None,
                labels = None, 
                colors=("lightgrey", 'grey'),
                startangle = 90,
                wedgeprops=dict(width=0.6, edgecolor='w'),
                textprops = dict(color ="red"))

        self.ax.legend(['Anlagenleistung', 'PV-Leistung', 'Übrige Leistung', 'Eigenverbrauch'], loc='lower center', bbox_to_anchor=(0.9, -0.15), fontsize=6) #Legend in Box


if __name__ == '__main__': #Create an Object of the Class and Start Application
    app = PVSchalter()
    app.mainwindow.mainloop()

