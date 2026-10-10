# 数据与依赖来源

项目自写代码采用 MIT。第三方依赖和数据仍受各自许可证约束。

## TUM RGB-D

- 来源：https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download
- 格式与标定说明：https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats
- 使用序列：`rgbd_dataset_freiburg1_xyz`。
- 原始数据、压缩包、派生帧和真实场景的 RRD 均不放进 Git 仓库。
- 本仓库提供官方来源下载脚本，不将数据许可改写为 MIT；再分发或商业部署前，
  使用者应核对发布方当前的数据条款并履行引用要求。
- 下载文件 SHA256 是本项目对官方文件的观测值，不是发布方签名。

## 合成样例

由本项目生成的简单 RGB-D 平面样例明确标记为合成数据，生成代码采用 MIT。
用于软件测试，不冒充真实机器人或真实标定结果。

## 直接依赖

NumPy、OpenCV、PyYAML、psutil 用于数值、图像、配置和环境诊断；Rerun 为可选可视化。
具体版本锁定在 `uv.lock`。各发行包内的许可与第三方 notices 为准。
没有将这些依赖源码复制到本项目，MIT 许可仅涵盖本项目自写部分。
