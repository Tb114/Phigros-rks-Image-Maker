import sys
import os
import subprocess
import re
import configparser
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, QTabWidget, 
                             QGroupBox, QScrollArea, QMessageBox, QFileDialog, QAction,
                             QFrame, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QTextCursor, QColor, QTextCharFormat, QPalette, QIcon
from datetime import datetime

# ANSI颜色代码到QTextCharFormat的映射
ANSI_COLOR_MAP = {
    '0': {'foreground': QColor(Qt.white), 'background': QColor(Qt.black)},  # 重置
    '30': {'foreground': QColor(Qt.black)},     # 黑色
    '31': {'foreground': QColor(Qt.red)},       # 红色
    '32': {'foreground': QColor(Qt.green)},     # 绿色
    '33': {'foreground': QColor(Qt.yellow)},    # 黄色
    '34': {'foreground': QColor(50,50,200,255)},      # 蓝色
    '35': {'foreground': QColor(Qt.magenta)},   # 洋红
    '36': {'foreground': QColor(Qt.cyan)},      # 青色
    '37': {'foreground': QColor(Qt.white)},      # 白色
    '40': {'background': QColor(Qt.black)},     # 黑色背景
    '41': {'background': QColor(Qt.red)},       # 红色背景
    '42': {'background': QColor(Qt.green)},     # 绿色背景
    '43': {'background': QColor(Qt.yellow)},    # 黄色背景
    '44': {'background': QColor(50,50,200,255)},     # 蓝色背景
    '45': {'background': QColor(Qt.magenta)},  # 洋红背景
    '46': {'background': QColor(Qt.cyan)},     # 青色背景
    '47': {'background': QColor(Qt.white)},     # 白色背景
    '1': {'bold': True},                       # 粗体
    '4': {'underline': True},                  # 下划线
    '7': {'invert': True}                      # 反显
}

