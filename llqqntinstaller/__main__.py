from argparse import ArgumentParser
from os import environ
from pathlib import Path
from platform import system
from shutil import rmtree

from loguru import logger
from lxml import etree
from pygit2 import clone_repository
from rich.prompt import Confirm,Console
from rich.table import Table

from .util import Spider

sys = system()
parser = ArgumentParser(
    prog='llqqntinstaller',
    description='LiteLoaderQQNT一键安装器')
parser.add_argument('-p', '--proxy', type=str)
parser.add_argument('--use-git-proxy', action='store_true',
                    default=False, )
args = parser.parse_args()
https_proxy: str = ''
spider = Spider(use_git_proxy=args.use_git_proxy)
if args.proxy:
    environ['https_proxy'] = args.proxy
    spider = Spider(proxy={'https': args.proxy},use_git_proxy=args.use_git_proxy)


def get_install_path() -> Path:
    global sys
    qq_default_path = {'Windows': Path(r'C:\Program Files\Tencent\QQNT\resources\app')
        , 'Linux': Path('/opt/QQ/resources/app')
        , 'Darwin': Path('/Applications/QQ.app/Contents/Resources/app')}[sys]
    res_path = {'Windows': Path('resources') / 'app'
        , 'Linux': Path('resources') / 'app'
        , 'Darwin': Path('/../../') / Path('Resources/app')}[sys]
    if qq_default_path.exists() and qq_default_path.is_dir():
        return qq_default_path
    logger.warning('QQNT未安装在默认目录，请手动输入路径')
    executable_path = input('路径为（含QQ可执行文件的目录）:')
    if not executable_path:
        raise Exception("路径不能为空")
    return Path(executable_path) / res_path


def install_via_git(folder: Path):
    repo_url = "https://github.com/LiteLoaderQQNT/LiteLoaderQQNT.git"
    if args.use_git_proxy:
        repo_url = "https://ghproxy.com/" + repo_url
    repo_path = folder / "LiteLoader"
    if repo_path.exists() and repo_path.is_dir():
        if Confirm.ask("发现LiteLoader不为空，是否删除？", default=False):
            if sys == "Windows":
                logger.warning(f"在Windows系统上，你可能需要手动删除此文件夹：{repo_path}")
                input()
            rmtree(repo_path)
        else:
            exit(0)
    repo = clone_repository(repo_url, repo_path)
    submodules = repo.listall_submodules()
    for submodule in submodules:
        url = 'https://github.com/LiteLoaderQQNT' + submodule[submodule.rfind("/"):] + '.git'
        if args.use_git_proxy:
            url = "https://ghproxy.com/" + url
        clone_repository(url, Path(repo_path) / submodule)
    del environ['https_proxy']


html = spider.get_text('https://github.com/LiteLoaderQQNT/LiteLoaderQQNT')


def get_current_version() -> str:
    global spider
    tree = etree.HTML(html)
    try:
        commit_id = tree.xpath('//code[@class="border d-lg-none mt-2 px-1 rounded-2"]//text()')[0]
    except IndexError:
        logger.warning("获取commit id失败，重试中……")
        commit_history = etree.HTML(spider.get_text('https://github.com/LiteLoaderQQNT/LiteLoaderQQNT/commits/main'))
        commit_id = commit_history.xpath(
            '//a[@class="Button--secondary Button--small Button text-mono f6"]//span[@class="Button-label"]')[0].text

    json_data = spider.get_json('https://raw.githubusercontent.com/LiteLoaderQQNT/LiteLoaderQQNT/main/package.json')

    return f'{json_data["version"]}+{commit_id}'


def print_info_table():
    tree = etree.HTML(html)
    header = tree.xpath('//thead/tr/th/text()')
    table = Table(title='支持矩阵')
    for column in header:
        table.add_column(column, style="bold")
    data_rows = tree.xpath('//tbody/tr')
    for row in data_rows:
        data = row.xpath('td/text()')
        table.add_row(*data)
    console = Console()
    console.print(table)


def get_permission() -> bool:
    if sys != "Windows":
        from os import getegid
        return getegid() == 0
    else:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0


is_admin = get_permission()
if sys != "Windows":
    if not is_admin:
        logger.warning('你当前正在使用类UNIX操作系统，你需要使用sudo权限运行脚本')
        exit(0)
else:
    if not is_admin:
        logger.warning('使用管理员权限运行脚本')
        exit(0)
try:
    logger.info(f'LiteLoaderQQNT 版本：{get_current_version()}')
    print_info_table()
except Exception:
    logger.error('无法爬取版本信息和帮助信息，请考虑使用VPN 并使用`--proxy`选项指定代理')
path: Path
try:
    path = get_install_path()
except Exception as e:
    logger.error((e))
    exit(1)
try:
    install_via_git(path)
except Exception as e:
    logger.error('在克隆仓库的过程中发生了一些错误 ' + str(e))
    exit(2)
logger.success('克隆完毕')
if Confirm.ask("修改package.json?", default=True):
    if (path / "package.json").exists():
        with open(path / "package.json", 'r+') as fp:
            data = fp.read()
            data = data.replace('./app_launcher/index.js', './LiteLoader')
            fp.seek(0)
            fp.write(data)
        logger.success('破解完成')
    else:
        logger.error('package.json不存在！')
if sys == 'Windows':
    logger.info("对于Windows系统，还需要进行进一步破解")
    logger.info('https://github.com/xh321/LiteLoaderQQNT-PatcherNFixer/releases/')
