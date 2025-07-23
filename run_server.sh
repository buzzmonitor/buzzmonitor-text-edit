#!/bin/bash

LOG_FILE=../log/log.txt
PID_FILE=../pids/gunicorn.pid
LOG_LEVEL=info
ENV_NAME="text-edit" #OK

if ! command -v conda &> /dev/null; then
    echo "Conda não encontrado. Instalando Miniconda..."
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
    bash ~/miniconda.sh -b -p $HOME/miniconda
    rm ~/miniconda.sh
    export PATH="$HOME/miniconda/bin:$PATH"
    conda init
    source ~/.bashrc
    echo "Miniconda instalado com sucesso."
else 
    echo "miniconda instalado"
fi

conda config --add channels defaults

if  conda env list | grep -q "^$ENV_NAME "; then
    echo "Ambiente Conda $ENV_NAME já criado. Atualizando com novas bibliotecas..."
    # Atualizar o ambiente com novas bibliotecas se o arquivo environment.yml foi modificado
    conda env update -f src/environment.yml --prune
else
    echo "criando env conda $ENV_NAME"
    conda env create -f src/environment.yml
fi

if [ ! -d log ] ; then
    mkdir log
fi

if [ ! -d pids ] ; then
    mkdir pids
fi

eval "$(conda shell.bash hook)"; #https://stackoverflow.com/questions/34534513/calling-conda-source-activate-from-bash-script
conda activate $ENV_NAME;
python -c "import sys;print(f'using python at {sys.executable}')";

# Se o .pid existir e o processo ainda estiver ativo:
# → Ele é encerrado (com kill, e se necessário kill -9), depois o .pid é removido.

# Se o .pid existir, mas o processo já morreu:
# → Apenas o .pid é removido.

# Se o .pid não existir:
# → O Gunicorn será iniciado normalmente e criará um novo .pid.

echo "verificando pids"
if [ -f "pids/gunicorn.pid" ]; then
    OLD_PID=$(cat "pids/gunicorn.pid")
    
    if ps -p "$OLD_PID" > /dev/null; then
        echo "Encontrado Gunicorn rodando com PID $OLD_PID"

        echo "Encerrando..."
        kill "$OLD_PID"
        sleep 2  # Aguarda um pouco para garantir que o processo foi encerrado
        if ps -p "$OLD_PID" > /dev/null; then
            echo "Processo $OLD_PID ainda está vivo. Forçando encerramento..."
            kill -9 "$OLD_PID"
        fi
    else
        echo "PID file existe mas o processo não está mais ativo."
    fi

    echo "Removendo PID file antigo..."
    rm -f "pids/gunicorn.pid"
else
    echo "Nenhum PID file encontrado"
fi

echo "loading env"


echo "runing service" 

# python -m gunicorn --bind :9090 --workers 3 --timeout 300 --chdir src/ src.app:app --worker-class uvicorn.workers.UvicornH11Worker --capture-output --log-level=$LOG_LEVEL --pid=$PID_FILE --log-file=$LOG_FILE --preload
python -m gunicorn -c src/gunicorn.conf.py --bind :9090 --workers 3 --timeout 300 --chdir src/ src.app:app --worker-class uvicorn.workers.UvicornH11Worker --capture-output --log-level=$LOG_LEVEL --pid=$PID_FILE --preload
    
 