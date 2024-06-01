import logging
import colorlog

log_colors_config = {
    'DEBUG': 'black',  # cyan white
    'INFO': 'black',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold_red',
}

def logger_init(print_level=logging.INFO):
    # 1. Create a logger
    logger = logging.getLogger('web3_sig_auth')
    logger.setLevel(logging.DEBUG)


    # 2. Create a handler, used for writing log to file
    fh = logging.FileHandler('logs.log')
    fh.setLevel(logging.DEBUG)

    # 3. Create a handler, used for writing log to console
    ch = logging.StreamHandler()
    ch.setLevel(print_level)

    #
    #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


    # 4. Create a formatter
    fh.setFormatter(logging.Formatter('[%(asctime)s] %(name)s line:%(lineno)d [%(levelname)s]: %(message)s'))
    ch.setFormatter(
        colorlog.ColoredFormatter(
        fmt='%(log_color)s[%(asctime)s] %(name)s line:%(lineno)d [%(levelname)s]: %(message)s',
        datefmt='%Y-%m-%d  %H:%M:%S',
        log_colors=log_colors_config))

    # 5. Add handler to logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

if __name__ == '__main__':
    logger = logger_init()
    logger.name = 'test'
    logger.debug('debug message')
    logger.info('info message')
    logger.warning('warn message')
    logger.error('error message')
    logger.critical('critical message')

