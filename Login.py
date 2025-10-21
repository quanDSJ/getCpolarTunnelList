import requests
import webbrowser
import json
import os
import time
import logging
from collections import defaultdict
from bs4 import BeautifulSoup
from threading import Timer

art = """
   ___                             ____                                      
  / _ \   _   _    __ _   _ __    / ___|    ___   _ __  __   __   ___   _ __ 
 | | | | | | | |  / _` | | '_ \   \___ \   / _ \ | '__| \ \ / /  / _ \ | '__|
 | |_| | | |_| | | (_| | | | | |   ___) | |  __/ | |     \ V /  |  __/ | |   
  \__\_\  \__,_|  \__,_| |_| |_|  |____/   \___| |_|      \_/    \___| |_|   
                                                    """

print(art)
art1 = """
                                        ___-------___
                                   _-~~             ~~-_
                                _-~                    /~-_
             /^\\__/^\\         /~  \\                   /    \\
           /|  O|| O|        /      \\_______________/        \\
          | |___||__|      /       /                \\          \\
          |          \\    /      /                    \\          \\
          |   (_______) /______/                        \\_________ \\
          |         / /         \\                      /            \\
           \\         \\^\\         \\                  /               \\     /
             \\         ||           \\______________/      _-_       //\\__//
               \\       ||------_-~~-_ ------------- \\ --/~   ~\\    || __/
                 ~-----||====/~     |==================|       |/~~~~~
                  (_(__/  ./     /                    \\_      \\.
                         (_(___/                         \\_____)_)-qj.25.10.4
                         """
