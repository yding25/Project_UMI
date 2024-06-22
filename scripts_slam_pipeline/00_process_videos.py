"""
python /home/$(whoami)/Project_UMI/scripts_slam_pipeline/00_process_videos.py

脚本的主要功能是对视频文件进行处理和组织，确保视频文件按照特定的结构存储并且创建相应的符号链接。
"""

import sys
import os
import pathlib
import shutil
from exiftool import ExifToolHelper
from umi.common.timecode_util import mp4_get_start_datetime

'''
设置根目录 ROOT_DIR 为 /home/{USER}/Project_UMI。
将根目录添加到 Python 的路径中，并切换当前工作目录到根目录。
'''
ROOT_DIR = '/home/{}/Project_UMI'.format(os.getenv('USER'))
sys.path.append(ROOT_DIR)
os.chdir(ROOT_DIR)

def main():
    '''
    session_dir 定义了会话目录的路径, 该项目默认为example_demo_session
    '''
    session_dir = pathlib.Path("/home/{}/Project_UMI/example_demo_session".format(os.getenv('USER')))
    session = session_dir.absolute()
    
    '''
    输入目录: raw_videos; 输出目录: demos
    '''
    input_dir = session.joinpath("raw_videos")
    output_dir = session.joinpath("demos")

    '''
    创建 raw_videos 目录并移动所有的 .mp4 视频文件到该目录
    '''
    if not input_dir.is_dir():
        input_dir.mkdir()
        print(
            f"{input_dir.name} subdir doesn't exist! Creating one and moving all mp4 videos inside."
        )
        for mp4_path in list(session.glob("**/*.MP4")) + list(
            session.glob("**/*.mp4")
        ):
            out_path = input_dir.joinpath(mp4_path.name)
            shutil.move(mp4_path, out_path)

    '''
    查找并处理 mapping.mp4 文件
    '''
    mapping_vid_path = None
    for ext in ["MP4", "mp4"]:
        potential_path = input_dir.joinpath(f"mapping.{ext}")
        if potential_path.exists():
            mapping_vid_path = potential_path
            break
    print(f"mapping_vid_path: {mapping_vid_path}") 
    if not mapping_vid_path:
        raise FileNotFoundError(
            "mapping.mp4 not found! Please specify which mp4 file is the mapping video."
        )

    '''
    查找并处理 gripper_calibration.mp4 文件
    '''
    gripper_cal_dir = input_dir.joinpath("gripper_calibration")
    gripper_cal_vid_path = None
    for ext in ["MP4", "mp4"]:
        potential_path = input_dir.joinpath(f"gripper_calibration.{ext}")
        if potential_path.exists():
            gripper_cal_vid_path = potential_path
            break
    if not gripper_cal_dir.is_dir():
        gripper_cal_dir.mkdir()
        print(
            "raw_videos/gripper_calibration doesn't exist! Creating one with the gripper calibration video."
        )
        if not gripper_cal_vid_path:
            raise FileNotFoundError(
                "gripper_calibration.mp4 not found! Please specify which mp4 file is the gripper calibration video."
            )
        else:
            out_path = gripper_cal_dir.joinpath(gripper_cal_vid_path.name)
            shutil.move(gripper_cal_vid_path, out_path)
            print(
                f"Moved {gripper_cal_vid_path.name} to gripper_calibration directory."
            )

    '''
    查找所有的 .mp4 文件
    '''
    input_mp4_paths = list(input_dir.glob("**/*.MP4")) + list(
        input_dir.glob("**/*.mp4")
    )
    print(f"Found {len(input_mp4_paths)} MP4 videos")

    '''
    使用 ExifTool 获取视频的元数据并处理视频文件
    '''
    with ExifToolHelper() as et:
        for mp4_path in input_mp4_paths:
            if mp4_path.is_symlink():
                print(f"Skipping {mp4_path.name}, already moved.")
                continue

            start_date = mp4_get_start_datetime(str(mp4_path))
            meta = list(et.get_metadata(str(mp4_path)))[0]
            cam_serial = meta["QuickTime:CameraSerialNumber"]
            out_dname = (
                "demo_"
                + cam_serial
                + "_"
                + start_date.strftime(r"%Y.%m.%d_%H.%M.%S.%f")
            )

            # special folders
            if mp4_path.name.startswith("mapping"):
                out_dname = "mapping"
            elif mp4_path.name.startswith(
                "gripper_cal"
            ) or mp4_path.parent.name.startswith("gripper_cal"):
                out_dname = (
                    "gripper_calibration_"
                    + cam_serial
                    + "_"
                    + start_date.strftime(r"%Y.%m.%d_%H.%M.%S.%f")
                )

            # create directory
            this_out_dir = output_dir.joinpath(out_dname)
            this_out_dir.mkdir(parents=True, exist_ok=True)

            # move videos
            vfname = "raw_video.mp4"
            out_video_path = this_out_dir.joinpath(vfname)
            shutil.move(mp4_path, out_video_path)

            # create symlink back from original location
            # relative_to's walk_up argument is not available until python 3.12
            dots = os.path.join(
                *[".."] * len(mp4_path.parent.relative_to(session).parts)
            )
            rel_path = str(out_video_path.relative_to(session))
            symlink_path = os.path.join(dots, rel_path)
            mp4_path.symlink_to(symlink_path)

if __name__ == "__main__":
    main()
