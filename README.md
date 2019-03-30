# IoTMonitor
Home network supervision tool mainly focusing IoT security flaws, using several multi-purposes scanners and trafic analyzers.

The application provides a home network control center through building a network map of all users connected appliances and a automated scanning system. Scanners rely on already written tools covering a wide range of purposes like **network discovery, related CVEs highlighting, default credentials bruteforcing, penetration testing,** ... based on *nmap*, *searchsploit*, *vulscan*, *IoTSeeker*, *metasploit* etc. 

### Main goals
* Home network overview with all connected devices and their characteristics : MAC & IP adresses, manufacturer, model, firmware, ports & services, used protocols ...

* Automated network security monitoring routine with email alert following threats discovery

* Flexible user interactivity : easy routine configuration, manual virtual device creation and fields completion, routine independant scripts launching, settable script parameters 

* Generic new monitoring modules definition : overlayer of real launched scripts like nmap can easily be written in Python and integrated in the app following an already provided skeleton architecture   

* Global logging facilities and information aggregation from tools outputs

This project is IoT devices oriented since these connected objects are perfect attack vectors to get control over a poorly monitored home network. However, all devices in such network will be considered and analyzed by the application (PCs, router, ...). 
