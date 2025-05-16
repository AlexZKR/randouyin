FROM mcr.microsoft.com/playwright:v1.52.0-noble

ENV USER=randouyin
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_DIR="/app" \
    PATH="/home/$USER/.local/bin:$PATH"

# Installing dependencies, along with make, git and python with pip
RUN apt-get update && apt-get install --no-install-recommends -y \
    && apt-get -y install git python3-pip python3-venv \
    && apt-get clean \
    # && useradd -m $USER \
    # && usermod -u 1001 -o $USER \
    # && groupmod -g 1001 -o $USER \
    # && chown -R 1001:1001 /home/$USER \
    && rm -rf /var/lib/apt/lists/*

# Setting home folder as workdir, copying dependencies files
WORKDIR $APP_DIR
COPY requirements.txt requirements-dev.txt Makefile  ./

#Switching to non-root user
# RUN chown -R $USER:$USER $APP_DIR
# USER $USER

#Creating and bootstraping venv, installing dependencies with make
RUN python3 -m venv venv \
    && . venv/bin/activate \
    && pip install --upgrade pip \
    && pip install -r requirements.txt -r requirements-dev.txt

RUN . venv/bin/activate \
    && venv/bin/playwright install --with-deps


#Append venv to path so that uvicorn and other venv packages can be executed
ENV PATH="/app/venv/bin:$PATH"

# Copying code in the end to make use of layer caching
COPY randouyin randouyin

# Running the app
CMD [ "uvicorn", "randouyin.drivers.web.main:app", "--host", "0.0.0.0", "--workers", "4", "--reload" ]
