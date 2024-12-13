
# base image
FROM python:3.10-bullseye AS base

# ENV  http_proxy = \
#      https_proxy = \
#      no_proxy =

# COPY proxy.conf /etc/apt/apt.conf.d/proxy.conf

# ENV REQUESTS_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"\
#     CURL_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"\
#     SSL_CERT_FILE="/etc/ssl/certs/ca-certificates.crt"\
#     GPRC_DEFAULT_SSL_ROOTS_FILE_PATH="/etc/ssl/certs/ca-certificates.crt"\
#     NODE_EXTRA_CA_CERTS="/etc/ssl/certs/ca-certificates.crt"

# COPY ca_cert_chain.pem /usr/local/share/ca-certificates/ca-bundle.crt
# RUN update-ca-certificates

# upgrading packages
RUN apt-get update -y \
    && apt-get dist-upgrade -y \
    && apt-get install curl lsb-release unzip -y


# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install


# Install Node.js and npm
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs

# Install AWS CDK
RUN npm install -g aws-cdk


# Installing packages
# RUN mkdir -p /home/md-user/wrkdir
# COPY ./requirements-dev.txt /home/md-user/wrkdir
# RUN python3 -m pip install -r /home/md-user/wrkdir/requirements-dev.txt


