import pexpect, pyotp, pytz, re, base64, requests
import datetime, time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

##############################################################################################
#### Note
#### NX-OS will be required when N3K work on BB
##############################################################################################
PSK = 'XXXXXX'        # SSH Public Key file location for SSH connection
KSS_SVR = 'XXXXXX'    # Jump Server hostname
ID = 'XXXXXX'         # Account name
PWENC = 'XXXXXX'      # Encrypted password with base64
PW = base64.b64decode(PWENC).decode('ascii')
KSSJPOTP = pyotp.TOTP('XXXXXX').now()     # Google OTP secret key for second authentication
Format = "%Y-%m-%d %H:%M"
NIDB_SW_List_API = 'XXXXXX.jsp'     # DB API
IHMS_POP_List_API = 'XXXXXX.jsp'    # DB API

SubnetMaskRe = re.compile(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/[0-9]{1,2}')
NETWMRe = re.compile('NETWM-[0-9]{1,6}')
ChromeDRV = 'XXXXXX'                # ChomeDriver location
ISSUE = 'https://issues.cdnetworks.com'
MasterPM = 'https://issues.cdnetworks.com/browse/GNOC-1802'
WikiPM = 'https://wiki.cdnetworks.com/confluence/display/infratech/2019+Vendor+Maintenance+Schedule'
DenyPolicyName = ''
CMD_DIC = {}
##############################################################################################
def Query_NIDB(CDNWC):
    SW_DIC = {}
    data = requests.get(IHMS_POP_List_API).text
    POP_List = data.splitlines()

    for i in POP_List:
        if CDNWC in i:
            NGPC = i.split('|')[1]
            Region = i.split('|')[-4]
    '''
    NGPC = 'inx1-ams'
    Region = 'EU'
    '''
    data = requests.get(NIDB_SW_List_API).text
    SW_List = data.splitlines()
    for i in SW_List:
        if NGPC in i and 'bb' in i:
           SW_DIC[i.split(':')[0]] = i.split(':')[-1]
    return SW_DIC, Region
def DisplayText(BF, AFT):
    DT = (BF + AFT)
    Z = bytes.decode(DT)
    print(Z)
def Convert_TimeZone(StartT, EndT):
    KSTZ = pytz.timezone("Asia/Seoul")
    PDTZ = pytz.timezone("US/Pacific")
    GMTZ = pytz.timezone("GMT")

    STT = datetime.datetime.strptime(StartT, Format)
    STT = GMTZ.localize(STT)

    EDT = datetime.datetime.strptime(EndT, Format)
    EDT = GMTZ.localize(EDT)

    GMTST = STT.astimezone(GMTZ).strftime(Format)
    KSTST = STT.astimezone(KSTZ).strftime(Format)
    PDTST = STT.astimezone(PDTZ).strftime(Format)

    GMTET = EDT.astimezone(GMTZ).strftime(Format)
    KSTET = EDT.astimezone(KSTZ).strftime(Format)
    PDTET = EDT.astimezone(PDTZ).strftime(Format)

    return GMTST, GMTET, KSTST, KSTET, PDTST, PDTET
def MakePMContents(Title, StartT, EndT, Reason, Reporter, Reporter_Team):
    Contents = '1.PM Title: ' + Title + '\n'
    Contents += '2.PM team / Owner Name / Contact information: '+Reporter_Team+' / '+Reporter+' / '+Reporter+'@cdnetworks.com\n'
    Contents += '3.PM date / Duration: ' + StartT + ' ~ ' + EndT + ' GMT\n'
    Contents += '4.PM purpose: ' + Reason + '\n'
    Contents += '5.PM information:\n'
    Contents += ' a.Traffic will be detoured to other circuits during the maintenance.\n b.\n'
    Contents += '6.PM estimated symptom / affected service:\n'
    Contents += ' a.There will be no service impact since we have multiple link\n b.\n'
    Contents += '7.Expected challenging / alternative:\n a.Before change: Abort\n b.After change: Rollback\n'
    Contents += '8.Relevant team cooperation:\n a.NONE\n b.\n c.\n'
    Contents += '9.Affected customer and etc:\n a.NONE\n'
    return Contents
def SaveIntDesc_JunOS(BF, AFT):
    CID_DIC = {}
    DT = (BF + AFT)
    Z = bytes.decode(DT)
    A = Z.splitlines()
    E = -1
    for i in A:
        E += 1
        if 'BDR' in A[E] and 'up    up' in A[E]:
            CID_DIC[A[E].split()[0]] = [A[E].split()[3].split(':')[5], A[E].split()[3].split(':')[7], A[E].split()[3].split(':')[4]]
    return CID_DIC
def SaveIntConfig_JunOS(BF, AFT, port, CID_DIC):
    DT = (BF + AFT)
    Z = bytes.decode(DT)
    A = Z.splitlines()
    E = -1
    for i in A:
        E += 1
        if 'inet address' in A[E]:
            SerialIP = SubnetMaskRe.findall(A[E])[0]
            CID_DIC[port] = [CID_DIC[port][0], CID_DIC[port][1], CID_DIC[port][2], SerialIP]
    return CID_DIC
def SaveBGPConfig_JunOS(BF, AFT):
    DT = (BF + AFT)
    Z = bytes.decode(DT)
    A = Z.splitlines()
    E = -1
    BGP_Config = ''
    for i in A:
        E += 1
        if "protocols bgp group" in A[E]:
            BGP_Config += A[E]+'\n'
    return BGP_Config
def Query_Circuit_Info_JunOS(Host):
    CID_Total = []
    SS = pexpect.spawn('ssh -i ' + PSK + " -o StrictHostKeyChecking=no " + ID + "@" + KSS_SVR + " -p 2113")
    SS.expect('word: ')
    DisplayText(SS.before, SS.after)
    SS.sendline(PW)
    SS.expect('code: ')
    DisplayText(SS.before, SS.after)
    SS.sendline(KSSJPOTP)
    SS.expect('\$')
    DisplayText(SS.before, SS.after)
    SS.sendline('kss 61.110.254.54')
    try:
        SS.expect('assword: ', timeout=2)
        DisplayText(SS.before, SS.after)
        SS.sendline(PW)
    except:
        pass
    SS.expect('\$ ')
    DisplayText(SS.before, SS.after)
    SS.sendline('ssh -o StrictHostKeyChecking=no ' + ID + '@' + Host)
    SS.expect('assword: ')
    DisplayText(SS.before, SS.after)
    SS.sendline(PW)
    SS.expect(Host+'>')
    DisplayText(SS.before, SS.after)
    Circuit = '|'.join(PMTarget)
    SS.sendline('show interfaces descriptions | match "'+Circuit+'"')
    SS.expect('\{master\}')
    DisplayText(SS.before, SS.after)
    CID_DIC = SaveIntDesc_JunOS(SS.before, SS.after)
    for key in CID_DIC:
        SS.sendline('show configuration interfaces '+key+' | display set | match "inet address"')
        SS.expect('\{master\}')
        CID_DIC = SaveIntConfig_JunOS(SS.before, SS.after, key, CID_DIC)
        SS.sendline('show configuration protocols bgp | display set | match '+CID_DIC[key][0])
        SS.expect('\{master\}')
        BGP_Config = SaveBGPConfig_JunOS(SS.before, SS.after)
        CID_Total.append([Host, key, CID_DIC[key][0], CID_DIC[key][1], CID_DIC[key][2], CID_DIC[key][3], BGP_Config])
    return CID_Total
def Find_DenyPolicy(BF, AFT):
    global DenyPolicyName
    Policy_Name = ''
    DT = (BF + AFT)
    Z = bytes.decode(DT)
    A = Z.splitlines()
    E = -1
    for i in A:
        E += 1
        if "V6" in A[E] or "v6" in A[E]:
            pass
        elif len(A[E].split()) <= 2:
            pass
        else:
            if Policy_Name == A[E].split(' ')[1]:
                pass
            else:
                Policy_Name = A[E].split(' ')[1]
    DenyPolicyName = Policy_Name
def SaveIntDesc_EOS(BF, AFT):
    CID_DIC = {}
    DT = (BF + AFT)
    Z = bytes.decode(DT)
    A = Z.splitlines()
    E = -1
    for i in A:
        E += 1
        if 'BDR' in A[E] and 'up             up' in A[E]:
            CID_DIC[A[E].split()[0]] = [A[E].split()[3].split(':')[5], A[E].split()[3].split(':')[7], A[E].split()[3].split(':')[4]]
    return CID_DIC
def SaveIntConfig_EOS(BF, AFT, port, CID_DIC):
    DT = (BF + AFT)
    Z = bytes.decode(DT)
    A = Z.splitlines()
    E = -1
    for i in A:
        E += 1
        if 'ip address' in A[E]:
            SerialIP = SubnetMaskRe.findall(A[E])[0]
            CID_DIC[port] = [CID_DIC[port][0], CID_DIC[port][1], CID_DIC[port][2], SerialIP]
    return CID_DIC
def SaveBGPConfig_EOS(BF, AFT):
    DT = (BF + AFT)
    Z = bytes.decode(DT)
    A = Z.splitlines()
    E = -1
    BGP_Config = ''
    for i in A:
        E += 1
        if "neighbor" in A[E]:
            BGP_Config += A[E]+'\n'
    return BGP_Config
def Query_Circuit_Info_EOS(Host):
    CID_Total = []
    SS = pexpect.spawn('ssh -i ' + PSK + " -o StrictHostKeyChecking=no " + ID + "@" + KSS_SVR + " -p 2113")
    SS.setwinsize(2000,2000)
    SS.expect('word: ')
    DisplayText(SS.before, SS.after)
    SS.sendline(PW)
    SS.expect('code: ')
    DisplayText(SS.before, SS.after)
    SS.sendline(KSSJPOTP)
    SS.expect('\$ ')
    DisplayText(SS.before, SS.after)
    SS.sendline('kss 121.78.64.102')
    try:
        SS.expect('Password: ', timeout=2)
        DisplayText(SS.before, SS.after)
        SS.sendline(PW)
    except:
        pass
    SS.expect('\$ ')
    DisplayText(SS.before, SS.after)
    SS.sendline('ssh -o StrictHostKeyChecking=no '+ID+'@'+Host)
    SS.expect('Password: ')
    DisplayText(SS.before, SS.after)
    SS.sendline(PW)
    SS.expect(Host+'#')
    DisplayText(SS.before, SS.after)
    Circuit = '|'.join(PMTarget)
    SS.sendline('show run | i ^route-map.*DENY-ANY')
    SS.expect(Host+'#')
    DisplayText(SS.before, SS.after)
    Find_DenyPolicy(SS.before, SS.after)
    SS.sendline('show inter description | i '+Circuit)
    SS.expect(Host+'#')
    DisplayText(SS.before, SS.after)
    CID_DIC = SaveIntDesc_EOS(SS.before, SS.after)
    for key in CID_DIC:
        SS.sendline('show run interfaces '+key)
        SS.expect(Host+'#')
        DisplayText(SS.before, SS.after)
        CID_DIC = SaveIntConfig_EOS(SS.before, SS.after, key, CID_DIC)
        SS.sendline('show run | include '+CID_DIC[key][0]+'.*route-map')
        SS.expect(Host+'#')
        DisplayText(SS.before, SS.after)
        BGP_Config = SaveBGPConfig_EOS(SS.before, SS.after)
        CID_Total.append([Host, key, CID_DIC[key][0], CID_DIC[key][1], CID_DIC[key][2], CID_DIC[key][3], BGP_Config])
    return CID_Total
def FindInt_CER(BF, AFT):
        PortList = []
        DT = (BF + AFT)
        Z = bytes.decode(DT)
        A = Z.splitlines()
        E = -1
        for i in A:
            E += 1
            if 'Forward' in A[E]:
                PortList.append(A[E].split()[0])
        return PortList
def SaveIntDesc_CER(BF, AFT):
        Desc = []
        DT = (BF + AFT)
        Z = bytes.decode(DT)
        A = Z.splitlines()
        E = -1
        for i in A:
            E += 1
            if 'port-name' in A[E]:
                tmp_list = A[E].split(':')
                Desc = [tmp_list[5], tmp_list[7], tmp_list[4]]
            if 'ip address' in A[E]:
                SerialIP = SubnetMaskRe.findall(A[E])[0]
                Desc.append(SerialIP)
        return Desc
def Query_Circuit_Info_CER(Host):
    CID_DIC = {}
    CID_Total = []
    SS = pexpect.spawn('ssh -i ' + PSK + " -o StrictHostKeyChecking=no " + ID + "@" + KSS_SVR + " -p 2113")
    SS.setwinsize(2000,2000)
    SS.expect('word: ')
    DisplayText(SS.before, SS.after)
    SS.sendline(PW)
    SS.expect('code: ')
    DisplayText(SS.before, SS.after)
    SS.sendline(KSSJPOTP)
    SS.expect('\$ ')
    DisplayText(SS.before, SS.after)
    SS.sendline('kss '+Host+'.net.cdngp.net '+ID)
    try:
        SS.expect('Password:', timeout=2)
        DisplayText(SS.before, SS.after)
        SS.sendline(PW)
    except:
        pass
    SS.expect('word:')
    DisplayText(SS.before, SS.after)
    SS.sendline(PW)
    SS.expect(Host+'#')
    DisplayText(SS.before, SS.after)
    SS.sendline('show run | i ^route-map.*DENY-ANY')
    SS.expect('#')
    Find_DenyPolicy(SS.before, SS.after)
    SS.sendline('show interface bri | i Up.*BDR')
    SS.expect('#')
    Port = FindInt_CER(SS.before, SS.after)
    E = -1
    for i in Port:
        E += 1
        SS.sendline('show run interface eth '+Port[E])
        SS.expect('#')
        Desc = SaveIntDesc_CER(SS.before, SS.after)
        F = -1
        for i in PMTarget:
            F += 1
            if PMTarget[F] in Desc[1]:
                CID_DIC[Port[E]] = [Desc[0], Desc[1], Desc[2], Desc[3]]
            else:
                pass
    for key in CID_DIC:
        SS.sendline('show run | include '+CID_DIC[key][0]+'.*route-map')
        SS.expect('#')
        BGP_Config = SaveBGPConfig_EOS(SS.before, SS.after)
        CID_Total.append([Host, key, CID_DIC[key][0], CID_DIC[key][1], CID_DIC[key][2], CID_DIC[key][3], BGP_Config])
    return CID_Total
def GatherCircuitInfo(SWDIC):
    Target_Total = []
    for i in SWDIC.keys():
        if SWDIC[i] == 'juniper':
            Target_Total.append(Query_Circuit_Info_JunOS(i))
        elif SWDIC[i] == 'arista':
            Target_Total.append(Query_Circuit_Info_EOS(i))
        elif SWDIC[i] == 'foundry':
            Target_Total.append(Query_Circuit_Info_CER(i))
    return Target_Total
def Pre_JuniperCheckInfo(Target_CID, CINFO):
        tmp_PortList = []
        tmp_PeerList = []
        tmp_BGPList = []
        ASN = ''
        for i in range(len(Target_CID)):
            CID = Target_CID[i]
            tmp_PortList.append(CINFO[CID][2])
            tmp_PeerList.append(CINFO[CID][4])
            BGP_Config = CINFO[CID][6].split('\n')
            for j in range(len(BGP_Config)):
                tmp_BGPList.append(BGP_Config[j])
            ASN = CINFO[CID][5]
        tmp_Contents = '(0) Check traffic amount for all BDR - > Melon'
        tmp_Contents += '\n\n(1) Check interfaces status\n'
        tmp_Contents += 'show interfaces descriptions | match "' +'|'.join(tmp_PeerList)+'"'
        tmp_Contents += '\n\n(2) Check BGP Status\n'
        tmp_Contents += 'show bgp summary | match ' + ASN
        tmp_Contents += '\n\n(3) Check routing configuration\n'
        tmp_Contents += 'show configuration protocols | display set | match "'+'|'.join(tmp_PeerList)+'"'
        tmp_Contents += '\n\n(4) Check traffic rate\n'
        for i in range(len(tmp_PortList)):
            tmp_Contents += 'show interfaces ' + tmp_PortList[i] + ' | match rate'
            tmp_Contents += '\n'
        tmp_Contents += '\n(5) Check int error\n'
        for i in range(len(tmp_PortList)):
            tmp_Contents += 'show interfaces ' + tmp_PortList[i] + ' extensive | match error'
            tmp_Contents += '\n'
        tmp_Contents += '\n(6) Check interface optical Level\n'
        for i in range(len(tmp_PortList)):
            tmp_Contents += 'show interfaces diagnostics optics ' + tmp_PortList[i] + ' | match dbm'
            tmp_Contents += '\n'
        tmp_Contents += '\n(7) Change routing configuration\n'
        tmp_Contents += '===========================================================================================\n'
        tmp_Contents += 'conf\n'
        for i in range(len(tmp_BGPList)):
            if 'import' in tmp_BGPList[i] or 'export' in tmp_BGPList[i]:
                    tmp_BGPConfList = tmp_BGPList[i].split()
                    tmp_Contents += 'deactivate ' + " ".join(tmp_BGPConfList[1:8]) + '\n'
        tmp_Contents += 'show | comapre\n'
        tmp_Contents += 'commit check\n'
        tmp_Contents += 'commit and-quit\n'
        tmp_Contents += '==========================================================================================='
        tmp_Contents += '\n\n(8) Check configuration\n'
        tmp_Contents += 'show configuration protocols | display set | match "'+'|'.join(tmp_PeerList)+'"'
        tmp_Contents += '\n\n(9) Check BGP Status\n'
        tmp_Contents += 'show bgp summary | match ' + ASN
        tmp_Contents += '\n\n(10) Check traffic rate (no traffic)\n'
        for i in range(len(tmp_PortList)):
            tmp_Contents += 'show interfaces ' + tmp_PortList[i] + ' | match rate'
            tmp_Contents += '\n'
        tmp_Contents += '\n\n(11) Check traffic amount for all BDR circuits => Melon\n\n'
        return tmp_Contents
def Pre_AristaCheckInfo(Target_CID, CINFO):
        tmp_PortList = []
        tmp_PeerList = []
        tmp_IntIPList = []
        tmp_BGPList = []
        ASN = ''
        for i in range(len(Target_CID)):
            CID = Target_CID[i]
            tmp_PortList.append(CINFO[CID][2])
            tmp_PeerList.append(CINFO[CID][4])
            tmp_IntIPList.append(CINFO[CID][3])
            tmp_BGPList.append(CINFO[CID][6])
            ASN = CINFO[CID][5]
        tmp_Contents = '(0) Check traffic amount for all BDR - > Melon'
        tmp_Contents += '\n\n(1) Check interfaces status\n'
        for i in range(len(tmp_PeerList)):
            tmp_Contents += 'show ip int bri | i ' + tmp_IntIPList[i]
            tmp_Contents += '\n'
        tmp_Contents += '\n(2) Check BGP Status\n'
        tmp_Contents += 'show ip bgp summary | i ' + ASN
        tmp_Contents += '\n\n(3) Check routing configuration\n'
        for i in range(len(tmp_PeerList)):
            tmp_Contents += 'show run | i neighbor '+tmp_PeerList[i]
            tmp_Contents += '\n'
        tmp_Contents += '\n\n(4) Check traffic rate\n'
        for i in range(len(tmp_PortList)):
            tmp_Contents += 'show int ' + tmp_PortList[i] + ' | i rate'
            tmp_Contents += '\n'
        tmp_Contents += '\n(5) Check int error\n'
        for i in range(len(tmp_PortList)):
            tmp_Contents += 'show int ' + tmp_PortList[i] + ' | i CRC|error'
            tmp_Contents += '\n'
        tmp_Contents += '\n(6) Check interface optical Level\n'
        for i in range(len(tmp_PortList)):
            tmp_Contents += 'show int transceiver | i ' + tmp_PortList[i]
            tmp_Contents += '\n'
        tmp_Contents += '\n(7) Change routing configuration\n'
        tmp_Contents += '===========================================================================================\n'
        tmp_Contents += 'conf t\n'
        tmp_Contents += 'router bgp 36408\n'
        for i in range(len(tmp_BGPList)):
            BGPConfList = tmp_BGPList[i].split('\n')
            Last_tmp_BGP = ''
            for j in range(len(BGPConfList)):
                if 'route-map' in BGPConfList[j]:
                    tmp_BGPConfList = BGPConfList[j].split()
                    if Last_tmp_BGP == ' '.join(tmp_BGPConfList[0:3]):
                        pass
                    else:
                        tmp_Contents += ' '.join(tmp_BGPConfList[0:3])+' '+ DenyPolicyName +' in\n'
                        tmp_Contents += ' '.join(tmp_BGPConfList[0:3])+' '+ DenyPolicyName +' out\n'
                        Last_tmp_BGP = ' '.join(tmp_BGPConfList[0:3])
        tmp_Contents += 'end\n'
        tmp_Contents += 'wr me\n'
        tmp_Contents += '===========================================================================================\n'
        tmp_Contents += '\n\n(8) Check configuration\n'
        for i in range(len(tmp_PeerList)):
            tmp_Contents += 'show run | i neighbor '+tmp_PeerList[i]
            tmp_Contents += '\n'
        tmp_Contents += '\n(9) Check BGP Status\n'
        tmp_Contents += 'show ip bgp summary | i ' + ASN
        tmp_Contents += '\n\n(10) Check traffic rate (no traffic)\n'
        for i in range(len(tmp_PortList)):
            tmp_Contents += 'show int ' + tmp_PortList[i] + ' | i rate'
            tmp_Contents += '\n'
        tmp_Contents += '\n(11) Check traffic amount for all BDR circuits => Melon\n\n'
        return tmp_Contents
def Pre_CERCheckInfo(Target_CID, CINFO):
    global CMD_DIC
    tmp_PortList = []
    tmp_PeerList = []
    tmp_IntIPList = []
    tmp_BGPList = []
    ASN = ''
    for i in range(len(Target_CID)):
        CID = Target_CID[i]
        tmp_PortList.append(CINFO[CID][2])
        tmp_PeerList.append(CINFO[CID][4])
        tmp_IntIPList.append(CINFO[CID][3])
        tmp_BGPList.append(CINFO[CID][6])
        ASN = CINFO[CID][5]
    tmp_Contents = '(0) Check traffic amount for all BDR - > Melon'
    tmp_Contents += '\n\n(1) Check interfaces status\n'
    for i in range(len(tmp_PeerList)):
        Interface_status = 'show ip int | i ' + tmp_IntIPList[i].split('/')[0]
        CMD_DIC['Interface_status'] = Interface_status
        tmp_Contents += Interface_status
        tmp_Contents += '\n'
    tmp_Contents += '\n(2) Check BGP Status\n'
    BGP_status = 'show ip bgp summary | i ' + ASN
    CMD_DIC['BGP_status'] = BGP_status
    tmp_Contents += BGP_status
    tmp_Contents += '\n\n(3) Check routing configuration\n'
    for i in range(len(tmp_PeerList)):
        Routing_config = 'show run | i neighbor ' + tmp_PeerList[i]
        CMD_DIC['Routing_config'] = Routing_config
        tmp_Contents += Routing_config
        tmp_Contents += '\n'
    tmp_Contents += '\n\n(4) Check traffic rate\n'
    for i in range(len(tmp_PortList)):
        Traffic_rate = 'show int eth ' + tmp_PortList[i] + ' | i rate'
        CMD_DIC['Traffic_rate'] = Traffic_rate
        tmp_Contents += Traffic_rate
        tmp_Contents += '\n'
    tmp_Contents += '\n(5) Check int error\n'
    for i in range(len(tmp_PortList)):
        Interface_error = 'show int eth ' + tmp_PortList[i] + ' | i CRC|error'
        CMD_DIC['Interface_error'] = Interface_error
        tmp_Contents += Interface_error
        tmp_Contents += '\n'
    tmp_Contents += '\n(6) Check interface optical Level\n'
    for i in range(len(tmp_PortList)):
        Optical_level = 'show optic ' + tmp_PortList[i].split('/')[0] +' | i ' + tmp_PortList[i]
        CMD_DIC['Optical_level'] = Optical_level
        tmp_Contents += Optical_level
        tmp_Contents += '\n'
    tmp_Contents += '\n(7) Change routing configuration\n'
    tmp_Contents += '===========================================================================================\n'
    Apply_config = 'conf t\n'
    Apply_config += 'router bgp\n'
    for i in range(len(tmp_BGPList)):
        BGPConfList = tmp_BGPList[i].split('\n')
        Last_tmp_BGP = ''
        for j in range(len(BGPConfList)):
            if 'route-map' in BGPConfList[j]:
                tmp_BGPConfList = BGPConfList[j].split()
                if Last_tmp_BGP == ' '.join(tmp_BGPConfList[0:3]):
                    pass
                else:
                    Apply_config += ' '.join(tmp_BGPConfList[0:3]) + ' ' + DenyPolicyName + ' in\n'
                    Apply_config += ' '.join(tmp_BGPConfList[0:3]) + ' ' + DenyPolicyName + ' out\n'
                    Last_tmp_BGP = ' '.join(tmp_BGPConfList[0:3])
    Apply_config += 'end\n'
    Apply_config += 'wr me\n'
    CMD_DIC['Apply_config'] = Apply_config
    tmp_Contents += Apply_config
    tmp_Contents += '===========================================================================================\n'
    tmp_Contents += '\n\n(8) Check configuration\n'
    for i in range(len(tmp_PeerList)):
        tmp_Contents += 'show run | i neighbor ' + tmp_PeerList[i]
        tmp_Contents += '\n'
    tmp_Contents += '\n(9) Check BGP Status\n'
    tmp_Contents += 'show ip bgp summary | i ' + ASN
    tmp_Contents += '\n\n(10) Check traffic rate (no traffic)\n'
    for i in range(len(tmp_PortList)):
        tmp_Contents += 'show int ' + tmp_PortList[i] + ' | i rate'
        tmp_Contents += '\n'
    tmp_Contents += '\n(11) Check traffic amount for all BDR circuits => Melon\n\n'
    return tmp_Contents
def Post_JuniperCheckInfo(Target_CID, CINFO):
        tmp_PortList = []
        tmp_PeerList = []
        tmp_BGPList = []
        ASN = ''
        for i in range(len(Target_CID)):
            CID = Target_CID[i]
            tmp_PortList.append(CINFO[CID][2])
            tmp_PeerList.append(CINFO[CID][4])
            BGP_Config = CINFO[CID][6].split('\n')
            for j in range(len(BGP_Config)):
                tmp_BGPList.append(BGP_Config[j])
            ASN = CINFO[CID][5]
        tmp_Contents = '(0) Check traffic amount for all BDR - > Melon'
        tmp_Contents += '\n\n(1) Check interfaces status\n'
        tmp_Contents += 'show interfaces descriptions | match "' +'|'.join(tmp_PeerList)+'"'
        tmp_Contents += '\n\n(2) Check BGP Status\n'
        tmp_Contents += 'show bgp summary | match ' + ASN
        tmp_Contents += '\n\n(3) Check routing configuration\n'
        tmp_Contents += 'show configuration protocols | display set | match "'+'|'.join(tmp_PeerList)+'"'
        tmp_Contents += '\n\n(4) Check traffic rate\n'
        for i in range(len(tmp_PortList)):
            tmp_Contents += 'show interfaces ' + tmp_PortList[i] + ' | match rate'
            tmp_Contents += '\n'
        tmp_Contents += '\n(5) Check interface optical Level\n'
        for i in range(len(tmp_PortList)):
            tmp_Contents += 'show interfaces diagnostics optics ' + tmp_PortList[i] + ' | match dbm'
            tmp_Contents += '\n'
        tmp_Contents += '\n(6) Clear error count\n'
        for i in range(len(tmp_PortList)):
            tmp_Contents += 'clear interfaces statistics ' + tmp_PortList[i]
            tmp_Contents += '\n'
        tmp_Contents += '\n(7) Check connectivity\n'
        for i in range(len(tmp_PeerList)):
            tmp_Contents += 'ping ' + tmp_PeerList[i] + ' count 1000 rapid'
            tmp_Contents += '\n'
        tmp_Contents += '\n(8) Check interface error\n'
        for i in range(len(tmp_PortList)):
            tmp_Contents += 'show interfaces ' + tmp_PortList[i] + ' extensive | match error'
            tmp_Contents += '\n'
        tmp_Contents += '\n(9) Change routing configuration\n'
        tmp_Contents += '===========================================================================================\n'
        tmp_Contents += 'conf\n'
        for i in range(len(tmp_BGPList)):
            if 'import' in tmp_BGPList[i] or 'export' in tmp_BGPList[i]:
                    tmp_BGPConfList = tmp_BGPList[i].split()
                    tmp_Contents += 'activate ' + " ".join(tmp_BGPConfList[1:8]) + '\n'
        tmp_Contents += 'show | comapre\n'
        tmp_Contents += 'commit check\n'
        tmp_Contents += 'commit and-quit\n'
        tmp_Contents += '==========================================================================================='
        tmp_Contents += '\n\n(10) Check configuration\n'
        tmp_Contents += 'show configuration protocols | display set | match "'+'|'.join(tmp_PeerList)+'"'
        tmp_Contents += '\n\n(11) Check BGP Status\n'
        tmp_Contents += 'show bgp summary | match ' + ASN
        tmp_Contents += '\n\n(12) Check traffic rate (no traffic)\n'
        for i in range(len(tmp_PortList)):
            tmp_Contents += 'show interfaces ' + tmp_PortList[i] + ' | match rate'
            tmp_Contents += '\n'
        tmp_Contents += '\n(13) Check traffic amount for all BDR circuits => Melon\n\n'
        return tmp_Contents
def Post_AristaCheckInfo(Target_CID, CINFO):
        tmp_PortList = []
        tmp_PeerList = []
        tmp_IntIPList = []
        tmp_BGPList = []
        ASN = ''
        for i in range(len(Target_CID)):
            CID = Target_CID[i]
            tmp_PortList.append(CINFO[CID][2])
            tmp_PeerList.append(CINFO[CID][4])
            tmp_IntIPList.append(CINFO[CID][3])
            tmp_BGPList.append(CINFO[CID][6])
            ASN = CINFO[CID][5]
        tmp_Contents = '(0) Check traffic amount for all BDR - > Melon'
        tmp_Contents += '\n\n(1) Check interfaces status\n'
        for i in range(len(tmp_PeerList)):
            tmp_Contents += 'show ip int bri | i ' + tmp_IntIPList[i]
            tmp_Contents += '\n'
        tmp_Contents += '\n(2) Check BGP Status\n'
        tmp_Contents += 'show ip bgp summary | i ' + ASN
        tmp_Contents += '\n\n(3) Check routing configuration\n'
        for i in range(len(tmp_PeerList)):
            tmp_Contents += 'show run | i neighbor '+tmp_PeerList[i]
            tmp_Contents += '\n'
        tmp_Contents += '\n(4) Check traffic rate\n'
        for i in range(len(tmp_PortList)):
            tmp_Contents += 'show int ' + tmp_PortList[i] + ' | i rate'
            tmp_Contents += '\n'
        tmp_Contents += '\n(5) Check int error\n'
        for i in range(len(tmp_PortList)):
            tmp_Contents += 'show int ' + tmp_PortList[i] + ' | i CRC|error'
            tmp_Contents += '\n'
        tmp_Contents += '\n(6) Check interface optical Level\n'
        for i in range(len(tmp_PortList)):
            tmp_Contents += 'show int transceiver | i ' + tmp_PortList[i]
            tmp_Contents += '\n'
        tmp_Contents += '\n(7) Check connectivity\n'
        for i in range(len(tmp_PeerList)):
            tmp_Contents += 'clear counters '+tmp_PortList[i]
            tmp_Contents += '\n'
            tmp_Contents += 'ping ' + tmp_PeerList[i] + ' repeat 1000'
            tmp_Contents += '\n'
        tmp_Contents += '\n(8) Change routing configuration\n'
        tmp_Contents += '===========================================================================================\n'
        tmp_Contents += 'conf t\n'
        tmp_Contents += 'router bgp 36408\n'
        for i in range(len(tmp_BGPList)):
            BGPConfList = tmp_BGPList[i].split('\n')
            for j in range(len(BGPConfList)):
                if 'route-map' in BGPConfList[j]:
                    tmp_Contents += BGPConfList[j]+'\n'
        tmp_Contents += 'end\n'
        tmp_Contents += 'wr me\n'
        tmp_Contents += '===========================================================================================\n'
        tmp_Contents += '\n\n(9) Check configuration\n'
        for i in range(len(tmp_PeerList)):
            tmp_Contents += 'show run | i neighbor '+tmp_PeerList[i]
            tmp_Contents += '\n'
        tmp_Contents += '\n(10) Check BGP Status\n'
        tmp_Contents += 'show ip bgp summary | i ' + ASN
        tmp_Contents += '\n\n(11) Check traffic rate (no traffic)\n'
        for i in range(len(tmp_PortList)):
            tmp_Contents += 'show int ' + tmp_PortList[i] + ' | i rate'
            tmp_Contents += '\n'
        tmp_Contents += '\n(12) Check traffic amount for all BDR circuits => Melon\n\n'
        return tmp_Contents
def Post_CERCheckInfo(Target_CID, CINFO):
    global CMD_DIC
    tmp_PortList = []
    tmp_PeerList = []
    tmp_IntIPList = []
    tmp_BGPList = []
    ASN = ''
    for i in range(len(Target_CID)):
        CID = Target_CID[i]
        tmp_PortList.append(CINFO[CID][2])
        tmp_PeerList.append(CINFO[CID][4])
        tmp_IntIPList.append(CINFO[CID][3])
        tmp_BGPList.append(CINFO[CID][6])
        ASN = CINFO[CID][5]
    tmp_Contents = '(0) Check traffic amount for all BDR - > Melon'
    tmp_Contents += '\n\n(1) Check interfaces status\n'
    for i in range(len(tmp_PeerList)):
        tmp_Contents += 'show ip int | i ' + tmp_IntIPList[i].split('/')[0]
        tmp_Contents += '\n'
    tmp_Contents += '\n(2) Check BGP Status\n'
    tmp_Contents += 'show ip bgp summary | i ' + ASN
    tmp_Contents += '\n\n(3) Check routing configuration\n'
    for i in range(len(tmp_PeerList)):
        tmp_Contents += 'show run | i neighbor ' + tmp_PeerList[i]
        tmp_Contents += '\n'
    tmp_Contents += '\n(4) Check traffic rate\n'
    for i in range(len(tmp_PortList)):
        tmp_Contents += 'show int eth ' + tmp_PortList[i] + ' | i rate'
        tmp_Contents += '\n'
    tmp_Contents += '\n(5) Check int error\n'
    for i in range(len(tmp_PortList)):
        tmp_Contents += 'show int eth ' + tmp_PortList[i] + ' | i CRC|error'
        tmp_Contents += '\n'
    tmp_Contents += '\n(6) Check interface optical Level\n'
    for i in range(len(tmp_PortList)):
        tmp_Contents += 'show optic ' + tmp_PortList[i].split('/')[0] +' | i ' + tmp_PortList[i]
        tmp_Contents += '\n'
    tmp_Contents += '\n(7) Check connectivity\n'
    for i in range(len(tmp_PeerList)):
        Clear_status = 'clear statistics eth ' + tmp_PortList[i]
        CMD_DIC['Clear_status'] = Clear_status
        tmp_Contents += Clear_status
        tmp_Contents += '\n'
        Ping_test = 'ping ' + tmp_PeerList[i] + ' count 1000'
        CMD_DIC['Ping_test'] = Ping_test
        tmp_Contents += Ping_test
        tmp_Contents += '\n'
    tmp_Contents += '\n(8) Change routing configuration\n'
    tmp_Contents += '===========================================================================================\n'
    Rollback_config = 'conf t\n'
    Rollback_config += 'router bgp\n'
    for i in range(len(tmp_BGPList)):
        BGPConfList = tmp_BGPList[i].split('\n')
        for j in range(len(BGPConfList)):
            if 'route-map' in BGPConfList[j]:
                Rollback_config += BGPConfList[j] + '\n'
    Rollback_config += 'end\n'
    Rollback_config += 'wr me\n'
    CMD_DIC['Rollback_config'] = Rollback_config
    tmp_Contents += Rollback_config
    tmp_Contents += '===========================================================================================\n'
    tmp_Contents += '\n\n(9) Check configuration\n'
    for i in range(len(tmp_PeerList)):
        tmp_Contents += 'show run | i neighbor ' + tmp_PeerList[i]
        tmp_Contents += '\n'
    tmp_Contents += '\n(10) Check BGP Status\n'
    tmp_Contents += 'show ip bgp summary | i ' + ASN
    tmp_Contents += '\n\n(11) Check traffic rate (no traffic)\n'
    for i in range(len(tmp_PortList)):
        tmp_Contents += 'show int eth ' + tmp_PortList[i] + ' | i rate'
        tmp_Contents += '\n'
    tmp_Contents += '\n(12) Check traffic amount for all BDR circuits => Melon\n\n'
    return tmp_Contents
def Select_Circuit(hostname, CIR_DIC):
    CID_List = []
    for CID in CIR_DIC.keys():
        if CIR_DIC[CID][0] == hostname:
            CID_List.append(CID)
    return CID_List
def MakeSubContents(Cir_DIC):
    tmp_Contents = '===========================================================================================\n'
    tmp_Contents += '===== Work Procedures\n'
    tmp_Contents += '===========================================================================================\n'
    tmp_Contents += '===== Before Maintenance Procedures\n'
    tmp_Contents += '===========================================================================================\n'
    Host_List = []
    for CID in Cir_DIC.keys():
        if Cir_DIC[CID][0] not in Host_List:
            Host_List.append(Cir_DIC[CID][0])
    for i in range(len(Host_List)):
        hostname = Host_List[i]
        tmp_Contents += '======= Target Device : ' + hostname + '\n'
        vendor = SW_DIC[hostname]
        CID_List = Select_Circuit(hostname, Cir_DIC)
        if vendor == 'juniper':
            tmp_Contents += Pre_JuniperCheckInfo(CID_List, Cir_DIC)
        elif vendor == 'arista':
            tmp_Contents += Pre_AristaCheckInfo(CID_List, Cir_DIC)
        elif vendor == 'foundry':
            tmp_Contents += Pre_CERCheckInfo(CID_List, Cir_DIC)
    tmp_Contents += '===========================================================================================\n'
    tmp_Contents += '===== After Maintenance Procedures\n'
    tmp_Contents += '===========================================================================================\n'
    Host_List = []
    for CID in Cir_DIC.keys():
        if Cir_DIC[CID][0] not in Host_List:
            Host_List.append(Cir_DIC[CID][0])
    for i in range(len(Host_List)):
        hostname = Host_List[i]
        tmp_Contents += '======= Target Device : ' + hostname + '\n'
        vendor = SW_DIC[hostname]
        CID_List = Select_Circuit(hostname, Cir_DIC)
        if vendor == 'juniper':
            tmp_Contents += Post_JuniperCheckInfo(CID_List, Cir_DIC)
        elif vendor == 'arista':
            tmp_Contents += Post_AristaCheckInfo(CID_List, Cir_DIC)
        elif vendor == 'foundry':
            tmp_Contents += Post_CERCheckInfo(CID_List, Cir_DIC)
    tmp_Contents += '=== After the work\n'
    tmp_Contents += 'Close Maintenance work\n'
    tmp_Contents += 'NETWORK Ticket : Completed or not\n'
    tmp_Contents += 'NETWM Ticket : Completed or not\n'
    tmp_Contents += 'Update Wiki Page : Completed or not'
    return tmp_Contents
def MakeWMContents(PMTitle, StartT, EndT, SW_DIC):
        Cir_DIC = {}
        CID_list = GatherCircuitInfo(SW_DIC)
        Contents = '===========================================================================================\n'
        Contents += PMTitle+'\n'
        Contents += '===========================================================================================\n'
        Contents += '= NET PM Procedures\n'
        Contents += '=== Basic Information\n'
        Contents += '1. Check Network Ticket and Date & Time : Completed or not\n\n'
        Contents += '2. Check '+str(datetime.date.today())[:4]+' ISP Maintenance Page and Update NETWM ticket info : Completed or not\n'
        Contents += WikiPM+'\n\n'
        Contents += '3. Provider Maintenance Schedule\n'
        Contents += Convert_TimeZone(StartT, EndT)[0]+' ~ '+Convert_TimeZone(StartT, EndT)[1]+' GMT\n'
        Contents += Convert_TimeZone(StartT, EndT)[2]+' ~ '+Convert_TimeZone(StartT, EndT)[3]+' KST\n'
        Contents += Convert_TimeZone(StartT, EndT)[4]+' ~ '+Convert_TimeZone(StartT, EndT)[5]+' PDT\n\n'
        Contents += '4. Target Circuit Information'
        N = 0
        for i in range(len(CID_list)):
            N += 1
            for j in range(len(CID_list[i])):
                Hostname, Interface, CircuitIP, CircuitID = CID_list[i][j][0], CID_list[i][j][1], CID_list[i][j][5], CID_list[i][j][3]
                PeerIP, PeerASN, BGPConfig  = CID_list[i][j][2], CID_list[i][j][4], CID_list[i][j][6]
                Vendor = SW_DIC[Hostname]
                Contents += '\n-Target Circuit #'+str(N)+'\n'
                Contents += 'Hostname : '+Hostname
                Contents += '\nInterface : '+Interface
                Contents += '\nCircuit IP address : '+CircuitIP
                Contents += '\nCircuit ID : '+CircuitID+'\n'
                Cir_DIC[CircuitID] = [Hostname, Vendor, Interface, CircuitIP, PeerIP, PeerASN, BGPConfig]
        Contents += MakeSubContents(Cir_DIC)
        return Contents

class WEB_Control:
    def __init__(self,PMTitle, PMContents, WMContents, StartTime, EndTime):
        self.PMTitle = PMTitle
        self.PMContents = PMContents
        self.WMContents = WMContents
        self.IM = 'https://im.cdnetworks.com'
        self.Schedule = '/network/pm_schedule.jsp?sd=2018-10-25&pidx=0'
        self.IMCalander = 'https://im.cdnetworks.com/network/pm_cal.jsp'
        self.STTDate = StartTime.split(' ')[0]
        self.STTHour = StartTime.split(' ')[1].split(':')[0]
        self.STTMin = StartTime.split(' ')[1].split(':')[1]
        self.ENDDate = EndTime.split(' ')[0]
        self.ENDHour = EndTime.split(' ')[1].split(':')[0]
        self.ENDMin = EndTime.split(' ')[1].split(':')[1]

    def IM_PM_Scheduler(self, GNOCTicket):
        browser = webdriver.Chrome(ChromeDRV)
        browser.get(self.IM)
        time.sleep(2)

        IMUID = browser.find_element_by_id('ep_id')
        IMUID.send_keys(ID)
        time.sleep(2)
        IMUPW = browser.find_element_by_id('ep_pass')
        IMUPW.send_keys(PW)
        IMUPW.send_keys(Keys.ENTER)

        browser.get(self.IM + self.Schedule)
        time.sleep(1)

        IMTitle = browser.find_element_by_name('pm_title')
        IMTitle.send_keys(self.PMTitle)
        time.sleep(1)

        STTD = browser.find_element_by_id('start_date')
        STTD.clear()
        STTD.send_keys(self.STTDate)
        time.sleep(1)

        STTH = Select(browser.find_element_by_id('start_hour'))
        STTH.select_by_value(self.STTHour)
        time.sleep(1)

        STTM = Select(browser.find_element_by_id('start_minute'))
        STTM.select_by_value(self.STTMin)
        time.sleep(1)

        ENDD = browser.find_element_by_id('end_date')
        ENDD.clear()
        ENDD.send_keys(self.ENDDate)
        time.sleep(1)

        ENDH = Select(browser.find_element_by_id('end_hour'))
        ENDH.select_by_value(self.ENDHour)
        time.sleep(1)

        ENDM = Select(browser.find_element_by_id('end_minute'))
        ENDM.select_by_value(self.ENDMin)
        time.sleep(1)

        GMT = Select(browser.find_element_by_id('gmt'))
        GMT.select_by_value('0')
        time.sleep(1)

        IMContents = browser.find_element_by_id('pm_content')
        IMContents.send_keys(self.PMContents)
        time.sleep(1)

        IMImpact = browser.find_element_by_id('impact')
        IMImpact.send_keys('No service impact due to multiple uplink')
        time.sleep(1)

        IMPM = browser.find_element_by_id('pm_ticket')
        IMPM.send_keys(GNOCTicket)
        time.sleep(1)

        BTN = browser.find_element_by_css_selector('input[onclick*=fnSaveSchedule]')
        BTN.click()
        time.sleep(1)

        alert1 = browser.switch_to_alert()
        alert1.accept()

        alert2 = browser.switch_to_alert()
        alert2.accept()

        browser.get(self.IMCalander)
    def ISSUE_GNOC(self):
        browser = webdriver.Chrome(ChromeDRV)
        time.sleep(2)
        browser.get(ISSUE)
        time.sleep(2)
        browser.get(ISSUE)
        time.sleep(2)
        browser.switch_to_frame('gadget-0')
        time.sleep(2)

        JiraUID = browser.find_element_by_id('login-form-username')
        JiraUID.send_keys(ID)
        time.sleep(1)

        JiraUPW = browser.find_element_by_id('login-form-password')
        JiraUPW.send_keys(PW)
        time.sleep(1)

        JiraLogin = browser.find_element_by_id('login')
        JiraLogin.click()
        time.sleep(3)

        browser.get(MasterPM)
        time.sleep(2)
        browser.get(MasterPM)
        time.sleep(2)

        PMTicketCreate = browser.find_element_by_id('stqc_show')
        PMTicketCreate.click()
        time.sleep(2)

        PMSummary = browser.find_element_by_id('summary')
        PMSummary.send_keys(self.PMTitle)
        time.sleep(2)

        PMComponent = browser.find_element_by_id('components-textarea')
        PMComponent.send_keys('PM\n')
        time.sleep(2)

        PMDescription = browser.find_element_by_id('description')
        PMDescription.send_keys(self.PMContents)
        time.sleep(2)

        PMTicketSubmit = browser.find_element_by_id('create-issue-submit')
        PMTicketSubmit.click()
        time.sleep(5)
        
        browser.get(MasterPM)
        time.sleep(2)

        numbers = browser.find_elements_by_xpath('//*[@data-issuekey]')
        N = 0
        for i in numbers:
            n = int(i.get_attribute('data-issuekey').split('-')[1])
            if n > N:
                N = n
        TicketNumber = 'GNOC-'+str(N)
        return TicketNumber
    def ISSUE_NETWM(self, GNOCTicket, refNum):
        browser = webdriver.Chrome(ChromeDRV)
        time.sleep(2)
        browser.get(ISSUE)
        time.sleep(2)
        browser.get(ISSUE)
        time.sleep(2)
        browser.switch_to_frame('gadget-0')
        time.sleep(2)

        JiraUID = browser.find_element_by_id('login-form-username')
        JiraUID.send_keys(ID)
        time.sleep(1)

        JiraUPW = browser.find_element_by_id('login-form-password')
        JiraUPW.send_keys(PW)
        time.sleep(1)

        JiraLogin = browser.find_element_by_id('login')
        JiraLogin.click()
        time.sleep(3)

        browser.get(ISSUE)
        time.sleep(2)
        browser.get(ISSUE)
        time.sleep(2)

        WMTicketCreate = browser.find_element_by_id('create_link')
        WMTicketCreate.click()
        time.sleep(2)

        WMProject = browser.find_element_by_id('project-field')
        WMProject.send_keys('netwm\n')
        time.sleep(2)

        WMSummary = browser.find_element_by_id("create-issue-dialog").find_element_by_id('summary')
        WMSummary.send_keys(self.PMTitle)
        time.sleep(2)

        WMComponent = browser.find_element_by_id('components-textarea')
        WMComponent.send_keys('PM\n')
        time.sleep(2)

        WMDescription = browser.find_element_by_id('description')
        WMDescription.send_keys(self.WMContents)
        time.sleep(2)

        WMTicketSubmit = browser.find_element_by_id('create-issue-submit')
        WMTicketSubmit.click()
        time.sleep(2)

        browser.get('https://issues.cdnetworks.com/secure/QuickSearch.jspa?searchString=NETWM%20'+refNum)
        time.sleep(2)
        browser.get('https://issues.cdnetworks.com/secure/QuickSearch.jspa?searchString=NETWM%20'+refNum)
        time.sleep(10)

        Attr = browser.find_element_by_xpath('//*[@data-issue-table-model-state]')
        Info = str(Attr.get_attribute('data-issue-table-model-state'))
        TicketNumber = NETWMRe.findall(Info)[0]

        browser.get('https://issues.cdnetworks.com/browse/'+TicketNumber)
        time.sleep(2)

        More = browser.find_element_by_id('opsbar-operations_more')
        More.click()
        time.sleep(2)

        Link = browser.find_element_by_id('link-issue')
        Link.click()
        time.sleep(2)

        LinkSearch = browser.find_element_by_id('jira-issue-keys-textarea')
        LinkSearch.send_keys(GNOCTicket)
        time.sleep(2)

        LinkIssue = browser.find_element_by_name('Link')
        LinkIssue.click()
        time.sleep(5)

################# main #######################################################################

POP = 'P37-ICN'
StartTime = '2019-09-02 17:00'
EndTime = '2019-09-02 21:00'
ISP = 'SJT'
RefNum = '3394879'
PMTarget = '2017001143'
PMType = 'Emergency'
PMReason = 'Maintenance Optical Fiber'

Reporter = 'jaekyeong.yun'
Reporter_Team = 'KR Network Team'

PMTarget = PMTarget.split(',')

SW_DIC, Region = Query_NIDB(POP)

PMTitle = '[PM]['+Region+'][' + POP + '] ' + ISP + ' (' + RefNum + ') ' + PMType + ' Maintenance,' + StartTime + ' ~ ' + EndTime + ' GMT'
PMContents = MakePMContents(PMTitle, StartTime, EndTime, PMReason, Reporter, Reporter_Team)
WMContents = MakeWMContents(PMTitle, StartTime, EndTime, SW_DIC)

print(PMTitle)
print(PMContents)
print(WMContents)


GNOCTicket = WEB_Control(PMTitle,PMContents, WMContents, StartTime, EndTime).ISSUE_GNOC()
print(GNOCTicket)
WEB_Control(PMTitle,PMContents, WMContents, StartTime, EndTime).IM_PM_Scheduler(GNOCTicket)
NETWMTicket = WEB_Control(PMTitle,PMContents, WMContents, StartTime, EndTime).ISSUE_NETWM(GNOCTicket, RefNum)
time.sleep(60)
