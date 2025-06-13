import ctypes
import sys
import json
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from dotenv import load_dotenv
import random
import os
from datetime import datetime, timedelta, timezone
from pytz import timezone
def add_corners(im, rad):
    """将图片裁剪为圆角"""
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    
    alpha = Image.new('L', im.size, 255)
    w, h = im.size
    
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    
    im.putalpha(alpha)
    return im

def add_rounded_rectangle(img, position, size, radius, color, alpha):
    """绘制圆角矩形（带透明度）"""
    x, y = position
    width, height = size
    
    # 处理颜色格式
    if isinstance(color, str):
        color = color.lstrip('#')
        color = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    
    rectangle = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(rectangle)
    
    draw.rounded_rectangle(
        [(0, 0), (width - 1, height - 1)],
        radius=radius,
        fill=color + (int(alpha),)
    )
    
    img.paste(rectangle, (x, y), rectangle)
    return img

# 预定义颜色常量
DIFFICULTY_COLORS = {
    'AT': (56, 56, 56),
    'IN': (207, 19, 19),
    'HD': (0, 117, 184),
    'EZ': (16, 178, 47)
}

INFO_BLOCK_COLOR = (57, 197, 187)
NEXT_COLOR = (196, 228, 164)
WHITE = (255, 255, 255)

