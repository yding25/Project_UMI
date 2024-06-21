"""
python /home/$(whoami)/Project_UMI/scripts_slam_pipeline/00_process_videos.py
"""

# %%
import sys
import os

ROOT_DIR = '/home/{}/Project_UMI'.format(os.getenv('USER'))
sys.path.append(ROOT_DIR)
os.chdir(ROOT_DIR)

# %%
import pathlib
import shutil
from exiftool import ExifToolHelper
from umi.common.timecode_util import mp4_get_start_datetime

def main():
    session_dir = pathlib.Path("/home/{}/Project_UMI/example_demo_session".format(os.getenv('USER')))
    session = session_dir.absolute()
    # hardcode subdirs
    input_dir = session.joinpath("raw_videos")
    output_dir = session.joinpath("demos")

    # create raw_videos if don't exist
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

    # create mapping video if don't exist
    mapping_vid_path = None
    for ext in ["MP4", "mp4"]:
        potential_path = input_dir.joinpath(f"mapping.{ext}")
        if potential_path.exists():
            mapping_vid_path = potential_path
            break
    if not mapping_vid_path:
        raise FileNotFoundError(
            "mapping.mp4 not found! Please specify which mp4 file is the mapping video."
        )

    # create gripper calibration video if don't exist
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

    # look for mp4 video in all subdirectories in input_dir
    input_mp4_paths = list(input_dir.glob("**/*.MP4")) + list(
        input_dir.glob("**/*.mp4")
    )
    print(f"Found {len(input_mp4_paths)} MP4 videos")

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

# %%
if __name__ == "__main__":
    main()
