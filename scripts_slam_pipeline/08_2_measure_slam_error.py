"""
python /home/$(whoami)/Project_UMI/scripts_slam_pipeline/08_measure_slam_error.py

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
import numpy as np
import os
import pickle
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation as R
from scipy.interpolate import interp1d


# 定义读取和处理CSV文件的函数
def read_and_process_csv(file_path, slam_start_time, delta):
    df = pd.read_csv(file_path)
    df["adjusted_timestamp"] = (
        (df["timestamp"] * 1e9).astype(np.int64) + slam_start_time + int(delta * 1e9)
    )  # 将时间戳从秒转换为纳秒并加上起始时间
    df["x"] = pd.to_numeric(df["x"])
    df["y"] = pd.to_numeric(df["y"])
    df["z"] = pd.to_numeric(df["z"])
    return df


# 定义读取和处理PKL文件的函数
def read_and_process_pkl(file_path):
    with open(file_path, "rb") as f:
        data = pickle.load(f)

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


# 计算最优的转换矩阵
def compute_transformation_matrix(A, B):
    assert len(A) == len(B)

    centroid_A = np.mean(A, axis=0)
    centroid_B = np.mean(B, axis=0)

    AA = A - centroid_A
    BB = B - centroid_B

    H = np.dot(AA.T, BB)

    U, S, Vt = np.linalg.svd(H)
    R = np.dot(Vt.T, U.T)

    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = np.dot(Vt.T, U.T)

    t = centroid_B.T - np.dot(R, centroid_A.T)

    return R, t


# 获取当前用户名并构建文件路径
user = os.getenv("USER")
slam_file_path = f"/home/{user}/Project_UMI/example_demo_session/demos/demo_C3441328010998_2024.06.20_15.32.21.852633/camera_trajectory.csv"
ground_truth_file_path = (
    f"/home/{user}/Project_UMI/example_demo_session/GT_GX011068.pkl"
)

# 设置SLAM的起始时间戳（占位符变量）
slam_start_time = 1718868741667852978  # 请根据实际需要输入

# 读取和处理Ground Truth文件
ground_truth_df = read_and_process_pkl(ground_truth_file_path)

# 设置Pandas选项以避免科学计数法，只影响adjusted_timestamp列
pd.set_option("display.float_format", "{:.0f}".format)
pd.options.display.float_format = lambda x: f"{x:.3f}"

# 定义delta的范围
delta_values = np.linspace(-5, 5, 50)  # 例如，范围从-1到1，共50个点

rmse_values = []

# 遍历每个delta值
for delta in delta_values:
    slam_df = read_and_process_csv(slam_file_path, slam_start_time, delta)

    # 打印SLAM轨迹的前5个点
    print(f"SLAM Trajectory first 5 points for delta {delta}:")
    print(slam_df[["adjusted_timestamp", "x", "y", "z"]].head())

    # 打印Ground Truth轨迹的前5个点
    print("Ground Truth Trajectory first 5 points:")
    print(ground_truth_df.head())

    # 对齐时间戳
    interp_func_x = interp1d(
        slam_df["adjusted_timestamp"], slam_df["x"], fill_value="extrapolate"
    )
    interp_func_y = interp1d(
        slam_df["adjusted_timestamp"], slam_df["y"], fill_value="extrapolate"
    )
    interp_func_z = interp1d(
        slam_df["adjusted_timestamp"], slam_df["z"], fill_value="extrapolate"
    )

    aligned_slam_x = interp_func_x(ground_truth_df["timestamp"])
    aligned_slam_y = interp_func_y(ground_truth_df["timestamp"])
    aligned_slam_z = interp_func_z(ground_truth_df["timestamp"])

    aligned_slam_df = pd.DataFrame(
        {
            "timestamp": ground_truth_df["timestamp"],
            "x": aligned_slam_x,
            "y": aligned_slam_y,
            "z": aligned_slam_z,
        }
    )

    A = aligned_slam_df[["x", "y", "z"]].to_numpy()
    B = ground_truth_df[["x", "y", "z"]].to_numpy()

    R, t = compute_transformation_matrix(A, B)

    # 应用转换矩阵
    transformed_A = np.dot(R, A.T).T + t

    # 计算误差
    errors = B - transformed_A

    # 计算每个轴的RMSE
    rmse_x = np.sqrt(np.mean(errors[:, 0] ** 2))
    rmse_y = np.sqrt(np.mean(errors[:, 1] ** 2))
    rmse_z = np.sqrt(np.mean(errors[:, 2] ** 2))

    # 计算总的RMSE
    total_rmse = np.sqrt(np.mean(np.sum(errors**2, axis=1)))

    # 计算欧几里得距离误差
    euclidean_errors = np.linalg.norm(errors, axis=1)
    max_error = np.max(euclidean_errors)
    min_error = np.min(euclidean_errors)
    mean_error = np.mean(euclidean_errors)

    print("-" * 40)
    print(f"Rotation matrix for delta {delta}:\n{R}")
    print(f"Translation vector for delta {delta}:\n{t}")
    print(
        f"RMSE (X) for delta {delta}: {rmse_x:.4f}; RMSE (Y) for delta {delta}: {rmse_y:.4f}; RMSE (Z) for delta {delta}: {rmse_z:.4f}"
    )
    print(f"Total RMSE for delta {delta}: {total_rmse:.4f}")
    print(
        f"Max error for delta {delta}: {max_error:.4f}; Min error for delta {delta}: {min_error:.4f}; Mean error for delta {delta}: {mean_error:.4f}"
    )
    print("-" * 40)

    rmse_values.append(total_rmse)

# 绘制误差随delta变化的曲线
plt.figure(figsize=(10, 6))
plt.plot(delta_values, rmse_values, marker="o")
plt.xlabel("Delta (seconds)")
plt.ylabel("Total RMSE")
plt.title("Error Variation with Delta")
plt.grid(True)
plt.show()


"""
可视化误差
"""
# import matplotlib.pyplot as plt

# # 可视化SLAM轨迹和Ground Truth轨迹
# fig = plt.figure()
# ax = fig.add_subplot(111, projection="3d")

# ax.plot(
#     aligned_slam_df["x"],
#     aligned_slam_df["y"],
#     aligned_slam_df["z"],
#     label="SLAM Trajectory",
# )
# ax.plot(
#     ground_truth_df["x"],
#     ground_truth_df["y"],
#     ground_truth_df["z"],
#     label="Ground Truth Trajectory",
# )
# ax.legend()

# plt.show()

# # 绘制误差随时间变化的图
# time = ground_truth_df["timestamp"]
# error_x = errors[:, 0]
# error_y = errors[:, 1]
# error_z = errors[:, 2]

# plt.figure()
# plt.plot(time, error_x, label="Error in X")
# plt.plot(time, error_y, label="Error in Y")
# plt.plot(time, error_z, label="Error in Z")
# plt.xlabel("Timestamp")
# plt.ylabel("Error")
# plt.legend()
# plt.show()
