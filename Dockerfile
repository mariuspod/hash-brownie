FROM --platform=linux/amd64 python:3.9.12-slim-bullseye as builder

RUN apt-get update && \
    apt-get install -y gcc

ADD requirements.txt  ./
RUN mkdir -p /install
RUN pip3 install --prefix=/install -r requirements.txt

FROM python:3.9.12-slim-bullseye
COPY --from=builder /install /usr/local

RUN mkdir -p /app/hash-brownie
WORKDIR /app/hash-brownie
ADD . /app/hash-brownie

ENTRYPOINT ["./entrypoint.sh"]