def createImage(a_path, output_path, target_size, blur_radius, avatar, b27, username, rks, challengeModeRank, data):
    # 初始化基础图像
    original_img = Image.open(a_path).convert('RGB')
    original_width, original_height = original_img.size
    target_width, target_height = target_size
    
    # 背景模糊处理
    ratio = max(target_width / original_width, target_height / original_height)
    new_size = (int(original_width * ratio), int(original_height * ratio))
    
    blurred_bg = original_img.resize(new_size, Image.LANCZOS)
    blurred_bg = blurred_bg.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    
    # 裁剪背景
    left = (blurred_bg.width - target_width) // 2
    top = (blurred_bg.height - target_height) // 2
    blurred_bg = blurred_bg.crop((left, top, left+target_width, top+target_height))
    
    final_img = Image.new("RGBA", target_size)
    final_img.paste(blurred_bg, (0, 0))
    
    # 绘制头像
    
    ava=''
    try:
        ava = Image.open(f'avatar/{avatar}.png').convert('RGBA')
    except:
        print(f"Avatar {avatar} not found, using default")
        ava = Image.open(f'Resource/noavatar.png').convert('RGBA')
    ava_round = add_corners(ava, 5)
    final_img.paste(ava_round, (64, 64), ava_round)    
     
    # 字体配置
    FONT_CONFIG = {
        'rank': ImageFont.truetype("Resource/SourceHanSansCN-Regular.ttf", 24),
        'difficulty': ImageFont.truetype("Resource/Saira-Regular.ttf", 17),
        'song_name': ImageFont.truetype("Resource/SourceHanSansCN-Regular.ttf", 20),
        'score': ImageFont.truetype("Resource/Saira-Bold.ttf", 32),
        'accuracy': ImageFont.truetype("Resource/Saira-Regular.ttf", 20),
        'next': ImageFont.truetype("Resource/Saira-Regular.ttf", 14),
        'username': ImageFont.truetype("Resource/SourceHanSansCN-Regular.ttf", 48),
        'rks': ImageFont.truetype("Resource/Saira-Regular.ttf", 26),
        'song_name_bigger': ImageFont.truetype("Resource/SourceHanSansCN-Regular.ttf", 24),
        'challenge_rank': ImageFont.truetype("Resource/Saira-Regular.ttf", 28),
        'data': ImageFont.truetype("Resource/Saira-Regular.ttf", 26),
    }
       
    # --- 新增：在头像右侧绘制用户名文本框 ---
    draw = ImageDraw.Draw(final_img)

    # 计算文本框位置（头像右侧 + 20px间距）
    username_x = 64 + ava_round.width + 20
    username_y = 64

    # 文本框背景（圆角矩形）
    username_bg_width = 600  # 宽度可根据需要调整
    username_bg_height = 96
    username_bg_radius = 10

    final_img = add_rounded_rectangle(
        final_img,
        (username_x, username_y),
        (username_bg_width, username_bg_height),
        radius=username_bg_radius,
        color=(50, 50, 50),  # 深灰色背景
        alpha=150
    )

    # 绘制用户名文本（居中）
    username_bbox = draw.textbbox((0, 0), username, font=FONT_CONFIG['username'])
    username_text_x = username_x + (username_bg_width - username_bbox[2]) // 2
    username_text_y = username_y + (username_bg_height - username_bbox[3]) // 2

    draw.text(
        (username_text_x, username_text_y),
        username,
        fill=WHITE,
        font=FONT_CONFIG['username']
    )
    draw = ImageDraw.Draw(final_img)
    username_font = FONT_CONFIG['username']
    username_x = 64 + ava_round.width + 20
    username_y = 64
    username_bg_width = 600
    username_bg_height = 96
    username_bg_radius = 10

    final_img = add_rounded_rectangle(
        final_img,
        (username_x, username_y),
        (username_bg_width, username_bg_height),
        radius=username_bg_radius,
        color=(50, 50, 50),
        alpha=150
    )
    draw.text(
        (username_x + (username_bg_width - username_bbox[2]) // 2, username_y + (username_bg_height - username_bbox[3]) // 2),
        username,
        fill=WHITE,
        font=username_font
    )

    # --- 新增：在用户名下方绘制RKS显示框 ---
    rks_font = FONT_CONFIG['rks']
    rks_text = f"{rks}"
    
    # 计算RKS文本框位置（用户名下方 + 10px间距）
    rks_x = username_x  # 与用户名左对齐
    rks_y = username_y + username_bg_height
    
    # RKS文本框尺寸（根据文本自动调整）
    rks_bbox = draw.textbbox((0, 0), rks_text, font=rks_font)
    rks_bg_width = rks_bbox[2] - rks_bbox[0] + 40  # 左右各加20px边距
    rks_bg_height = rks_bbox[3] - rks_bbox[1] + 20  # 上下各加10px边距
    
    # 绘制白底黑字的RKS框
    final_img = add_rounded_rectangle(
        final_img,
        (rks_x, rks_y),
        (rks_bg_width, rks_bg_height),
        radius=5,  # 圆角半径
        color=(230,230,230),
        alpha=255  # 不透明
    )
    
    # 绘制RKS文本（居中）
    draw.text(
        (rks_x + (rks_bg_width - rks_bbox[2]) // 2, rks_y + (rks_bg_height - rks_bbox[3]) // 2 - 5),
        rks_text,
        fill=(0, 0, 0),  # 黑色文字
        font=rks_font
    )
    
    challenge_rank = challengeModeRank
    rank_tier = challenge_rank // 100
    rank_number = challenge_rank % 100

    # 确定图标路径
    icon_map = {
        1: "Resource/green.png",
        2: "Resource/blue.png",
        3: "Resource/red.png",
        4: "Resource/gold.png",
        5: "Resource/rainbows.png"
    }
    icon_path = icon_map.get(rank_tier, "Resource/grey.png")

    # 加载并调整图标大小
    try:
        icon = Image.open(icon_path).convert('RGBA')
        icon_size = (100, 60)  # 保持与RKS框相同高度
        icon = icon.resize(icon_size, Image.LANCZOS)
        
        # 图标位置（RKS框右侧+10px间距）
        icon_x = rks_x + rks_bg_width + 10
        icon_y = rks_y-10
        
        # 粘贴图标
        final_img.paste(icon, (icon_x, icon_y), icon)
        
        # 在图标上绘制居中数字
        rank_font = FONT_CONFIG['challenge_rank']
        rank_bbox = draw.textbbox((0, 0), str(rank_number), font=rank_font)
        
        draw.text(
            (icon_x + (icon_size[0] - rank_bbox[2]) // 2, 
            icon_y + (icon_size[1] - rank_bbox[3]) // 2-7),
            str(rank_number),
            fill=WHITE,
            font=rank_font
        )
    except Exception as e:
        print(f"Failed to load challenge rank icon: {e}")
    data_font = FONT_CONFIG['data']

    # 1. 计算数据框宽度（动态调整）
    data_icon = Image.open("Resource/data.png").convert('RGBA')
    data_icon_size = (30, 30)  # 数据图标大小
    data_icon = data_icon.resize(data_icon_size, Image.LANCZOS)

    data_text_width = draw.textlength(data, font=data_font)
    data_box_width = data_icon_size[0] + 10 + int(data_text_width) + 25  # 图标+间距+文字+边距
    data_box_height = 40  # 与挑战模式图标同高

    # 2. 绘制半透明背景（70%透明度）
    data_box_pos = (icon_x - data_box_width +350, icon_y+10)  # 挑战模式图标左侧-10px
    final_img = add_rounded_rectangle(
        final_img,
        data_box_pos,
        (data_box_width, data_box_height),
        radius=5,
        color=(80, 80, 80),  # 深灰色背景
        alpha=int(255 * 0.7)  # 70%透明度
    )

    # 3. 粘贴数据图标（左侧居中）
    data_icon = Image.open("Resource/data.png").convert('RGBA')
    original_width, original_height = data_icon.size  # 原始尺寸 20x12
    
    # 计算等比缩放后的新尺寸（高度固定为数据框高度-8px=32px）
    new_height = 24  # 略小于数据框高度以留出边距
    new_width = int(original_width * (new_height / original_height))  # 20*(32/12)=53
    
    data_icon = data_icon.resize((new_width, new_height), Image.LANCZOS)
    
    # 图标位置（左侧居中，距离左边框10px）
    data_icon_x = data_box_pos[0] + 10
    data_icon_y = data_box_pos[1] + (data_box_height - new_height) // 2
    final_img.paste(data_icon, (data_icon_x, data_icon_y), data_icon)
    
    # 调整数据文本起始位置（图标右侧+10px）
    data_text_x = data_icon_x + new_width + 10

    # 4. 绘制数据文本（右侧居中）
    data_text_x = data_icon_x + data_icon_size[0] + 15
    data_text_y = data_box_pos[1] + (data_box_height - data_font.size) // 2 -5
    draw.text(
        (data_text_x, data_text_y),
        data,
        fill=WHITE,
        font=data_font
    )
    # 布局参数
    start_y = 128 + 80  # 增加头像下方间距
    cell_width = 256 + 180 + 50
    cell_height = 135 + 100  # 增加行高

    def truncate_text(text, max_width, font):
        draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))  # 临时画布
        ellipsis = "..."
        
        # 如果原始文本宽度 <= max_width，直接返回原文本
        if draw.textlength(text, font=font) <= max_width:
            return text
        
        # 否则逐步缩短文本并检查宽度
        max_len = len(text)
        while max_len > 0:
            truncated = text[:max_len] + ellipsis
            text_width = draw.textlength(truncated, font=font)
            if text_width <= max_width:
                return truncated
            max_len -= 1
        
        return ellipsis  # 极端情况（max_width极小）

    # 绘制所有B27元素
    for idx, item in enumerate(b27):
        row = idx // 3
        col = idx % 3
        
        # 计算位置
        x = 50 + col * (cell_width + 50)
        y = start_y + row * (cell_height - 20)
        if idx >= 30: y+=50
        # 边界检查
            
        draw = ImageDraw.Draw(final_img)
        
        # 1. 绘制编号
        b_text = item[1]
        text_bbox = draw.textbbox((0,0), b_text, font=FONT_CONFIG['rank'])
        # b_width = text_bbox[2] - text_bbox[0] + 20
        b_width = 50
        
        b_height = text_bbox[3] - text_bbox[1] + 10
        
        final_img = add_rounded_rectangle(
            final_img,
            (x, y),
            (b_width, b_height),
            0,
            WHITE,
            255
        )
        draw.text(
            (x + (b_width - text_bbox[2])//2, y + (b_height - text_bbox[3])//2 - 5),
            b_text,
            fill=(0,0,0),
            font=FONT_CONFIG['rank']
        )
        
        # 2. 歌曲插图
        img_path = f"illustrationLowRes/{item[0]}.png"
        if not os.path.exists(img_path):
            img_path = "Resource/nodata.png"
            
        song_img = Image.open(img_path).convert('RGB').resize((256, 135))
        final_img.paste(song_img, (x + b_width, y))
        
        # 3. 难度标签（左下角）
        diff_type = item[7]
        tag_size = (70, 45)
        tag_pos = (x + b_width, y + 135 - tag_size[1])  # 左下角位置
        
        final_img = add_rounded_rectangle(
            final_img,
            tag_pos,
            tag_size,
            0,
            DIFFICULTY_COLORS.get(diff_type, WHITE),
            200
        )
        
        # 难度文字
        diff_text = f'{diff_type} {item[4]}\n'+'%.3f'%item[3]
        text_bbox = draw.textbbox((0,0), diff_text, font=FONT_CONFIG['difficulty'])
        # draw.text(
        #     (tag_pos[0] + (tag_size[0]-text_bbox[2])//2, tag_pos[1]),
        #     diff_text,
        #     fill=WHITE,
        #     font=FONT_CONFIG['difficulty']
        # )
        xx,yy = tag_pos[0] + (tag_size[0]-text_bbox[2])//2, tag_pos[1]
        for line in diff_text.split('\n'):
            draw.text(
                (xx, yy),
                line, 
                font=FONT_CONFIG['difficulty'], 
                fill=WHITE
            )
            yy += -2 + int(17*4/3)
        # 1. 定义info_block的尺寸
        info_block_width = 225
        info_block_height = 110
        # 2. 绘制info_block（圆角矩形背景）
        info_pos = (x + b_width + 256, y + (135 - info_block_height)//2)
        final_img = add_rounded_rectangle(
            final_img,
            info_pos,
            (info_block_width, info_block_height),
            radius=0,
            color=INFO_BLOCK_COLOR,
            alpha=200
        )

        # 3. 计算居中坐标（关键修改）
        def get_centered_x(text, font, box_width):
            """计算文本在指定宽度内的居中x坐标"""
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            return (box_width - text_width) // 2

        # 4. 绘制歌曲名称（居中）
        max_name_width = 200
        truncated_name = truncate_text(item[2], max_name_width, FONT_CONFIG['song_name'])
        song_name_font = FONT_CONFIG['song_name']
        if len(item[2]) <= 15:
            song_name_font = FONT_CONFIG['song_name_bigger']

        # 计算居中位置
        name_x = info_pos[0] + get_centered_x(truncated_name, song_name_font, info_block_width)
        draw.text(
            (name_x, info_pos[1] + 5),  # y坐标保持原样
            truncated_name,
            fill=WHITE,
            font=song_name_font
        )

        # # 5. 绘制分数（居中）
        # score_text = f"{item[6]}"
        # score_x = info_pos[0] + get_centered_x(score_text, FONT_CONFIG['score'], info_block_width)
        # draw.text(
        #     (score_x, info_pos[1] + 25),
        #     score_text,
        #     fill=WHITE,
        #     font=FONT_CONFIG['score']
        # )
        # 4. 右侧信息块
        '''info_pos = (x + b_width + 256, y + (135 - 90)//2)
        final_img = add_rounded_rectangle(
            final_img,
            info_pos,
            (225, 110),  # 增大尺寸
            radius=0,
            color=INFO_BLOCK_COLOR,
            alpha=200  # 60%透明度
        )
        
        # 歌曲名称（白色，自动截断）
        
        max_name_width = 200
        truncated_name = truncate_text(item[2], max_name_width, FONT_CONFIG['song_name'])
        song_name_font = FONT_CONFIG['song_name']
        if(len(item[2]) <= 15): song_name_font=FONT_CONFIG['song_name_bigger']
        name_bbox = draw.textbbox((0,0), truncated_name, font=song_name_font)
        draw.text(
            (info_pos[0] + 100 - name_bbox[2]/2, info_pos[1] + 5),
            truncated_name,
            fill=WHITE,
            font=song_name_font
        )'''
        
        # 分数显示（无逗号，加粗）
        score_text = f"{item[6]}"
        score_bbox = draw.textbbox((0,0), score_text, font=FONT_CONFIG['score'])
        draw.text(
            (info_pos[0] + 100 - score_bbox[2]/2+30, info_pos[1] + 30),
            score_text,
            fill=WHITE,
            font=FONT_CONFIG['score']
        )
        
        # 分割线（右移10px）
        line_start = (info_pos[0] + 36, info_pos[1] + 65)  # 右移10px
        # draw.line([line_start, (line_start[0]+128, line_start[1])], 
        #          fill=WHITE, width=4)
        
        # 精度和NEXT
        acc_text ='%.2f'%item[5]+'%'
        acc_width = draw.textlength(acc_text, font=FONT_CONFIG['accuracy'])
        draw.text(
            (line_start[0]+25, line_start[1]),
            acc_text,
            fill=WHITE,
            font=FONT_CONFIG['accuracy']
        )
        
        next_text = f">> {item[8]}"
        draw.text(
            (line_start[0] + acc_width + 40, line_start[1]),
            next_text,
            fill=NEXT_COLOR,
            font=FONT_CONFIG['next']
        )
        
        # 评级图标
        icon_path = "Resource/"
        score = item[6]
        if score == 1000000:
            icon_path += "Phi.png"
        elif item[9]:
            icon_path += "FC.png"
        else:
            if score >= 960000: icon_path += "V.png"
            elif score >=920000: icon_path += "S.png"
            elif score >=880000: icon_path += "A.png"
            elif score >=820000: icon_path += "B.png"
            elif score >=700000: icon_path += "C.png"
            else: icon_path += "F.png"
        if os.path.exists(icon_path):
            icon = Image.open(icon_path).convert('RGBA').resize((64,64))
            final_img.paste(icon, (info_pos[0], info_pos[1]+40), icon)
    
    # 最终保存
    final_img.convert('RGB').save(output_path, format="PNG")
# 使用示例
def classToNum(a : str) -> int:
    if(a == 'EZ'): return 0
    elif(a == 'HD'): return 1
    elif(a == 'IN'): return 2
    elif(a == 'AT'): return 3
    return 4

load_dotenv('.env')
# 重定向print输出到文件
sys.stdout = open('output.txt', 'w', encoding='utf-8')
if(sys.platform.startswith('linux')): phigros = ctypes.CDLL("./libphigros.so")
elif(sys.platform.startswith('win32')): phigros = ctypes.CDLL("./phigros-64.dll")
else: sys.exit(1)
# print(phigros)
phigros.get_handle.argtypes = ctypes.c_char_p,
phigros.get_handle.restype = ctypes.c_void_p
phigros.free_handle.argtypes = ctypes.c_void_p,
phigros.get_nickname.argtypes = ctypes.c_void_p,
phigros.get_nickname.restype = ctypes.c_char_p
phigros.get_summary.argtypes = ctypes.c_void_p,
phigros.get_summary.restype = ctypes.c_char_p
phigros.get_save.argtypes = ctypes.c_void_p,
phigros.get_save.restype = ctypes.c_char_p
phigros.load_difficulty.argtypes = ctypes.c_void_p,
phigros.get_b19.argtypes = ctypes.c_void_p,
phigros.get_b19.restype = ctypes.c_char_p
# phigros.re8.argtypes = ctypes.c_void_p,

sessionToken = os.getenv('SESSIONTOKEN').encode('UTF-8')
handle = phigros.get_handle(sessionToken)   # 获取handle,申请内存,参数为sessionToken
# print(handle)
nickname = phigros.get_nickname(handle).decode('utf-8')        # 获取玩家昵称
summary = json.loads(phigros.get_summary(handle).decode('utf-8'))
savedata = json.loads(phigros.get_save(handle).decode('utf-8'))
print(summary)
print(savedata)
progress = summary['progress']
gameRecords = savedata['gameRecord']
data = savedata['gameProgress']['money']
user = savedata['user']
# print(savedata)             # 获取存档

singlefile = open('info.tsv', 'r', encoding='utf-8')
songid = singlefile.readlines()    
songname = {}
for idx in range(len(songid)):
    now = songid[idx]
    songid[idx] = now.split('\t')[0]
    songname.update({songid[idx]:now.split('\t')[1]})
# print(songname)
# print(gameRecords)
difffile = open('difficulty.tsv', 'r', encoding='utf-8')
diff = {}
contect = difffile.readlines()
for idx in range(len(contect)):
    contect[idx] = contect[idx].rstrip('\n')
# print(contect)
for i in contect:
    sum = i.count('\t')
    str1 = i.split('\t')
    if sum == 3:
        diff[str1[0]] = [float(str1[1]), float(str1[2]), float(str1[3]), 0.0]
    else:
        diff[str1[0]] = [float(str1[1]), float(str1[2]), float(str1[3]), float(str1[4])]



rksContribution = {}
score = []
phi = []

for i in songid: 
    if not i in gameRecords:
        rksContribution[i] = [0.0, 0.0, 0.0, 0.0]
        continue
    rksEZ = pow((gameRecords[i][1]-55.0)/45,2)*diff[i][0] if gameRecords[i][1] >= 70 else 0
    rksHD = pow((gameRecords[i][4]-55.0)/45,2)*diff[i][1] if gameRecords[i][4] >= 70 else 0
    rksIN = pow((gameRecords[i][7]-55.0)/45,2)*diff[i][2] if gameRecords[i][7] >= 70 else 0
    rksAT = pow((gameRecords[i][10]-55.0)/45,2)*diff[i][3] if gameRecords[i][10] >= 70 else 0
    rksContribution[i] = [rksEZ, rksHD, rksIN, rksAT]
    if rksEZ : score.append((rksEZ,i,'EZ',diff[i][0],bool(gameRecords[i][2])))
    if rksHD : score.append((rksHD,i,'HD',diff[i][1],bool(gameRecords[i][5])))
    if rksIN : score.append((rksIN,i,'IN',diff[i][2],bool(gameRecords[i][8])))
    if rksAT : score.append((rksAT,i,'AT',diff[i][3],bool(gameRecords[i][11])))
    if(rksEZ == diff[i][0] and diff[i][0]) : phi.append((rksEZ,i,'EZ',diff[i][0],True))
    if(rksHD == diff[i][1] and diff[i][1]) : phi.append((rksHD,i,'HD',diff[i][1],True))
    if(rksIN == diff[i][2] and diff[i][2]) : phi.append((rksIN,i,'IN',diff[i][2],True))
    if(rksAT == diff[i][3] and diff[i][3]) : phi.append((rksAT,i,'AT',diff[i][3],True))
    # print(i, rksContribution[i])
score.sort()
score.reverse()
# print(score)
phi.sort()
phi.reverse()
# print(phi)
# print(rksContribution) 
rks = 0.0
for i in range(min(27,len(score))):
    rks = rks + score[i][0]
for i in range(min(3,len(phi))):
    rks = rks + phi[i][0]

rks = rks / 30.0

updatetime = datetime.now().astimezone(timezone('Asia/Shanghai')).replace(tzinfo=None)
# print(rks)
# sys.exit(0)
print(updatetime)
print('Save version: ', summary['saveVersion'])
print('Challenge mode rank: ', summary['challengeModeRank'])
print('RKS: ', summary['rankingScore'])
print('GameVersion: ', summary['gameVersion'])
print('Avatar: ', user['avatar'])
print('Data: ', end='')
data_num = ''
if data[4]:   data_num=f'{data[4]}PiB {data[3]}TiB {data[2]}GiB {data[1]}MiB {data[0]}KiB'
elif data[3]: data_num=f'{data[3]}TiB {data[2]}GiB {data[1]}MiB {data[0]}KiB'
elif data[2]: data_num=f'{data[2]}GiB {data[1]}MiB {data[0]}KiB'
elif data[1]: data_num=f'{data[1]}MiB {data[0]}KiB'
else: f'{data[0]}KiB'
print(data_num)
print('/    EZ   HD   IN   AT')
print(f'C   {progress[0]: 3d} {progress[3]: 3d} {progress[6]: 3d} {progress[9]: 3d} ')
print(f'FC  {progress[1]: 3d} {progress[4]: 3d} {progress[7]: 3d} {progress[10]: 3d} ')
print(f'AT  {progress[2]: 3d} {progress[5]: 3d} {progress[8]: 3d} {progress[11]: 3d} ')
print()
for i in range(min(3,len(phi))):
    print(f'P{i+1} {phi[i][1]}, ACC: {round(gameRecords[phi[i][1]][classToNum(phi[i][2])*3+1],2)}%, RKS: {round(phi[i][0],2)}/{diff[phi[i][1]][classToNum(phi[i][2])]} Score:{gameRecords[phi[i][1]][classToNum(phi[i][2])*3]}')
print()
for i in range(min(33,len(score))):
    print(f'B{i+1} {score[i][1]}, ACC: {round(gameRecords[score[i][1]][classToNum(score[i][2])*3+1],2)}%, RKS: {round(score[i][0],2)}/{diff[score[i][1]][classToNum(score[i][2])]} Score:{gameRecords[score[i][1]][classToNum(score[i][2])*3]}')
    if(i == 27):
        print('————OVER FLOW————')

# print(rks)
# print(diff)
# phigros.load_difficulty(b"../difficulty.tsv")# 读取difficulty.tsv,参数为文件路径
# b19 = phigros.get_b19(handle).decode('utf-8')
# print(b19)             # 从存档读取B19,依赖load_difficulty
phigros.free_handle(handle)                 # 释放handle的内存,不会被垃圾回收,使用完handle请确保释放
b27 = [] # (songid,rank,songname,rks,difficulty,acc,score,type,nxt,fc)
for i in range(min(3,len(phi))):
    id = phi[i][1]
    accuary = gameRecords[phi[i][1]][classToNum(phi[i][2])*3+1]
    scr = gameRecords[phi[i][1]][classToNum(phi[i][2])*3]
    b27.append((id,f'P{i+1}',songname[id],phi[i][0],phi[i][3],accuary,scr,phi[i][2],'00.00%',phi[i][4]))
for i in range(min(33,len(score))):
    id = score[i][1]
    accuary = gameRecords[score[i][1]][classToNum(score[i][2])*3+1]
    scr = gameRecords[score[i][1]][classToNum(score[i][2])*3]
    b27.append((id,f'B{i+1}',songname[id],score[i][0],score[i][3],accuary,scr,score[i][2],'00.00%',score[i][4]))
createImage(
    
    a_path=f"illustrationLowRes/{random.choice(os.listdir('illustrationLowRes'))}",  # 替换为你的图片路径
    output_path="output.png",
    target_size=(1800, 3000),
    blur_radius=55,  # 可根据需要调整虚化程度
    avatar=user['avatar'],
    b27=b27,
    username=nickname,
    rks=round(summary['rankingScore'],4),
    challengeModeRank=summary['challengeModeRank'],
    data=data_num
)
## a