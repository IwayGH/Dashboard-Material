import sqlite3
from flask import g

DATABASE = 'dashboard_material.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def close_db(exception=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        region TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT, name TEXT, type TEXT, vendor TEXT,
        spare INTEGER DEFAULT 0, used INTEGER DEFAULT 0,
        faulty INTEGER DEFAULT 0, licensed INTEGER DEFAULT 0
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS regional_stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER, region TEXT, stock INTEGER DEFAULT 0,
        FOREIGN KEY(material_id) REFERENCES materials(id)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER, region TEXT, quantity INTEGER,
        status TEXT DEFAULT 'Pending', requested_by TEXT,
        FOREIGN KEY(material_id) REFERENCES materials(id)
    )''')

    # Default Accounts
    cursor.execute("SELECT * FROM users WHERE username='Iway'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role, region) VALUES ('Iway', 'admin123', 'Superuser', 'Jakarta')")
        cursor.execute("INSERT INTO users (username, password, role, region) VALUES ('JakartaAdmin', 'jkt123', 'Jakarta', 'Jakarta')")

    # Tabel Repairs
    cursor.execute('''CREATE TABLE IF NOT EXISTS repairs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER,
        delivery_date TEXT, delivery_dn TEXT, delivery_serial TEXT,
        inbound_date TEXT, inbound_dn TEXT, inbound_serial TEXT,
        outbound_date TEXT, outbound_dn TEXT, outbound_serial TEXT,
        repair_status TEXT, repair_date TEXT, repair_dn TEXT, repair_serial TEXT,
        FOREIGN KEY(material_id) REFERENCES materials(id)
    )''')
    
    # Tambah kolom remark jika belum ada (safe alter table)
    try:
        cursor.execute("ALTER TABLE materials ADD COLUMN remark TEXT")
    except sqlite3.OperationalError:
        pass # Kolom sudah ada
    try:
        cursor.execute("ALTER TABLE materials ADD COLUMN material_baru INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE materials ADD COLUMN after_repair INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Tambah kolom status untuk setiap tahapan repair
    try:
        cursor.execute("ALTER TABLE repairs ADD COLUMN delivery_status TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE repairs ADD COLUMN inbound_status TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE repairs ADD COLUMN outbound_status TEXT")
    except sqlite3.OperationalError:
        pass

    db.commit()

# Data Material Anda
MATERIAL_DATA = """
WBTX000029	Am-E3-6-6-CIRC-SH	Antenna	Ceragon
WBTX000066	Am-E3-6-7_8-CIRC-SH	Antenna	Ceragon
WBTX000026	ANT-6G-DP-6ft	Antenna	Need Check
WBTX000069	Am-E3-6-6-SH	Antenna	Need Check
WBTX000062	Am-E3-6-7_8-SH	Antenna	Ceragon
WBTX000025	ANT-6G-DP-4ft	Antenna	Need Check
WBTX000006	7G/8G 1.2m HP ANTENNA	Antenna	Need Check
WBTX000018	ANT-15G-DP-4ft	Antenna	Need Check
WBTX000081	ANT,AFT,10,125-11.700GHz,DP,RFU-CTYPE/CIRCULAR,E3	Antenna	Ceragon
WBTX000061	Am-E3-4-7_8-Sh	Antenna	Need Check
WBTX000040	AN-4711-0	Antenna	Need Check
WBTX000065	Am-E3-4-7_8-CIRC-SH	Antenna	Ceragon
WBTX000051	AN-4688-0	Antenna	Need Check
WBTX000080 	ANT,4FT,10.125-11.700GHz,Sp	Antenna	Need Check
WBTX000045 	AN-4706-0	Antenna	Need Check
WBTX000075 	ANT-23G-DP-4ft	Antenna	Need Check
WBTX000044 	AN-4690-0	Antenna	Need Check
WBTX000068	AN-4698-0	Antenna	Need Check
WBTX000011	ANT-11G-DP-4ft	Antenna	Need Check
WBTX000009 	ANT-11-SP-4ft	Antenna	Need Check
WBTX000056 	AN-4689-0	Antenna	Need Check
WBBF000072 	MOUNTING BRACKET Pole Mount 6G ANT:N-Connector,ODU:R70	Mountig	Need Check
WBBF000010 	ANC-23G-HYBRID-ANT:R220-ODU:Direct	Bracket ODU	Need Check
WBZJ000037 	VR2-MDP-1200MB	IDU	NEC
WBBF000035 	IP-20_MIMO_Prot_mng_cbl_20m	Cable Protection	Ceragon
WBZJ000171 	IP-20C-HP-7-161F-5W6-L- ESS	IP-20C	Ceragon
WBZJ000104	MK-7404-0	Adapter	Need Check
WBZJ000170	IP-20C-HP-7-161F-5W6-H-ESS	IP-20C	Ceragon
WBBF000011	ANC-7/8G-BRACKET(Pole)	Bracket Mounting	Need Check
WBBF000090	Standard Material Portion Full Ethernet 2x(1+1 SD)	Installation Material	Ceragon
WBBF000089	Radio Portion Full Ethernet 2x(1+1 SD)	Installation Material	Ceragon
WBBF000015	ANC-11G-BRACKET(Pole)	Bracket Mounting	Need Check
WBBF000014 	ANC-6G-BRACKET(Pole)-ANT:PDR70	Bracket Mounting	NEC
WBBF000018 	ANC-FlexWG-11G-UDR100-UDR100	Waveguide	Ceragon
WBBF000016 	RF-Jumper-F1A-PNMNM-1M-COM-1+0	Cable Jumper	NEC
WBBF000095 	RF Jumper Cable N(M)-1M-N(M) F1A-PNMNM-1M, CBG-001829-600, COM 1+0+Transducer 6G	Cable Jumper	NEC
WBBF000024 	IF-Connector-300BPTR-C	IF Connector	NEC
WBZJ000040 	IPASO OPT MODEM-EV	Modem EV	NEC
WBZJ000016	TRP-8G-2E-311M-Lo-C-N	ODU	NEC
WBTX000050	Am-E3-2-13-SH	Antenna	Ceragon
WBTX000037	Am-E3-1-23-CIRC-SH	Antenna	Ceragon
WBTX000049	Am-E3-1-13-SH	Antenna	Ceragon
WBTX000020	ANT-23G-SP-1ft	Antenna	Need Check
WBTX000096	ANT,2FT,10.125-11.700GHz,DP	Antenna	Need Check
WBTX000079	ANT,2FT,10.125-11.700GHz,SP,RFU-C TYPE/UBR100,E3	Antenna	Ceragon
WBZJ000115	TRP-6G-1F-340M-Lo-F	ODU	NEC
WBZJ000015	TRP-8G-2E-311M-Up-C-N	ODU	NEC
WBZJ000114	TRP-6G-1F-340M-Up-F	ODU	NEC
WBZJ000116	TRP-6G-1F-340M-Up-G	ODU	NEC
WBZJ000117 	TRP-6G-1F-340M-Lo-G	ODU	NEC
WBBF000009 	ANC-15G-HYBRID-ANT:R140-ODU:Direct	Bracket ODU	Need Check
WBZJ000239	TRP-6G-2E-340M-Up-F-N	ODU	NEC
WBZJ000240	TRP-6G-2E-340M-Lo-F-N	ODU	NEC
WBBF000081	Installation material for radio portion full ethernet 1 hop [1+0]	Installation Material	Ceragon
WBBF000082 	nstallation material for standard material portion full ethernet 1 hop [1+0]	Installation Material	Ceragon
WBZJ000027 	TRP-15G-1F-490M-Up-J	ODU	NEC
WBZJ000028 	TRP-15G-1F-490M-Lo-J	ODU	NEC
WBZJ000033 	TRP-15G-1F-490M-Up-M	ODU	NEC
WBZJ000034 	TRP-15G-1F-490M-Lo-M	ODU	NEC
WBBF000019 	ANC-FlexWG-15G-UBR140-UBR140	Adapter	Ceragon
WBBF000020 	ANC-FlexWG-23G-UBR220-UBR220	Adapter	Ceragon
WBBF000083	Radio Portion Full Ethernet (2+0)	Installation Material	Ceragon
WBBF000084 	Standard Material Portion Full Ethernet (2+0)	Installation Material	Ceragon
WBBF000012 	ANC-13/15G-BRACKET(Pole)-ANT:PBR140	Bracket Mounting	Need Check
WBBF000013 	ANC-18/23G-BRACKET(Pole)-ANT:PBR220	Bracket Mounting	Need Check
WBBF000088 	Standard Material Portion Full Ethernet (1+1 SD)	Installation Material	Ceragon
WBBF000087	Radio Portion Full Ethernet (1+1 SD)	Installation Material	Ceragon
WBZJ000123	TRP-11G-1F-530M-Lo-S	ODU	NEC
WBZJ000122	TRP-11G-1F-530M-Up-S	ODU	NEC
WBZJ000144	TRP-23G-1F-1008M-Lo-C	ODU	NEC
WBZJ000143	TRP-23G-1F-1008M-Up-C	ODU	NEC
WBZJ000126	VR4-ADV-MDP-1200MB-1AA 2M2P	IDU	NEC
WBTX000033	AN-4670-0	Antenna	Need Check
WBTX000038	AN-4671-0	Antenna	Need Check
WBTX000032	AN-4648-0	Antenna	Need Check
WBZJ000105 	IP-20C_OMT_kit_23G	OMT	Ceragon
WBBF000078	IP-20C OMT kit 6GHz	OMT	Ceragon
WBZJ000067	IP-20C-OMT_kit_7-8G	OMT	Ceragon
WBZJ000069	IP-20C-HP-8-311A-1W4-H-ESS	IP-20C	Ceragon
WBZJ000068	IP-20C-HP-8-311A-1W4-L-ESS	IP-20C	Ceragon
WBZJ000255 	IP-20C-HP-11-500-6W12-H-ESS	IP-20C	Ceragon
WBZJ000256 	IP-20C DUAL SPLITTER KIT 10-11GHz	Spliiter	Ceragon
WBBF000036 	IP-20C MIMO SHARING KIT 20m	Sharing Cable	Ceragon
WBBF000061 	IP-20C_OMT_kit_10-11G	OMT	Ceragon
WBZJ000187 	IP-20S-HP-8-119A-4W6-L-ESS	IP-20S	Ceragon
WBZJ000099 	IP-20C-DUAL_SPLTR_kit_7-8G	Spliiter	Ceragon
WBZJ000057	IP-20S-E-13-266-5W8-L-ESS	IP-20S	Ceragon
WBZJ000058	IP-20S-E-13-266-5W8-H-ESS	IP-20S	Ceragon
WBZJ000070 	IP-20C-E-13-266-1W4-L-ESS	IP-20C	Ceragon
WBZJ000102 	MK-7447-0	Adapter	Need Check
WBZJ000236 	IP-20C-E-23-H-ESS	IP-20C	Ceragon
WBZJ000235 	IP-20C-E-23-L-ESS	IP-20C	Ceragon
WBZJ000223	IP-20C-HP-6H-340A-1W4-L-ESX	IP-20C	Ceragon
WBZJ000224	IP-20C-HP-6H-340A-1W4-H-ESX	IP-20C	Ceragon
WBZJ000166	IP-20C-HP-7-161F-2W3-H-ESS	IP-20C	Ceragon
WBZJ000167 	IP-20C-HP-7-161F-2W3-L-ESS	IP-20C	Ceragon
WBZJ000214 	IP-20C-HP-11-500-6W12-L-ESS	IP-20C	Ceragon
WBZJ000056	IP-20S-E-13-266-1W4-H-ESS	IP-20S	Ceragon
WBZJ000055	IP-20S-E-13-266-1W4-L-ESS	IP-20S	Ceragon
WBZJ000059	IP-20S-E-23-L-ESS	IP-20S	Ceragon
WBBF000034	IP-20C MIMO or Prot management odu spltr	Cable Protection	Ceragon
WBBF000037	SOURCE_SHARING_20M	Source Sharing Cable	Ceragon
WBBF000042	IP-20C_DC_Conn	Connector Power	Ceragon
WBBF000043	UNIV_GRD_KIT_1/2	Grounding Kit	Ceragon
WBBF000045	GBE_Connector_kit	RJ45 Connector	Ceragon
WBBF000046	CABLE,1/4 INCH TO 1/4INC - CBL-GND	Grounding Cable	Need Check
WBBF000074	ADP-WG-PDR70/NF-6H	Waveguide	NEC
WBBF000075 	PT-20C 6G Remote Mount adaptor	Adapter	Ceragon
WBBF000076 	Flex.WG kit WR-137,4 FT,(PDR70)	Waveguide	Ceragon
WBBF000077	IP-20C DUAL SPLITTER KIT 6GHz	Spliiter	Ceragon
WBZJ000060	IP-20S-E-23-H-ESS	IP-20S	Ceragon
WBZJ000071	IP-20C-E-13-266-1W4-H-ESS	IP-20C	Ceragon
WBZJ000089	IP-20C_7-8G_Rmt_Mnt_adpt	Adapter	Ceragon
WBZJ000091	IP-20C-Pole-Mount	Mountig	Ceragon
WBZJ000094	Flx-WG-4FT-7_8	Waveguide	Ceragon
WBZJ000097	LDF4-JA-15M/ LDF	Cable Jumper	Ceragon
WBZJ000098	ADP-WG-PBR84/NF	Waveguide	NEC
WBZJ000103 	IP-20C_OMT_kit_13G	OMT	Ceragon
WBZJ000156	IP-20C-HP-8-119A-1W3-H-ESS	IP-20C	Ceragon
WBZJ000157	IP-20C-HP-8-119A-1W3-L-ESS	IP-20C	Ceragon
WBZJ000158	IP-20C-HP-8-119A-4W6-H-ESS	IP-20C	Ceragon
WBZJ000159	IP-20C-HP-8-119A-4W6-L-ESS	IP-20C	Ceragon
WBZJ000160	IP-20C-HP-11-500-1W6-H-ESS	IP-20C	Ceragon
WBZJ000161	IP-20C-HP-11-500-1W6-L-ESS	IP-20C	Ceragon
WBZJ000164	IP-20C-HP-7-161F-1W2-H-ESS	IP-20C	Ceragon
WBZJ000165	IP-20C-HP-7-161F-1W2-L-ESS	IP-20C	Ceragon
WBZJ000168 	IP-20C-HP-7-161F-4W5-H-ESS	IP-20C	Ceragon
WBZJ000169 	IP-20C-HP-7-161F-4W5-L-ESS	IP-20C	Ceragon
WBZJ000172	IP-20S-HP-6H-340A-1W4-H-ESS	IP-20S	Ceragon
WBZJ000173	IP-20S-HP-6H-340A-1W4-L- ESS	IP-20S	Ceragon
WBZJ000174 	IP-20S-HP-6H-340A-5W8-H-ESS	IP-20S	Ceragon
WBZJ000175	IP-20S-HP-6H-340A-5W8-L-ESS	IP-20S	Ceragon
WBZJ000176	IP-20S-HP-7-161A-2W3-H-ESS	IP-20S	Ceragon
WBZJ000177 	IP-20S-HP-7-161F-1W2-L-ESS	IP-20S	Ceragon
WBZJ000180 	IP-20S-HP-7-161F-4W5-H-ESS	IP-20S	Ceragon
WBZJ000181 	IP-20S-HP-7-161F-4W5-L-ESS	IP-20S	Ceragon
WBZJ000182 	IP-20S-HP-7-161F-5W6-H-ESS	IP-20S	Ceragon
WBZJ000183	IP-20S-HP-7-161F-5W6-L-ESS	IP-20S	Ceragon
WBZJ000186 	IP-20S-HP-8-119A-4W6-H-ESS	IP-20S	Ceragon
WBZJ000190 	IP-20S-HP-11-500-4W9-H-ESS	IP-20S	Ceragon
WBZJ000191	IP-20S-HP-11-500-4W9-L-ESS	IP-20S	Ceragon
WBZJ000192	IP-20S-HP-11-500-7W13-H-ESS	IP-20S	Ceragon
WBZJ000193 	IP-20S-HP-11-500-7W13-L-ESS	IP-20S	Ceragon
WBZJ000194 	IP-20S-E-15-490A-1W8-H-ESS	IP-20S	Ceragon
WBZJ000195	IP-20S-E-15-490A-1W8-L-ESS	IP-20S	Ceragon
WBZJ000196	IP-20S-E-15-490B-9W16-H-ESS	IP-20S	Ceragon
WBZJ000197	IP-20S-E-15-490B-9W16-L-ESS	IP-20S	Ceragon
WBZJ000221	IP-20C-HP-6H-340A-5W8-L-ESS	IP-20C	Ceragon
WBZJ000222	IP-20C-HP-6H-340A-5W8-H-ESS	IP-20C	Ceragon
WBZJ000225	IP-20C-HP-6H-340A-5W8-L-ESX	IP-20C	Ceragon
WBZJ000226 	IP-20C-HP-6H-340A-SW8-H-ESX	IP-20C	Ceragon
WBZJ000231	IP-20C-HP-7-161F-4W5-H-ESX	IP-20C	Ceragon
WBZJ000232	IP-20C-HP-7-161F-4W5-L-ESX	IP-20C	Ceragon
WBZJ000233	IP-20C-HP-7-161F-5W6-H-ESX	IP-20C	Ceragon
WBZJ000234	IP-20C-HP-7-161F-5W6-L-ESX	IP-20C	Ceragon
WBBF000047	SI-0027-0	Adapter	Need Check
WBTX000055	Am-E3-2-13-CIRC-SH	Antenna	Ceragon
WBTX000043	Am-E3-2-15-SH	Antenna	Need Check
WBTX000002	ANT-7/8G-SP-4ft	Antenna	Need Check
WBTX000046	ANT,2FT,14.400-15.350GHz,SP,RFU-C TYPE/UBR140,E3	Antenna	Ceragon
WBTX000013	ANT-15G-SP-1ft	Antenna	Need Check
WBTX000024	ANT-23G-DP-2ft	Antenna	Need Check
WBTX000014	ANT-15G-SP-2ft	Antenna	Need Check
WBBF000023	IF-Cable-CNT-300A	IF Cable	NEC
WBBF000038	Outdoor_DC_cbl_2x18AWG_drum( 1 lot = 0,5 drum=152m )	Outdoor Power Cable	Ceragon
WBBF000040	CAT5E_SFUTP_Outdoor_305m_drum	LAN Cable	Ceragon
WBTX000031	Ant Pol mount 4-6FT	Mountig	Need Check
WBBF000027	ANT-MOUNT-1.8	Mountig	Need Check
WBBF000025-GMT	ANT-MOUNT-0.6	Mountig	Need Check
WBBF000025-SST	ANT-MOUNT-0.6	Mountig	Need Check
WBTX000030	Ant Pol mount 1-3FT	Mountig	Need Check
WBBF000032	ADDITIONAL BRACKET FIX STRUT FOR ANTENNA	Bracket Fix Strut	Need Check
WBBF000026	ANT-MOUNT-1.2	Mountig	Need Check
WBZJ000049	IP-20S-HP-7-161A-1W2-L-ESS	IP-20S	Ceragon
WBZJ000050 	IP-20S-HP-7-161A-1W2-H-ESS	IP-20S	Ceragon
WBZJ000051 	IP-20S-HP-7-161A-2W3-L-ESS	IP-20S	Ceragon
WBZJ000052 	IP-20S-HP-7-161A-2W3-H-ESS	IP-20S	Ceragon
WBZJ000227 	IP-20C-HP-7-161F-1W2-H-ESX	IP-20C	Ceragon
WBZJ000228 	IP-20C-HP-7-161F-1W2-L-ESX	IP-20C	Ceragon
WBZJ000188 	IP-20S-HP-11-500-1W6-H-ESS	IP-20S	Ceragon
WBZJ000178 	IP-20S-HP-7-161F-2W3-H-ESS	IP-20S	Ceragon
WBZJ000179 	IP-20S-HP-7-161F-2W3-L-ESS	IP-20S	Ceragon
WBZJ000189 	IP-20S-HP-11-500-1W6-L-ESS	IP-20S	Ceragon
WBTX000052 	ANT,4FT,12.750-13.250GHz,SP,RFU-C TYPE/UBR120,E3	Antenna	Ceragon
WBZJ000100 	IP-20C_DUAL_SPLTR_kit_13G	Spliiter	Ceragon
WBTX000042 	Am-E3-1-15-SH	Antenna	Need Check
WBTX000059 	ANT,2FT,7.125- 8.500GHz,SP,RFU-C TYPE/UBR84,E3	Antenna	Ceragon
WBZJ000074 	IP-20S-HP-8-311A-5W8-L-ESS	IP-20S	Ceragon
WBZJ000075 	IP-20S-HP-8-311A-5W8-H-ESS	IP-20S	Ceragon
WBBF000098 	GRND CABLE 16MM2	Grounding Cable	Need Check
WBBF000099 	6AWG _38in Blue Termn	Outdoor Power Cable	Ceragon
WBZJ000220 	IP-20C-HP-6H-340A-1W4-H-ESS	IP-20C	Ceragon
WBZJ000219 	IP-20C-HP-6H-340A-1W4-L-ESS	IP-20C	Ceragon
KSSID0400000095 	Cable 16mm2 (10 M) with connector	Grounding Cable	Need Check
WBTX000057 	ANT,4FT,12.750- 13.250GHz,SP,RFU-C TYPE/CIRC,E3	Antenna	Ceragon
WBZJ000162 	IP-20C-E-13-266-5W8-H- ESS	IP-20C	Ceragon
WBZJ000163 	IP-20C-E-13-266-5W8-L- ESS	IP-20C	Ceragon
WBZJ000073 	IP-20S-HP-8-311A-1W4- H-ESS	IP-20S	Ceragon
WBZJ000072 	IP-20S-HP-8-311A-1W4- L-ESS	IP-20S	Ceragon
KSSID0400000094 	Alumunium busbar 300x100x10mm 14 hole for M8 bolt	Busbar	Need Check
WBZJ000038 	VR4-MDP-1200MB-1AA 2M2P	IDU	NEC
WBTX000072 	Ant Pol mount 8-12FT	Mountig	Need Check
WBTX000098 	ANT,8FT,5.925- 7.125GHz,DP,PDR70	Antenna	Need Check
WBBF000071 	ANC 7/8G BRACKET (Pole) ANT:N	Bracket Mounting	Need Check
WBZJ000247 	TRP-7G-1F-161M-Up-J	ODU	NEC
WBZJ000248 	TRP-7G-1F-161M-Lo-J	ODU	NEC
WBZJ000249 	TRP-7G-1F-161M-Up-K	ODU	NEC
WBZJ000250 	TRP-7G-1F-161M-Lo-K	ODU	NEC
WBZJ000253 	TRP-8G-1F-311M-Up-D	ODU	NEC
WBZJ000254 	TRP-8G-1F-311M-Lo-D	ODU	NEC
WBZJ000251 	TRP-8G-1F-311M-Up-C	ODU	NEC
WBZJ000252 	TRP-8G-1F-311M-Lo-C	ODU	NEC
WBZJ000243 	TRP-7G-1F-161M-Up-G	ODU	NEC
WBZJ000244 	TRP-7G-1F-161M-Lo-G	ODU	NEC
WBZJ000029 	TRP-15G-1F-490M-Up-K	ODU	NEC
WBZJ000030 	TRP-15G-1F-490M-Lo-K	ODU	NEC
WBZJ000031 	TRP-15G-1F-490M-Up-L	ODU	NEC
WBZJ000032 	TRP-15G-1F-490M-Lo-L	ODU	NEC
WBZJ000112 	TRP-6G-1F-340M-Up-E	ODU	NEC
WBZJ000113 	TRP-6G-1F-340M-Lo-E	ODU	NEC
WBZJ000262 	TRP-8G-2F-311M-Up-D	ODU	NEC
WBZJ000263 	TRP-8G-2F-311M-Lo-D	ODU	NEC
WBZJ000264 	TRP-6G-2F-340M-Up-E	ODU	NEC
WBZJ000265 	TRP-6G-2F-340M-Lo-E	ODU	NEC
WBZJ000266 	TRP-6G-2F-340M-Up-G	ODU	NEC
WBZJ000267 	TRP-6G-2F-340M-Lo-G	ODU	NEC
WBZJ000261 	IP-20C-HP-8-311A-1W4-L-ESX	IP-20C	Ceragon
WBTX000099 	SH Circular Trans 7.125 - 8.500GHz	Circular Adapter	Ceragon
WBZJ000155 	IP-20C-HP-8-311A-5W8-L-ESS	IP-20C	Ceragon
WBZJ000154 	IP-20C-HP-8-311A-5W8-H-ESS	IP-20C	Ceragon
WBZJ000260 	IP-20C-HP-8-311A-1W4-H-ESX	IP-20C	Ceragon
WBZJ000215 	IP-20C-HP-11-500-7W13-L-ESS	IP-20C	Ceragon
WBZJ000216 	IP-20C-HP-11-500-7W13-H-ESS	IP-20C	Ceragon
WBZJ000305 	NEC 调制解调盘-EV	Modem EV	NEC
WBTX000005 	ANT-7/8G-DP-2ft	Antenna	Need Check
WBBF000025 	ANT-MOUNT-0.6	Mountig	Need Check
WBBF000091 	INST-MAT-RADIO-4+0	Installation Material	Ceragon
WBBF000092 	INST-MAT-STANDARD- MATERIAL-4+0	Installation Material	Ceragon
WBZJ000127 	TRP-8G-1E-311M-Up-C-N	ODU	NEC
WBZJ000128 	TRP-8G-1E-311M-Lo-C-N	ODU	NEC
WBZJ000258 	IP-20C-E-15-490A-1W8-L-ESS	IP-20C	Ceragon
WBZJ000259 	IP-20C-E-15-490A-1W8-H-ESS	IP-20C	Ceragon
WBZJ000198 	IP-20S-E-13-266A-3W5-H-ESS	IP-20S	Ceragon
WBZJ000199 	IP-20S-E-13-266A-3W5-L-ESS	IP-20S	Ceragon
WBZJ000047 	IP-20C-E-13-266-1W4-L-ESX	IP-20C	Ceragon
WBZJ000218 	IP-20C-HP-11-500-4W9-H-ESS	IP-20C	Ceragon
WBZJ000217 	IP-20C-HP-11-500-4W9-L-ESS	IP-20C	Ceragon
WBZJ000184 	IP-2-0S-HP-8-119A-1W3-H-ESS	IP-20S	Ceragon
WBZJ000229 	IP-20C-HP-7-161F-2W3-H-ESX	IP-20C	Ceragon
WBZJ000268 	IP-20C-HP-7-161A-1W2-L-ESS	IP-20C	Ceragon
WBZJ000257 	IP-20C-HP-7-161A-1W2-H-ESS	IP-20C	Ceragon
WBZJ000185 	IP-20S-HP-8-119A-1W3-L- ESS	IP-20S	Ceragon
WBTX000001 	7G/8G 0.6m HP ANTENNA	Antenna	Need Check
WBZJ000327 	TRP-8G-2F-311M-Up-C	ODU	NEC
WBZJ000328 	TRP-8G-2F-311M-Lo-C	ODU	NEC
WBZJ000329 	TRP-6G-2F-340M-Up-F	ODU	NEC
WBZJ000330 	TRP-6G-2F-340M-Lo-F	ODU	NEC
WBZJ000039 	VR10-MDP-1200MB-1BB	IDU	NEC
Part of WBTX000046 	RFU-C15-OMT-D14-KIT	OMT	Ceragon
Part of WBTX000029 	Am-E3-6-6-CIRC-SH (MW bolts)	Circular Adapter	Ceragon
Part of WBTX000029 	Am-E3-6-6-CIRC-SH (Feedhorn)	Circular Adapter	Ceragon
Part of WBTX000029 	ANT,6FT,5.925-7.125GHz,SP,RFU-C TYPE/CIRC,E3	Antenna	Ceragon
Part of WBTX000031 	Ant Pol mount 4-6FT	Mountig	Need Check
WBZJ000230 	IP-20C-HP-7-161F-2W3-L-ESX	IP-20C	Ceragon
WBZJ000196-NEW 	IP-20C-E-15-490B-9W16-H-ESS	IP-20C	Ceragon
WBZJ000197-NEW 	IP-20C-E-15-490B-9W16-L-ESS	IP-20C	Ceragon
Part of WBBF000028 	Bracket-Fix-Strut (Part of Antenna Mounting 2.4)	Bracket Fix Strut	Need Check
Part of WBTX000025,26,27 	Part of WBTX000025,26,27	Need check	Need Check
Part of WBTX000027 	Side Strut (Part of Antenna 6G DP 2.4m)	Bracket Fix Strut	Need Check
Part Of WBTX00030 	Part Of WBTX00030	Need check	Need Check
Part of WBZJ000126 	Part of WBZJ000126	Need check	Need Check
part of WXTB000068 	Am-E3-4-6-SH	Antenna	Need Check
WBZJ000129 	TRP-8G-1E-311M-Up-D-N	ODU	NEC
part of WBTX000030 	U BOLT MOUNTING MW - part of WBTX000030	U Bolt	Need Check
Part of WBTX000056 	Am-E3-3-13-CIRC-SH	Antenna	Ceragon
Part of WBTX000065 	Am-E3-4-7_8-CIRC-SH	Antenna	Ceragon
Part of WBTX0000207 	ANT,2FT,12.750-13.250GHz,SP,RFU-C TYPE/CIRC,E3	Antenna	Ceragon
Part of WBTX000055 	ANT,4FT,7.125-8.500GHz,SP,RFU-C TYPE/CIRC,E3	Antenna	Ceragon
SM80971410204-ID 	Bakti OM NEC IDU Repair VR4 ADV(Jakarta)	IDU	NEC
WBZJ000048 	IP-20C-E-13-266-1W4-H-ESX	IP-20C	Ceragon
WBZJ000053 	IP-20S-HP-7-161A-3W4-L-ESS	IP-20S	Ceragon
WBZJ000054 	IP-20S-HP-7-161A-3W4-H-ESS	IP-20S	Ceragon
Fan of WBZJ000038 	Fan of VR4-MDP-1200MB-1AA 2M2P	Fan IDU	NEC
WBTX000207 	Am-E3-1-23-SH	Antenna	Ceragon
SM80971410161-ID 	Bakti OM NEC IDU Repair(Jakarta)	IDU	NEC
SM80971410203-ID 	Bakti OM NEC IDU Repair VR4(Jakarta)	IDU	NEC
SM80971410164-ID 	Bakti OM NEC Modem EV Repair(Jakarta)	Modem EV	NEC
WBZJ000017 	TRP-8G-2E-311M-Up-D-N	ODU	NEC
WBZJ000018 	TRP-8G-2E-311M-Lo-D-N	ODU	NEC
WBZJ000120 	TRP-8G-1F-311M-Up-D-N	ODU	NEC
WBZJ000121 	TRP-8G-1F-311M-Lo-D-N	ODU	NEC
WBZJ000130 	TRP-8G-1E-311M-Lo-D-N	ODU	NEC
WBZJ000200 	TRP-6G-1E Subband E High/340MHz IAG N type	ODU	NEC
WBZJ000201 	TRP-6G-1E Subband E Low/340MHz IAG N type	ODU	NEC
WBZJ000212 	TRP-7G-1F-161M-Up-K-N	ODU	NEC
WBZJ000213 	TRP-7G-1F-161M-Lo-K-N	ODU	NEC
WBZJ000237 	TRP-6G-2E-340M-Up-E-N	ODU	NEC
WBZJ000238 	TRP-6G-2E-340M-Lo-E-N	ODU	NEC
WBZJ000241 	TRP-6G-2E-340M-Up-G-N	ODU	NEC
WBZJ000242 	TRP-6G-2E-340M-Lo-G-N	ODU	NEC
SM80971400159-ID	Bakti OM Caragon ODU Repair(IP-20C)	IP-20C	Ceragon
SM80961710208-ID	Bakti OM Ceragon ODU Repair(IP-20S)	IP-20S	Ceragon
"""

def seed_materials():
    db = get_db()
    cursor = db.cursor()
    
    regions = ['Jakarta', 'Kalimantan', 'Maluku', 'Natuna', 'NTT', 'Sumatera', 'Sulawesi']
    seen = set()
    
    for line in MATERIAL_DATA.strip().split('\n'):
        parts = tuple(p.strip() for p in line.split('\t'))
        if len(parts) == 4 and parts not in seen:
            seen.add(parts)
            code, name, mtype, vendor = parts
            
            # Cek apakah material dengan kode ini sudah ada di database
            cursor.execute("SELECT id FROM materials WHERE code=?", (code,))
            mat = cursor.fetchone()
            
            if not mat:
                # Jika belum ada, insert material baru
                cursor.execute("INSERT INTO materials (code, name, type, vendor) VALUES (?, ?, ?, ?)", parts)
                mat_id = cursor.lastrowid
                
                # Buatkan stock kosong (0) untuk semua regional
                for reg in regions:
                    cursor.execute("INSERT INTO regional_stocks (material_id, region, stock) VALUES (?, ?, 0)", (mat_id, reg))
                    
    db.commit()