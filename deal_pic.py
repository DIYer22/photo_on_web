# -*- coding: utf-8 -*-


from __future__ import unicode_literals


import PIL
from PIL import Image
import os
import webbrowser
STAND_SIZE = (400,300)  # 想要输出的标准显示图片大小

EORR_PATH = []  # 未含有EXIF信息的图片



def get_list(path='.',file_types=['jpg']):
    '''获取文件路径列表'''
    pics = os.listdir(path)
    abspath = os.path.abspath(path)
    def del_other_file(name):
        index = name.rfind('.')
        if index == -1 :
            return False
        typee = name[index+1:]
        for file_type in file_types:
            if typee == file_type:
                return True
        else:
            return False
    pics = filter(del_other_file, pics)
    if not (len(path) > 1 and ':' == path[1]):
        abspath = path
    return map(lambda x:abspath+'\\'+x, pics)

def print_dic(dic):
    for i in dic:
        print i,'=',dic[i]

def get_info(path):
    '''获取exif信息 返回dic'''
    def init_time(t):  # 标准化时间大小 从1970起
        moth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        def is_4(y):
            return (y % 4 == 0 and y % 100 != 0) or y % 400 ==0
        raw_time = 0
        for year in range(1970, t[0]):
            if is_4(year):
                raw_time += 31622400
            else:
                raw_time += 31536000
                
        if is_4(t[0]):
            moth[1] = 29
        for i in range(t[1]-1):
            raw_time += moth[i] * 86400
        
        raw_time += (t[2] - 1) * 86400
        raw_time += t[3] * 3600
        raw_time += t[4] * 60
        raw_time += t[5]
        return raw_time
    try:
        img = Image.open(path)
    except:
        print os.path.basename(path),'can not open!'
        return
    try:
        exif_data = 0
        exif_data = img._getexif()

        if not exif_data:
            print os.path.basename(path),'`s exif_data is',
            print exif_data
            print img._getexif()
            global EORR_PATH
            EORR_PATH += [path]
            return
        drive = exif_data[272]
        xy = img.size
        time = exif_data[306].split(' ')
        time = time[0].split(':') + time[1].split(':') 
        name = os.path.basename(path)
        size = os.path.getsize(path)
        t = map(lambda x: int(x), time)
        raw_t = init_time(t)
        dic = {'name':name,
               'path':path,
               'raw_t':time,
               'time':raw_t,
               'size':size,
               'drive':drive,
               'xy':xy,  # 长宽像素的元组 如：(1920,1080)
               }
    except :
        print os.path.basename(path),'is ERROR'
        if  exif_data:
            print_dic(exif_data)
        return
    if 34853 in exif_data and 2 in exif_data[34853]:
        dic['gps_p'] = exif_data[34853]
#        print_dic(exif_data[34853])
#        print '='*20
    return dic

def add_info(pics):
    '''将文件路径转换为信息dic'''
    pics = map(get_info, pics)
    pics = filter(lambda x:x,pics)  # 去除因为没exif信息 造成的 None
    pics.sort(lambda x, y:1 if x['time']>y['time'] else -1)
    return pics



def make_thumbnail(path, stand_size=(400, 300)):
    '''使用path制作缩略图'''    
    name = os.path.basename(path)
    dir_name = os.path.dirname(path) +'/.my_thumbnail/' 
    thu_path = dir_name+name[:name.rfind('.')]+\
    '_thumbnail'+name[name.rfind('.'):]
    if os.path.isfile(thu_path):
        img = Image.open(thu_path)  
        if img.size[0] == STAND_SIZE[0]*2 or img.size[1] == STAND_SIZE[1]*2:
            return thu_path
    img = Image.open(path)
    
    size = img.size
    
    if 1.0*size[0]/size[1] < 1.0*stand_size[0]/stand_size[1]:
        re_size = (int(round(1.0*size[0]*stand_size[1]/size[1])),
                   stand_size[1])
    else:
        re_size = (stand_size[0],
                   int(round(1.0*size[1]*stand_size[0]/size[0])))
    
    thumbnail = img.resize(re_size,Image.ANTIALIAS)
    
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name)
    thumbnail.save(thu_path)
    return thu_path
 
 
