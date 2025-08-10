import os
import requests
from urllib.parse import urljoin
# 配置参数
GITHUB_PROXY = "https://git.yylx.win/" #"https://github.akams.cn/"
LOCAL_FOLDER = "illustrationLowRes"
LOCAL_FOLDER1 = 'avatar'
RAW_CONTENT_URL =  "https://raw.githubusercontent.com/7aGiven/Phigros_Resource/illustrationLowRes"
RAW_CONTENT_URL1 = "https://raw.githubusercontent.com/7aGiven/Phigros_Resource/info"
RAW_CONTENT_URL2 = "https://raw.githubusercontent.com/7aGiven/Phigros_Resource/avatar"
RAW_CONTENT_URL_BAK = GITHUB_PROXY+"https://github.com/7aGiven/Phigros_Resource/blob/illustrationLowRes"
RAW_CONTENT_URL1_BAK = GITHUB_PROXY+"https://github.com/7aGiven/Phigros_Resource/blob/info"
RAW_CONTENT_URL2_BAK = GITHUB_PROXY+"https://github.com/7aGiven/Phigros_Resource/blob/avatar"
API_URL =  "https://api.github.com/repos/7aGiven/Phigros_Resource/contents?ref=illustrationLowRes"
API_URL1 = "https://api.github.com/repos/7aGiven/Phigros_Resource/contents?ref=avatar"
API_URL2 = "https://api.github.com/repos/7aGiven/Phigros_Resource/contents?ref=info"
API_URL_BAK =  GITHUB_PROXY+"https://api.github.com/repos/7aGiven/Phigros_Resource/contents?ref=illustrationLowRes"
API_URL1_BAK = GITHUB_PROXY+"https://api.github.com/repos/7aGiven/Phigros_Resource/contents?ref=avatar"
API_URL2_BAK = GITHUB_PROXY+"https://api.github.com/repos/7aGiven/Phigros_Resource/contents?ref=info"

def get_github_files(api_url):
    """使用GitHub API获取文件列表"""
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code in [200,301,302]:
            return [item['name'] for item in response.json() if item['type'] == 'file']
        # print(f"GitHub API请求失败: HTTP {response.status_code}")
        # raise Exception(f'网络错误: {e}')
    except Exception as e:
        # print(f"网络错误: {e}")
        raise Exception(f'网络错误: {e}')

def get_local_files(file_folder):
    """获取本地文件夹中的文件列表"""
    if not os.path.exists(file_folder):
        os.makedirs(file_folder)
        return []
    
    return [f for f in os.listdir(file_folder) if os.path.isfile(os.path.join(file_folder, f))]

