# Usage

## run with default parameters
bambu_timelapse_download.exe --ip 192.168.0.20 --pass 12345678

## save timelapse file in diffrent directory
bambu_timelapse_download.exe --ip 192.168.0.20 --pass 12345678 --download_dir "Z:\Video\3D Druck\Timelapse"


# Parameter
| Name                 | Description                           | Required | Default   |
|----------------------|---------------------------------------|----------|-----------|
| ip                   | IP address of printer.                | Yes      | -         |
| port                 | FTP Port.                             | No       | 990       |
| user                 | FTP User.                             | No       | bblp      |
| password             | Access code shown on printer display. | Yes      | -         |
| download_dir         | Download foldername.                  | No       | timelapse |
| ftp_timelapse_folder | FTP timelapse folder on ftp.          | No       | timelapse |
| -d                   | Delete timelapse file after download. | No       | -         |
| -v                   | Show Version                          | No       | -         |