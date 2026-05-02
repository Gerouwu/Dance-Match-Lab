FROM mambaorg/micromamba:2.3.2

WORKDIR /workspace

COPY environment.yml /tmp/environment.yml

RUN micromamba create -y -n appenv -f /tmp/environment.yml && \
    micromamba clean --all --yes

ENV MAMBA_DOCKERFILE_ACTIVATE=1
SHELL ["/usr/local/bin/_dockerfile_shell.sh"]

WORKDIR /workspace/app

COPY app/ /workspace/app/

CMD ["tail", "-f", "/dev/null"]