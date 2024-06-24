"""
python /home/$(whoami)/Project_UMI/scripts_slam_pipeline/08_1_visualize_trajectory.py

脚本的功能有:
1, 展示和绘制SLAM算出来的trajectory文件, 比如
- /home/$(whoami)/Project_UMI/example_demo_session/demos/mapping/mapping_camera_trajectory.csv
- /home/$(whoami)/Project_UMI/example_demo_session/demos/mapping/camera_trajectory.csv
- /home/$(whoami)/Project_UMI/example_demo_session/demos/demo_C3441328010998_2024.06.20_15.32.21.852633/camera_trajectory.csv
- /home/$(whoami)/Project_UMI/example_demo_session/demos/demo_C3441328010998_2024.06.20_15.33.06.981050/camera_trajectory.csv
- /home/$(whoami)/Project_UMI/example_demo_session/demos/demo_C3441328010998_2024.06.20_15.34.27.911900/camera_trajectory.csv
- ...

2, 展示和绘制ground truth的trajectory文件, 比如
- /home/$(whoami)/Project_UMI/example_demo_session/GT_GX011068.pkl
- /home/$(whoami)/Project_UMI/example_demo_session/GT_GX011069.pkl
- /home/$(whoami)/Project_UMI/example_demo_session/GT_GX011070.pkl
- ...

3, 计算SLAM和ground truth之间的误差
"""

import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os
import pickle


# 定义读取和处理CSV文件的函数
def read_and_process_csv(file_path, global_init_time=0.0):
    df = pd.read_csv(file_path)
    df["adjusted_timestamp"] = df["timestamp"] + global_init_time
    df["x"] = pd.to_numeric(df["x"])
    df["y"] = pd.to_numeric(df["y"])
    df["z"] = pd.to_numeric(df["z"])
    df["adjusted_timestamp"] = pd.to_numeric(df["adjusted_timestamp"])
    return df


# 定义读取和处理PKL文件的函数
def read_and_process_pkl(file_path):
    with open(file_path, "rb") as f:
        data = pickle.load(f)

    # 打印PKL文件内容
    print(f"Contents of {file_path}:")
    if "GT_GX011098" in file_path:
        for record in data:
            print(record)

    # 提取所需的字段
    timestamps = []
    x_values = []
    y_values = []
    z_values = []

    for record in data:
        timestamps.append(record["timestemp"])
        flange_pose = record["flangePose"]
        x_values.append(flange_pose[0])
        y_values.append(flange_pose[1])
        z_values.append(flange_pose[2])

    df = pd.DataFrame(
        {"timestamp": timestamps, "x": x_values, "y": y_values, "z": z_values}
    )

    return df


# 获取当前用户名并构建文件路径
user = os.getenv("USER")

# SLAM Trajectories (CSV)
csv_file_paths = [
    f"/home/{user}/Project_UMI/example_demo_session/demos/mapping/mapping_camera_trajectory.csv",
    f"/home/{user}/Project_UMI/example_demo_session/demos/mapping/camera_trajectory.csv",
    f"/home/{user}/Project_UMI/example_demo_session/demos/demo_C3441328010998_2024.06.24_13.18.16.365183/camera_trajectory.csv",
    # f"/home/{user}/Project_UMI/example_demo_session/demos/demo_C3441328010998_2024.06.24_13.20.57.342667/camera_trajectory.csv",
    # f"/home/{user}/Project_UMI/example_demo_session/demos/demo_C3441328010998_2024.06.24_13.21.38.133417/camera_trajectory.csv",
]
global_init_time = 0.0  # 根据需要调整

# 读取和处理CSV文件
csv_dataframes = [read_and_process_csv(fp, global_init_time) for fp in csv_file_paths]

# 计算所有数据的x、y、z范围
all_csv_x = pd.concat([df["x"] for df in csv_dataframes])
all_csv_y = pd.concat([df["y"] for df in csv_dataframes])
all_csv_z = pd.concat([df["z"] for df in csv_dataframes])

csv_x_range = (all_csv_x.min(), all_csv_x.max())
csv_y_range = (all_csv_y.min(), all_csv_y.max())
csv_z_range = (all_csv_z.min(), all_csv_z.max())

