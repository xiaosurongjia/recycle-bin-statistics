# 回收站统计

> 这是一款为 Windows 回收站打造的字节统计工具。
> 它可以实时监控回收站的大小、文件数量和类型分布，让你清空回收站变成一种享受。

Windows 平台 · Python + tkinter 制作 · 当前版本 **0.1.1**

## 下载

到 [Releases](https://github.com/xiaosurongjia/recycle-bin-statistics/releases) 页面下载 `回收站统计.exe`，双击即用，无需安装 Python。

## 功能

- **精确统计**：直接扫描各磁盘 `$Recycle.Bin`，解析 `$I` 元数据取出文件原始路径与删除时间，递归计算 `$R` 的真实占用字节数
- **多维度查看**：按磁盘、文件类型、时间分布查看占用，另有历史明细表格与趋势图
- **历史记录**：每次扫描的结果自动留存，可回溯回收站体积变化
- **游戏化**：等级、成就、积分商城（称号 / 特效 / 主题）、满仓抽奖
- **一键清空**：带确认提示的一键清空回收站
- **实用细节**：托盘常驻、音效、深色 / 浅色主题、CSV 导出、最小文件大小与忽略后缀过滤

## 运行源码

需要 Python 3（自带 tkinter）：

```
python 回收站统计.pyw
```

可选依赖 `pystray`、`Pillow`（托盘图标），缺失时会自动降级，不影响主功能。

## 打包

`打包文件.pyw` 是一个基于 PyInstaller 的图形化打包工具，可直接用它把源码打包成单文件 exe。

## 数据位置

配置与历史记录保存在 `%APPDATA%\RecycleStat`：

- `settings.json` — 设置
- `history.json` — 扫描历史
- `game.json` — 等级 / 成就 / 积分

## 说明

- 仅支持 Windows。扫描 `$Recycle.Bin` 与清空回收站属于系统操作，建议以正常用户权限运行。
- 本项目仅供学习交流使用。

## 链接

- GitHub：<https://github.com/xiaosurongjia/recycle-bin-statistics>
- 哔哩哔哩：<https://space.bilibili.com/3493129137163081>

## 许可

[MIT](LICENSE) © 2026 xiaosurongjia
