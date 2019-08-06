FROM pip:latest
MAINTAINER Alex Cornford <alex.cornford@contino.io>

ENV AWS_DEFAULT_REGION="us-east-2"
ENV AWS_ACCESS_KEY_ID=""
ENV AWS_SECRET_ACCESS_KEY=""

RUN pip install boto3

ADD ./api.py .
ENTRYPOINT ["api.py"]
