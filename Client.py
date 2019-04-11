import socket
import os
from threading import Thread
import subprocess
import time
import logging
import threading
import platform

import sys
# ComputerName = 'DMS_EX_COM_1'
ComputerName = platform.uname()[1]
Sequence_Path = 'C:/origCfp'
Temp_Path = 'C:/CodecTemp'

HOST = '192.168.0.5'
# HOST = 'localhost'
# HOST = '223.195.38.111'
PORT = 3100
BUFSIZE = 1024
ADDR = (HOST, PORT)

lock = threading.Lock()

class LoggingHelper(object):
    INSTANCE = None

    def __init__(self):
        if LoggingHelper.INSTANCE is not None:
            raise ValueError("An instantiation already exists!")

        os.makedirs(Temp_Path, exist_ok=True)
        self.logger = logging.getLogger()

        logging.basicConfig(filename='LOGGER', level=logging.DEBUG)

        fileHandler = logging.FileHandler(Temp_Path + '/msg.log')
        streamHandler = logging.StreamHandler()

        fomatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s > %(message)s')
        fileHandler.setFormatter(fomatter)
        streamHandler.setFormatter(fomatter)

        self.logger.addHandler(fileHandler)
        self.logger.addHandler(streamHandler)

    @classmethod
    def get_instace(cls):
        if cls.INSTANCE is None:
            cls.INSTANCE = LoggingHelper()
        return cls.INSTANCE

    @staticmethod
    def diff_time_logger(messege, start_time):
        LoggingHelper.get_instace().logger.info("[{}] :: running time {}".format(messege, time.time() - start_time))


class TaskGroup(object):
    def __init__(self, tgname, tmppath, basepath, logpath, binpath, encpath, decpath, cfgspath):
        self.tgname = tgname
        self.tmppath = tmppath
        self.basepath = basepath
        self.logpath = logpath
        self.binpath = binpath
        self.encpath = encpath
        self.decpath = decpath
        self.cfgspath = cfgspath