def thumbnail(pics):
    '''对pics制作缩略图并添加缩略图路径'''
    def _thumbnail_for_dic(dic):
        path = dic['path']
        stand_size = (STAND_SIZE[0]*2,STAND_SIZE[1]*2)
        thu_path = make_thumbnail(path, stand_size)
        dic['thu_path'] = thu_path
    
    map(_thumbnail_for_dic, pics)


class Time_line_position(object):
    '''层次的容器，已知y轴位置，返还在第几道上'''
    def __init__(self, stand_size, max_level=100000):
        self.size = stand_size
        self.y = stand_size[1] + 30
        self.x = stand_size[0] + 30
        self.max_level = max_level
        self.levels = []
        self.level_len = 0
        
    def get_level(self, position):
        flag = 0
        for i in range(self.level_len):
            if position > self.levels[i]:
                flag = 1
                break
        if flag:
            self.levels[i] = position + self.y
            level = i
        else:
            if self.level_len < self.max_level:
                self.levels += [position + self.y]
                self.level_len += 1
                level = self.level_len - 1
            else:
                self.levels[i] = position + self.y
                level = i
        return level
    
    def get_x_position(self, position):
        level = self.get_level(position)
        return self.x * level


def time_line(pics, MAX_LEVEL=10000, html_name='time_line.html'):
    '''获得时间线,MAX_LEVEL为最大显示层数
    创作一个html文件'''  
    
    get_level = Time_line_position(STAND_SIZE)
    
    pics.sort(lambda x, y:1 if x['time']>y['time'] else -1)
    p = [x['time'] for x in pics]
    time_minn = min(p)
    time_long = max(p) - time_minn
    strr = ''
    def creat_img(dic, strr):
        href = dic['path']
        thu_path = dic['thu_path']
        size = dic['xy']
        if 1.0*size[0]/size[1] < 1.0*STAND_SIZE[0]/STAND_SIZE[1]:
            show_size = (int(round(1.0*size[0]*STAND_SIZE[1]/size[1])), 
                         STAND_SIZE[1])
        else:
            show_size = (STAND_SIZE[0], 
                         int(round(1.0*size[1]*STAND_SIZE[0]/size[0])))
        
        time = dic['time']    
        top = int(round(10000.0 * (time - time_minn) / time_long))
        left = get_level.get_x_position(top)
        max_left = (STAND_SIZE[0]+30)*MAX_LEVEL
        if left > max_left:
            left = max_left
        img = '''
    <img class="photo"  id = "%s" src="%s"  onclick="open_pic(this.id)"
         style="width:%.2fpx;height:%.2fpx;position:absolute;top:%.2fpx;left:%.2fpx" />
    '''
        strr += img % (href, thu_path, show_size[0], show_size[1], top, left)
        return strr
    
    for i in pics:
        strr = creat_img(i, strr)
    
    f = open('html_model\\time_line_model.html')
    html = f.read()
    f = f.close()
    
    html = html.decode('utf-8')
    html = html.replace('{for_img}', strr)
    
    def creat_file(content, name='1.txt',tag='w'):
        '''
        创造文件(内容， 名字， 写入模式)
        '''
        f = open(name, tag)
        f.write(content.encode('utf-8'))
        f.close()
    
    creat_file(html, html_name)
    webbrowser.open(html_name)      




