from pathlib import Path
from platform import system
from pygit2 import clone_repository
from os import environ
from argparse import ArgumentParser
from loguru import logger
from lxml import etree
from rich.prompt import Console
from rich.table import Table
from os import getegid
from .util import Spider
from rich.prompt import Confirm
from shutil import rmtree
sys = system()
parser = ArgumentParser(
    prog='llqtinstaller',
    description='LiteLoaderQQNT一键安装器')
parser.add_argument('-p', '--proxy', type=str)
parser.add_argument('--use-git-proxy',action='store_true',
                    default=False,)
args = parser.parse_args()
https_proxy: str = ''
spider = Spider()
if args.proxy:
    https_proxy = environ.pop('https_proxy', None)
    environ['https_proxy'] = args.proxy
    spider = Spider(proxy={'https': args.proxy})


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
        repo_url="https://ghproxy.com/"+repo_url
    repo_path = folder / "LiteLoader"
    if repo_path.exists() and repo_path.is_dir():
        if Confirm.ask("发现LiteLoader不为空，是否删除？",default=False):
            rmtree(repo_path)
        else:
            exit(0)
    repo = clone_repository(repo_url, repo_path)
    submodules = repo.listall_submodules()
    for submodule in submodules:
        url = 'https://github.com/LiteLoaderQQNT' + submodule[submodule.rfind("/"):]
        if args.use_git_proxy:
            url = "https://ghproxy.com/" + url
        clone_repository(url, Path(repo_path) / submodule)
    del environ['https_proxy']


html = spider.get_text('https://github.com/LiteLoaderQQNT/LiteLoaderQQNT')


def get_current_version():
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


if sys != "Windows":
    if getegid() != 0:
        logger.warning('你当前正在使用类UNIX操作系统，你需要使用sudo权限运行脚本')
        exit(0)
logger.info(f'LiteLoaderQQNT 版本：{get_current_version()}')
print_info_table()
if https_proxy:
    environ['https_proxy'] = https_proxy
path: Path
try:
    path = get_install_path()
except Exception as e:
    logger.error((e))
    exit(1)
try:
    install_via_git(path)
except Exception as e:
    logger.error('在克隆仓库的过程中发生了一些错误' + str(e))
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
