#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

languages = ["no", "en-GB"]

senders ={
        "no": "Meteorologisk Institutt",
        "en-GB": "MET Norway",
        }


contact={
        "no": "https://www.met.no/kontakt-oss",
        "en-GB": "https://www.met.no/en/contact-us",
}


sender = "noreply@met.no"
identifier_prefix= "2.49.0.1.578.0."
web = "https://www.met.no/vaer-og-klima/farevarsel-og-ekstremvaer"

instructions={
        "no":u"",
        "en-GB": u""
}

responseType = "Monitor"
urgency = "Future"

geographicDomain={
"wind":"land",
"snow":"land",
"blowingSnow":"land",
"drivingConditions": "land",
"thunder":"land",
"fog":"land",
"highTemperature":"land",
"lowTemperature":"land",
"stormSurge":"land",
"forestFire":"land",
"avalanches":"land",
"rain":"land",
"flooding":"land",
"rainFlood":"land",
"polarLow":None,
"gale":"marine",
"icing":"marine",
"uvRadiation": None,
"pollen": "land",
"airPollution": "land"
}


# mapping from ted id to administrative ids
ted2Geocode = {
"0601": {"iso":"NO-01","county":"01:30", # Østfold, 30 is code for Viken from 2020
         "MunicipalityId":"0101;0104;0105;0106;0111;0118;0119;0121;0122;0123;0124;0125;0127;0128;0135;0136;"
                          "0137;0138"},
"0602": {"iso":"NO-02","county":"02:30",  # Akershus, 30 is code for Viken from 2020
         "MunicipalityId":"0211;0213;0214;0215;0216;0217;0219;0220;0221;0226;0227;0228;0229;0230;0231;0233;0234;"
                          "0235;0236;0237;0238;0239"},
"0603": {"iso":"NO-03","county":"03",  # Oslo
         "MunicipalityId":"0301"},
"0604": {"iso":"NO-04","county":"04:34", # Hedmark, 34 is code for Innlandet from 2020
         "MunicipalityId":"0402;0403;0412;0415;0417;0418;0419;0420;0423;0425;0426;0427;0428;0429;0430;0432;"
                          "0434;0436;0437;0438;0439;0441"},
"0605": {"iso":"NO-05","county":"05:34", # Oppland,, 34 is code for Innlandet from 2020
        "MunicipalityId":"0501;0502;0511;0512;0513;0514;0515;0516;0517;0519;0520;0521;0522;0528;0529;0532;"
                         "0533;0534;0536;0538;0540;0541;0542;0543;0544;0545"
         },
"0606": {"iso":"NO-06","county":"06:30", # Buskerud, 30 is code for Viken from 2020
         "MunicipalityId": "0602;0604;0605;0612;0615;0616;0617;0618;0619;0620;0621;0622;0623;0624;0625;0626;0627;"
                           "0628;0631;0632;0633"},
"0607": {"iso":"NO-07","county":"07:38",  # Vestfold, 38 is code for Telemark og Vestfold from 2020
         "MunicipalityId":"0701;0704;0710;0711;0712;0713;0715;0716;0729"
         },
"0608": {"iso":"NO-08","county":"08:38", # Telemark, 38 is code for Telemark og Vestfold from 2020
         "MunicipalityId": "0805;0806;0807;0811;0814;0815;0817;0819;0821;0822;0826;0827;0828;0829;0830;0831;0833;"
                           "0834"},
"0609": {"iso":"NO-09","county":"09:42",  # Aust-Agder, 42 is code for Agder from 2020
         "MunicipalityId":"0901;0904;0906;0911;0912;0914;0919;0926;0928;0929;0935;0937;0938;0940;0941"
         },
"0610": {"iso":"NO-10","county":"10:42",# Vest-Agder, 42 is code for Agder from 2020
         "MunicipalityId":"1001;1002;1003;1004;1014;1017;1018;1021;1026;1027;1029;1032;1034;1037;1046"},
"0611": {"iso":"NO-11","county":"11", # Rogaland
         "MunicipalityId":"1101;1102;1103;1106;1111;1112;1114;1119;1120;1121;1122;1124;1127;1129;1130;1133;"
                          "1134;1135;1141;1142;1144;1145;1146;1149;1151;1154;1159;1160"},
"0612": {"iso":"NO-12","county":"12:46", # Hordaland, 46 is code for Vestlandet from 2020
         "MunicipalityId":"1201;1211;1214;1216;1219;1221;1222;1223;1224;1227;1228;1231;1232;1233;1234;1235;1238;"
                          "1241;1242;"
         "1243;1244;1245;1246;1247;1251;1252;1253;1256;1259;1260;1263;1264;1265;1266"},
"0614": {"iso":"NO-14","county":"14:46", # Sogn og Fjordane, 46 is code for Vestlandet from 2020
         "MunicipalityId":"1401;1449;1412;1413;1416;1417;1418;1419;1420;1421;1422;1424;1426;1428;1429;1430;"
                          "1431;1432;1433;1438;1439;1441;1443;1444;1445;1411"},
"0615": {"iso":"NO-15","county":"15",   # Møre og Romsdal
         "MunicipalityId":"1573;1572;1502;1503;1504;1505;1511;1514;1515;1516;1517;1519;1520;1523;1524;1525;"
                          "1526;1528;1529;1531;1532;1534;1535;1539;1543;1545;1546;1547;1548;1551;1554;1556;"
                          "1557;1560;1563;1566;1567;1569;1571;1576"},
"0616": {"iso":"NO-16","county":"16:50", # Sør-Trøndelag, 50 is new code for Trøndelag from 2018
         "MunicipalityId":"5033;5054;5001;5011;5012;5013;5014;5015;5016;5017;5018;5019;5020;5021;5022;5023;"
                          "5024;5025;5026;5027;5028;5029;5030;5031;5032"},
"0617": {"iso":"NO-17","county":"17:50", # Nord-Trøndelag, 50 is new code for Trøndelag from 2018
         "MunicipalityId":"5035:5034;5036;5037;5038;5039;5040;5041;5042;5043;5044;5045;5046;5047;5048;5049;5050;"
                          "5051;5052;5053;5004;5005;5054"},
"0618": {"iso":"NO-18","county":"18",  # Nordland
         "MunicipalityId":"1804;1805;1811;1812;1813;1815;1816;1818;1820;1822;1824;1825;1826;1827;1828;1832;"
                          "1833;1834;1835;1836;1837;1838;1839;1840;1841;1842;1845;1848;1849;1850;1851;1852;1853;"
                          "1854;1856;1857;1859;1860;1865;1866;1867;1868;1870;1871;1874"},
"0619": {"iso":"NO-19","county":"19:54",  # Troms, 54 is code for Troms og Finnmark from 2020
         "MunicipalityId":"1931;1929;1936;1938;1939;1940;1941;1942;1943;1901;1902;1903;1911;1913;1915;1917;"
                          "1919;1920;1922;1923;1924;1925;1926;1927;1928;1933"
         },
"0620": {"iso":"NO-20","county":"20:54",  # Finnmark, , 54 is code for Troms og Finnmark from 2020
         "MunicipalityId":"2002;2030;2004;2011;2012;2014;2015;2017;2018;2019;2020;2021;2022;2023;2024;2025;2027;2028;"
                          "2003"},
"9001": {"iso":"NO-18","county":"18",   # Helgeland
         "MunicipalityId": "1811;1812;1813;1815;1816;1818;1820;1822;1824;1825;1826;1827;1828;1832;1833;1834;1835;1836;"
                           "1837"},
"9002": {"iso":"NO-18","county":"18",     # Saltfjellet
         "MunicipalityId": "1833;1839;1840"},
"9003": {"iso":"NO-18","county":"18",     # Salten
         "MunicipalityId": "1804;1838;1839;1840;1841;1845;1848;1849"},
"9004": {"iso":"NO-18","county":"18",     # Lofoten
         "MunicipalityId": "1856;1857;1859;1860;1865;1874"},
"9005": {"iso":"NO-18","county":"18",     # Ofoten
         "MunicipalityId": "1805;1850;1851;1852;1853;1854"},
"9006": {"iso":"NO-18","county":"18",     # Vesterålen
         "MunicipalityId": "1866;1867;1868;1870;1871"},
"9007": {"iso":"NO-19","county":"19:54",  # Sør-Troms
         "MunicipalityId": "1903;1911;1913;1917;1919;1920;1923"},
"9008": {"iso":"NO-19","county":"19:54",  # Nord-Troms
         "MunicipalityId": "1902;1933;1936;1938;1939;1940;1941;1942;1943"},
"9009": {"iso":"NO-20","county":"20:54",  # Øst-Finnmark
         "MunicipalityId": "2002;2003;2022;2023;2024;2025;2027;2028;2030"},
"9010": {"iso":"NO-20","county":"20:54",  # Kyst- og fjordstrøkene i Vest-Finnmark
         "MunicipalityId": "2004;2012;2014;2015;2017;2018;2019;2020"},
"9011": {"iso":"NO-20","county":"20:54",  # Finnmarksvidda
         "MunicipalityId": "2011;2021"},
"9018": {"iso":"NO-21","county":"21",
         "MunicipalityId":"2111"},   # Nordenskiöld Land på Spitsbergen
# Fjellet i Sør-Norge berører fylkene
    # Sør-Trøndelag, Oppland, Hedmark, Buskerud,Telemark, Aust-Agder, Vest-Agder, Rogaland,Hordaland,
    # Sogn og Fjordane, Møre og Romsdal
"0710" : {"iso":"NO-16:NO-05:NO-04:NO-06:NO-08:NO-09:NO-10:NO-11:NO-12:NO-14:NO-15",
          "county":"16:05:04:06:08:09:10:11:12:14:15:50:34:30:38:42:46",
          "MunicipalityId": "437;439;441;511;512;513;514;545;618;619;620;633;826;831;833;834;938;940;941;1026;1046;1134;"
                            "1228;1231;1232;1233;1421;1422;1424;1426;1449;1524;1525;1539;1543;1563;1566;1567;5033;5021;"
                            "5022;5026;5027"}
}
