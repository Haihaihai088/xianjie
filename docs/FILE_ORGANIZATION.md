# 文件分类管理规范

## 项目结构（完整版）
2d-game/
├── main.py # 唯一入口，只做初始化+启动循环
│
├── src/ # 所有源代码
│ ├── core/ # 框架层（与具体游戏逻辑无关）
│ │ ├── game_loop.py # 主循环（帧率、事件队列）
│ │ ├── input.py # 输入抽象（键盘/鼠标）
│ │ └── renderer.py # 渲染抽象（支持切换后端）
│ │
│ ├── entities/ # 游戏实体（数据+行为）
│ │ ├── player.py # 玩家（位置、速度、生命）
│ │ ├── enemy.py # 敌人基类
│ │ ├── bullet.py # 子弹
│ │ └── particle.py # 特效粒子（可选）
│ │
│ ├── systems/ # 系统（跨实体的逻辑）
│ │ ├── collision.py # 碰撞检测（矩形/圆形）
│ │ ├── spawner.py # 敌人/道具生成器
│ │ ├── health.py # 伤害/死亡/重生逻辑
│ │ └── scoring.py # 分数/连击系统
│ │
│ ├── ui/ # 界面（不包含核心玩法）
│ │ ├── hud.py # 血条、分数、弹药数
│ │ ├── menu.py # 主菜单/暂停菜单
│ │ └── game_over.py # 结束画面
│ │
│ └── utils/ # 纯工具函数（无游戏状态）
│ ├── loader.py # 加载图片/音频
│ ├── math.py # 向量/矩形/碰撞辅助
│ └── timer.py # 倒计时/冷却辅助
│
├── assets/ # 资源文件（按类型分）
│ ├── images/
│ │ ├── player/
│ │ ├── enemies/
│ │ └── ui/
│ ├── audio/
│ │ ├── bgm/
│ │ └── sfx/
│ └── levels/ # 关卡数据（JSON/Tile地图）
│
├── tests/ # 单元测试（对应 src 结构）
│ ├── test_collision.py
│ ├── test_player.py
│ └── ...
│
├── docs/ # 文档
│ ├── gameplay.md # 玩法说明
│ ├── FILE_ORGANIZATION.md # 本文件
│ └── PR_TEMPLATE.md # PR模板
│
├── .github/
│ └── pull_request_template.md # GitHub PR模板
│
├── README.md # 项目介绍+依赖+启动+视频链接
└── requirements.txt # Python依赖（如使用Pygame）

## 依赖关系规则（避免循环引用）
main.py
↓
src/core/game_loop.py
↓
src/entities/*.py ←── src/systems/*.py
↓ ↓
src/utils/*.py ←── src/ui/*.py

**禁止**：
- `src/utils/` 导入 `src/entities/`
- `src/ui/` 导入 `src/systems/`（UI只通过 core 获取数据）

## 新增文件流程

1. 判断属于哪个目录（参考上表）
2. 如果新文件超过 100 行，考虑拆分为多个文件
3. 在 PR 描述中说明新增文件的职责
4. 更新本文件的"项目结构"部分（如果添加了新的子目录）
