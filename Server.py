from config import Config
import numpy as np
import pandas as pd
import os
import queue
import shutil
import time
from collections import OrderedDict
from parse import *

# 0: Name,    1: FileName,   2: BitDepth,    3: Format,  4: FrameRate,   5: 0,   6: width,   7:height,   8:Frames,   9:Level (minus 1)
class SequnceInfo(object):
    def __init__(self, info):
        self.name = info[0]
        self.yuvName = info[1]
        self.bitdepth = info[2]
        self.format = info[3]
        self.frameRate = info[4]
        self.zero = info[5]
        self.width = info[6]
        self.height = info[7]
        self.numframe = info[8]
        self.level = info[9]
        self.frameskip = 0


def strTap(msg):
    return '\t'+str(msg)



class task(object):
    enctimepath = "EncTime.yml"
    if not os.path.exists(enctimepath):
        os.mkdir(enctimepath)
    enctimelist = Config(enctimepath)

    def __init__(self, gid, gname, taskname, gtnum, enc_path, dec_path, cnd_path, bin_path, sequenceInfo, qp, rasid, rasnum, intra_period,  state):
        self.gid = gid
        self.gname = gname
        self.taskid = gid + gtnum
        self.seq_info = sequenceInfo
        self.cnd_name = os.path.basename(cnd_path)
        self.qp = qp
        # self.name = self.seq_info.name+'_Q'+str(self.qp)+'_'+ self.cnd_name.split('.')[0]
        self.name = taskname
        # print(self.name)
        # if rasnum>1:
        #     self.name += '_r' + str(rasid)
        self.enc_path = enc_path
        self.dec_path = dec_path
        self.bin_path = bin_path
        #self.result_info = resultDesc
        self.rasid = rasid
        self.rasnum = rasnum
        self.ip = intra_period # 1 : Intra, -1: LDB, -2:LDP, Others : RA
        self.state = 0 # 0 : none, 1 : in progress, 2 : done
        self.priority = self.initPriority()
        self.framesToBeEncoded = 0
        self.frameskip = 0
        self.renewforRas()
        self.ismd5error = False
        self.state = state
        #print('{0} : {1}'.format(self.name, self.priority))


    def renewforRas(self):
        self.frameskip = self.rasid * self.ip
        self.framesToBeEncoded = self.seq_info.numframe
        if self.rasnum>1:
            if self.rasid == self.rasnum-1:
                self.framesToBeEncoded = self.seq_info.numframe - self.rasid * self.ip
            else :
                self.framesToBeEncoded = self.ip+1

    def __lt__(self, other):
        return self.taskid < other.taskid


    def initPriority(self):
        """
        Priority Rule:
            The following rules are followed in order. (The higher rule has higher priority than the lower rule.)
                0. Group Number(self.gid) smaller First
                1. Lowdelay > RandomAccess > Intra
                2. High Resolution(width*height) > Low Resolution(width*height)
                4. smaller QP value > lager QP value

            qp: 0~100
            resolution  *=100 : (0~1e9) ( 1e8 - width * height)
            cndMode *=10000000 (0~10) (LD: 0, RA : 1, Intra 2)
            gid *= 100000000

        :return: task Priority to be into Priorty queue
        """

        prio = ''
        prio += (str)((int)(self.gid)) # gid Setting
        if self.ip==1:       # LD, RA Check
            prio += '3'
        elif self.ip==-1:
            prio += '1'
        else:
            prio += '2'
        numpix = (int)(1e10 - (self.seq_info.width)//100*(self.seq_info.height)//100*((self.seq_info.numframe+50)//100+1))
        prio += str(numpix)
        prio += str(self.qp)
        prio += str(10000000)
        if getattr(self.enctimelist, self.name.lower()):
            prio += str(10000000 - (getattr(self.enctimelist, self.name.lower())))
        return prio


    def TaskToTaskMessege(self):
        seq = self.seq_info
        msg = str(self.gid)
        msg += strTap(self.name)
        msg += strTap(self.cnd_name)
        msg += strTap(self.qp)
        msg += strTap(self.ip)
        msg += strTap(seq.yuvName)
        msg += strTap(seq.bitdepth)
        msg += strTap(seq.format)
        msg += strTap(seq.frameRate)
        msg += strTap(self.frameskip)
        msg += strTap(seq.width)
        msg += strTap(seq.height)
        msg += strTap(self.framesToBeEncoded)
        msg += strTap(seq.level)
        msg += strTap(str(self.taskid))
        return msg



    def setEncDecData(self, encpath, decpath):
        with open(encpath, 'r') as f:
            data = f.read()
            totaldata = parse('{}Total Frames{}\n{}\n{}', data)
            totaldata = totaldata[2].split()
            codedframe = int(totaldata[0])
            kbps = float(totaldata[2])
            Ypsnr = float(totaldata[3])
            Upsnr = float(totaldata[4])
            Vpsnr = float(totaldata[5])
            # print(totalframe, kbps, Ypnsr, Upsnr, Vpsnr)
            encT = parse('{} Total Time:     {} sec{}', data)
            encT = float(encT[1])
            # print(totalenctime)
            ikbps = iYpsnr = iUpsnr = iVpsnr = iencT = 0
            if self.rasnum>1 and self.rasid !=0:
                poc1data = parse(
                    '{}POC    0 TId: {} ( I-SLICE, QP {} )     {} bits [Y {} dB    U {} dB    V {} dB]{}[ET   {} ] {}',
                    data)
                ikbps = float(poc1data[3])
                iYpsnr = float(poc1data[4])
                iUpsnr = float(poc1data[5])
                iVpsnr = float(poc1data[6])
                iencT = float(poc1data[8])
                ikbps = (ikbps*self.seq_info.frameRate)/1000.0
                # print(ikbps, iYpsnr, iUpsnr, iVpsnr, iencT)
            if self.rasnum>1:
                kbps = kbps*codedframe - ikbps
                Ypsnr = Ypsnr*codedframe - iYpsnr
                Upsnr = Upsnr*codedframe - iUpsnr
                Vpsnr = Vpsnr*codedframe - iVpsnr
                encT = encT - iencT

        with open(decpath, 'r') as f:
            data = f.read()
            decT = parse('{} Total Time:{}sec{}', data)
            decT = float(decT[1].split()[0])
            # print(decT[1])
            idecT = 0
            if self.rasnum > 1 and self.rasid != 0:
                idecT = parse('{}POC    0 TId{}[DT{}]{}', data)
                idecT = float(idecT[2].split()[0])
                decT = decT - idecT
            # print(idecT[2])
            iserror = parse('{}ERROR{}', data)
            if iserror != None:
                self.ismd5error = True
            if self.rasid>0:
                decT = decT - idecT
        return kbps, Ypsnr, Upsnr, Vpsnr, encT, decT, codedframe
            # print(iserror)

class taskGroup(object):
    tasks = queue.PriorityQueue()
    FinishedTask = OrderedDict()
    RunningTask = OrderedDict()
    def __init__(self, configpath):
        self.task_group_num = 0
        self.task_finish_num = 0
        self.gid = (int)(time.time())
        config = Config(configpath)
        self.gname = config.Name
        self.resultpath = config.DirectoryPath + '/' + config.Name
        self.binpath = self.resultpath + '/bin'
        os.makedirs(self.binpath, exist_ok=True)
        os.makedirs(self.resultpath, exist_ok=True)
        os.makedirs(config.DirectoryPath, exist_ok=True)
        os.makedirs(self.resultpath, exist_ok=True)
        self.qp = config.QP
        self.dir = config.DirectoryPath
        self.cfgdir = config.ConfigPath
        self.cfglist = self.getFileList(self.cfgdir)
        self.encPath = config.EncoderPath
        self.decPath = config.DecoderPath
        shutil.copy(self.encPath, self.resultpath)
        shutil.copy(self.decPath, self.resultpath)
        self.origPath = config.InputPath
        self.frameNum = config.ToBeEncodeFrameNumber
        self.enc_class = config.ToBeEncodeClass
        self.class_info = Config(config.ClassInfoPath)
        self.seqPath = config.SequencesPath
        self.useRas = config.UseRas
        self.rasGroup = []
        self.resultDic = OrderedDict()
        self.setTask()





    def ParseResult(self):
        if self.task_group_num != self.task_finish_num:
            return False
        resultlist = []
        for raslist in self.rasGroup:
            totalFrame = 1
            kbps = ypsnr = upsnr = vpsnr = enct = dect = 0
            taskname = ''
            for task in raslist:
                taskname = task.name.split('_ras')[0]
                enc_log = self.binpath + '/enc_' + task.name + '.log'
                dec_log = self.binpath + '/dec_' + task.name + '.log'
                (rkbps, rypsnr, rupsnr, rvpsnr, renct, rdect, codedframe) = task.setEncDecData(encpath=enc_log, decpath=dec_log)
                kbps += rkbps
                ypsnr += rypsnr
                upsnr += rupsnr
                vpsnr += rvpsnr
                enct += renct
                dect += rdect
                totalFrame += codedframe
            if len(raslist)>1:
                kbps /= totalFrame
                ypsnr /= totalFrame
                upsnr /= totalFrame
                vpsnr /= totalFrame
            resultlist.append((taskname, kbps, ypsnr, upsnr, vpsnr, enct, dect))
        resultlist = sorted(resultlist, key = lambda s : s[0])
        for result in resultlist:
            self.resultDic[result[0]] = (result[1], result[2], result[3], result[4], result[5], result[6])
        with open(self.resultpath+'/'+self.gname+'result.csv', 'w') as f:
            f.write('seq, bitrate, ypsnr, upsnr, vpsnr, encT, decT \n')
            for name, result in self.resultDic.items():
                if result == None:
                    f.write('%s, , , , , , \n' %(name))
                else:
                    f.write('%s, %s, %s, %s, %s, %s, %s\n' %(name, result[0], result[1], result[2], result[3], result[4], result[5]))
        return True

    def getFileList(self, dir, pattern='.cfg'):
        matches = []
        for root, dirnames, filenames in os.walk(dir):
            for filename in filenames:
                if filename.endswith(pattern):
                    matches.append(os.path.join(root, filename))
        return matches

    def getSequences(self, classes):
        clsses = []
        for types in classes:
            if getattr(self.class_info, types.lower()):
                clsses.extend(self.getSequences(getattr(self.class_info,types.lower())))
            else:
                clsses.append(types)
        return clsses


    def initSeqeuences(self):
        candis = self.getSequences(self.enc_class)
        candis = np.array(candis)
        seqs = pd.read_csv(self.seqPath, sep=",")
        seqs = seqs.as_matrix()
        seqlist = []
        #format
        #0: Name,    1: FileName,   2: BitDepth,    3: Format,  4: FrameRate,   5: 0,   6: width,   7:height,   8:Frames,   9:Level (minus 1)
        for seq in seqs:
            for candi in candis:
                if seq[0]==candi:
                    seqlist.append(SequnceInfo(seq))
                    #seqdic[seq[0]] = seq[1:]
        return seqlist

    def getIntraPeriod(self, frameRate, cfgfile):
        intra_period = {20:16, 24:32, 30:32, 50:48, 60:64, 100:96}
        cfg = Config(cfgfile)
        # if cfg.IntraPeriod<0:
        #     if((cfg.Frame1)[0]=='B'):
        #         return -1
        #     else:
        #         return -2
        if cfg.IntraPeriod<2:
            return cfg.IntraPeriod
        return intra_period[frameRate]

    def getEncodeFrame(self, seq):
        if self.frameNum==0:
            return seq.numframe
        if self.frameNum>0:
            return min([seq.numframe, self.frameNum])
        else:
            return min([-self.frameNum*seq.frameRate, seq.numframe])

    def getRasNum(self, intraPeriod, tobeEncodeFrame):
        if (not self.useRas) or (intraPeriod < 2):
            return 1
        return (tobeEncodeFrame + intraPeriod - 1) // intraPeriod

    def getCndName(self, cfgfile, ip):
        if ip==1:
            return 'AI'
        elif ip<0:
            cfg = Config(cfgfile)
            if ((cfg.Frame1)[0] == 'B'):
                return 'LDB'
            else:
                return 'LDP'
        else:
            return 'RA'


    def setTask(self):
        '''
        Task number = SequenceNum * QPNum * ConfigNum * RasNum(Intra&LD is 1)
        '''
        seqlist = self.initSeqeuences()
        qplist = self.qp
        for cfgfile in self.cfglist:
            for seq in seqlist:
                for qp in qplist:
                    #print(os.path.basename(cfgfile).split('.')[0]+'_'+ seq.name + '_' + str(qp))
                    tobeEncodeFrame = self.getEncodeFrame(seq)
                    seq.numframe = tobeEncodeFrame
                    intraPeriod = self.getIntraPeriod(seq.frameRate, cfgfile)
                    rasnum = self.getRasNum(intraPeriod, tobeEncodeFrame)
                    raslist = []
                    cndName = self.getCndName(cfgfile, intraPeriod)
                    taskname = seq.name.lower() + '_Q' + str(qp) + '_' + cndName
                    for rid in range(rasnum):
                        self.task_group_num += 1
                        tmptask = task(self.gid, self.gname, taskname + '_ras' + str(rid), self.task_group_num, self.encPath, self.decPath, cfgfile, self.binpath, seq, qp, rid, rasnum, intraPeriod, 0)
                        raslist.append(tmptask)
                        self.tasks.put((tmptask.priority, tmptask))
                    self.rasGroup.append(raslist)
        self.setResultGroup()
        return

    def setResultGroup(self):
        sortedSeq = self.class_info.sort
        cndlist = ['AI', 'RA', 'LDB', 'LDP']
        qplist = ['22', '27', '32', '37']
        for cnd in cndlist:
            for name in sortedSeq:
                for qp in qplist:
                    resultname = name.lower() + '_Q' + qp + '_' + cnd
                    self.resultDic[resultname] = None
        return







if __name__=='__main__':
    # print(taskGroup.tasks)
    mtask = taskGroup("config.yml")
    # while taskGroup.tasks.qsize()!=0:
    #     tmptask = taskGroup.tasks.get()[1]
    #     print('%s , %s (h : %s) (ip : %s) : %s' %(tmptask.name, tmptask.gid, tmptask.seq_info.height, tmptask.ip, tmptask.priority))
    print("Done")

    # try:
    #     data = f.read(2048)
    #     while data:
    #         data_transfered += conn.send(data)
    #         data = f.read(2048)
    # except Exception as e:
    #     self.logger.info(e)