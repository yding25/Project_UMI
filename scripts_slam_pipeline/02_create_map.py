"""
python /home/$(whoami)/Project_UMI/scripts_slam_pipeline/02_create_map.py --input_dir /home/$(whoami)/Project_UMI/example_demo_session/demos/mapping --map_path /home/$(whoami)/Project_UMI/example_demo_session/demos/mapping/map_atlas.osa

脚本的功能是从指定目录中的 GoPro 视频和 IMU 数据中创建一个 SLAM 地图
"""

import sys
import os
import pathlib
import click
import subprocess
import numpy as np
import cv2
from umi.common.cv_util import draw_predefined_mask

'''
设置根目录 ROOT_DIR 为 /home/{USER}/Project_UMI。
将根目录添加到 Python 的路径中，并切换当前工作目录到根目录。
'''
ROOT_DIR = '/home/{}/Project_UMI'.format(os.getenv('USER'))
sys.path.append(ROOT_DIR)
os.chdir(ROOT_DIR)

'''
定义命令行参数
使用 click 库定义命令行参数
input_dir 指定了包含映射视频的目录
map_path 指定了保存生成的地图文件的路径
docker_image 指定要使用的 Docker 镜像
no_docker_pull 用于控制是否从 Docker Hub 拉取最新的 Docker 镜像。
no_mask 参数决定是否生成遮罩文件，用于屏蔽不需要的图像区域（例如，夹持器和镜子）
'''
@click.command()
@click.option('-i', '--input_dir', required=True, help='Directory for mapping video')
@click.option('-m', '--map_path', default=None, help='ORB_SLAM3 *.osa map atlas file')
@click.option('-d', '--docker_image', default="chicheng/orb_slam3:latest")
@click.option('-np', '--no_docker_pull', is_flag=True, default=False, help="pull docker image from docker hub")
@click.option('-nm', '--no_mask', is_flag=True, default=False, help="Whether to mask out gripper and mirrors. Set if map is created with bare GoPro no on gripper.")

def main(input_dir, map_path, docker_image, no_docker_pull, no_mask):
    video_dir = pathlib.Path(input_dir).absolute()
    for fn in ['raw_video.mp4', 'imu_data.json']:
        assert video_dir.joinpath(fn).is_file(), f"{fn} not found in {video_dir}"

    if map_path is None:
        map_path = video_dir.joinpath('map_atlas.osa')
    else:
        map_path = pathlib.Path(map_path).absolute()
    map_path.parent.mkdir(parents=True, exist_ok=True)

    '''
    检查 Docker 权限, 拉取 Docker 镜像
    '''
    if not no_docker_pull:
        print(f"Pulling docker image {docker_image}")
        cmd = [
            'docker',
            'pull',
            docker_image
        ]
        p = subprocess.run(cmd)
        if p.returncode != 0:
            print("Docker pull failed!")
            exit(1)

    # TODO: 需要绘制我们自己夹爪的遮罩文件, 遮罩文件用于屏蔽特定区域,以提高地图构建和定位的准确性。
    '''
    准备文件路径和遮罩文件(如果需要，创建遮罩文件来屏蔽不需要的图像区域。)
    '''
    mount_target = pathlib.Path('/data')
    csv_path = mount_target.joinpath('mapping_camera_trajectory.csv')
    video_path = mount_target.joinpath('raw_video.mp4')
    json_path = mount_target.joinpath('imu_data.json')
    mask_path = mount_target.joinpath('slam_mask.png')
    if not no_mask:
        '''
        定义遮罩文件的路径和初始化遮罩数组
        '''
        mask_write_path = video_dir.joinpath('slam_mask.png')
        slam_mask = np.zeros((2028, 2704), dtype=np.uint8)
        '''
        绘制预定义遮罩
        '''
        slam_mask = draw_predefined_mask(
            slam_mask, color=255, mirror=True, gripper=False, finger=True)
        '''
        保存生成的遮罩图像
        '''
        cv2.imwrite(str(mask_write_path.absolute()), slam_mask)

    '''
    设置地图路径并挂载目标路径
    '''
    map_mount_source = pathlib.Path(map_path)
    map_mount_target = pathlib.Path('/map').joinpath(map_mount_source.name)

    '''
    构建并运行 SLAM 命令 (使用 Docker 容器运行 ORB-SLAM3 算法来处理视频和 IMU 数据)
    '''
    cmd = [
        'docker',
        'run',
        '--rm', # delete after finish
        '--volume', str(video_dir) + ':' + '/data',
        '--volume', str(map_mount_source.parent) + ':' + str(map_mount_target.parent),
        docker_image,
        '/ORB_SLAM3/Examples/Monocular-Inertial/gopro_slam',
        '--vocabulary', '/ORB_SLAM3/Vocabulary/ORBvoc.txt',
        '--setting', '/ORB_SLAM3/Examples/Monocular-Inertial/gopro10_maxlens_fisheye_setting_v1_720.yaml',
        '--input_video', str(video_path),
        '--input_imu_json', str(json_path),
        '--output_trajectory_csv', str(csv_path),
        '--save_map', str(map_mount_target)
    ]
    if not no_mask:
        cmd.extend([
            '--mask_img', str(mask_path)
        ])

    '''
    将生成的地图文件和相机轨迹文件保存到指定位置
    '''
    stdout_path = video_dir.joinpath('slam_stdout.txt')
    stderr_path = video_dir.joinpath('slam_stderr.txt')

    result = subprocess.run(
        cmd,
        cwd=str(video_dir),
        stdout=stdout_path.open('w'),
        stderr=stderr_path.open('w')
    )
    print(result)

# %%
if __name__ == "__main__":
    main()
