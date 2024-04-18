## Python Script Operation Manual for [Data Processing](https://github.com/stachusar/network-collector/blob/main/spuber.py)
### Table of Contents
1. [Script Overview](#script-overview)
2. [Requirements](#requirements)
   - [Installing collectd](#installing-collectd)
     - [Debian/Ubuntu Systems](#debianubuntu-systems)
     - [RedHat/CentOS Systems](#redhatcentos-systems)
   - [Configuring collectd](#configuring-collectd)
     - [Finding the Network Interface Name](#finding-the-network-interface-name)
     - [Editing the Configuration File](#editing-the-configuration-file)
     - [Configuring Network Data Collection](#configuring-network-data-collection)
   - [Restarting collectd](#restarting-collectd)
3. [Script Configuration](#script-configuration)
4. [Directory Structure](#directory-structure)
5. [Running the Script](#running-the-script)
   - [Creating a Systemd Service File (.service)](#creating-a-systemd-service-file-service)
   - [Creating a Systemd Timer File (.timer)](#creating-a-systemd-timer-file-timer)
6. [Activation and Execution](#activation-and-execution)
7. [Monitoring and Logs](#monitoring-and-logs)
8. [Glossary of Terms](#glossary-of-terms)

### Script Overview
This script is designed to collect, process, and save statistical data on network traffic on a Debian server using RRD files (collectd). It aggregates hourly, daily, and monthly data and saves it to CSV files. It also allows for optional logging of script activities and data display.

### Requirements
Installation and configuration of collectd for Network Monitoring
collectd is a performance monitoring system that collects metrics from various sources and saves them in various formats, including Round-Robin Databases (RRD). To monitor a network interface such as ens3, you need to install and configure collectd as follows:

#### Installing collectd
##### Debian/Ubuntu Systems:
Open a terminal and enter the following command:

    sudo apt-get update
    sudo apt-get install collectd collectd-utils

##### RedHat/CentOS Systems:
Use the following command:

    sudo yum install epel-release
    sudo yum install collectd

### Configuring collectd
#### Finding the Network Interface Name
To check the name of your network interface on a Linux operating system, you can use the ip command, which displays detailed information about all network interfaces in the system. 
To display a list of all active interfaces, use:

    ip link show
or in shortened form:

    ip a

The output of the command will show a list of interfaces along with their assigned IP addresses and additional information. Interface names can usually be found in the first column (e.g., ens33, eth0, wlan0).

#### Editing the Configuration File
The collectd configuration file is usually located in /etc/collectd/collectd.conf.  
Open this file in a text editor:

    sudo nano /etc/collectd/collectd.conf

#### Configuring Network Data Collection:
To collect data from the network interface, you need to activate the interface plugin and the rrdtool plugin in the collectd.conf file.   
Add or uncomment the following sections:

    LoadPlugin interface
    LoadPlugin rrdtool
    <Plugin "interface">
      Interface "ens3" #interface names may vary
      IgnoreSelected false
    </Plugin>
    <Plugin rrdtool>
      DataDir "/var/lib/collectd/rrd/"
      CacheFlush 120
    </Plugin

In the above configuration, Interface "ens3" tells collectd to collect data from the ens3 interface. DataDir specifies the directory where collectd will save RRD data.

#### Restarting collectd:
After finishing the configuration, restart the collectd service for the changes to take effect:

    sudo systemctl restart collectd

### Script Configuration
Configure the following variables before running the script:
- RRD_DIR: Path to the directory with RRD files.
- STATISTIC_DIR: Path to the directory for processed statistical data.
- LOG_DIR: Path to the directory for script operation logs.
- TEST_MODE: Setting True enables testing data display, False activates normal operation mode.

### Directory Structure
The script automatically creates necessary directories for data and logs.

### Running the Script
The script can be run manually or automatically using systemd.

#### Creating a Systemd Service File (.service)
1. Create a file data_processing.service in /etc/systemd/system/.
2. Content of the file:

    [Unit]
    Description=Data processing statistical service
    [Service]
    Type=simple
    ExecStart=/usr/bin/python3 /path/to/script.py
    User=ubuntu
    Group=ubuntu
    [Install]
    WantedBy=multi-user.target

#### Creating a Systemd Timer File (.timer)
1. Create a file data_processing.timer in /etc/systemd/system/.
2. Content of the file:

    [Unit]
    Description=Triggers data processing hourly
    [Timer]
    OnCalendar=hourly

    Persistent=true
    [Install]
    WantedBy=timers.target

### Activation and Execution
Activate and start the timer:

    sudo systemctl daemon-reload
    sudo systemctl enable data_processing.timer
    sudo systemctl start data_processing.timer

### Monitoring and Logs
Logs of the script's operation can be found in LOG_DIR.  
Check the status of the service:

    systemctl status data_processing.service

### Glossary of Terms
A few key terms and elements used in this document:
- Network Interface: A network port in a computer that enables communication with other devices in a network.
- collectd: A system daemon that gathers metrics from various sources and saves them in Round-Robin Database (RRD) formats.
- RRD (Round-Robin Database): A database format that stores numeric variables; mainly used for collecting performance data.
- Plugin: An addition to collectd that extends its functionality, allowing it to gather data from various sources, including network interfaces.
- Systemd: A system and service manager for Linux operating systems, which enables management of system services.
- Service file (.service): A configuration file for systemd that specifies how a service should be launched.
- Timer file (.timer): A configuration file for systemd that defines a schedule for launching a service.
- Daemon: A computer program in Unix that runs in the background, usually without direct interaction from the user.