def download_file(file_name, raw_url, file_folder, unexpected_url, flag = True):
    """从GitHub下载文件"""
    file_url = urljoin(raw_url, file_name)
    # unexpected_url = urljoin(unexpected_url, file_name) ## 垃圾东西，不科学，把我//硬变成了/
    if(flag): unexpected_url = f'{unexpected_url}/{file_name}'
    try:
        response = requests.get(file_url, timeout=10)
        if response.status_code in [200,301,302]:
            file_path = os.path.join(file_folder, file_name)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"已下载: {file_name}")
        else: raise Exception(f"下载失败: {file_name} (HTTP {response.status_code})")
    except Exception as e:
        # print(f"下载 {file_name} 时出错: {e}\n尝试使用代理网站")
        try:
            response = requests.get(unexpected_url, timeout=10)
            if response.status_code in [200,301,302]:
                file_path = os.path.join(file_folder, file_name)
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                print(f"已下载: {file_name}")
            else:
                # print('=-------=')
                print(unexpected_url)
                print(f"下载失败: {file_name} (HTTP {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"下载 {file_name} 时出错: {e}")

def verify_file(file_name, raw_url, file_folder, unexpected_url):
    """验证本地文件与GitHub上的文件内容是否一致"""
    file_url = urljoin(raw_url, file_name)
    local_path = os.path.join(file_folder, file_name)
    # unexpected_url = urljoin(unexpected_url, file_name) ## 垃圾东西，不科学，把我//硬变成了/
    unexpected_url = f'{unexpected_url}/{file_name}'
    
    # 获取GitHub文件内容
    try:
        response = requests.get(file_url, timeout=10)
        # if response.status_code != 200:
        #     print(f"无法验证 {file_name}: GitHub文件访问失败")
        #     return False
        github_content = response.content
    except requests.exceptions.RequestException as e:
        # print(f"获取GitHub文件 {file_name} 时出错: {e}\n尝试使用代理网站")
        try:
            response = requests.get(unexpected_url, timeout=10)
            # if response.status_code != 200:
            #     print(f"无法验证 {file_name}: GitHub文件访问失败")
            #     return False
            github_content = response.content
        except requests.exceptions.RequestException as e:
            print(f"代理网站下载 {file_name} 时出错: {e}")
            return False
    
    # 检查本地文件是否存在
    if not os.path.exists(local_path):
        print(f"本地文件 {file_name} 不存在，将下载")
        download_file(file_name, raw_url, file_folder, unexpected_url, False)
        return True
    
    # 获取本地文件内容
    try:
        with open(local_path, 'rb') as f:
            local_content = f.read()
    except IOError as e:
        print(f"读取本地文件 {file_name} 失败: {e}")
        return False
    
    # 比较内容
    if github_content != local_content:
        print(f"文件不一致: {file_name}, 重新下载...")
        download_file(file_name, raw_url, file_folder, unexpected_url, False)
        return False
    
    return True

def sync_folder(api_url, raw_url, local_folder, unexpected_raw_url, unexpected_api_url):
    """同步单个文件夹"""
    print(f"开始同步 {local_folder} 文件夹...")
    
    # 获取文件列表
    try:
        github_files = get_github_files(api_url)
    except Exception as e:
        # print(f"同步 {local_folder} 时出错: {e}\n尝试使用代理网站")
        try:
            github_files = get_github_files(unexpected_api_url)
        except:
            print(f"同步 {local_folder} 时出错: {e}")
            return False
    local_files = get_local_files(local_folder)
    print(f"GitHub文件数: {len(github_files)}, 本地文件数: {len(local_files)}")
    
    if not github_files:
        print(f"警告: 无法获取 {local_folder} 的GitHub文件列表")
        return
    
    # 检查缺失的文件
    missing_files = set(github_files) - set(local_files)
    if missing_files:
        print(f"发现 {len(missing_files)} 个新文件需要下载:")
        for file in missing_files:
            download_file(file, raw_url, local_folder, unexpected_raw_url)
    else:
        print("没有发现需要下载的新文件")
    
    # 验证现有文件
    # common_files = set(github_files) & set(local_files)
    # if common_files:
    #     print(f"开始验证 {len(common_files)} 个现有文件内容...")
    #     for file in common_files:
    #         verify_file(file, raw_url, local_folder)

def main():
    # 同步illustrationLowRes文件夹
    sync_folder(API_URL, RAW_CONTENT_URL, LOCAL_FOLDER, RAW_CONTENT_URL_BAK, API_URL_BAK)
    
    # 同步avatar文件夹
    sync_folder(API_URL1, RAW_CONTENT_URL2, LOCAL_FOLDER1, RAW_CONTENT_URL2_BAK, API_URL1_BAK)
    
    # 验证根目录下的两个特殊文件
    print("开始验证根目录下的曲目与难度文件...")
    verify_file('difficulty.tsv', RAW_CONTENT_URL1, '.', RAW_CONTENT_URL1_BAK)
    verify_file('info.tsv', RAW_CONTENT_URL1, '.', RAW_CONTENT_URL1_BAK)
    
    print("同步完成")
    # if platform.startswith('win32'): os.system('cls')
    # else: os.system('Clear')

if __name__ == "__main__":
    main()