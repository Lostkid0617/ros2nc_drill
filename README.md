# ros2nc_drill

用于用 ROS2 控制数控机床（首个试点为数控钻床）的项目骨架与实验仓库。

目标
- 用 ROS2 替代传统 G-code 流程，提供更结构化、可编排且更易集成的机床控制栈。
- 先提供一个最小可运行的原型（仿真 + 启动/演示节点），后续逐步接入 ros2_control 硬件接口与真实驱动。

当前状态（2026-09-28）
- 该仓库基于 ros2_control 的代码结构（fork 自 ros-controls/ros2_control）。
- 新增了一个最小演示层，用于快速验证 ROS2 通信与控制流程：
  - drill_sim：简单的钻床仿真节点，发布 /drill/joint_states，订阅 /drill/command（支持 start/stop/set_rpm 指令）。
  - drill_bringup：用于启动 drill_sim 的 launch 包（bringup）。

## 系统框图

![System architecture](diagrams/drill_system.svg)

## 快速开始（本地构建）
1. 环境要求
   - 已安装 ROS2（例如 humble/iron/rolling，确保 source 对应版本的 setup.bash）。
   - colcon 工具（用于构建工作区）。

2. 获取代码并放入工作区
```bash
# 假设在 ~/ws_drill
mkdir -p ~/ws_drill/src
cd ~/ws_drill/src
# 克隆整个仓库或仅复制 drill_sim 与 drill_bringup 两个包到 src/
# 例如：
git clone https://github.com/Lostkid0617/ros2nc_drill.git
# 或直接把 drill_sim/ 和 drill_bringup/ 目录放到 src/
```

3. 安装依赖并构建
```bash
cd ~/ws_drill
rosdep update || true
rosdep install --from-paths src --ignore-src -r -y || true
colcon build --symlink-install
source install/setup.bash
```

4. 运行
- 直接运行 drill_sim 节点：
```bash
ros2 run drill_sim drill_sim
```
- 使用 bringup launch（会启动 drill_sim）：
```bash
ros2 launch drill_bringup bringup_launch.py
```

5. 简单验证
```bash
# 在另一个终端（记得 source install/setup.bash）
ros2 topic echo /drill/joint_states
ros2 topic pub /drill/command std_msgs/String "data: 'start'" -1
ros2 topic pub /drill/command std_msgs/String "data: 'set_rpm 1200'" -1
ros2 topic pub /drill/command std_msgs/String "data: 'stop'" -1
```

接下来的工作建议
- 把通信消息从 std_msgs/String 替换为专用的 drill_msgs（例如 DrillCommand/DrillStatus），以便表达更丰富的任务与状态。
- 基于 ros2_control 实现 drill_hardware_interface（read/write + lifecycle），与 controller_manager 集成真机驱动。
- 添加一个 drill_controller 包，负责任务编排（钻孔序列、点阵钻孔、刀具管理、错误处理）。
- 增加单元测试、CI（GitHub Actions）和使用文档（示意图、流程图、安全说明）。

贡献
- 欢迎通过 PR 提交新增功能、修复或说明文档。如果你希望我把某个功能作为 PR 提交到本仓库，请告知我需要的变更与目标分支。

License
- Apache-2.0（继承本仓库现有许可）
