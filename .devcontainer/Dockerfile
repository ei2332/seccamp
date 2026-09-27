# Official Python devcontainer; multi-platform digest checked on 2026-09-24.
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm@sha256:7876580dc67fd460fd962f004cbeb480027e9bbc0657096f1087db11f9eaff39

USER root
# This Python lesson does not use Yarn. Its inherited apt source has an
# expired/missing signing key that can prevent apt-get update.
RUN if [ -f /etc/apt/sources.list.d/yarn.list ]; then \
      mv /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/yarn.list.disabled; \
    fi
COPY pylock.toml /tmp/pylock.toml
RUN python -m venv /opt/lesson-venv \
    && /opt/lesson-venv/bin/python -m pip install --no-cache-dir pip==26.2.1 \
    && /opt/lesson-venv/bin/python -m pip install --no-cache-dir -r /tmp/pylock.toml \
    && /opt/lesson-venv/bin/python -m pip check

ENV PATH="/opt/lesson-venv/bin:${PATH}"
ENV VIRTUAL_ENV="/opt/lesson-venv"
ENV SEMGREP_SEND_METRICS="off"

# Login/interactive shells can reset the image PATH. Restore the lesson venv
# after shell initialization so terminals use the installed lesson packages.
RUN printf '%s\n' \
      'export VIRTUAL_ENV=/opt/lesson-venv' \
      'export PATH="/opt/lesson-venv/bin:$PATH"' \
      > /etc/profile.d/99-lesson-venv.sh \
    && printf '\n. /etc/profile.d/99-lesson-venv.sh\n' >> /home/vscode/.bashrc \
    && printf '\n. /etc/profile.d/99-lesson-venv.sh\n' >> /home/vscode/.zshrc

USER vscode