print(art1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量：用于超时自动打开
g_selected_url = None
g_timer = None


def load_config():
    """从JSON文件加载配置（包含自动打开的隧道名称）"""
    config_path = os.path.join("config", "loginCpolar.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        required_keys = ["CPOLAR_EMAIL", "CPOLAR_PASSWORD", "LOGIN_URL", "AFTER_LOGIN_URL", "TARGET_URL", "AUTO_OPEN_TUNNEL"]
        for key in required_keys:
            if key not in config:
                raise ValueError(f"配置文件缺少必要项：{key}")
        logger.info(f"配置文件加载成功，自动打开的隧道名称：{config['AUTO_OPEN_TUNNEL']}")
        return config
    except FileNotFoundError:
        raise Exception(f"配置文件不存在，请检查路径：{config_path}")
    except json.JSONDecodeError:
        raise Exception(f"配置文件格式错误，无法解析JSON")


def login(config):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    })

    try:
        # 1. 访问登录页面
        logger.info("访问登录页面...")
        login_page_resp = session.get(config["LOGIN_URL"], allow_redirects=True, timeout=10)
        login_page_resp.raise_for_status()
        logger.info(f"登录页面状态码: {login_page_resp.status_code}")

        # 2. 解析表单
        logger.info("解析登录表单...")
        soup = BeautifulSoup(login_page_resp.text, "html.parser")
        login_form = soup.find("form", id="captcha-form")
        if not login_form:
            raise Exception("未找到登录表单，页面结构可能变化")

        # 提取表单字段
        form_data = {}
        for input_tag in login_form.find_all("input"):
            name = input_tag.get("name")
            value = input_tag.get("value", "")
            if name:
                form_data[name] = value
                logger.info(f"提取表单字段: {name} = {value if name != 'password' else '***'}")

        # 3. 填写账号密码
        form_data["login"] = config["CPOLAR_EMAIL"]
        form_data["password"] = config["CPOLAR_PASSWORD"]

        # 4. 发送登录请求
        time.sleep(1)
        logger.info("发送登录请求...")
        login_resp = session.post(
            config["LOGIN_URL"],
            data=form_data,
            headers={
                "Referer": config["LOGIN_URL"],
                "Origin": "https://dashboard.cpolar.com",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            allow_redirects=True,
            timeout=10
        )
        login_resp.raise_for_status()
        logger.info(f"登录请求状态码: {login_resp.status_code}")
        logger.info(f"登录后跳转URL: {login_resp.url}")

        # 验证登录成功
        if login_resp.url != config["AFTER_LOGIN_URL"]:
            raise Exception(f"登录未跳转至目标页，当前URL: {login_resp.url}")
        
        logger.info("验证/get-started页面内容...")
        after_login_resp = session.get(config["AFTER_LOGIN_URL"], timeout=10)
        after_login_resp.raise_for_status()

        if "captcha-form" in after_login_resp.text or "邮箱" in after_login_resp.text:
            raise Exception("登录失败，/get-started页面仍显示登录表单")
        
        logger.info("✅ 登录成功！已进入/get-started页面")
        
        # 5. 访问目标页
        logger.info(f"访问目标页: {config['TARGET_URL']}")
        target_resp = session.get(config["TARGET_URL"], timeout=10)
        target_resp.raise_for_status()
        logger.info(f"目标页状态码: {target_resp.status_code}")

        return target_resp.text

    except requests.exceptions.RequestException as e:
        logger.error(f"网络错误: {str(e)}", exc_info=True)
    except Exception as e:
        logger.error(f"执行错误: {str(e)}", exc_info=True)
    finally:
        session.close()


def parse_cpolar_tunnels(html_content):
    """解析所有隧道信息"""
    soup = BeautifulSoup(html_content, 'html.parser')
    tunnel_table = soup.find('table', class_='table table-sm')
    if not tunnel_table:
        raise ValueError("未找到隧道信息表格")

    # 提取表头
    th_tags = tunnel_table.find('thead').find_all('th')
    columns = [th.get_text(strip=True) for th in th_tags]
    logger.info(f"解析到表头：{columns}")

    # 提取数据行
    tunnel_data = []
    for tr in tunnel_table.find('tbody').find_all('tr'):
        td_tags = tr.find_all(['td', 'th'])
        row = []
        for tag in td_tags:
            a_tag = tag.find('a')
            row.append(a_tag['href'] if (a_tag and 'href' in a_tag.attrs) else tag.get_text(strip=True))
        
        if len(row) == len(columns):
            tunnel_data.append(dict(zip(columns, row)))
        else:
            logger.warning(f"跳过格式异常的行：{row}")

    return columns, tunnel_data


def filter_http_https_tunnels(tunnel_data):
    """过滤出HTTP/HTTPS隧道，相同名称保留HTTPS"""
    filtered = {}
    for tunnel in tunnel_data:
        name = tunnel["隧道名称"]
        url = tunnel["URL"]
        proto = url.split(":")[0].lower()

        if proto not in ["http", "https"]:
            continue  # 过滤非HTTP/HTTPS
        
        # 相同名称保留HTTPS
        if name not in filtered or (proto == "https" and filtered[name]["URL"].split(":")[0].lower() != "https"):
            filtered[name] = tunnel
    
    return sorted(filtered.values(), key=lambda x: x["隧道名称"])


def print_tunnel_table(columns, tunnel_data, title):
    """通用表格打印函数"""
    if not tunnel_data:
        print(f"没有{title}隧道信息")
        return
    
    # 计算列宽
    column_widths = defaultdict(int)
    for col in columns:
        column_widths[col] = len(col)
    for tunnel in tunnel_data:
        for col in columns:
            value = str(tunnel[col])
            if col == "URL" and len(value) > 50:
                value = value[:47] + "..."
            column_widths[col] = max(column_widths[col], len(value))
    
    # 打印表格
    header = " | ".join([f"{col.ljust(column_widths[col])}" for col in columns])
    print("\n" + "="*len(header))
    print(f"=== {title}（共 {len(tunnel_data)} 条） ===")
    print(header)
    print("-"*len(header))
    for idx, tunnel in enumerate(tunnel_data, 1):
        row = []
        for col in columns:
            value = str(tunnel[col])
            if col == "URL" and len(value) > 50:
                value = value[:47] + "..."
            row.append(value.ljust(column_widths[col]))
        print(f"{idx}. " + " | ".join(row))
    print("="*len(header) + "\n")


def auto_open_url():
    """超时自动打开配置文件中指定的隧道URL"""
    global g_selected_url
    if g_selected_url:
        print(f"\n⌛5秒未输入，自动打开配置中指定的隧道...")
        webbrowser.open(g_selected_url)
    else:
        print(f"\n⌛5秒未输入，但未找到配置中指定的隧道")


def user_select_tunnel(filtered_tunnels, auto_tunnel_name):
    """用户选择隧道，支持超时自动打开（使用配置文件中的隧道名称）"""
    global g_selected_url, g_timer

    # 查找配置文件中指定的隧道URL（用于超时自动打开）
    for tunnel in filtered_tunnels:
        if tunnel["隧道名称"] == auto_tunnel_name:
            g_selected_url = tunnel["URL"]
            break

    # 启动3秒定时器
    g_timer = Timer(5, auto_open_url)
    g_timer.start()

    try:
        choice = input(f"请输入要打开的隧道序号（1-{len(filtered_tunnels)}，3秒未输入自动打开[{auto_tunnel_name}]，输入q退出）: ")
        g_timer.cancel()  # 取消定时器

        if choice.lower() == "q":
            print("程序已退出")
            return
        index = int(choice) - 1
        if 0 <= index < len(filtered_tunnels):
            selected_url = filtered_tunnels[index]["URL"]
            print(f"🔍 正在打开: {selected_url}")
            webbrowser.open(selected_url)
        else:
            print("❌ 序号无效")
    except ValueError:
        print("❌ 请输入有效的数字")
    except Exception as e:
        print(f"选择出错: {e}")


if __name__ == "__main__":
    try:
        # 加载配置（包含自动打开的隧道名称）
        config = load_config()
        auto_tunnel_name = config["AUTO_OPEN_TUNNEL"]  # 从配置中获取自动打开的隧道名称
        
        # 获取隧道信息
        print("开始获取cpolar隧道信息\n")
        html_content = login(config)
        if not html_content:
            exit()
        
        # 解析并打印完整列表
        columns, all_tunnels = parse_cpolar_tunnels(html_content)
        print_tunnel_table(columns, all_tunnels, "完整隧道列表")
        
        # 过滤并打印HTTP/HTTPS列表
        filtered_tunnels = filter_http_https_tunnels(all_tunnels)
        print_tunnel_table(columns, filtered_tunnels, "过滤后的HTTP/HTTPS隧道列表")
        
        # 用户选择（支持超时自动打开配置中的隧道）
        if filtered_tunnels:
            user_select_tunnel(filtered_tunnels, auto_tunnel_name)

    except Exception as e:
        print(f"操作失败：{str(e)}")
        input("\n按回车键退出...") 