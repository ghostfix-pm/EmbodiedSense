# MVP 1 验收记录

日期：2026-10-10。以下结果由命令实际运行产生，不是目标值。

## 环境

Windows 11，Python 3.12.5，24 个逻辑 CPU，15.71 GiB RAM。
RTX 4060 Laptop GPU 可枚举，显存 8188 MiB；没有执行 GPU 推理测试。
核心在 CPU 上运行。项目、独立环境、数据和输出位于 D 盘。

uv 0.13.0；NumPy 2.5.3；OpenCV headless 4.14.0.94；PyYAML 6.0.3；
Rerun SDK 0.29.2。完整依赖版本见 uv.lock。

## 自动验证

- `pytest -q`：20 项通过，包括三维坐标与深度单位数值测试、时间戳精度、
  故障处理、CLI 端到端、记录校验和回放一致性、无界面 Rerun 导出。
- `ruff check .` 和 `ruff format --check .`：通过。
- `uv build`：成功生成 wheel 和源码发行包。
- Windows 命令行入口和 `dev.ps1 run embodiedsense --version`：返回 0.1.0。
- GitHub Actions 配置提供 Windows/Linux 合成测试；远程执行结果以 Actions 页面为准。

## 真实 RGB-D 运行

TUM 官方 `fr1/xyz` 压缩包下载、SHA256 校验并解压。
哈希：`a0236d97b8c30cd93b653656d2b6c293ff7c982a4130ef2a1a8beecdb124ef98`。

```powershell
.venv\Scripts\embodiedsense.exe run --config configs/tum_rgbd.yaml --data-root data/rgbd_dataset_freiburg1_xyz --out outputs/tum-d-v01 --limit 120 --rerun --ply
.venv\Scripts\embodiedsense.exe replay --recording outputs/tum-d-v01 --speed 0
.venv\Scripts\python.exe -m rerun rrd verify outputs/tum-d-v01/scene.rrd
```

| 指标 | 实测值 |
|---|---:|
| RGB 观测数 | 120 |
| 容差内匹配的深度观测数 | 120 |
| 输出点数，跨帧累计 | 1,731,525 |
| 绝对同步差 P95 | 16.86815 ms |
| 解码、校验、点云投影耗时 P95 | 40.45 ms |
| 包括压缩存储、PLY、RRD 的总耗时 | 14.52 s |
| 包括输出的离线处理吞吐 | 8.26 组/s |
| 采样到的进程 RSS 最大值 | 100.60 MiB |
| 自包含回放观测数 | 120 |
| Rerun 结构校验 | 1 file verified without error |

120 帧均为 WARN：全部包含局部无效深度像素，9 帧还标记了深度复用。
这不是整帧解码失败；有效像素仍正确产生点云。报告不将这些质量标记包装成安全概率。

这些数据为前 120 组观测、stride=4、当前电脑和具体输出配置下的一次运行结果。
不是全数据集结果，也不代表在线机器人控制频率。点云在相机光学坐标系中，
没有融合为世界地图。大文件位于本地 outputs/，不上传 GitHub。

Rerun 文件已生成并通过结构校验；由于用户要求命令操作，未自动打开查看器，
因此不声称做过 GUI 视觉验收。用户可按 README 中的命令自行查看。
