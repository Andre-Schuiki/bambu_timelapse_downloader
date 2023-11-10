import ftplib
import ssl
import os
import sys
import argparse
import configparser
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

app_name = __name__
version = '1.0.0.0'

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)


def setup_logging(log_root_directory=f'{application_path}/logs', logger_name=app_name, log_file_max_byte_size=104857, log_file_max_backup=3, log_default_level=logging.DEBUG, console_level=logging.INFO, logfile_level=logging.DEBUG):
    """
    :param logger_name:
    :param default_level:
    :return: logger
    """
    today = datetime.today()
    year = today.strftime('%Y')
    month = today.strftime('%m')
    log_name_ = logger_name.rstrip('.log') + f'_{os.getlogin()}' + '.log'
    log_name = today.strftime(f'%Y%m%d_{log_name_}')
    # create an initial logger. It will only log to console and it will disabled
    log_format_console = "[%(asctime)s:%(filename)s:%(lineno)s:%(name)s.%(funcName)s()] %(levelname)s %(message)s"
    log_format_file = "[%(asctime)s:%(filename)s:%(lineno)s:%(name)s.%(funcName)s()] %(levelname)s %(message)s"
    log_date_format = '%Y%m%d %H:%M:%S'
    if logger_name:
        logger = logging.getLogger(logger_name)
    else:
        logger = logging.getLogger()
    log_directory = f'{log_root_directory}/{year}/{month}'
    if not os.path.exists(log_directory):
        logger.debug(f'create log dir {log_directory}')
        os.makedirs(log_directory)

    log_file_path = f'{log_directory}/{log_name}'
    logger.debug(f'add log file handler {log_file_path}')
    log_file_handler = RotatingFileHandler(filename=log_file_path, mode='a',
                                           maxBytes=log_file_max_byte_size,
                                           backupCount=log_file_max_backup,
                                           delay="false",
                                           encoding='utf8')
    log_console_handler = logging.StreamHandler()
    log_console_handler.setLevel(console_level)
    log_console_handler.setFormatter(logging.Formatter(log_format_console))

    log_file_handler.setLevel(logfile_level)
    log_file_handler.setFormatter(logging.Formatter(log_format_file, datefmt=log_date_format))

    logger.setLevel(log_default_level)
    logger.addHandler(log_console_handler)
    logger.addHandler(log_file_handler)
    return logger

class ImplicitFTP_TLS(ftplib.FTP_TLS):
    """FTP_TLS subclass that automatically wraps sockets in SSL to support implicit FTPS."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sock = None

    @property
    def sock(self):
        """Return the socket."""
        return self._sock

    @sock.setter
    def sock(self, value):
        """When modifying the socket, ensure that it is ssl wrapped."""
        if value is not None and not isinstance(value, ssl.SSLSocket):
            value = self.context.wrap_socket(value)
        self._sock = value


def ftp_download(args):
    try:
        if not os.path.exists(args.download_dir):
            os.makedirs(args.download_dir)

        downloaded_files = [f for f in os.listdir(args.download_dir) if f.endswith('.avi')]

        logger.info(f'Connecting to printer {args.user}@{args.ip}:{args.port}')
        ftp_client = ImplicitFTP_TLS()
        ftp_client.connect(host=args.ip, port=990)
        ftp_client.login(user=args.user, passwd=args.password)
        ftp_client.prot_p()
        logger.info('Connected.')
    except Exception as e:
        logger.error(f'FTP connection failed, error: "{e}"')
        sys.exit(1)

    try:
        if args.ftp_timelapse_folder in ftp_client.nlst():
            ftp_client.cwd(args.ftp_timelapse_folder)
            try:
                logger.info('Looking avi files for download.')
                ftp_timelapse_files = [f for f in ftp_client.nlst() if f.endswith('.avi')]
                ftp_timelapse_files = [f for f in ftp_timelapse_files if f not in downloaded_files]

                if ftp_timelapse_files:
                    logger.info(f'Found {len(ftp_timelapse_files)} files for download.')
                    for f in ftp_timelapse_files:
                        filesize = ftp_client.size(f)
                        filesize_mb = round(filesize/1024/1024, 2)
                        download_file_name = f
                        download_file_path = f'{args.download_dir}/{download_file_name}'
                        if filesize == 0:
                            logger.info(f'Filesize of file {f} is 0, skipping file and continue')
                            continue
                        try:
                            logger.info(f'Downloading file "{f}" size: {filesize_mb} MB')
                            fhandle = open(download_file_path, 'wb')
                            ftp_client.retrbinary('RETR %s' % f, fhandle.write)
                            if args.delete_files_from_sd_card_after_download:
                                try:
                                    ftp_client.delete(f)
                                except Exception as e:
                                    logger.error('Failed to delete file after download, continue with next file')
                                    continue
                        except Exception as e:
                            fhandle.close()
                            os.remove(download_file_path)
                            logger.error(f'failed to download file {f}: {e}, continue with next file')
                            continue
            except ftplib.error_perm as resp:
                if str(resp) == "550 No files found":
                    logger.error("No files in this directory")
                else:
                    raise
        else:
            logger.info(f'{args.ftp_timelapse_folder} not found on ftp server.')
            sys.exit(1)
    except Exception as e:
        logger.error(f'Programm failed: {e}')
        sys.exit(1)

if __name__ == '__main__':
    logger = setup_logging()

    logger.info(f'Starting bambu timelapse downloader v{version}')
    parser = argparse.ArgumentParser(description='Download bambu timelaps from printer ftp server.')
    parser.add_argument('--ip', type=str)
    parser.add_argument('--port', type=int, default=990, required=False)
    parser.add_argument('--user', type=str, default='bblp', required=False)
    parser.add_argument('--password', type=str)
    parser.add_argument('--download_dir', type=str, default=f'{application_path}/timelapse', required=False)
    parser.add_argument('--ftp_timelapse_folder', type=str, default='timelapse', required=False)
    parser.add_argument('--delete_files_from_sd_card_after_download', '-d', action='store_true')
    parser.add_argument("-v", "--version", action="version", version=f'%(prog)s - Version {version}')
    args = parser.parse_args()

    ftp_download(args)