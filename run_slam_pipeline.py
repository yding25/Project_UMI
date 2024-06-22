import subprocess
import os


def run_script(script_path, *args):
    cmd = ["python", script_path] + list(args)
    result = subprocess.run(cmd, text=True, capture_output=True)

    print(f"Running {script_path} with arguments: {' '.join(args)}")
    if result.returncode != 0:
        print(f"Error running {script_path}: {result.stderr}")
    else:
        print(f"Successfully ran {script_path}")
        print(result.stdout)


def main():
    username = os.getenv("USER") or os.getenv("USERNAME") or os.getlogin()
    base_dir = f"/home/{username}/Project_UMI/scripts_slam_pipeline"
    example_session_dir = f"/home/{username}/Project_UMI/example_demo_session"

    scripts = [
        "00_process_videos.py",
        "01_extract_gopro_imu.py",
        "02_create_map.py",
        "03_batch_slam.py",
        "04_detect_aruco.py",
        "05_run_calibrations.py",
    ]

    # Run all the scripts in sequence
    for script in scripts:
        script_path = os.path.join(base_dir, script)
        if script == "02_create_map.py":
            run_script(
                script_path,
                "--input_dir",
                f"{example_session_dir}/demos/mapping",
                "--map_path",
                f"{example_session_dir}/demos/mapping/map_atlas.osa",
            )
        elif script == "03_batch_slam.py":
            run_script(
                script_path,
                "--input_dir",
                f"{example_session_dir}/demos",
                "--map_path",
                f"{example_session_dir}/demos/mapping/map_atlas.osa",
            )
        elif script == "04_detect_aruco.py":
            run_script(
                script_path,
                "-i",
                f"{example_session_dir}/demos",
                "-ci",
                f"example/calibration/gopro_intrinsics_2_7k.json",
                "-ac",
                f"example/calibration/aruco_config.yaml",
            )
        elif script == "05_run_calibrations.py":
            run_script(script_path, example_session_dir)
        else:
            run_script(script_path)


if __name__ == "__main__":
    main()
