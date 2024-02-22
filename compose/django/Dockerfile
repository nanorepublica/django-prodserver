FROM ubuntu:22.04

ARG BUILD_ENVIRONMENT=local
ARG APP_HOME=/app
ARG DEBIAN_FRONTEND=noninteractive
ARG MULTIPLE_PYTHON  # Set to True if you want to use multiple Python versions

ARG PYTHON_3_9=3.9.18
ARG PYTHON_3_10=3.10.13
ARG PYTHON_3_11=3.11.6
ARG PYTHON_3_12=3.12.0

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV BUILD_ENV ${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

# Install apt packages
RUN apt-get update
RUN apt-get install -y \
    # Some basic tools and libraries
    bash curl wget git make \
    build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev \
    libsqlite3-dev llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev \
    libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# Install pyenv
RUN git clone https://github.com/pyenv/pyenv.git .pyenv
ENV PYENV_ROOT ${APP_HOME}/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

# Install Python version(s)
RUN if [ "$MULTIPLE_PYTHON" = "True" ] ; then \
    pyenv install ${PYTHON_3_12}; \
    pyenv install ${PYTHON_3_11}; \
    pyenv install ${PYTHON_3_10}; \
    pyenv install ${PYTHON_3_9}; \
    else \
    pyenv install 3.11; \
    fi

# Initialize pyenv
RUN eval "$(pyenv init -)"

# Add deadsnakes PPA
RUN apt-get install -y software-properties-common
RUN add-apt-repository 'ppa:deadsnakes/ppa'
RUN apt-get update

# Make Python version(s) accessible in the project and install Python venv
RUN if [ "$MULTIPLE_PYTHON" = "True" ] ; then \
    apt-get install -y python3.11-venv python3.9-venv python3.10-venv python3.12-venv; \
    pyenv local ${PYTHON_3_11} ${PYTHON_3_9} ${PYTHON_3_10} ${PYTHON_3_12}; \
    else \
    apt-get install -y python3.11-venv; \
    pyenv local 3.11; \
    fi

# Ensure pip is installed
RUN apt-get install -y python3-pip

# Install Poetry
RUN pip install poetry

# Copy application files
COPY noxfile.py manage.py poetry.lock pyproject.toml ${APP_HOME}
COPY .darglint .editorconfig .flake8 .gitignore .pre-commit-config.yaml .prettierignore .readthedocs.yml bandit.yml ${APP_HOME}
COPY CHANGELOG.md CODE_OF_CONDUCT.md CONTRIBUTING.md LICENSE README.md ${APP_HOME}

COPY ./docs/ ${APP_HOME}/docs
COPY ./example_project/ ${APP_HOME}/example_project/
COPY ./tests/ ${APP_HOME}/tests/
COPY ./src/ ${APP_HOME}/
COPY ./src/ ${APP_HOME}/src/

# Install dependencies:
RUN poetry config virtualenvs.create false \
    && poetry install --with dev --no-interaction --no-ansi --no-root

# Rehash pyenv shims
RUN pyenv rehash

# Project initialization:
COPY ./compose/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

# Initialize git and add .
RUN git init
RUN git add .

ENTRYPOINT ["/entrypoint"]
