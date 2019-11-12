# Vendor_PM_support
Auto internal ticketing and define preconfiguration for Vendor maintenance

[Purpose]

When Vendor notice their Maitenance work, we have to prepare this work.
 - Traffic shift to other circuit (Apply BGP deny policy or remove static route)
 - Create internal ticket for sharing information
 - Register time window on work scheduler to announce via email
 
[Requirement]
 - Python higher than Version 3
 - ChromeDrive (Web Crawling with Google Chrome browser)
 - Selenium (Web Crawling)
 - PyQT5 (GUI Toolkit for Data input interface)
 
[Procedure]
 1) Enter Vendor maintenance information - PyQT5 define data input interface with GUI
    - Location (Country / City)
    - Maintenance start time / end time (Time zone : GMT)
    - Vendor name (GTT, NTT, KDDI, Telia,....so on)
    - Vendor ticket number (Vendor notice their internal ticket number)
    - Circuit ID (Maintenance target circuit ID)
    - Maintenance reaon
 2) Script find target interface and router - Search in switch/router database with Location/Vendor name
 3) Collect current configuration and status
    - Routing status is related with target interface
    - BGP policy if BGP is used
    - Default deny policy(route-map) name for BGP announcement
 4) Script define pre-configuration for traffic shift
    *** Configure BGP policy(route-map) - Stop & Start BGP announcement, clear soft BGP session  
    - Remove traffic from target interface before start time
    - Rollback traffic to target interface after end time
    
