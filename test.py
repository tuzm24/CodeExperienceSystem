import multiprocessing
import time
import psutil


# # 시작시간
# start_time = time.time()
#
#
# # 멀티쓰레드 사용 하는 경우 (20만 카운트)
# # Pool 사용해서 함수 실행을 병렬
# def count(name):
#     for i in range(1, 50001):
#         print(name, " : ", i)
#
#
# num_list = ['p1', 'p2', 'p3', 'p4']
#
# if __name__ == '__main__':
#     # 멀티 쓰레딩 Pool 사용
#     pool = multiprocessing.Pool(processes=2)  # 현재 시스템에서 사용 할 프로세스 개수
#     pool.map(count, num_list)
#     pool.close()
#     pool.join()
#
# print("--- %s seconds ---" % (time.time() - start_time))
#
# print(psutil.cpu_percent(percpu=True))

#
# from pyftpdlib.authorizers import DummyAuthorizer
# from pyftpdlib.handlers import FTPHandler
# from pyftpdlib.servers import FTPServer
#
#
# # The port the FTP server will listen on.
# # This must be greater than 1023 unless you run this script as root.
# FTP_PORT = 2121
#
# # The name of the FTP user that can log in.
# FTP_USER = "myuser"
#
# # The FTP user's password.
# FTP_PASSWORD = "1234"
#
# # The directory the FTP user will have full read/write access to.
# FTP_DIRECTORY = "C:/"
#
#
# def main():
#     authorizer = DummyAuthorizer()
#
#     # Define a new user having full r/w permissions.
#     authorizer.add_user(FTP_USER, FTP_PASSWORD, FTP_DIRECTORY, perm='elradfmw')
#
#     handler = FTPHandler
#     handler.authorizer = authorizer
#
#     # Define a customized banner (string returned when client connects)
#     handler.banner = "pyftpdlib based ftpd ready."
#
#     # Optionally specify range of ports to use for passive connections.
#     #handler.passive_ports = range(60000, 65535)
#
#     address = ('192.168.0.9', FTP_PORT)
#     server = FTPServer(address, handler)
#
#     server.max_cons = 256
#     server.max_cons_per_ip = 5
#
#     server.serve_forever()
#
#
from debug.logging import LoggingHelper as lh
from config import Config
import time
import queue
class tasedd(object):
    def __init__(self):
        print("d")
if __name__ == '__main__':
    # # config = Config("config.yml")
    # # logger = lh.get_instace(config).logger
    # # logger.info("Hello!??")
    # import queue
    #
    # q = queue.PriorityQueue()  # 아이템이 2개만 저장가능하도록 설정
    # q.put((10000000000000000000000000000000000000000000000000000000, tasedd()))
    # q.put((10000000000000000000000000000000000000000000000000000000,tasedd()))
    # q.put((10, 'c'))
    # # print(q.get())
    # # print(q.get())
    # # print(q.get())
    # T = int(input())
    # # 여러개의 테스트 케이스가 주어지므로, 각각을 처리합니다.
    # for test_case in range(1, T + 1):
    #     n = int(input())
    #     ans = 0
    #     tmp = input()
    #     for i in range(n):
    #         ans += int(pow(int(tmp.split(' ')[i]) // 10, int(tmp.split(' ')[i]) % 10))
    #     print("#%d %.0d" % (test_case, ans))
    import socketserver
    from os.path import exists

    HOST = ''
    PORT = 9009


    class MyTcpHandler(socketserver.BaseRequestHandler):
        def handle(self):
            data_transferred = 0
            print('[%s] 연결됨' % self.client_address[0])
            filename = self.request.recv(1024)  # 클라이언트로 부터 파일이름을 전달받음
            filename = filename.decode()  # 파일이름 이진 바이트 스트림 데이터를 일반 문자열로 변환

            if not exists(filename):  # 파일이 해당 디렉터리에 존재하지 않으면
                return  # handle()함수를 빠져 나온다.

            print('파일[%s] 전송 시작...' % filename)
            with open(filename, 'rb') as f:
                try:
                    data = f.read(1024)  # 파일을 1024바이트 읽음
                    while data:  # 파일이 빈 문자열일때까지 반복
                        data_transferred += self.request.send(data)
                        data = f.read(1024)
                except Exception as e:
                    print(e)

            print('전송완료[%s], 전송량[%d]' % (filename, data_transferred))


    def runServer():
        print('++++++파일 서버를 시작++++++')
        print("+++파일 서버를 끝내려면 'Ctrl + C'를 누르세요.")

        try:
            server = socketserver.TCPServer((HOST, PORT), MyTcpHandler)
            server.serve_forever()
        except KeyboardInterrupt:
            print('++++++파일 서버를 종료합니다.++++++')


    runServer()