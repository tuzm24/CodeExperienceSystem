from parse import *


filepath = 'C:/DMSExperience/ywkim_Test/bin/enc_bqsquare_Q22_LDP_ras0.log'
decfilepath = 'C:/DMSExperience/ywkim_Test/bin/dec_bqsquare_Q22_LDP_ras0.log'


with open(filepath, 'r') as f:
    data = f.read()
    poc1data = parse('{}POC    0 TId: {} ( I-SLICE, QP {} )     {} bits [Y {} dB    U {} dB    V {} dB]{}[ET   {} ] {}', data)
    # totaldata = parse('{}Total Frames{}\n	       {}    {}    {}   {}   {}   {}   {}\n{}', data)
    # totaldata = parse('{}Total Frames{}\n	        {}    a   12869.2800   43.1015   44.5392   45.3946   43.6337\n{}', data)
    totaldata = parse('{}Total Frames{}\n{}\n{}', data)
    totaldata = totaldata[2].split()
    totalframe = totaldata[0]
    kbps = totaldata[2]
    Ypnsr = totaldata[3]
    Upsnr = totaldata[4]
    Vpsnr = totaldata[5]
    print(totalframe, kbps, Ypnsr, Upsnr, Vpsnr)

    totalenctime = parse('{} Total Time:     {} sec{}', data)
    totalenctime = totalenctime[1]
    print(totalenctime)

    ikbps = poc1data[3]
    iYpsnr = poc1data[4]
    iUpsnr = poc1data[5]
    iVpsnr = poc1data[6]
    iencT = poc1data[8]
    print(ikbps, iYpsnr, iUpsnr, iVpsnr, iencT)


with open(decfilepath, 'r') as f:
    data = f.read()
    decT = parse('{} Total Time:{}sec{}', data)
    print(decT[1].split()[0])
    idecT = parse('{}POC    0 TId{}[DT{}]{}', data)
    print(idecT[2].split()[0])
    iserror = parse('{}ERROR{}', data)
    print(iserror)


