# LLQQNTInstaller.py
## 安装
```commandline
git clone https://github.com/kaixinol/LLQQNTInstaller.py.git
cd LLQQNTInstaller.py
pip install poetry
poetry install
```
## 运行
```commandline
poetry run python3 -m llqqntinstaller  --proxy socks5://127.0.0.1:7890 # 使用socks5代理
# 或
poetry run python3 -m llqqntinstaller  --use-git-proxy # 使用默认git代理
```
