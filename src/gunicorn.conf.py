logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,  # Mantém loggers existentes, mas sem propagação
    "handlers": {
        # Handler para o terminal (stdout)
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "detailed",
            "stream": "ext://sys.stdout",
        },
        # Handler para Graylog
        "graylog": {
            "class": "graypy.GELFUDPHandler",
            "host": "graylog.buzzmonitor.com.br",
            #"port": ,
        },
    },
    "formatters": {
    "detailed": {
        "format": "[buzzmonitor-text-edit] %(asctime)s - %(levelname)s - %(name)s - %(message)s",
    }
    },
    "root": {
        "handlers": ["graylog"],
        "level": "INFO",
    },
    "loggers": {
        # Seu logger personalizado
        "api": {
            "handlers": ["console", "graylog"],
            "level": "INFO",
            "propagate": False,  # Impede propagação para outros loggers
        },
        # Desativa logs do Gunicorn e Uvicorn
        
        "gunicorn.access": {
            "handlers": [],
            "level": "CRITICAL",
            "propagate": False,
        },
        "gunicorn.error": {
            "handlers": ["console", "graylog"],
            "level": "ERROR",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["console", "graylog"],
            "level": "ERROR",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["console", "graylog"],
            "level": "CRITICAL",
            "propagate": False,
        },
    },
}
