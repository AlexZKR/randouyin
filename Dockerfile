FROM mcr.microsoft.com/playwright:v1.52.0-noble

ENV USER=randouyin
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_DIR="/app" \
    PATH="/home/$USER/.local/bin:$PATH"

RUN apt-get update && apt-get install --no-install-recommends -y \
    && apt-get -y install make git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1001 $USER


WORKDIR $APP_DIR
COPY requirements.txt requirements-dev.txt Makefile  ./
RUN chown -R $USER:$USER $APP_DIR
USER $USER

RUN make requirements
COPY randouyin randouyin

CMD [ "uvicorn", "randouyin.drivers.web.main:app", "--host", "0.0.0.0", "--workers", "4", "--reload" ]
