import ctypes
import sys
from json import loads
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageEnhance
from dotenv import load_dotenv
from random import choice
import os
from datetime import datetime, timezone
from pytz import timezone

VERSION = 'Unknown'
with open("VERSION", "r") as f:
    VERSION = f.read()
def printwithcolor(text: str, option: list, end1: str='\n'):
    '''
    option: 
            0	关闭所有格式，还原为初始状态
            1	粗体/高亮显示
            2	模糊（※）
            3	斜体（※）
            4	下划线（单线）
            5	闪烁（慢）
            6	闪烁（快）（※）
            7	交换背景色与前景色
            8	隐藏（伸手不见五指，啥也看不见）（※）
            30-37	前景色, 即30+x, x表示不同的颜色 (参见下面的“颜色表”)
            40-47	背景色, 即40+x, x表示不同的颜色 (参见下面的“颜色表”)
0	1	2	3	4	5	6	7
黑	红	绿	黄	蓝	紫	青	白
    '''
    if type(option)==int:option=[option]
    res : str = '\033['
    for i in option:
        if(type(i)!=int): raise('Invaild type')
        if((0<=i and i<=8)or(30<=i<=37)or(40<=i<=47)): res+=str(i)+';'
        else: raise('Invaild type')
    res = res[:-1]
    res+=f'm{text}\033[0m'
    print(res, end=end1)

def fuck(info : str, errcode : int = 0):
    printwithcolor(f'程序已中止(停止代码: {str(errcode).zfill(2)})',[1,31])
    print(info)
    input("按下Enter以继续...")
    sys.exit(1)
    
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

def classToNum(a : str) -> int:
    # 将难度字符串转换为数字
    if(a == 'EZ'): return 0
    elif(a == 'HD'): return 1
    elif(a == 'IN'): return 2
    elif(a == 'AT'): return 3
    return 4

# 预定义颜色常量
DIFFICULTY_COLORS = {
    'AT': (56, 56, 56),
    'IN': (207, 19, 19),
    'HD': (0, 117, 184),
    'EZ': (16, 178, 47)
}

INFO_BLOCK_COLOR = (57, 197, 187)
WHITE = (255, 255, 255)