class Ex_Client(object):
    os.makedirs(Temp_Path, exist_ok=True)
    logger = LoggingHelper.get_instace().logger
    taskgroup = {}
    running_task = {}
    willSendFiles = []
    def __init__(self):
        self.myName = ComputerName
        self.host = HOST
        self.port = PORT
        self.ADDR = (self.host, self.port)
        self.bufsize = BUFSIZE
        self.orgPath = Sequence_Path
        self.tmppath = Temp_Path
        os.makedirs(self.tmppath, exist_ok=True)
        os.makedirs(self.orgPath, exist_ok=True)

    def make_seqcfg_file(self, filepath, taskdata):
        image_path = Sequence_Path +'/' + taskdata[5]
        with open(filepath, 'w') as f:
            f.write("InputFile : %s\n" %(image_path))
            f.write("InputBitDepth : %s\n" %(taskdata[6]))
            f.write("InputChromaFormat : %s\n" %(taskdata[7]))
            f.write("FrameRate : %s\n" %(taskdata[8]))
            f.write("FrameSkip : %s\n" %(taskdata[9]))
            f.write("SourceWidth : %s\n" %(taskdata[10]))
            f.write("SourceHeight : %s\n" %(taskdata[11]))
            f.write("FramesToBeEncoded : %s\n" %(taskdata[12]))
            level = float(taskdata[13])
            if level%1==0:
                level = int(level)
            f.write("Level : %s\n" %(level))


    def get_enc_dec_comand(self, taskdata):
        gid = taskdata[0]
        taskname = taskdata[1]
        cndname = taskdata[2]
        enc_logpath = self.taskgroup[gid].logpath + '/' + 'enc_' + taskname + '.log'
        dec_logpath = self.taskgroup[gid].logpath + '/' + 'dec_' +  taskname + '.log'
        enc_path = self.taskgroup[gid].encpath
        dec_path = self.taskgroup[gid].decpath
        cnd_path = self.taskgroup[gid].basepath + '/' + cndname
        seqcfg_path = self.taskgroup[gid].tmppath + '/' + taskname + '.cfg'
        bin_path = self.taskgroup[gid].binpath + '/' + taskname + '.bin'
        qp = taskdata[3]
        enc_command = enc_path + ' -c ' + cnd_path + ' -c ' + seqcfg_path + ' -q ' + qp + ' -b ' + bin_path
        dec_command = dec_path + ' -b ' + bin_path
        if int(taskdata[4]) > 1: # intra Period
            enc_command += ' -ip ' + taskdata[4]
        self.make_seqcfg_file(seqcfg_path, taskdata)
        return enc_command, enc_logpath, dec_command, dec_logpath, bin_path



    def getFileList(self, dir, pattern=('.yuv')):
        matches = []
        for root, dirnames, filenames in os.walk(dir):
            for filename in filenames:
                if filename.endswith(pattern):
                    matches.append(os.path.join(root, filename))
        return matches

    def rcvfile(self, sock ,taskgroupname):
        filedata = sock.recv(2048).decode().strip().split('\t')
        filename = filedata[0]
        filesize = filedata[1]
        sock.send(filedata[0].encode())
        data = sock.recv(2048)
        data_transferred = 0
        filesize = (int)(filesize)
        filepath = Temp_Path+'/' + taskgroupname +'/' +filename
        with open(filepath, 'wb') as f:
            try:
                while data:
                    f.write(data)
                    data_transferred +=len(data)
                    if data_transferred==filesize:
                        break
                    data = sock.recv(2048)
            except Exception as e:
                self.logger.error(e)
        self.logger.info("(Filename : %s), (Filesize :  %s), (File Transferred : %s)" %(filename, filesize, data_transferred))
        sock.send(str(data_transferred).encode())
        return filepath


    def FileSend(self, sock, filepath):
        data_transfered = 0
        filesize = os.path.getsize(filepath)
        filename = os.path.basename(filepath)
        sock.send((filename+'\t'+str(filesize)).encode())
        sock.recv(2048) # recv : filename
        with open(filepath, 'rb') as f:
            try:
                data = f.read(2048)
                while data:
                    data_transfered += sock.send(data)
                    data = f.read(2048)
            except Exception as e:
                self.logger.info(e)
        #recv_size = int(sock.recv(2048))
        recv_size = sock.recv(2048)
        recv_size = int(recv_size)
        if data_transfered==recv_size:
            self.logger.info("      Send Success (%s : %s)" %(filename, data_transfered))
            os.remove(filepath)
        else:
            self.logger.error("     Send Fail (%s : %s)" %(filename, data_transfered))
        return


    def RunTask(self, data, sock):
        # try:
        taskname = data[1]
        enc_command, enclog, dec_command, declog, binpath = self.get_enc_dec_comand(data)
        # print(enc_command, enclog, dec_command, declog, binpath)
        self.logger.info('Encoder is start : (%s)' %taskname)
        enc_log = open(enclog, 'w')
        sub_proc = subprocess.Popen(enc_command, stdout=enc_log)
        sub_proc.wait()
        enc_log.close()
        self.logger.info('Decoder is start : (%s)' % taskname)
        dec_log = open(declog, 'w')
        sub_proc = subprocess.Popen(dec_command, stdout= dec_log)
        sub_proc.wait()
        dec_log.close()
        self.logger.info('Decoder is Finish : (%s)' % taskname)


        # lock.acquire()
        # sock.send('FinishTask'.encode())
        finishtask = (data[0] + '\t' + data[14])
        # sock.send(('FinishTask\t' + data[0] + '\t' + data[14]).encode())
        # sock.recv(2048)
        self.willSendFiles.append((finishtask, enclog, declog, binpath))
        # self.willSendFiles.append(declog)
        # self.willSendFiles.append(binpath)
        #print(sock.recv(2048).decode())
        # self.FileSend(sock, enclog)
        # self.FileSend(sock, declog)
        # self.FileSend(sock, binpath)
        # lock.release()
        # except Exception as e:
        #     print(e)
        #     return False
        return

    def FlushFiles(self, sock):
        (msg, encpath, decpath, binpath) = self.willSendFiles[0]
        # print(msg)
        sock.recv(2048)
        sock.send((msg).encode())
        sock.recv(2048)
        self.FileSend(sock, encpath)
        self.FileSend(sock, decpath)
        self.FileSend(sock, binpath)
        del self.willSendFiles[0]
        # lock.release()
        return

    def rcvTaskGroup(self, sock):
        # lock.acquire()
        data = sock.recv(2048)
        data = data.decode().strip().split('\t')
        sock.send('recv'.encode())
        tgid = data[0]
        tgname = data[1]
        cfgnum = (int)(data[2])
        tgpath = Temp_Path +'/' + tgname
        logpath = tgpath+'/log'
        binpath = tgpath+'/bin'
        tmppath = tgpath+'/temp'
        os.makedirs(tgpath, exist_ok=True)
        os.makedirs(logpath, exist_ok=True)
        os.makedirs(binpath, exist_ok=True)
        os.makedirs(tmppath, exist_ok=True)
        self.logger.info("(TaskGroupName : %s), (Transfer File Number : %s)" %(tgname, cfgnum+2))
        encfile = self.rcvfile(sock, tgname)
        decfile = self.rcvfile(sock, tgname)
        cfgfile = []
        for i in range(cfgnum):
            cfgfile.append(self.rcvfile(sock, tgname))
        self.taskgroup[tgid] = TaskGroup(tgname= tgname, basepath=tgpath, tmppath = tmppath, logpath=logpath, binpath=binpath, encpath=encfile, decpath=decfile, cfgspath = cfgfile)
        sock.recv(2048)
        sock.send('Finish'.encode())
        # lock.release()
        return

    def rcvMsg(self, sock):
        while True:
            try:
                data = sock.recv(2048)
                data = data.decode().strip()
                data = data.split('\t')
                if data[0]=='Finish':
                    continue
                elif data[0] == 'Flush':
                    flushnum = len(self.willSendFiles)
                    sock.send(('Flush\t'+ str(flushnum)).encode())
                    for i in range(flushnum):
                        self.FlushFiles(sock)
                    continue
                # if'AssTask' != data[0]:
                sock.send(data[0].encode())
                self.logger.info("Messege Receive.. %s" %(data[0]))
                if 'initTaskGroup' in data[0]:
                    self.rcvTaskGroup(sock)
                    #self.rcvfile(sock, data.split('\t')[1], data.split('\t')[2])
                elif data[0] == 'AssTask':
                    t = Thread(target=self.RunTask, args = (data[1:], sock,))
                    t.daemon = True
                    t.start()
                if not data[0]:
                    break
            except Exception as e:
                self.logger.error(e)

    def SendinitMessage(self, sock):
        # msg = ComputerName
        # sock.send(msg.encode())
        self.logger.info('Host와 연결 성공')
        origlist = self.getFileList(self.orgPath)
        # sock.send(str(os.cpu_count()).encode())
        # sock.send(str(len(origlist)).encode())
        msg = ComputerName+"\t"+str(os.cpu_count())+"\t"+str(len(origlist))
        for seq in origlist:
            msg = msg+"\t"+seq
        sock.send(msg.encode())

    def runClient(self):
        flag = True
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((HOST, PORT))
                    flag = True
                    t = Thread(target=self.rcvMsg, args=(sock,))
                    t.daemon = True
                    t.start()
                    self.SendinitMessage(sock)
                    while True:
                        pass
            except Exception as e:
                if flag:
                    self.logger.warning(e)
                    flag = False
                time.sleep(10)


if __name__=='__main__':
    myClient = Ex_Client()
    myClient.runClient()
