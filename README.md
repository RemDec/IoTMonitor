# IoTMonitor
Home network supervision tool and framework for DIY integration mainly focusing IoT security flaws, using several multi-purposes scanners and trafic analyzers.

The application provides a home network control center through building a network map of all users connected appliances and an automated scanning system. Scanners rely on already written tools covering a wide range of purposes like **network discovery, related CVEs highlighting, default credentials bruteforcing, penetration testing,** ... based on *nmap*, *searchsploit*, *vulscan*, *IoTSeeker*, *metasploit* etc. 

The application is built integrating a **framework** so that programmers can easily integrate new tools in the application. It can be done simply extending already for this purpose written code or building from scratch following a given interface that the core of the app is able to understand.
### Main goals and features
* Home network overview with all connected devices and their characteristics : MAC & IP adresses, manufacturer, model, firmware, ports & services, used protocols ...

* Automated network security monitoring routine with email alert following threats discovery

* Flexible user interactivity : easy routine configuration, manual virtual device creation and fields completion, routine independant scripts launching, settable script parameters 

* Generic new monitoring modules definition : overlayer of real launched scripts like nmap can easily be written in Python and integrated in the app following an already provided skeleton architecture   

* Global logging facilities and information aggregation from tools outputs

This project is IoT devices oriented since these connected objects are very well suited attack vectors to get control over a poorly monitored home network. However, all devices in such network will be considered and analyzed by the application (PCs, router, smartphones, servers, ...). 

### Requirements
Ideally this application should run in a standalone device connected in the network to monitor. To use its full set of features, a superuser access is necessary.

#### Needed
* Superuser rights
* Linux distribution with Python >=3.6 available 
* Network interface and IP address in the target network
* Underlying tools installed : *nmap*, *Snort*, *metasploit* and so on (detailed in modules requirements)

#### Optional
* Second wireless network interface monitor mode enabled for sniffing
* Configurable router for trafic duplication towards device where the app is running
