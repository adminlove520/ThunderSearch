import json
import requests
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Treeview
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
class Application(Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master=master
        self.createWidget()
        self.pack()
        
    def createWidget(self):
        self.u_label = Label(self, text='账号').grid(row=0,column=0)
        self.p_label = Label(self, text='密码').grid(row=1,column=0)
        self.USERNAME = Entry(self,width=16)
        self.USERNAME.grid(row=0,column=1)
        self.PASSWORD = Entry(self,width=16,show="*")
        self.PASSWORD.grid(row=1,column=1)
        self.thread_label = Label(self, text='线程数').grid(row=0,column=2)
        self.query_label = Label(self, text='查询语句').grid(row=1,column=2)
        self.thread_choice = StringVar(self)
        self.thread_choice.set('5')
        self.THREAD = OptionMenu(self,self.thread_choice,'1','5','10','20','30')
        self.THREAD.grid(row=0,column=3)
        self.page_label = Label(self,text='查询页数').grid(row=0,column=4)
        self.page_choice = StringVar(self)
        self.page_choice.set('1')
        self.PAGE = OptionMenu(self,self.page_choice,'1','2','3','4','5','6','7','8','9','10','15','20','30','40','50','60','70','80','90','100','200','300','500','1000')
        self.PAGE.grid(row=0,column=5)
        self.START = Button(self,text='一键查询',command=self.thread)
        self.START.grid(row=0,column=6)
        self.QUERY = Entry(self, width=18)
        self.QUERY.grid(row=1,column=3,columnspan=2)
        self.file_label = Label(self,text='存储文件名').grid(row=1,column=5)
        self.FILE = Entry(self,width=8)
        self.FILE.grid(row=1,column=6)
        self.TREEVIEW = Treeview(self)
        self.TREEVIEW.grid(row=2,column=0,columnspan=7)
        self.TREEVIEW['columns'] = ("IP","PORT","OS")
        self.TREEVIEW.column("IP",width=200)
        self.TREEVIEW.column("PORT",width=100)
        self.TREEVIEW.column("OS",width=100)
        self.TREEVIEW.heading("IP",text="IP")
        self.TREEVIEW.heading("PORT",text="PORT")
        self.TREEVIEW.heading("OS",text="OS")
        self.LOG = Text(self,relief=SOLID,borderwidth=1,height=10,width=86)
        self.LOG.grid(row=3,column=0,columnspan=7)

    def log_insert(self,str):       # update log
        self.LOG.insert(END,chars=str)
        self.LOG.see(END)

    def login(self):
        try:
            with open("access_token.txt", "r") as f:
                access_token = f.read().strip('\n')
            self.log_insert("Load file 'access_token.txt' successfully.\n")
        except FileNotFoundError:
            self.log_insert("Fail to find access_token.txt. Need to Login now.\n")
            url = 'https://api.zoomeye.org/user/login'
            data = {
                'username':self.USERNAME.get().strip(),
                'password':self.PASSWORD.get().strip()
            }
            encoded_data = json.dumps(data)
            resp_json = requests.post(url, encoded_data).json()
            try:
                access_token = resp_json['access_token']
            except:
                self.log_insert(f'[-] Login fail. {resp_json["message"]}\n')
            else:
                self.log_insert('[+] Login success!\n')
                with open("access_token.txt", "w") as f:
                    f.write(access_token)

        self.headers = {
            'Authorization':'JWT ' + access_token
        }
        print(self.headers)
        self.log_insert(f"Access_Token: {self.headers['Authorization']}\n")
    
    def thread(self):
        if self.QUERY.get() != "" and self.FILE.get() != "":
            t1 = Thread(target=self.run,daemon=True)
            t1.start()
        else:
            messagebox.showerror(title='Error',message='Query or FilePATH empty!')

    def run(self):
        self.info_list = []
        self.login()
        self.log_insert('Start searching...\n')
        query = self.QUERY.get().replace(" ",'%20')
        self.host_search(query=query,page=self.page_choice.get(),thread=int(self.thread_choice.get()))
        j = 1
        with open(self.FILE.get(),"w") as f:
            f.write("ip:port\tcountry\tos\thostname\n")
            for each_dic in self.info_list:
                self.TREEVIEW.insert("",END,text=j,values=(each_dic['ip'],each_dic['port'],each_dic['os']))
                f.write(f"{each_dic['ip']}:{each_dic['port']},{each_dic['country']},{each_dic['os']},{each_dic['hostname']}\n")
                j += 1
        self.log_insert(f'Complete information has been stored into {self.FILE.get()}.\n')
        self.resource()

    def host_search(self, query, page, thread):
        with ThreadPoolExecutor(thread) as t:
            for i in range(1,int(page)+1):
                t.submit(self.host_search_threadpool, query=query, page=i)
        self.log_insert("End of search.\n")

    def host_search_threadpool(self, query, page):
        url = f'https://api.zoomeye.org/host/search?query={query}&page={page}&sub_type=v4&facets=app,os'
        print(url)
        try:
            matches = requests.get(url, headers=self.headers).json()
            for each in matches['matches']:
                each_dic = {}
                each_dic['ip'] = each['ip']
                each_dic['port'] = each['portinfo']['port']
                each_dic['country'] = each['geoinfo']['country']['names']['en']
                each_dic['os'] = each['portinfo']['os']
                each_dic['hostname'] = each['portinfo']['hostname']
                
                self.info_list.append(each_dic)
        except Exception as e:
            if str(e.message) == 'matches':
                print ()
                self.log_insert('[-] info : account was break, excceeding the max limitations\n')
            else:
                print  ()
                self.log_insert(f'[-] info : {str(e.message)}\n')

    def resource(self):     # user_info
        resp = requests.get('https://api.zoomeye.org/resources-info', headers=self.headers)
        last = resp.json()['resources']['search']
        self.log_insert(f"[!] Your account's Remaining query quota: {last} (this month).\n")
        

if __name__=='__main__':
    root = Tk()
    root.geometry('640x404+450+100')
    root.title('ThunderSearch v1.0')
    Application(master=root)
    root.mainloop()