class Map_matrix(object):
    '''方便处理经纬度'''
    def __init__(self, matrix, SCREEN_SIZE=(1920, 1080)):
        self.matrix = matrix
        self.top = matrix[0]
        self.bottom = matrix[1]
        self.left = matrix[2]
        self.right = matrix[3]
        self.x = self.right - self.left
        self.y = self.top - self.bottom
        
        if self.x == 0:
            self.x = 1
        if self.y == 0:
            self.y = 1
        
        if not 1.0*self.x/self.y > 1.0*SCREEN_SIZE[0]/SCREEN_SIZE[1]:
            show_size = (int(round(self.x*SCREEN_SIZE[1]*1.0/self.y)), 
                         SCREEN_SIZE[1])
        else:
            show_size = (SCREEN_SIZE[0], 
                         int(round(1.0*self.y*SCREEN_SIZE[0]/self.x)))
            
        self.size = show_size
    def __str__(self):
        strr = ''
        strr += 'x=' +str(self.x) +'\ny=' + str(self.y) + \
        '\nmatrix='+str(self.matrix)+'\n'
        return strr
    __repr__ = __str__
    
    def get_xy(self, gps):
        x = self.size[0] * (gps[0] - self.left) * 1.0/self.x
        y = self.size[1] * (1 - (gps[1] - self.bottom) * 1.0/self.y)
        return (x, y)


def photo_on_map(pics,MAP_SIZE=(3840, 2160), SHOW_SIZE=(160, 120),
                 html_name='photo_on_map.html'):
    '''创造 photo_on_map.html 
    MAP_SIZE想要输出的地图大小
    SHOW_SIZE每个图片的显示大小'''
    def get_matrix(pics):
        '''获得最小矩形'''
        x_l = [i['gps'][0] for i in pics]
        y_l = [i['gps'][1] for i in pics]
        top = max(y_l)
        bottom = min(y_l)
        left = min(x_l)
        right = max(x_l)
        matrix = (top, bottom, left, right)
        return matrix
        
    def gps(dic):
    
        x = dic['gps_p'][4]
        y = dic['gps_p'][2]
        x = [i[0] for i in x]
        y = [i[0] for i in y]
        dic['raw_gps'] = (x, y)
        x = x[0]*3600 + x[1]*60 + x[2]*0.01
        y = y[0]*3600 + y[1]*60 + y[2]*0.01
        dic['gps'] = (x, y)
    
    
    pics = filter(lambda x:1 if 'gps_p' in x else 0, pics)
    
    if len(pics) < 3:
        print '含有GPS信息的图片少于两个，将不展示GPS！'
        return
    map(gps,pics)
    pics = filter(lambda x:0 if x['raw_gps'][0][0]< 115 else 1,pics)
    # 筛选经度
    matrix = get_matrix(pics)
    
    
    
    Matrix = Map_matrix(matrix, MAP_SIZE)
    
    strr = ''
    def creat_img(dic, strr):
        href = dic['path']
        thu_path = dic['thu_path']
        size = dic['xy']
        if 1.0*size[0]/size[1] < 1.0*SHOW_SIZE[0]/SHOW_SIZE[1]:
            show_size = (int(round(1.0*size[0]*SHOW_SIZE[1]/size[1])),
                         SHOW_SIZE[1])
        else:
            show_size = (SHOW_SIZE[0], 
                         int(round(1.0*size[1]*SHOW_SIZE[0]/size[0])))
        
        gps = dic['gps']
        xy = Matrix.get_xy(gps)
        top = xy[1]
        left = xy[0]
        img = '''
    <img class="photo_stream"  id = "%s" src="%s"  
         onclick="open_pic(this.id)" onMouseOut="go_down(this.id)" 
         onMouseOver="go_up(this.id)"
         style="width:%.2fpx;height:%.2fpx;
         position:absolute;top:%.2fpx;left:%.2fpx;z-index:-1" />
    '''
        strr += img % (href, thu_path, show_size[0], show_size[1], top, left)
        return strr
    
    for i in pics:
        strr = creat_img(i, strr)
    
    f = open('html_model\\photo_map_model.html')
    html = f.read()
    f = f.close()
    
    html = html.decode('utf-8')
    html = html.replace('{for_img}', strr)
    
    def creat_file(content, name='1.txt',tag='w'):
        '''
        创造文件(内容， 名字， 写入模式)
        '''
        f = open(name, tag)
        f.write(content.encode('utf-8'))
        f.close()
    
    creat_file(html, html_name)
    webbrowser.open(html_name)      