# 创建6个子图（2行3列）用于CSV数据
fig_csv, axs_csv = plt.subplots(2, 3, subplot_kw={"projection": "3d"})
fig_csv.suptitle("Trajectories from SLAM (CSV)")

# 绘制每个CSV文件的3D图
csv_titles = [
    "mapping_camera_trajectory.csv",
    "camera_trajectory.csv",
    "GX011098/camera_trajectory.csv",
    "GX011100/camera_trajectory.csv",
    "GX011101/camera_trajectory.csv",
]

for i, (df, title) in enumerate(zip(csv_dataframes, csv_titles)):
    row = i // 3
    col = i % 3
    ax = axs_csv[row, col]
    ax.scatter(
        df["x"].values, df["y"].values, df["z"].values, c="b", marker="o"
    )  # 所有点为蓝色
    ax.scatter(
        df["x"].values[0],
        df["y"].values[0],
        df["z"].values[0],
        c="g",
        marker="o",
        s=100,
    )  # 起始点为绿色
    ax.scatter(
        df["x"].values[-1],
        df["y"].values[-1],
        df["z"].values[-1],
        c="r",
        marker="o",
        s=100,
    )  # 末端点为红色
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_xlim(csv_x_range)
    ax.set_ylim(csv_y_range)
    ax.set_zlim(csv_z_range)
    ax.set_title(title)

# 预留空白的子图
for i in range(len(csv_dataframes), 6):
    row = i // 3
    col = i % 3
    axs_csv[row, col].set_visible(False)

# Ground Truth Trajectories (PKL)
pkl_file_paths = [
    f"/home/{user}/Project_UMI/example_demo_session/GT_GX011098.pkl",
    # f"/home/{user}/Project_UMI/example_demo_session/GT_GX011100.pkl",
    # f"/home/{user}/Project_UMI/example_demo_session/GT_GX011101.pkl",
]

# 读取和处理PKL文件
gt_dataframes = [read_and_process_pkl(fp) for fp in pkl_file_paths]

# 计算所有数据的x、y、z范围，过滤NaN和Inf值
all_gt_x = (
    pd.concat([df["x"] for df in gt_dataframes])
    .replace([float("inf"), -float("inf")], float("nan"))
    .dropna()
)
all_gt_y = (
    pd.concat([df["y"] for df in gt_dataframes])
    .replace([float("inf"), -float("inf")], float("nan"))
    .dropna()
)
all_gt_z = (
    pd.concat([df["z"] for df in gt_dataframes])
    .replace([float("inf"), -float("inf")], float("nan"))
    .dropna()
)

gt_x_range = (all_gt_x.min(), all_gt_x.max())
gt_y_range = (all_gt_y.min(), all_gt_y.max())
gt_z_range = (all_gt_z.min(), all_gt_z.max())

# 创建6个子图（2行3列）用于PKL数据
fig_pkl, axs_pkl = plt.subplots(2, 3, subplot_kw={"projection": "3d"})
fig_pkl.suptitle("Ground Truth Trajectories (PKL)")

# 绘制每个PKL文件的3D图
# gt_titles = ["GT_GX011068.pkl", "GT_GX011069.pkl", "GT_GX011070.pkl"]
gt_titles = ["GT_GX011098.pkl"]

for i, (df, title) in enumerate(zip(gt_dataframes, gt_titles)):
    row = i // 3
    col = i % 3
    ax = axs_pkl[row, col]
    ax.scatter(
        df["x"].values, df["y"].values, df["z"].values, c="b", marker="o"
    )  # 所有点为蓝色
    ax.scatter(
        df["x"].values[0],
        df["y"].values[0],
        df["z"].values[0],
        c="g",
        marker="o",
        s=100,
    )  # 起始点为绿色
    ax.scatter(
        df["x"].values[-1],
        df["y"].values[-1],
        df["z"].values[-1],
        c="r",
        marker="o",
        s=100,
    )  # 末端点为红色
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_xlim(gt_x_range)
    ax.set_ylim(gt_y_range)
    ax.set_zlim(gt_z_range)
    ax.set_title(title)

# 预留空白的子图
for i in range(len(gt_dataframes), 6):
    row = i // 3
    col = i % 3
    axs_pkl[row, col].set_visible(False)

# 显示图形
plt.show()