def createImage(a_path, output_path, target_size, blur_radius, avatar, b27, username, rks, challengeModeRank, data, updatetime, progress):
    # (songid,rank,songname,rks,difficulty,acc,score,type,nxt,fc)
    # 初始化基础图像
    original_img = Image.open(a_path).convert('RGB')
    enhancer = ImageEnhance.Brightness(original_img)
    original_img = enhancer.enhance(0.7)
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
        ava_round = add_corners(ava, 5)
        final_img.paste(ava_round, (64, 64), ava_round)    
    # except Exception as e:
        #     fuck(f'找不到头像png文件, 请检查avatar是否为最新数据:{e}',5)
    except:
        ava = Image.new("RGBA",(64,64),(57,197,187))
        ava_round = add_corners(ava, 5)
    
     
    # 字体配置
    FONT_CONFIG = {
        'rank': ImageFont.truetype("Resource/SourceHanSansCN-Regular.ttf", 24),
        'difficulty': ImageFont.truetype("Resource/SourceHanSans&SairaHybrid-Regular.ttf", 17),
        'song_name': ImageFont.truetype("Resource/SourceHanSans&SairaHybrid-Regular.ttf", 20),
        'score': ImageFont.truetype("Resource/SourceHanSans&SairaHybrid-Regular.ttf", 36),
        'accuracy': ImageFont.truetype("Resource/SourceHanSans&SairaHybrid-Regular.ttf", 26),
        'next': ImageFont.truetype("Resource/SourceHanSans&SairaHybrid-Regular.ttf", 16),
        'username': ImageFont.truetype("Resource/SourceHanSans&SairaHybrid-Regular.ttf", 48),
        'rks': ImageFont.truetype("Resource/SourceHanSans&SairaHybrid-Regular.ttf", 26),
        'song_name_bigger': ImageFont.truetype("Resource/SourceHanSans&SairaHybrid-Regular.ttf", 24),
        'challenge_rank': ImageFont.truetype("Resource/SourceHanSans&SairaHybrid-Regular.ttf", 36),
        'data': ImageFont.truetype("Resource/SourceHanSans&SairaHybrid-Regular.ttf", 26),
        'updatetime': ImageFont.truetype("Resource/SourceHanSans&SairaHybrid-Regular.ttf", 22),
        'sheet': ImageFont.truetype("Resource/SourceHanSans&SairaHybrid-Regular.ttf", 26),
        'version': ImageFont.truetype("Resource/SourceHanSans&SairaHybrid-Regular.ttf", 30),
        'open-sourced': ImageFont.truetype("Resource/SourceHanSans&SairaHybrid-Regular.ttf", 24),
        # 'open-sourced': ImageFont.truetype("Resource/Saira-Regular.ttf", 24),
        # 'rank': ImageFont.truetype("Resource/SourceHanSansCN-Regular.ttf", 24),
        # 'difficulty': ImageFont.truetype("Resource/SourceHanSansCN-Regular.ttf", 17),
        # 'song_name': ImageFont.truetype("Resource/SourceHanSansCN-Regular.ttf", 20),
        # 'score': ImageFont.truetype("Resource/Saira-Regular.ttf", 32),
        # 'accuracy': ImageFont.truetype("Resource/SourceHanSansCN-Regular.ttf", 22),
        # 'next': ImageFont.truetype("Resource/SourceHanSansCN-Regular.ttf", 16),
        # 'username': ImageFont.truetype("Resource/SourceHanSansCN-Regular.ttf", 48),
        # 'rks': ImageFont.truetype("Resource/SourceHanSansCN-Regular.ttf", 26),
        # 'song_name_bigger': ImageFont.truetype("Resource/SourceHanSansCN-Regular.ttf", 24),
        # 'challenge_rank': ImageFont.truetype("Resource/Saira-Regular.ttf", 28),
        # 'data': ImageFont.truetype("Resource/Saira-Regular.ttf", 26),
        # 'updatetime': ImageFont.truetype("Resource/SourceHanSansCN-Regular.ttf", 22),
        # 'sheet': ImageFont.truetype("Resource/SourceHanSansCN-Regular.ttf", 26),
        # 'version': ImageFont.truetype("Resource/Saira-Regular.ttf", 30),
        # 'open-sourced': ImageFont.truetype("Resource/Saira-Regular.ttf", 24),

        
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

    
    draw = ImageDraw.Draw(final_img)
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
        (username_x + (username_bg_width - username_bbox[2]) // 2, username_y + (username_bg_height - username_bbox[3]) // 2 - 10),
        username,
        fill=WHITE,
        font=FONT_CONFIG['username']
    )
    
    final_img = add_rounded_rectangle(
        final_img,
        (username_x, username_y - 28),
        (500,30),
        radius=5,
        color=(50, 50, 50),
        alpha=150
    )
    draw.text(
        (username_x + 10, username_y - 28),
        'Updated at: '+updatetime[:-7]+' UTC+08:00',
        fill=WHITE,
        font=FONT_CONFIG['updatetime']
    )
    
    # 在username绘制代码之后添加以下内容

    # 表格参数配置  
    table_x = username_x + username_bg_width + 400  # 表格起始x坐标（username框右侧20px）
    table_y = username_y - 10  # 与username框对齐
    cell_width = 80  # 单元格宽度
    cell_height = 40  # 单元格高度
    header_height = 40  # 表头高度
    row_height = cell_height  # 行高
    border_radius = 5  # 圆角半径
    bg_alpha = 150  # 背景透明度

    # 表头文本
    headers = ["", "EZ", "HD", "IN", "AT"]
    row_labels = ["C", "FC", "AP"]

    # 1. 绘制表头
    for col in range(5):
        cell_x = table_x + col * cell_width
        cell_y = table_y
        
        # 表头单元格背景
        final_img = add_rounded_rectangle(
            final_img,
            (cell_x, cell_y),
            (cell_width if col > 0 else 80, header_height),  # 第一列较窄
            radius=0,
            color=(70, 70, 70),
            alpha=bg_alpha
        )
        
        # 表头文字
        header_text = headers[col] if col < len(headers) else ""
        text_bbox = draw.textbbox((0, 0), header_text, font=FONT_CONFIG['sheet'])
        draw.text(
            (cell_x + (cell_width - text_bbox[2])//2, cell_y + (header_height - text_bbox[3])//2-3),
            header_text,
            fill=WHITE,
            font=FONT_CONFIG['sheet']
        )

    # 2. 绘制数据行
    for row in range(3):
        for col in range(5):
            cell_x = table_x + col * cell_width
            cell_y = table_y + header_height + row * row_height
            
            # 第一列特殊处理（行标签）
            if col == 0:
                final_img = add_rounded_rectangle(
                    final_img,
                    (cell_x, cell_y),
                    (80, row_height),  # 行标签列较窄
                    radius=0,
                    color=(60, 60, 60),
                    alpha=bg_alpha
                )
                
                label_text = row_labels[row] if row < len(row_labels) else ""
                text_bbox = draw.textbbox((0, 0), label_text, font=FONT_CONFIG['sheet'])
                draw.text(
                    (cell_x + (80 - text_bbox[2])//2, cell_y + (row_height - text_bbox[3])//2),
                    label_text,
                    fill=WHITE,
                    font=FONT_CONFIG['sheet']
                )
            else:
                # 数据单元格背景
                final_img = add_rounded_rectangle(
                    final_img,
                    (cell_x, cell_y),
                    (cell_width, row_height),
                    radius=0,
                    color=(50, 50, 50),
                    alpha=bg_alpha
                )
                
                # 进度数据（确保progress数组存在且足够大）
                if len(progress) > row and len(progress[row]) > col-1:
                    progress_text = f"{progress[row][col-1]:4d}"
                else:
                    progress_text = "0d"
                    
                text_bbox = draw.textbbox((0, 0), progress_text, font=FONT_CONFIG['sheet'])
                draw.text(
                    (cell_x + (cell_width - text_bbox[2])//2, cell_y + (row_height - text_bbox[3])//2),
                    progress_text,
                    fill=WHITE,
                    font=FONT_CONFIG['sheet']
                )

    # 3. 添加表格外边框（可选）
    table_width = 5 * cell_width
    table_height = header_height + 3 * row_height
    final_img = add_rounded_rectangle(
        final_img,
        (table_x, table_y),
        (table_width, table_height),
        radius=border_radius,
        color=(100, 100, 100),
        alpha=50,  # 半透明边框
    )
    
    # --- 新增：在用户名下方绘制RKS显示框 ---
    rks_font = FONT_CONFIG['rks']
    rks_text = f'%.4f'%rks
    
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
        (rks_x + (rks_bg_width - rks_bbox[2]) // 2, rks_y + (rks_bg_height - rks_bbox[3]) // 2 - 3),
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
        icon_y = rks_y - 8
        
        # 粘贴图标
        final_img.paste(icon, (icon_x, icon_y), icon)
        
        # 在图标上绘制居中数字
        rank_font = FONT_CONFIG['challenge_rank']
        rank_bbox = draw.textbbox((0, 0), str(rank_number), font=rank_font)
        
        draw.text(
            (icon_x + (icon_size[0] - rank_bbox[2]) // 2, 
            icon_y + (icon_size[1] - rank_bbox[3]) // 2-5),
            str(rank_number),
            fill=WHITE,
            font=rank_font
        )
    except Exception as e:
        fuck(f"Failed to load challenge rank icon: {e}")
        
    data_font = FONT_CONFIG['data']

    # 1. 计算数据框宽度（动态调整）
    data_icon = Image.open("Resource/data.png").convert('RGBA')
    data_icon_size = (30, 30)  # 数据图标大小
    data_icon = data_icon.resize(data_icon_size, Image.LANCZOS)
    
    data_text_width = draw.textlength(data, font=data_font)
    data_box_width = data_icon_size[0] + 10 + int(data_text_width) + 35  # 图标+间距+文字+边距
    data_box_height = 40  # 与挑战模式图标同高

    # 2. 绘制半透明背景（70%透明度）
    data_box_pos = (460, icon_y+10)  # 挑战模式图标左侧-10px
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
    data_text_y = data_box_pos[1] + (data_box_height - data_font.size) // 2 
    draw.text(
        (data_text_x, data_text_y),
        data,
        fill=WHITE,
        font=data_font
    )
    # 布局参数
    start_y = 128 + 120 # 增加头像下方间距
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
    try:
        OVERFLOW=Image.open("Resource/overflow.png").convert('RGBA').resize((600,157))
    except:
        try:
            OVERFLOW=Image.open("Resource/OVERFLOW.png").convert('RGBA').resize((600,157))
        except Exception as e:
            fuck(e)
    final_img.paste(OVERFLOW,(600,2315),mask=OVERFLOW)
    # 绘制所有B27元素
    for idx, item in enumerate(b27):
        row = idx // 3
        col = idx % 3
        
        # 计算位置
        x = 50 + col * (cell_width + 100)
        y = start_y + row * (cell_height - 20)
        if idx >= 30: y += 65
        # 边界检查
            
        draw = ImageDraw.Draw(final_img)
        
        # 1. 绘制编号
        b_text = item[1]
        text_bbox = draw.textbbox((0,0), b_text, font=FONT_CONFIG['rank'])
        # b_width = text_bbox[2] - text_bbox[0] + 20
        b_width = 50
        
        b_height = text_bbox[3] - text_bbox[1] + 10
        color1 = (220,220,220)
        if(item[1][0]=='P'): color1=(240,235,0)
        final_img = add_rounded_rectangle(
            final_img,
            (x, y),
            (b_width, b_height),
            5,
            color1,
            200
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
            
        song_img = Image.open(img_path).convert('RGB').resize((int(256*1.2), int(135*1.2)))
        final_img.paste(song_img, (x + b_width, y))
        if(item[0] != 'No Data'):
        # 3. 难度标签（左下角）
            diff_type = item[7]
            tag_size = (70, 45)
            tag_pos = (x + b_width, y + 135 - tag_size[1] +25)  # 左下角位置
            
            final_img = add_rounded_rectangle(
                final_img,
                tag_pos,
                tag_size,
                5,
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
            xx,yy = tag_pos[0] + (tag_size[0]-text_bbox[2])//2, tag_pos[1]+5
            for line in diff_text.split('\n'):
                draw.text(
                    (xx, yy),
                    line, 
                    font=FONT_CONFIG['difficulty'], 
                    fill=WHITE
                )
                yy += -2 + int(17*4/3)
        # 1. 定义info_block的尺寸
        info_block_width = 240
        info_block_height = 130
        # 2. 绘制info_block（圆角矩形背景）
        info_pos = (x + b_width + 256 + 50, y + (135 - info_block_height)//2 + 25)
        # final_img = add_rounded_rectangle(
        #     final_img,
        #     info_pos,
        #     (info_block_width, info_block_height),
        #     radius=5,
        #     color=INFO_BLOCK_COLOR,
        #     alpha=200
        # )
        info_block = Image.open('Resource/infoblock.png').convert('RGBA').resize((info_block_width,info_block_height))
        final_img.paste(info_block, (info_pos[0], info_pos[1] - 13), info_block)
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
            (info_pos[0] + 100 - score_bbox[2]/2+40, info_pos[1] + 30),
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
            (line_start[0]+35, line_start[1]+5),
            acc_text,
            fill=WHITE,
            font=FONT_CONFIG['accuracy']
        )
        
        # next_text = f"{item[8]}"
        # draw.text(
        #     (line_start[0] + acc_width + 30, line_start[1] + 5),
        #     next_text,
        #     fill=NEXT_COLOR,
        #     font=FONT_CONFIG['next']
        # )
        
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
    draw.text(
        (5, 2950),
        'Ver. '+VERSION,
        fill=WHITE,
        font=FONT_CONFIG['version']
    )
    draw.text(
        (1265, 2950),
        'Phigros rks Image Maker',
        fill=WHITE,
        font=FONT_CONFIG['version']
    )
    draw.text(
        (1610, 2960),
        'open-sourced on Github',
        fill=WHITE,
        font=FONT_CONFIG['open-sourced']
    )
    # 最终保存
    final_img.convert('RGB').save(output_path, format="PNG")


if(sys.platform.startswith('linux')): phigros = ctypes.CDLL("./libphigros.so")
elif(sys.platform.startswith('win32')): phigros = ctypes.CDLL("./phigros-64.dll")
else: fuck('暂不支持除Linux/Windows外的操作系统',1)
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


current_dir = os.getcwd()
try: os.system(f'cd \"{current_dir}\"')
except: printwithcolor('无法切换到文件所在目录, 可能无法正常运行',[1,31])
settings : dict = {
    'AutoUpdate' : True,        #自动更新数据
    'EnterToContiune' : True,   #按下Enter以继续
    'yywMode' : False,          #演示模式
    'outputLog' : True,         #是否保留历史记录
    } 

flag1 : bool = False
try:
    sessionToken=str(sys.argv[1])
    try: sessionToken=sessionToken.encode('UTF-8')
    except: pass
    try:
        handle = phigros.get_handle(sessionToken)
        nickname = phigros.get_nickname(handle).decode('utf-8')        # 获取玩家昵称
        if(nickname == 'ERROR:Could not find user.'):raise('114514')
        flag1 = True
    except:
        raise('114514')
except:
    if os.path.exists('.env'):
        load_dotenv('.env')
        try:
            sessionToken = os.getenv('SESSIONTOKEN').encode('UTF-8')
        except:
            sessionToken = None
        if(not sessionToken): 
            print('.env文件中没有SESSIONTOKEN项, 请输入Sessiontoken, 输入0则结束程序')
            sessionToken = None
            flag1 : bool = True
            try:
                while True:
                    sessionToken : str = input().strip()
                    if(sessionToken == '0'): break
                    if(sessionToken != ''):
                        flag1 = False
                        break
                if(flag1): sys.exit(0)  
            except:
                fuck('?')
    else:
        print('未检测到.env文件')
        print('请输入Sessiontoken, 输入0则结束程序')
        sessionToken = None
        flag1 : bool = True
        while True:
            sessionToken : str = input().strip()
            if(sessionToken == '0'): break
            if(sessionToken != ''):
                flag1 = False
                break
        if(flag1): sys.exit(0)   
   
if os.path.exists('config.ini'):
    load_dotenv('config.ini')
    for key in settings.keys():
        try:
            set1 = os.getenv(key).encode('UTF-8')
            if(set1 == 1 or set1 == b'True' or set1 == b'true'): set1 = 1     # strictly enabled
            elif(set1 == 0 or set1 == b'False' or set1 == b'false'): set1 = 0 # strictly disabled
            else: set1 = -1                                                   # normal case
            settings[key] = set1
        except:
            pass
# else:
#     f = open('config.ini', 'w')
#     for key, value in settings.items():
#         f.write(f'{key}={"True" if value else "False"}\n')
#     f.close()

try:  sessionToken = sessionToken.encode('utf-8')
except: pass

# print(phigros)
try:
    if settings['AutoUpdate'] == 1: raise(Exception)
    elif settings['AutoUpdate'] == -1:
        updatefileOption = input('是否更新本地的曲绘、头像、歌曲难度、歌曲信息文件(y/n)默认为y\n')
        if (updatefileOption == 'Y' or updatefileOption == 'y'):
            raise(Exception)
except Exception as e: 
    if(e != KeyboardInterrupt):
        try:
            import updatefile
            updatefile.main()
        except Exception as e:
            printwithcolor(f'无法更新文件{e}',[31])


# phigros.re8.argtypes = ctypes.c_void_p,
try:
    singlefile = open('info.tsv', 'r', encoding='utf-8')
except:
    fuck('无法打开info.tsv文件',11)
songid = singlefile.readlines()    
songname = {}
for idx in range(len(songid)):
    now = songid[idx]
    songid[idx] = now.split('\t')[0]
    songname.update({songid[idx]:now.split('\t')[1]})
# print(songname)
# print(gameRecords)
try:
    difffile = open('difficulty.tsv', 'r', encoding='utf-8')
except:
    fuck('无法打开info.tsv文件',11)
diff = {}
allRksRanking = {}
contect = difffile.readlines()
for idx in range(len(contect)):
    contect[idx] = contect[idx].rstrip('\n')
# print(contect)
for i in contect:
    sum = i.count('\t')
    str1 = i.split('\t')
    if sum == 3:
        diff[str1[0]] = [float(str1[1]), float(str1[2]), float(str1[3]), 0.0]
        for _ in range(1,4):
            allRksRanking[(str1[0],_)]=[diff[str1[0]][_-1]]
    else:
        diff[str1[0]] = [float(str1[1]), float(str1[2]), float(str1[3]), float(str1[4])]
        for _ in range(1,5):
            allRksRanking[(str1[0],_)]=[diff[str1[0]][_-1]]
allRksRanking = sorted(allRksRanking.items(), key=lambda x: x[1])
allRksRanking.reverse()
def getMaxRks()->int:
    res = 0
    for idx,i in zip(allRksRanking,range(0,min(27,len(allRksRanking)))):
        res+=idx[1][0]
        if i<=2: res+=idx[1][0]
    return res/30

if not settings['yywMode']:
        
    try:
        if(not flag1): handle = phigros.get_handle(sessionToken)   # 获取handle,申请内存,参数为sessionToken
    except Exception as e:
        fuck(e)
    # print(handle)
    nickname = phigros.get_nickname(handle).decode('utf-8')        # 获取玩家昵称
    if(nickname == 'ERROR:Could not find user.'):
        fuck('Sessiontoken错误',4)
    summary = loads(phigros.get_summary(handle).decode('utf-8'))
    savedata = loads(phigros.get_save(handle).decode('utf-8'))
    gameRecords = savedata['gameRecord']
    data = savedata['gameProgress']['money']
    user = savedata['user']
    # print(savedata)             # 获取存档
else:
    nickname = 'Sample'
    summary={'challengeModeRank':551,'rankingScore':getMaxRks()}
    user = {'avatar':''}
    savedata={'gameRecord':{},'gameProgress':{'challengeModeRank':551,'money':[3,7,4,3,0]} }
    for idx in contect:
        sum = idx.count('\t')
        str1 = idx.split('\t')
        if sum == 3:
            savedata['gameRecord'][str1[0]]=[1000000,100,1,1000000,100,1,1000000,100,1,0,0,0]
        else:
            savedata['gameRecord'][str1[0]]=[1000000,100,1,1000000,100,1,1000000,100,1,1000000,100,1]
    gameRecords = savedata['gameRecord']
    data = savedata['gameProgress']['money']
        
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
progress = [[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]]
levelToNumMap = {'EZ':0, 'HD':1, 'IN':2, 'AT':3, 0:'EZ', 1:'HD', 2:'IN', 3:'AT'}
for i in songid: 
    rksContribution[i] = [0.0, 0.0, 0.0, 0.0]
    if not i in gameRecords: continue
    for now in range(4):
        # if(diff[i][now]>=16.4):
        #     gameRecords[i]=[1000000,100,1,1000000,100,1,1000000,100,1,1000000,100,1]
        #     rksContribution[i][now] = diff[i][now]
        #     progress[0][now]+=1
        #     progress[1][now]+=1
        #     progress[2][now]+=1
        #     score.append((rksContribution[i][now],i,levelToNumMap[now],diff[i][now],True))
        #     phi.append((rksContribution[i][now],i,levelToNumMap[now],diff[i][now],True))
        # continue
        rksContribution[i][now] = pow((gameRecords[i][now*3+1]-55.0)/45,2)*diff[i][now] if gameRecords[i][now*3+1] >= 70 else 0
        progress[0][now]+=(gameRecords[i][now*3+1] >= 70)
        progress[1][now]+=bool(gameRecords[i][now*3+2])
        progress[2][now]+=bool(rksContribution[i][now] == diff[i][now] and diff[i][now])
        if rksContribution[i][now] : score.append((
            rksContribution[i][now],            #  0                
            i,                                  #  1
            levelToNumMap[now],                 #  2          
            diff[i][now],                       #  3    
            bool(gameRecords[i][now*3+2]),      #  4                     
            songname[i],                        #  5   
            gameRecords[i][now*3],#score        #  6                   
            diff[i][now], #difficulty           #  7                
            gameRecords[i][now*3+1] #acc        #  8                   
            ))
        if(rksContribution[i][now] >= diff[i][now] and diff[i][now]) : phi.append((
            rksContribution[i][now],            #  0                
            i,                                  #  1
            levelToNumMap[now],                 #  2          
            diff[i][now],                       #  3    
            bool(gameRecords[i][now*3+2]),      #  4                     
            songname[i],                        #  5   
            gameRecords[i][now*3],#score        #  6                   
            diff[i][now], #difficulty           #  7                
            gameRecords[i][now*3+1] #acc        #  8    
            ))
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

original_stdout = sys.stdout
sys.stdout = open('result.txt', 'w', encoding='utf-8')
if(not settings['yywMode']): print(updatetime)
else: print('已开启演示模式，所有成绩均为演示作用')
# print('Save version: ', summary['saveVersion'])
def challengeModeRankToChinese(cmr : int) -> str:
    res : str = ''
    if(cmr//100==0): res+='灰'
    elif(cmr//100==1): res+='绿'
    elif(cmr//100==2): res+='蓝'
    elif(cmr//100==3): res+='红'
    elif(cmr//100==4): res+='金'
    else: res+='彩'
    res += str(cmr%100)
    return res
cmrcn = challengeModeRankToChinese(summary['challengeModeRank'])
print('昵称: ', nickname)
print('课题模式:', cmrcn)
print('RKS: ', summary['rankingScore'])
# print('GameVersion: ', summary['gameVersion'])
# print('头像: ', user['avatar'])
print('Data: ', end='')

data_num = ''
if data[4]:   data_num=f'{data[4]}PiB {data[3]}TiB {data[2]}GiB {data[1]}MiB {data[0]}KiB'
elif data[3]: data_num=f'{data[3]}TiB {data[2]}GiB {data[1]}MiB {data[0]}KiB'
elif data[2]: data_num=f'{data[2]}GiB {data[1]}MiB {data[0]}KiB'
elif data[1]: data_num=f'{data[1]}MiB {data[0]}KiB'
else: f'{data[0]}KiB'
print(data_num, end='\n\n')
print('\\    EZ   HD   IN   AT')
print(f'C   {progress[0][0]: 3d} {progress[0][1]: 3d} {progress[0][2]: 3d} {progress[0][3]: 3d} ')
print(f'FC  {progress[1][0]: 3d} {progress[1][1]: 3d} {progress[1][2]: 3d} {progress[1][3]: 3d} ')
print(f'AT  {progress[2][0]: 3d} {progress[2][1]: 3d} {progress[2][2]: 3d} {progress[2][3]: 3d} ')
print()
for i in range(min(3,len(phi))):
    print(f'P{i+1} {phi[i][5]},  ACC: {round(phi[i][8],2)}%, RKS: {round(phi[i][0],3)}/{phi[i][7]}, Score:{phi[i][6]}')
print()
for i in range(min(33,len(score))):
    print(f'B{i+1} {score[i][5]},  ACC: {round(score[i][8],2)}%, RKS: {round(score[i][0],3)}/{score[i][7]}, Score:{score[i][6]}')
    if(i == 27):
        print('————OVERFLOW————')
sys.stdout = original_stdout
# print(rks)
# print(diff)
# phigros.load_difficulty(b"../difficulty.tsv")# 读取difficulty.tsv,参数为文件路径
# b19 = phigros.get_b19(handle).decode('utf-8')
# print(b19)             # 从存档读取B19,依赖load_difficulty
if(not settings['yywMode']): phigros.free_handle(handle)                 # 释放handle的内存,不会被垃圾回收,使用完handle请确保释放
b27 = [] # (songid,rank,songname,rks,difficulty,acc,score,type,nxt,fc)


for i in range(3):
    if(i>=len(phi)):
        phi.append(('No Data',f'B{i+1}','No Data',0,0,0,0,0,'',0))
        continue
    id = phi[i][1]
    accuary = gameRecords[phi[i][1]][classToNum(phi[i][2])*3+1]
    scr = gameRecords[phi[i][1]][classToNum(phi[i][2])*3]
    b27.append((id,f'P{i+1}',songname[id],phi[i][0],phi[i][3],accuary,scr,phi[i][2],'推分建议已经被砍了',phi[i][4]))
for i in range(33):
    if(i>=len(score)):
        b27.append(('No Data',f'B{i+1}','No Data',0,0,0,0,0,'',0))
        continue
    id = score[i][1]
    accuary = gameRecords[score[i][1]][classToNum(score[i][2])*3+1]
    scr = gameRecords[score[i][1]][classToNum(score[i][2])*3]
    # cnt1 = int(rks*100)/100.0  +0.01
    # nxt = (cnt1-rks)*30
    # # nxt = ((cnt1+0.008 if rks-cnt1<0.005 else cnt1+0.018)-rks)*30
    # target_rks = nxt + score[i][0]
    # target_acc = pow(target_rks / score[i][3], 1/2) * 45 + 55
    # print(score[i][0])
    # print((cnt1+0.005 if rks-cnt1<0.005 else cnt1+0.015),f'{target_rks:f}',target_rks,target_acc,pow((target_acc-55)/45,2)*score[0][3])
    b27.append((id,f'B{i+1}',songname[id],score[i][0],score[i][3],accuary,scr,score[i][2],'推分建议已经被砍了' '''f'{round(target_acc,2)}%' if target_acc<=100 else '无法推分' ''',score[i][4]))

# score[i][2] ->EZ/HD/IN/AT
if settings['outputLog']:
    filename = f'{str(updatetime).replace(" ", "_").replace(":", "_").replace(".", "_")}'
    if settings['yywMode']: 
        filename = filename + "_yywmode"
    if(os.path.exists('log')): 
        if(not os.path.isfile('/log')): pass
        else: os.system('mkdir log')
    else: os.system('mkdir log')
    
    if(sys.platform.startswith('linux')): os.system(f'cp ./result.txt ./log/{filename}.txt >/dev/null')
    elif(sys.platform.startswith('win32')): 
        os.system(f'copy .\\result.txt .\\log\\{filename}.txt > NUL')
    
createImage(
    
    a_path=f"illustrationLowRes/{choice(os.listdir('illustrationLowRes'))}",  # 替换为你的图片路径
    output_path="result.png",
    target_size=(1875, 3000),
    blur_radius=55,  # 可根据需要调整虚化程度
    avatar=user['avatar'],
    b27=b27,
    username=nickname,
    rks=round(rks,4),
    challengeModeRank=summary['challengeModeRank'],
    data=data_num,
    updatetime=str(updatetime),
    progress=progress
)
printwithcolor('成绩图片已输出至result.png, 文字文件已输出至result.txt',[36])

if(not settings['yywMode']): print(updatetime)
else: print('已开启演示模式，所有成绩均为演示作用')
if(cmrcn[0]=='灰'):printwithcolor(cmrcn,[30,1],' ')
elif(cmrcn[0]=='绿'):printwithcolor(cmrcn,[32,1],' ')
elif(cmrcn[0]=='蓝'):printwithcolor(cmrcn,[36,1],' ')
elif(cmrcn[0]=='红'):printwithcolor(cmrcn,[31,1],' ')
elif(cmrcn[0]=='金'):printwithcolor(cmrcn,[33,1],' ')
else:printwithcolor(cmrcn,[35,1],' ')
printwithcolor('%.6f'%(round(summary['rankingScore'],6)),[7,1],' ')
# print('GameVersion: ', summary['gameVersion'])
printwithcolor(data_num, [1,3])
print('\\   ',end='')
printwithcolor('EZ',[1,32],'   ')
printwithcolor('HD',[1,36],'   ')
printwithcolor('IN',[1,31],'   ')
printwithcolor('AT',[1,37])
printwithcolor('C',37,'')
print(f'   {progress[0][0]: 3d} {progress[0][1]: 3d} {progress[0][2]: 3d} {progress[0][3]: 3d} ')
printwithcolor('FC',34,'')
print(f'  {progress[1][0]: 3d} {progress[1][1]: 3d} {progress[1][2]: 3d} {progress[1][3]: 3d} ')
printwithcolor('AP',33,'')
print(f'  {progress[2][0]: 3d} {progress[2][1]: 3d} {progress[2][2]: 3d} {progress[2][3]: 3d} ')
print()
for i in range(min(3,len(phi))):
    printwithcolor(f'P{i+1}',[43,1],' ')
    printwithcolor(songname[phi[i][1]],0,' ')
    printwithcolor(f'{round(gameRecords[phi[i][1]][classToNum(phi[i][2])*3+1],2)}%',[1],' ')
    printwithcolor(f'{round(phi[i][0],3)}/{diff[phi[i][1]][classToNum(phi[i][2])]}',[44],' ')
    printwithcolor(f'{gameRecords[phi[i][1]][classToNum(phi[i][2])*3]}',[1,33])
print()
for i in range(min(33,len(score))):
    printwithcolor(f'B{i+1}',[43,1],' ')
    printwithcolor(songname[score[i][1]],0,' ')
    printwithcolor(f'{round(gameRecords[score[i][1]][classToNum(score[i][2])*3+1],2)}%',[1],' ')
    printwithcolor(f'{round(score[i][0],3)}',[44],'')
    printwithcolor(f'/{diff[score[i][1]][classToNum(score[i][2])]}',[0],' ')
    printwithcolor(f'{gameRecords[score[i][1]][classToNum(score[i][2])*3]}',[1,36])
    # print(f'B{i+1} {songname[score[i][1]]},  ACC: {round(gameRecords[score[i][1]][classToNum(score[i][2])*3+1],2)}%, RKS: {round(score[i][0],3)}/{diff[score[i][1]][classToNum(score[i][2])]}, Score:{gameRecords[score[i][1]][classToNum(score[i][2])*3]}')
    if(i == 27):
        printwithcolor('————OVERFLOW————',[0])
if settings['EnterToContiune']:
    try: input('按下Enter以继续')
    except: pass
sys.exit(0)