# 暗色模式样式表
DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #2d2d30;
    color: #e0e0e0;
}
QGroupBox {
    border: 1px solid #3e3e42;
    border-radius: 5px;
    margin-top: 1ex;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px 0 3px;
    color: #b0b0b0;
}
QPushButton {
    background-color: #3e3e42;
    color: #e0e0e0;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 5px;
}
QPushButton:hover {
    background-color: #555;
}
QPushButton:pressed {
    background-color: #2a2a2a;
}
QPushButton:disabled {
    background-color: #2d2d30;
    color: #888;
}
QLineEdit {
    background-color: #252526;
    color: #e0e0e0;
    border: 1px solid #3e3e42;
    padding: 5px;
}
QTextEdit, QPlainTextEdit {
    background-color: #1e1e1e;
    color: #d0d0d0;
    border: 1px solid #3e3e42;
}
QTabWidget::pane {
    border: 1px solid #3e3e42;
    background: #2d2d30;
}
QTabBar::tab {
    background: #3e3e42;
    color: #b0b0b0;
    padding: 5px 10px;
}
QTabBar::tab:selected {
    background: #2d2d30;
    color: #e0e0e0;
}
QStatusBar {
    background-color: #252526;
    color: #e0e0e0;
}
QMenuBar {
    background-color: #252526;
    color: #e0e0e0;
}
QMenu {
    background-color: #3e3e42;
    color: #e0e0e0;
    border: 1px solid #555;
}
QMenu::item:selected {
    background-color: #555;
}
QCheckBox {
    color: #e0e0e0;
}
"""

class AnsiTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setReadOnly(True)
        self.setFont(QFont("Consolas", 10))
        self.current_format = QTextCharFormat()
        self.reset_format()
    
    def reset_format(self):
        self.current_format = QTextCharFormat()
        
        # 根据应用主题设置默认颜色
        app = QApplication.instance()
        if app and app.property("dark_mode"):
            self.current_format.setForeground(QColor(Qt.white))
            self.current_format.setBackground(QColor(Qt.black))
        else:
            self.current_format.setForeground(QColor(Qt.black))
            self.current_format.setBackground(QColor(Qt.white))
            
        self.current_format.setFontWeight(QFont.Normal)
        self.current_format.setFontUnderline(False)
    
    def append_ansi_text(self, text):
        # 如果传入的是字节，则尝试解码
        if isinstance(text, bytes):
            try:
                text = text.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text = text.decode('gbk', errors='replace')
                except:
                    text = text.decode('latin-1', errors='replace')
        
        # 处理ANSI转义序列
        parts = re.split(r'(\x1b\[[\d;]*m)', text)
        
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        in_escape = False
        for part in parts:
            if not part:
                continue
                
            if part.startswith('\x1b[') and part.endswith('m'):
                # 处理ANSI转义序列
                codes = part[2:-1].split(';')
                for code in codes:
                    if not code:
                        continue
                    if code == '0':
                        self.reset_format()
                    elif code in ANSI_COLOR_MAP:
                        attr = ANSI_COLOR_MAP[code]
                        if 'foreground' in attr:
                            self.current_format.setForeground(attr['foreground'])
                        if 'background' in attr:
                            self.current_format.setBackground(attr['background'])
                        if 'bold' in attr:
                            self.current_format.setFontWeight(QFont.Bold if attr['bold'] else QFont.Normal)
                        if 'underline' in attr:
                            self.current_format.setFontUnderline(attr['underline'])
                        if 'invert' in attr:
                            # 反显处理：交换前景色和背景色
                            fg = self.current_format.foreground().color()
                            bg = self.current_format.background().color()
                            self.current_format.setForeground(bg)
                            self.current_format.setBackground(fg)
                in_escape = True
            else:
                # 插入文本
                if in_escape:
                    in_escape = False
                
                cursor.setCharFormat(self.current_format)
                cursor.insertText(part)
        
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

class UpdateThread(QThread):
    finished = pyqtSignal(str)
    progress = pyqtSignal(str)
    log_output = pyqtSignal(str)  # 修改为发送字符串

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            self.progress.emit("正在更新曲绘、头像和歌曲信息...\n")
            self.log_output.emit("启动更新进程...\n")
            
            # 运行updatefile.py并捕获输出
            process = subprocess.Popen(
                [sys.executable, 'updatefile.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1
            )
            
            # 实时读取输出并发送信号
            while True:
                output = process.stdout.readline()
                if output == b'' and process.poll() is not None:
                    break
                if output:
                    # 尝试解码为UTF-8
                    try:
                        decoded_output = output.decode('utf-8')
                    except UnicodeDecodeError:
                        # 如果UTF-8解码失败，尝试GBK（中文常见编码）
                        try:
                            decoded_output = output.decode('gbk', errors='replace')
                        except:
                            # 最后尝试latin-1
                            decoded_output = output.decode('latin-1', errors='replace')
                    self.log_output.emit(decoded_output)
            
            process.wait()
            
            if process.returncode == 0:
                self.finished.emit("文件更新完成！")
            else:
                self.finished.emit(f"文件更新失败，返回码: {process.returncode}")
        except Exception as e:
            self.finished.emit(f"更新过程中出错: {str(e)}")

class GenerateThread(QThread):
    finished = pyqtSignal(str, str, str)
    progress = pyqtSignal(str)
    log_output = pyqtSignal(str)  # 修改为发送字符串

    def __init__(self, session_token):
        super().__init__()
        self.session_token = session_token

    def run(self):
        try:
            # 保存SessionToken到.env文件
            with open('.env', 'w') as f:
                f.write(f'SESSIONTOKEN=\'{self.session_token}\'')
            
            self.progress.emit("正在生成成绩图片...\n")
            self.log_output.emit("启动生成进程...\n")
            
            # 运行main.py并捕获输出
            process = subprocess.Popen(
                [sys.executable, 'main.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1
            )
            
            # 实时读取输出并发送信号
            while True:
                output = process.stdout.readline()
                if output == b'' and process.poll() is not None:
                    break
                if output:
                    # 尝试解码为UTF-8
                    try:
                        decoded_output = output.decode('utf-8')
                    except UnicodeDecodeError:
                        # 如果UTF-8解码失败，尝试GBK（中文常见编码）
                        try:
                            decoded_output = output.decode('gbk', errors='replace')
                        except:
                            # 最后尝试latin-1
                            decoded_output = output.decode('latin-1', errors='replace')
                    self.log_output.emit(decoded_output)
            
            process.wait()
            
            # 检查结果文件
            if os.path.exists('result.png') and os.path.exists('result.txt'):
                self.finished.emit("success", "result.png", "result.txt")
            else:
                self.finished.emit("error", "", "生成失败：未找到结果文件\n")
        except Exception as e:
            self.finished.emit("error", "", f"生成过程中出错: {str(e)}\n")

class PhigrosRKSMaker(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            self.setWindowIcon(QIcon('Resource/icon.ico'))
        except:
            pass
        self.setWindowTitle("Phigros RKS Image Maker GUI ver")
        self.setGeometry(100, 100, 900, 700)
        
        # 初始化暗色模式状态
        self.dark_mode = False
        
        # 创建菜单栏
        self.create_menu()
        
        self.init_ui()
        self.load_settings()
        self.apply_theme()

    def create_menu(self):
        # 创建菜单栏
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        # 主题切换菜单
        theme_menu = menubar.addMenu('主题')
        
        # 亮色模式动作
        light_action = QAction('亮色模式', self)
        light_action.triggered.connect(lambda: self.toggle_theme(False))
        theme_menu.addAction(light_action)
        
        # 暗色模式动作
        dark_action = QAction('暗色模式', self)
        dark_action.triggered.connect(lambda: self.toggle_theme(True))
        theme_menu.addAction(dark_action)
        
        # 退出动作
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.exit_app)  # 修改为连接exit_app方法
        file_menu.addAction(exit_action)

    def toggle_theme(self, dark_mode):
        """切换亮色/暗色模式"""
        self.dark_mode = dark_mode
        self.apply_theme()
        self.save_settings()
        
        # 更新UI中的切换按钮状态
        if hasattr(self, 'theme_switch'):
            self.theme_switch.setChecked(dark_mode)

    def apply_theme(self):
        """应用当前主题设置"""
        app = QApplication.instance()
        
        # 设置全局属性
        app.setProperty("dark_mode", self.dark_mode)
        
        if self.dark_mode:
            # 应用暗色模式样式表
            self.setStyleSheet(DARK_STYLESHEET)
            
            # 更新日志背景色
            palette = self.log_output.palette()
            palette.setColor(QPalette.Base, QColor("#1e1e1e"))
            palette.setColor(QPalette.Text, QColor("#d0d0d0"))
            self.log_output.setPalette(palette)
            
            # 更新结果文本区域
            palette = self.text_output.palette()
            palette.setColor(QPalette.Base, QColor("#1e1e1e"))
            palette.setColor(QPalette.Text, QColor("#d0d0d0"))
            self.text_output.setPalette(palette)
            
            # 更新图片预览区域
            self.image_label.setStyleSheet("border: 1px solid #555; background-color: #252526; min-height: 400px;")
            
        else:
            # 恢复亮色模式
            self.setStyleSheet("")
            
            # 重置日志背景色
            palette = self.log_output.palette()
            palette.setColor(QPalette.Base, QColor("#ffffff"))
            palette.setColor(QPalette.Text, QColor("#000000"))
            self.log_output.setPalette(palette)
            
            # 重置结果文本区域
            palette = self.text_output.palette()
            palette.setColor(QPalette.Base, QColor("#ffffff"))
            palette.setColor(QPalette.Text, QColor("#000000"))
            self.text_output.setPalette(palette)
            
            # 重置图片预览区域
            self.image_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0; min-height: 400px;")
        
        # 重置ANSI格式
        self.log_output.reset_format()

    def init_ui(self):
        # 创建主部件和布局
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # 创建标签页
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # 创建"生成"标签页
        self.create_generate_tab()
        # 创建"结果"标签页
        self.create_result_tab()
        # 创建"设置"标签页
        self.create_settings_tab()

        # 状态栏
        self.status_label = QLabel("就绪")
        self.statusBar().addWidget(self.status_label)

    def create_generate_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Session Token 输入组
        token_group = QGroupBox("Session Token")
        token_layout = QVBoxLayout()
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("在此输入您的SessionToken")
        token_layout.addWidget(self.token_input)
        
        # 从.env加载按钮
        load_btn = QPushButton("从.env文件加载")
        load_btn.clicked.connect(self.load_token_from_env)
        token_layout.addWidget(load_btn)
        
        token_group.setLayout(token_layout)
        layout.addWidget(token_group)

        # 更新按钮
        update_btn = QPushButton("更新曲绘和歌曲信息")
        update_btn.clicked.connect(self.update_files)
        layout.addWidget(update_btn)

        # 生成按钮
        generate_btn = QPushButton("生成成绩图片")
        generate_btn.setStyleSheet("background-color: #4CAF50; color: white; font-size: 16px; padding: 10px;")
        generate_btn.clicked.connect(self.generate)
        layout.addWidget(generate_btn)

        # 日志输出
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout()
        self.log_output = AnsiTextEdit()  # 使用自定义的ANSI文本编辑框
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        self.tabs.addTab(tab, "生成")

    def create_result_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # 图片预览
        image_group = QGroupBox("成绩图片预览")
        image_layout = QVBoxLayout()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText("图片将在此处显示")
        self.image_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0; min-height: 400px;")
        image_layout.addWidget(self.image_label)
        
        # 保存图片按钮
        save_image_btn = QPushButton("保存图片")
        save_image_btn.clicked.connect(self.save_image)
        image_layout.addWidget(save_image_btn)
        
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)

        # 文本结果
        text_group = QGroupBox("成绩详情")
        text_layout = QVBoxLayout()
        self.text_output = QTextEdit()
        # self.text_output.setReadOnly(True)
        self.text_output.setFont(QFont("Consolas", 10))
        text_layout.addWidget(self.text_output)
        
        # 保存文本按钮
        save_text_btn = QPushButton("保存文本")
        save_text_btn.clicked.connect(self.save_text)
        text_layout.addWidget(save_text_btn)
        
        text_group.setLayout(text_layout)
        layout.addWidget(text_group)

        self.tabs.addTab(tab, "结果")

    def create_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # 主题切换区域
        theme_group = QGroupBox("主题设置")
        theme_layout = QVBoxLayout()
        
        # 主题切换开关
        self.theme_switch = QCheckBox("启用暗色模式")
        self.theme_switch.setChecked(self.dark_mode)
        self.theme_switch.stateChanged.connect(lambda: self.toggle_theme(self.theme_switch.isChecked()))
        theme_layout.addWidget(self.theme_switch)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        theme_layout.addWidget(separator)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)

        # 说明部分
        help_group = QGroupBox("使用说明")
        help_layout = QVBoxLayout()
        
        help_text = """
        <h3>Phigros RKS Image Maker 使用指南</h3>
        
        <p><b>1. 获取SessionToken</b></p>
        <p>从Phigros游戏存档中提取您的SessionToke。</p>
        
        <p><b>2. 输入SessionToken</b></p>
        <p>在"生成"标签页的输入框中粘贴您的SessionToken，或点击"从.env文件加载"按钮。</p>
        
        <p><b>3. 更新资源文件（可选）</b></p>
        <p>点击"更新曲绘和歌曲信息"按钮下载最新资源文件。</p>
        
        <p><b>4. 生成成绩图片</b></p>
        <p>点击"生成成绩图片"按钮开始处理，生成过程可能需要1-2分钟。</p>
        
        <p><b>5. 查看结果</b></p>
        <p>在"结果"标签页查看生成的成绩图片和详细数据。</p>
        
        <p><b>6. 保存结果</b></p>
        <p>您可以将图片和文本结果保存到本地。</p>
        
        <p><b>注意：</b></p>
        <p>• 首次使用时需要更新文件</p>
        <p>• 确保网络连接正常以便下载所需文件</p>
        """
        
        help_label = QLabel(help_text)
        help_label.setWordWrap(True)
        help_layout.addWidget(help_label)
        help_group.setLayout(help_layout)
        layout.addWidget(help_group)

        # 关于部分
        about_group = QGroupBox("关于")
        about_layout = QVBoxLayout()
        VERSION = 'Unknown'
        with open("VERSION", "r") as f:
            VERSION = f.read()
        about_text = f"""
        <p><b>Phigros RKS Image Maker ver {VERSION} </b></p>
        <p>Phigros RKS Image Maker的GUI版本</p>
        <p>感谢D老师的代码编写</p>
        <p>开源地址: <a href="https://github.com/Tb114/Phigros-rks-Image-Maker">GitHub项目地址</a></p>
        """
        
        about_label = QLabel(about_text)
        about_label.setWordWrap(True)
        about_label.setOpenExternalLinks(True)
        about_layout.addWidget(about_label)
        about_group.setLayout(about_layout)
        layout.addWidget(about_group)

        self.tabs.addTab(tab, "帮助")

    def load_settings(self):
        """加载设置，处理无[settings]部分的设置文件"""
        self.dark_mode = False  # 默认值
        
        # 检查设置文件是否存在
        if os.path.exists('config.ini'):
            try:
                # 直接读取设置文件内容
                with open('config.ini', 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('dark_mode='):
                            # 解析dark_mode值
                            value = line.split('=', 1)[1].strip()
                            self.dark_mode = value.lower() in ['true', '1', 'yes', 'on']
                            break
            except Exception as e:
                print(f"加载设置文件时出错: {str(e)}")
                self.dark_mode = False
        else:
            # 如果设置文件不存在，创建默认设置
            self.save_settings()
            
        # 尝试从.env加载SessionToken
        if os.path.exists('.env'):
            try:
                with open('.env', 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if 'SESSIONTOKEN' in content:
                        token = content.split('=')[1].strip()
                        if token[0]=='\'': token=token[1:]
                        if token[-1]=='\'': token=token[:-1]
                        self.token_input.setText(token)
                        # 确保日志框是只读的但允许程序写入
                        self.log_output.append_ansi_text("已从.env文件加载SessionToken")
            except Exception as e:
                self.log_output.append_ansi_text(f"加载.env文件出错: {str(e)}")
    
    def create_default_settings(self):
        """创建默认设置文件"""
        try:
            self.config = configparser.ConfigParser()
            self.config.add_section('Settings')
            self.config.set('Settings', 'dark_mode', 'False')
            self.save_settings()
        except Exception as e:
            print(f"创建默认设置文件时出错: {str(e)}")

    def save_settings(self):
        """保存设置到配置文件，使用简单的键值对格式"""
        try:
            # 读取现有设置文件（如果有）
            settings_lines = []
            if os.path.exists('config.ini'):
                with open('config.ini', 'r', encoding='utf-8') as f:
                    settings_lines = f.readlines()
            
            # 更新或添加dark_mode设置
            dark_mode_found = False
            new_settings = []
            
            for line in settings_lines:
                stripped = line.strip()
                # 跳过空行和注释
                if not stripped or stripped.startswith('#'):
                    new_settings.append(line)
                    continue
                    
                if stripped.startswith('dark_mode='):
                    # 更新现有的dark_mode行
                    new_settings.append(f"dark_mode={str(self.dark_mode)}\n")
                    dark_mode_found = True
                else:
                    # 保留其他设置
                    new_settings.append(line)
            
            # 如果没有找到dark_mode设置，添加新行
            if not dark_mode_found:
                new_settings.append(f"dark_mode={str(self.dark_mode)}\n")
            
            # 写入更新后的设置文件
            with open('config.ini', 'w', encoding='utf-8') as f:
                f.writelines(new_settings)
                
        except Exception as e:
            print(f"保存设置时出错: {str(e)}")

    def load_token_from_env(self):
        if os.path.exists('.env'):
            try:
                with open('.env', 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if 'SESSIONTOKEN' in content:
                        token = content.split('=')[1].strip()
                        if token[0]=='\'': token=token[1:]
                        if token[-1]=='\'': token=token[:-1]
                        self.token_input.setText(token)
                        self.log_output.append_ansi_text("已从.env文件加载SessionToken")
                        return
            except Exception as e:
                self.log_output.append_ansi_text(f"加载.env文件出错: {str(e)}")
        self.log_output.append_ansi_text("未找到.env文件或其中不包含有效的SessionToken")

    def update_files(self):
        """更新资源文件"""
        self.log_output.clear()
        self.log_output.append_ansi_text("开始更新资源文件...")
        
        # 禁用UI元素
        self.tabs.setEnabled(False)
        self.status_label.setText("正在更新...")
        
        # 创建并启动更新线程
        self.update_worker = UpdateThread()
        self.update_worker.progress.connect(self.status_label.setText)
        self.update_worker.log_output.connect(self.log_output.append_ansi_text)
        self.update_worker.finished.connect(self.on_update_finished)
        self.update_worker.start()

    def on_update_finished(self, message):
        self.log_output.append_ansi_text(message)
        self.status_label.setText(message)
        self.tabs.setEnabled(True)

    def generate(self):
        """生成成绩图片"""
        token = self.token_input.text().strip()
        if not token:
            QMessageBox.warning(self, "输入错误", "请输入SessionToken！")
            return
        
        self.log_output.clear()
        self.log_output.append_ansi_text("开始生成Phigros成绩图片...")
        self.log_output.append_ansi_text(f"使用的SessionToken: {token[:6]}...{token[-6:]}")
        
        # 禁用UI元素
        self.tabs.setEnabled(False)
        self.status_label.setText("正在生成...")
        
        # 创建并启动工作线程
        self.generate_worker = GenerateThread(token)
        self.generate_worker.progress.connect(self.status_label.setText)
        self.generate_worker.log_output.connect(self.log_output.append_ansi_text)
        self.generate_worker.finished.connect(self.on_generation_finished)
        self.generate_worker.start()

    def on_generation_finished(self, status, image_path, message):
        self.log_output.append_ansi_text(message)
        self.status_label.setText(message)
        self.tabs.setEnabled(True)
        
        if status == "success":
            # 显示图片
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # 计算适当的缩放比例以保持宽高比
                label_width = self.image_label.width()
                label_height = self.image_label.height()
                scaled_pixmap = pixmap.scaled(
                    label_width, label_height, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                self.log_output.append_ansi_text("图片生成成功！")
            else:
                self.image_label.setText("无法加载图片")
                self.log_output.append_ansi_text("错误：生成的图片无法加载")
            
            # 显示文本结果
            try:
                with open('result.txt', 'r', encoding='utf-8') as f:
                    self.text_output.setText(f.read())
                    self.log_output.append_ansi_text("文本结果加载成功！")
            except Exception as e:
                self.text_output.setText("无法加载文本结果")
                self.log_output.append_ansi_text(f"错误：无法加载文本结果文件: {str(e)}")
            
            # 切换到结果标签页
            self.tabs.setCurrentIndex(1)
        else:
            QMessageBox.critical(self, "生成失败", message)

    def save_image(self):
        if not self.image_label.pixmap() or self.image_label.pixmap().isNull():
            QMessageBox.warning(self, "保存失败", "没有可用的图片")
            return
        
        # 设置默认文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_file = f"phigros_rks_result_{timestamp}.png"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存图片", default_file, "图片文件 (*.png)"
        )
        
        if file_path:
            # 确保文件名以.png结尾
            if not file_path.lower().endswith('.png'):
                file_path += '.png'
                
            success = self.image_label.pixmap().save(file_path)
            if success:
                self.log_output.append_ansi_text(f"图片已保存至: {file_path}")
            else:
                self.log_output.append_ansi_text(f"保存图片失败: 无法写入文件")

    def save_text(self):
        text = self.text_output.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "保存失败", "没有可用的文本内容")
            return
        
        # 设置默认文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_file = f"phigros_rks_result_{timestamp}.txt"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存文本", default_file, "文本文件 (*.txt)"
        )
        
        if file_path:
            # 确保文件名以.txt结尾
            if not file_path.lower().endswith('.txt'):
                file_path += '.txt'
                
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                self.log_output.append_ansi_text(f"文本已保存至: {file_path}")
            except Exception as e:
                self.log_output.append_ansi_text(f"保存文本失败: {str(e)}")
    
    def exit_app(self):
        """菜单退出动作的处理函数"""
        self.save_settings()
        # 直接退出，不显示确认对话框
        QApplication.quit()
                  
    def closeEvent(self, event):
        """窗口关闭时保存设置"""
        self.save_settings()
        # 询问用户是否确认退出
        reply = QMessageBox.question(
            self, '确认退出', 
            '确定要退出Phigros RKS Image Maker GUI ver吗?',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    # 确保使用UTF-8编码
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"
    
    app = QApplication(sys.argv)
    window = PhigrosRKSMaker()
    window.show()
    sys.exit(app.exec_())