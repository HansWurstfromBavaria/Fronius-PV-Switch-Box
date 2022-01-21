#PV-Schalter v1.0 --- by Hans Wurst 6.1.2022
#Gestestet auf Raspberry Pi Zero W v1.1 mit 3,5" Display.
#Auslesen der Werte getestet für Fronius Symo 10.0-3-M Wechselrichter.

import tkinter as tk
import requests
from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import RPi.GPIO as GPIO #Um die Software auf dem PC zu testen => dies auskommentieren, und 5 eitere Zeilen (2x in Init, 1x in Fkt_Reset, 2x in Fkt_UpdateGUI), da auf PC keine GPIOs...

hostname = "http://192.168.2.151" #IP-Adresse des Fronius Wechselrichters
PV_Max_Leistung = 9750 #Maximale Leistung der PV-Anlage in W
Switch_GPIO_Port = 5 #Port an dem das Relais (mit Ansteuerung) hängt
Abschaltschwelle_Netzbezug = 200 #Fix. Wenn so viel Leistung in W vom Netz gezogen wird, wird abgeschaltet
GUI_Updaterate = 15000 #Updaterate der GUI in ms

class PVSchalter:
    def __init__(self, master=None):

        GPIO.setmode(GPIO.BCM) #Muss bei anderem Raspberry Pi-Modell evtl. geändert werden.
        GPIO.setwarnings(False) #Unterdrücke Fehlermeldungen dass der gewählte Port evtl. schon in Benutzung ist.
        GPIO.setup(Switch_GPIO_Port, GPIO.OUT)

        self.TopLevel = tk.Tk() #Tkinter Objekt
        self.TopLevel.title("PV-Schalter")
        self.TopLevel.attributes('-fullscreen', True)

        self.fig = Figure(figsize=(2.8, 2.8), dpi=100) #Matplotlib Pie-Chart Figure erzeugen
        self.ax = self.fig.add_subplot(111)

        self.Schaltschwelle = 3100 #Startwert für die Schaltschelle

        #Erstelle GUI. Linker Frame (Pie Chart) und Rechter Frame (Labels und Bottons) mit Inhalt.
        #Größtenteils mit PyGubu erstellt.
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
        self.Anzeige_PV_Leistung.configure(background='#ffff00', font='{Arial} 12 {}', text='') #Text wird gleich beim ersten Aufruf von Fkt_UpdateGUI ersetzt.
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

        self.MatPlotLibCanvas = FigureCanvasTkAgg(self.fig, master = self.LinkerFrame) #Canvas für MatPlotLib Pie Chart erstellen. Wird gefüllt beim ersten Aufruf von Fkt_UpdateGUI
        self.MatPlotLibCanvas.get_tk_widget().grid(column='0', row='0')

        self.Fkt_UpdateGUI() #Erster Aufrauf hier, dann automatischer selbstaufruf alle xx Sekunden

        self.mainwindow = self.TopLevel #Main widget
    
    def Fkt_HoleWerte(self):
        # Funktion um Werte vom Fronius Symo PV-Wechselrichter zu holen (über CGI-Skript als JSON) und auszuwerten
        #Rückgabewerte:
        #Netzbezug => Positiv wenn Strom aus Netz bezogen wird, Negativ wenn Strom in Netz geliefert wird
        #PV_Leistung => Aktuelle PV-Leistung in W
        #PV_Eigenverbrauch => Wie viel PV-Leistung in W wird gerade selbst verbraucht
        #PV_Potential => #Aktuell offenes Potential der Anlage wegen zu geringer Sonneneinstrahlung
        #PV_EigenverbrauchsPotential => #Akutell offenes Potential an Eigenverbrauch wegen zu wenig Eigenverbauch. Bei Netzbezug >0 => =0, Bei Netzbezug <0 => =Netzbezug
        
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
            self.Anzeige_ONOFF.config(text = 'Auslesefehler!', background='#FFFF00') #Fehlerindikator in der GUI
        
        if (PV_Leistung > PV_Max_Leistung) or PV_Leistung<0: #Fehlerhafte AusleseWerte abfangen.
            PV_Leistung = 0 

        GesamtHausverbrauch = Netzbezug + PV_Leistung #Stimmt immer, da Netzbezug negativ werden kann. 

        if Netzbezug<0: #überschüssiger Strom wird ins Netz gespeist
            PV_Eigenverbrauch = GesamtHausverbrauch
        elif Netzbezug>=0: #Strom wird aus Netz entnommen
            PV_Eigenverbrauch = PV_Leistung #100% des PV-Stroms wird verwendet

        PV_Potential = PV_Max_Leistung-PV_Leistung 

        if PV_Potential<0: #Schutz vor negativen Werten
            PV_Potential=0

        PV_EigenverbrauchsPotential = PV_Leistung-PV_Eigenverbrauch 

        return Netzbezug, PV_Leistung, PV_Eigenverbrauch, PV_Potential, PV_EigenverbrauchsPotential

    def Fkt_UpdateGUI(self):
        #Funktion um die GUI zu aktualisieren. 

        print("Aktualisieren...")
        Netzbezug, PV_Leistung, PV_Eigenverbrauch, PV_Potential, PV_EigenverbrauchsPotential = self.Fkt_HoleWerte()

        if PV_Leistung>0: #Umrechnung in kW und jeweils check ob wirklich >0 um Fehler zu vermeiden
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

        self.Anzeige_PV_Leistung.config(text = str(round(PV_Leistung_kW,2))+'kW') #Ändern der Anzeigen in der GUI (rechte Seite)
        self.Anzeige_Eigenverbrauch.config(text = str(round(PV_Eigenverbrauch_kW,2))+'kW')
        self.Anzeige_LeistungUebrig.config(text = str(round(PV_EigenverbrauchsPotential_kW,2))+'kW')

        #GPIO bzw. Relais Schalten
        if PV_EigenverbrauchsPotential>self.Schaltschwelle:
            GPIO.output(Switch_GPIO_Port, GPIO.HIGH)
            self.Anzeige_ONOFF.config(text = 'AN', background='#00FF00') #AN und grüner Hintergrund
        elif Netzbezug>Abschaltschwelle_Netzbezug:
            GPIO.output(Switch_GPIO_Port, GPIO.LOW)
            self.Anzeige_ONOFF.config(text = 'AUS', background='#ff0000') #AUS und roter Hintergrund

        self.ax.clear() #Löschen und neuzeichnen des Pie Charts
        self.Ftk_ZeichneKuchenDiagramm(PV_Leistung, PV_Eigenverbrauch, PV_Potential, PV_EigenverbrauchsPotential)
        self.MatPlotLibCanvas.draw_idle()

        self.TopLevel.after(GUI_Updaterate, self.Fkt_UpdateGUI) #Automatischer selbstaufruf alle {GUI_Updaterate}ms

    def Fkt_Reset(self): 
        #Funktion für Reset-Button
        
        GPIO.output(Switch_GPIO_Port, GPIO.LOW) #Schalte GPIO bzw. Relais aus.
        self.Anzeige_ONOFF.config(text = 'AUS', background='#ff0000') #Anzeige 'AUS' und roter Hintergrund

    def Fkt_SchwelleAb(self): 
        #Funktion für Schwelle Ab-Button
        
        if self.Schaltschwelle>100: #minimaler Wert ist 100W
            self.Schaltschwelle = self.Schaltschwelle - 100
            self.Anzeige_Schaltschwelle.config(text = str(self.Schaltschwelle)+'W')
            self.Fkt_Reset() #Neubewertung der Situation

    def Fkt_SchwelleAuf(self): 
        #Funktion für Schwelle Auf-Button
        
        if self.Schaltschwelle<5000: #mehr als 5000W (3500W+Puffer) ist für diese Anwendung nicht sinnvoll.
            self.Schaltschwelle = self.Schaltschwelle + 100
            self.Anzeige_Schaltschwelle.config(text = str(self.Schaltschwelle)+'W')
            self.Fkt_Reset() #Neubewertung der Situation

    def Ftk_ZeichneKuchenDiagramm(self, PV_Leistung, PV_Eigenverbrauch, PV_Potential, PV_EigenverbrauchsPotential):
        #Funktion um das Pie Chart auf der linken Seite des GUI zu erstellen

        if PV_Leistung>0: #Zeiche Pie Chart bei PV-Leistung >0
            
            #Mögliche Beschriftung (Labels) des Pie Charts => Nicht verwendet.
            #PV_Leistung_kW = PV_Leistung/1000
            #BeschriftungAußen = ['', 'PV-Leistung: ' + '{v:.2f}kW'.format(v=PV_Leistung_kW)]
            #BeschriftungInnen = ['', 'Eigenverbauch: ({x:.2f}%)'.format(x=(PV_Eigenverbrauch/PV_Leistung)*100)]

            KuchenWerteAußen = [PV_Potential, PV_Leistung]
            self.wedges1 = self.ax.pie( KuchenWerteAußen, #Tortendiagramm, welches die aktuelle Leistung und das verbleibende Potential der PV-Anlage zeigt.
                    radius=1.5,
                    autopct=None,
                    labels = None, 
                    colors=("cornflowerblue", "blue"),
                    startangle = 90,
                    wedgeprops=dict(width=1, edgecolor='w'),
                    textprops = dict(color ="blue"))

            KuchenWerteInnen = [PV_EigenverbrauchsPotential, PV_Eigenverbrauch]
            self.wedges2 = self.ax.pie( KuchenWerteInnen, #Tortendiagramm, welches den Eigenverbrauch und das verbleibende Potential an Eigenverbrauch zeigt.
                    radius=0.8,
                    autopct=None,
                    labels = None,
                    labeldistance=1.2, 
                    colors=("lime", "darkgreen"),
                    startangle = 90,
                    wedgeprops=dict(width=0.8, edgecolor='w'),
                    textprops = dict(color ="darkgreen"))

        else: #Bei PV_Leistung <=0, zeichne nur symbolisches, leeres Pie Chart.
            self.wedges1 = self.ax.pie( [100,0], 
                radius=1,
                autopct=None,
                labels = None, 
                colors=("lightgrey", 'grey'),
                startangle = 90,
                wedgeprops=dict(width=0.6, edgecolor='w'),
                textprops = dict(color ="red"))

        self.ax.legend(['Anlagenleistung', 'PV-Leistung', 'Übrige Leistung', 'Eigenverbrauch'], loc='lower center', bbox_to_anchor=(0.9, -0.15), fontsize=6) #Legende in Box rechts unten


if __name__ == '__main__': #Erzeuge ein Objekt der Klasse und starte Anwendung.
    app = PVSchalter()
    app.mainwindow.mainloop()

