import logging
import graypy
import sys
# Configurar o logger
logger = logging.getLogger('graylog_text_edit')
logger.setLevel(logging.DEBUG)  # Define o nível do log

# Configurar o handler para enviar logs via UDP
graylog_handler = graypy.GELFUDPHandler('graylog.buzzmonitor.com.br', )  
logger.addHandler(graylog_handler)


# --- Handler 2: Exibir logs no terminal ---
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)  # Define nível mínimo de log
console_formatter = logging.Formatter('[buzzmonitor-text-edit] %(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)
