**A DIY Photovoltaic Switch Box for a Fronius Symo Inverter.**

I got a new Photovoltaic System installed to the roof of my house, and so I was thinking 
about how to switch a simple load like a heater depending on the currently available amount of power.

The sun comes out and shines on the cells. Part of the Energy is used by myself depending on what loads are currently active in the house. All remaining energy is pushed to the grid for more or less nothing (currently 7,5 Euro-Cent per kWh). So the idea is to switch an heater (eg. 3kW) whenever the "leftover"/unused energy of the system exceeds a certain (adjustable value).

My Inverter is a Fronius Symo 10.0-3-M and it supports the readout of Data over Ethernet or WLAN. As far as I know all of the Fronius Symo Inverters (and especially the Gen24 devices) support this.
How this works? A CGI-Script on the Inverter receives enquiries via the standard http protocol and answers them with a JSON file output.
For details search for "Fronius Solar API" in Google.
To test it, just use your browser and try: http://<<<IP-ADDRESS OF INVERTER>>>/solar_api/v1/GetMeterRealtimeData.cgi?Scope=System
So in my case I need to type in: http://192.168.2.151/solar_api/v1/GetMeterRealtimeData.cgi?Scope=System
You should get a JSON-File displayed on your browser, showing some current values of your Inverter.

The Python Script in this repository simply takes the output of this JSON file and processes its content:
1. It creates a Pie Chart and shows some values on a Tkinter GUI visualized on a 3,5" Display. 
2. It switches a GPIO pin depending on the available amount of power. This GPIO is connected to a Relais which switches
a wall plug.

Rough Material List for this Project:
- Raspberry Pi Zero W v1.1 
- 3,5" Display with resistive Touch
- 5V Supply (for Raspberry Pi + Display)
- 12V Supply (for Relais)
- Main Switch
- Wall Plug Socket
- Power Relais (12V Control)

What does the display show? (Sorry for the German)
- Outer Pie Chart: The current PV Sytem Power in relation to the maximum possible Power.
- Inner Pie Chart: The currently self used amount of power and the "unused" amount delivered to the grid.
Right side:
- The 3 core values
- The switch on Threshold
- Buttons for decreasing and increasing the switch on threshold
- A reset button for switching off the relais and getting to an initial state.

Note: The switch on threshold defines which amount of PV system power must be available (unused, delivered to the grid)
for the relais (gpio) to switch on. The switch off threshold is fixed to a value of 200W - drawn from the grid. This means that, if for any reason, more than 200W are drawn from the grid the switch is set to an off state.

Some more details:
- The Raspberry Pi is running on Raspberry Pi Os.
- The Python Script starts automatically after boot. This solution (with increased waiting times) worked out: [RaspPi Autostart](https://forums.raspberrypi.com/viewtopic.php?t=236186 "RaspPi Autostart")
- The Touch Screen function was flipped at the beginning. There are several suggestions
how to fix this, however the configuration that finally worked for me was inserting
a Transformation Matrix to /etc/X11/xorg.conf.d/99-calibration.conf => 0 -1 1 -1 0 1 0 0 1
- I used a reverse Diode attached to Relais coil 
- The output of the RaspPi GPIO is connected to NPN-Transistor via a Resistor. Additionally there is a pull down built in. This transistor switches the relais coil.

Pictures:
![Pic1](https://github.com/HansWurstfromBavaria/Photovoltaic-Switch/blob/main/Pictures/1.JPG?raw=true)

![Pic2](https://github.com/HansWurstfromBavaria/Photovoltaic-Switch/blob/main/Pictures/2.JPG?raw=true)

![Pic3](https://github.com/HansWurstfromBavaria/Photovoltaic-Switch/blob/main/Pictures/3.JPG?raw=true)

![Pic4](https://github.com/HansWurstfromBavaria/Photovoltaic-Switch/blob/main/Pictures/4.JPG?raw=true)