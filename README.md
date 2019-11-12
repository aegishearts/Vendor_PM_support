# Vendor_PM_support
Auto internal ticketing and define preconfiguration for Vendor maintenance for Tier1 engineer

[Purpose]

When Vendor notice their Maitenance work, we have to prepare this work.
 - Traffic shift to other circuit (Apply BGP deny policy or remove static route)
 - Create internal ticket for sharing information
 - Register time window on work scheduler to announce via email
 
[Function]
 - Support GUI environment - Enter input data and show terminal output via SSH(possible to check on real time)
 - Tier1 engineer get notification from vendor, then run this script
 - Script create pre/post configuration to prepare maintenance and make internal ticket for sharing information
 - Script register this ticket and work information at scheduler
 - Scheduler send email start time - 1hour to operation unit group mail
 - All operator can recognize there is maintenance and expect event will be occurred at this DC


[Manual]
 - how to run script
        
        python Vendor_Maintenance_Auto_Ticketing.py
            Enter POP Code :                                            # Enter DC name(Country, location)
            Enter PM Start time - GMT timezone(ex: 2019-09-02 17:00):   # Enter Maintenance start time (Timezone : GMT)
            Enter PM End time - GMT timezone(ex: 2019-09-02 21:00):     # Enter Maintenance end time (Timezone : GMT)
            Enter ISP name:                                             # Enter Circuit vendor name
            Enter ISP ticket number for maintenance:                    # Enter Vendor work ticket number if they have             
            Enter target circuit ID(ex: A0001, A0002):                  # Enter maintenance target circuit ID. possible to enter multiple
            Enter maintenance type(Planned / Urgent):                   # Enter maintenance type. Scheduled urgently or not.
            Enter maintenance reason:                                   # Enter maintenance reason
            Enter engineer name:                                        # Enter our engineer name who take care this work
            Enter engineer's own team:                                  # Enter our team name that have ownership for this work

[Requirement]
 - Python higher than Version 3
 - ChromeDrive (Web Crawling with Google Chrome browser)
 - Selenium (Web Crawling)
 - PyQT5 (GUI Toolkit for Data input interface) 
    

[Supported Vendor]
 - Juniper
 - Arista
 - Cisco NXOS
 - Cisco IOS
 - Brocade / Foundry
 - Dell
 
[Note]
 - Will be added 'Huawei' vendor
 - Will merge with PM_Automation script to full automation work