class Banch_pic(object):
    '''照片流算法'''
    def __init__(self, web_width=1180, want_hight=300, gap_x=0, gap_y=0):
        '''web_width为网页宽度
        want_hight为期望单排高度（实际会比期望的小一点）
        gap_x, gap_y 每张照片的横纵距离'''
        self.width = web_width - gap_x
        self.hight = want_hight
        self.x_in_y = self.width * 1.0 / self.hight
        self.box = []
        self.box_h = [gap_y]  # 每排的高度
        self.level = []  # 最新一排的当前成员
        self.sum = 0  # 最新一排的当前比例
        self.gap_x = gap_x
        self.gap_y = gap_y
    
    def new_level(self):
        count = [self.gap_x]  # 用于计算left
        def _to_dic(dic, _hight):
            x, y = dic['xy'][0], dic['xy'][1]
            width = x * _hight * 1.0 / y
            dic['width'], dic['height'] = width, _hight
            dic['top'] = sum(self.box_h)
            dic['left'] = sum(count)
            ocuppy = width + self.gap_x
            return ocuppy
        
        _hight = (self.width-(len(self.level)+1)*self.gap_x) * 1.0 / self.sum
        for i in self.level:
            count += [_to_dic(i, _hight)]
        
        self.box += [self.level]
        self.sum = 0
        self.level = []
        self.box_h += [_hight + self.gap_y]
        
    def add_xy(self, dic):
        x = dic['xy'][0] + self.gap_x
        y = dic['xy'][1] 
        x_in_y = x * 1.0 / y
        self.sum += x_in_y
        self.level += [dic]
        now_xy = (self.width - (len(self.level)+1)*self.gap_x)*1.0/self.hight
        if self.sum >= now_xy:
            self.new_level()
            return
            
    def over(self):
        if self.level:
            self.new_level()
        


def photo_stream(pics, web_width=1180, want_hight=300, gap_x=50, gap_y=50,
                 html_name = 'photo_stream.html'):
    '''创建照片流页面
    web_width为网页宽度
    want_hight为期望单排高度（实际会比期望的小一点）
    gap_x, gap_y 每张照片的横纵距离
    html_name为文件名字'''                 

    def dic_to_min(dic):
        minn = {}
        minn['path'] = dic['path']
        minn['thu_path'] = dic['thu_path']
        minn['xy'] = dic['xy']
        minn['x/y'] = dic['xy'][0] * 1.0 / dic['xy'][1]
        return minn
    
    pics = map(dic_to_min, pics)
    
    X_IN_Y = web_width * 1.0 / want_hight
    
    banch_pic = Banch_pic(web_width, want_hight, gap_x, gap_y)
    for i in pics:
        banch_pic.add_xy(i)
        
    banch_pic.over()
    
    strr = ''
    def creat_img(dic, strr):
        href = dic['path']
        thu_path = dic['thu_path']
        
        top = dic['top']
        left = dic['left']
        img = '''
    <img class="photo_map"  id = "%s" src="%s"  onclick="open_pic(this.id)"
         style="width:%.2fpx;height:%.2fpx;position:absolute;top:%.2fpx;left:%.2fpx" />
    '''
        strr += img % (href, thu_path, dic['width'], dic['height'], top, left)
        return strr
    
    for i in pics:
        strr = creat_img(i, strr)
    
    f = open('html_model\\photo_stream_model.html')
    html = f.read()
    f = f.close()
    
    html = html.decode('utf-8')
    html = html.replace('{for_img}', strr)
    
    def creat_file(content, name='1.txt',tag='w'):
        '''
        创造文件(内容， 名字， 写入模式)
        '''
        f = open(name, tag)
        f.write(content.encode('utf-8'))
        f.close()
    
    creat_file(html, html_name)
    webbrowser.open(html_name)    


        



dirr = r'test_pic'

pics = get_list(dirr)

pics = add_info(pics)

thumbnail(pics)

photo_stream(pics)

time_line(pics, 12)

photo_on_map(pics)










